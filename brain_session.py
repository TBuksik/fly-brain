"""Stateful interface to the existing PyTorch fly-brain model."""

import sys
import math
from pathlib import Path

import pyarrow  # Import before torch, as required by the existing runner.
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent / "code"))

from benchmark import get_experiment, path_comp, path_con, path_wt
from run_pytorch import TorchModel, MODEL_PARAMS, DT, get_hash_tables, get_weights


class BrainSession:
    def __init__(self, experiment="sugar", seed=42):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.config = get_experiment(experiment)
        self.id_to_index, _ = get_hash_tables(str(path_comp))
        self.input_ids = tuple(self.config["neu_exc"])
        self.input_indices = [
            self.id_to_index[neuron] for neuron in self.input_ids
        ]

        weights = get_weights(
            str(path_con), str(path_comp), str(path_wt), csr=True
        ).to(self.device)

        self.model = TorchModel(
            batch=1,
            size=weights.shape[0],
            dt=DT,
            params=MODEL_PARAMS,
            weights=weights,
            exc_indices=self.input_indices,
            device=self.device,
        )
        self.model.eval()
        self.rates = torch.zeros(1, weights.shape[0], device=self.device)
        self.generator = torch.Generator(device=self.device)
        self.reset(seed)

    def reset(self, seed=42):
        self.state = self.model.state_init()
        self.rates.zero_()
        self.steps = 0
        self.generator.manual_seed(seed)

    def set_stimulus(self, rate_hz):
        rate_hz = float(rate_hz)
        if not math.isfinite(rate_hz) or not 0 <= rate_hz <= 1000 / DT:
            raise ValueError("Invalid stimulus frequency.")
        self.rates.zero_()
        self.rates[:, self.input_indices] = rate_hz

    @torch.no_grad()
    def advance(self, duration_ms):
        duration_ms = float(duration_ms)
        if not math.isfinite(duration_ms) or duration_ms <= 0:
            raise ValueError("Duration must be positive and finite.")
        steps = round(duration_ms / DT)
        if steps < 1 or not math.isclose(
            steps * DT, duration_ms, rel_tol=0, abs_tol=1e-8
        ):
            raise ValueError(f"Duration must be a multiple of {DT} ms.")

        counts = torch.zeros(
            self.rates.shape[1], dtype=torch.int64, device=self.device
        )
        for _ in range(steps):
            self.state = self.model(
                self.rates, *self.state, generator=self.generator
            )
            counts += (self.state[2][0] > 0).to(torch.int64)

        self.steps += steps
        return counts.cpu()

    @property
    def time_ms(self):
        return self.steps * DT


if __name__ == "__main__":
    print("Loading brain...")
    brain = BrainSession()

    # The same random input must give the same result whether
    # we advance once for 100 ms or twice for 50 ms.
    brain.set_stimulus(200)
    whole = brain.advance(100)

    brain.reset()
    brain.set_stimulus(200)
    first = brain.advance(50)
    second = brain.advance(50)

    assert torch.equal(whole, first + second), (
        "Splitting the simulation changed the result."
    )
    print("OK: 100 ms and 50 + 50 ms give identical spike counts.")
    print("Time:", brain.time_ms, "ms")
    print("Active neurons:", int((whole > 0).sum()))
    print("Spikes:", int(whole.sum()))

    brain.reset()
    silent = brain.advance(100)
    assert int(silent.sum()) == 0, "Unexpected spikes without stimulus."
    print("OK: fresh brain without stimulus is silent.")
