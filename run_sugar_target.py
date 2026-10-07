"""Prototype position feedback using sugar input and DNg103 readout."""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from brain_session import BrainSession
from movement_controller import MovementController
from target_controller import TargetController


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=45)
    parser.add_argument("--target", type=float, default=1.0)
    parser.add_argument("--min-rate", type=float, default=50.0)
    args = parser.parse_args()

    controller = TargetController(
        target=args.target,
        max_rate_hz=200,
        min_rate_hz=args.min_rate,
        mode="decreasing",
    )
    brain = BrainSession(experiment="sugar", seed=args.seed)

    output_ids = (720575940635179871, 720575940606866377)
    assert all(n not in brain.input_ids for n in output_ids)
    indices = [brain.id_to_index[n] for n in output_ids]
    movement = MovementController(indices)

    rows = []
    reached_ms = None

    for _ in range(100):
        start = brain.time_ms
        rate = controller.stimulus(movement.position)
        brain.set_stimulus(rate)
        counts = brain.advance(10)
        displacement = movement.update(counts)

        if (
            reached_ms is None
            and movement.position >= args.target - 1e-9
        ):
            reached_ms = brain.time_ms

        rows.append({
            "seed": args.seed,
            "target": args.target,
            "min_rate_hz": args.min_rate,
            "start_ms": start,
            "end_ms": brain.time_ms,
            "sugar_hz": rate,
            "dng103_left_spikes": int(counts[indices[0]]),
            "dng103_right_spikes": int(counts[indices[1]]),
            "displacement": displacement,
            "position": movement.position,
        })

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (
        Path(__file__).resolve().parent
        / "data/results/sugar_target"
        / f"seed{args.seed}-{stamp}.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("Seed:", args.seed)
    print("Cel:", args.target)
    print("Minimalne pobudzenie [Hz]:", args.min_rate)
    print("Granica celu osiągnięta/przekroczona po [ms]:", reached_ms)
    print("Końcowa pozycja:", round(movement.position, 4))
    print("Przekroczenie:", round(
        max(0, movement.position - args.target), 4
    ))
    print("Impulsy DNg103:", movement.total_spikes)
    print("Zapisano:", output)


if __name__ == "__main__":
    main()
