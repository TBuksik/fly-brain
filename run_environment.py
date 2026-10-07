"""Run a prototype sugar-region environment with DNg103 readout."""

import argparse
import csv
import math
from datetime import datetime, timezone
from pathlib import Path

from brain_session import BrainSession
from movement_controller import MovementController
from sugar_environment import SugarEnvironment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--region-start", type=float, default=0.0)
    parser.add_argument("--region-end", type=float, default=1.0)
    parser.add_argument("--region-rate", type=float, default=200.0)
    parser.add_argument("--start-position", type=float, default=0.0)
    args = parser.parse_args()
    if not math.isfinite(args.start_position):
        parser.error("--start-position must be finite")

    brain = BrainSession(experiment="sugar", seed=args.seed)
    output_ids = (720575940635179871, 720575940606866377)
    indices = [brain.id_to_index[n] for n in output_ids]
    movement = MovementController(indices)
    movement.position = args.start_position
    environment = SugarEnvironment(
        start=args.region_start,
        end=args.region_end,
        rate_hz=args.region_rate,
    )
    rows = []
    exit_ms = (
        0.0 if movement.position >= environment.end - 1e-9 else None
    )

    for _ in range(30):
        start = brain.time_ms
        position_before = movement.position
        rate = environment.stimulus(position_before)
        brain.set_stimulus(rate)

        counts = brain.advance(10)
        displacement = movement.update(counts)

        if exit_ms is None and movement.position >= environment.end - 1e-9:
            exit_ms = brain.time_ms

        rows.append({
            "seed": args.seed,
            "initial_position": args.start_position,
            "region_start": environment.start,
            "region_end": environment.end,
            "region_rate_hz": environment.rate_hz,
            "distance_per_spike": movement.distance_per_spike,
            "start_ms": start,
            "end_ms": brain.time_ms,
            "position_before": position_before,
            "sugar_hz": rate,
            "dng103_left_spikes": int(counts[indices[0]]),
            "dng103_right_spikes": int(counts[indices[1]]),
            "displacement": displacement,
            "position": movement.position,
        })

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (
        Path(__file__).resolve().parent
        / "data/results/environment"
        / f"seed{args.seed}-{stamp}.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    stimulated = False
    off_row = None
    for row in rows:
        if row["sugar_hz"] > 0:
            stimulated = True
        elif stimulated:
            off_row = row
            break

    print("Seed:", args.seed)
    if off_row is not None:
        print("Wyłączenie bodźca [ms]:", off_row["start_ms"])
        print(
            "Pozycja przy wyłączeniu:",
            round(off_row["position_before"], 4),
        )
        print(
            "Ruch po wyłączeniu:",
            round(movement.position - off_row["position_before"], 4),
        )
    elif stimulated:
        print("Bodziec nie został wyłączony w zapisanym przebiegu.")
    else:
        print("Bodziec był wyłączony przez cały przebieg.")
    print("Wyjście z obszaru odnotowane po [ms]:", exit_ms)
    print("Końcowa pozycja:", round(movement.position, 4))
    print("Impulsy DNg103:", movement.total_spikes)
    print("Liczba zapisanych kroków:", len(rows))
    print("Zapisano:", output)


if __name__ == "__main__":
    main()
