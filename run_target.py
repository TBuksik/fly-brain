"""Run a position-feedback experiment with direct P9 stimulation."""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from brain_session import BrainSession
from movement_controller import MovementController
from target_controller import TargetController


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("constant", "decreasing"),
        default="decreasing",
    )
    parser.add_argument("--seed", type=int, default=45)
    parser.add_argument("--target", type=float, default=1.0)
    args = parser.parse_args()

    controller = TargetController(target=args.target, mode=args.mode)
    brain = BrainSession(experiment="p9", seed=args.seed)
    movement = MovementController(brain.input_indices)
    reached_ms = None
    rows = []

    print("Czas [ms] | Bodziec [Hz] | Impulsy P9 | Pozycja")

    for _ in range(100):
        start = brain.time_ms
        rate = controller.stimulus(movement.position)
        brain.set_stimulus(rate)

        counts = brain.advance(10)
        displacement = movement.update(counts)
        spikes = sum(int(counts[i]) for i in movement.neuron_indices)

        if reached_ms is None and movement.position >= args.target - 1e-9:
            reached_ms = brain.time_ms

        rows.append({
            "seed": args.seed,
            "mode": args.mode,
            "target": args.target,
            "start_ms": start,
            "end_ms": brain.time_ms,
            "stimulus_hz": rate,
            "p9_spikes": spikes,
            "displacement": displacement,
            "position": movement.position,
        })

        print(
            f"{start:5.0f}–{brain.time_ms:5.0f} | "
            f"{rate:12.2f} | {spikes:10} | "
            f"{movement.position:7.2f}",
            flush=True,
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (
        Path(__file__).resolve().parent
        / "data/results/target"
        / f"{args.mode}-seed{args.seed}-{stamp}.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("\nMetoda:", args.mode)
    print("Seed:", args.seed)
    print("Cel:", args.target)
    print("Granica celu osiągnięta/przekroczona po [ms]:", reached_ms)
    print("Końcowa pozycja:", round(movement.position, 4))
    print("Przekroczenie:", round(max(0, movement.position - args.target), 4))
    print("Zapisano:", output)


if __name__ == "__main__":
    main()
