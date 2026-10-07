"""Step-by-step sugar environment with a stateful brain."""

import math

from brain_session import BrainSession
from movement_controller import MovementController
from sugar_environment import SugarEnvironment


class EnvironmentSession:
    STEP_MS = 10
    OUTPUT_IDS = (720575940635179871, 720575940606866377)

    def __init__(
        self,
        seed=42,
        region_start=0.0,
        region_end=1.0,
        region_rate=200.0,
        start_position=0.0,
    ):
        start_position = float(start_position)
        if not math.isfinite(start_position):
            raise ValueError("Initial position must be finite.")

        self.environment = SugarEnvironment(
            start=region_start,
            end=region_end,
            rate_hz=region_rate,
        )
        self.brain = BrainSession(experiment="sugar", seed=seed)
        self.indices = [
            self.brain.id_to_index[n] for n in self.OUTPUT_IDS
        ]
        self.movement = MovementController(self.indices)
        self.movement.position = start_position
        self.seed = seed
        self.initial_position = start_position
        self.exit_ms = (
            0.0
            if start_position >= self.environment.end - 1e-9
            else None
        )

    def step(self):
        start = self.brain.time_ms
        position_before = self.movement.position
        rate = self.environment.stimulus(position_before)
        self.brain.set_stimulus(rate)

        counts = self.brain.advance(self.STEP_MS)
        displacement = self.movement.update(counts)

        if (
            self.exit_ms is None
            and self.movement.position >= self.environment.end - 1e-9
        ):
            self.exit_ms = self.brain.time_ms

        return {
            "seed": self.seed,
            "initial_position": self.initial_position,
            "region_start": self.environment.start,
            "region_end": self.environment.end,
            "region_rate_hz": self.environment.rate_hz,
            "distance_per_spike": self.movement.distance_per_spike,
            "start_ms": start,
            "end_ms": self.brain.time_ms,
            "position_before": position_before,
            "sugar_hz": rate,
            "dng103_left_spikes": int(counts[self.indices[0]]),
            "dng103_right_spikes": int(counts[self.indices[1]]),
            "displacement": displacement,
            "position": self.movement.position,
        }
