"""Run a prototype sugar-region environment with DNg103 readout."""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from brain_session import BrainSession
from movement_controller import MovementController
from sugar_environment import SugarEnvironment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    brain = BrainSession(experiment="sugar", seed=args.seed)
    output_ids = (720575940635179871, 720575940606866377)
    indices = [brain.id_to_index[n] for n in output_ids]
    movement = MovementController(indices)
    environment = SugarEnvironment()
    rows = []
    exit_ms = None

    for _ in range(30):
        start = brain.time_ms
        position_before = movement.position
        rate = environment.stimulus(position_before)
        brain.set_stimulus(rate)

        counts = brain.advance(10)
        displacement = movement.update(counts)

        if exit_ms is None and movement.position >= environment.end:
            exit_ms = brain.time_ms

        rows.append({
            "seed": args.seed,
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

    print("Seed:", args.seed)
    print("Wyjście z obszaru odnotowane po [ms]:", exit_ms)
    print("Końcowa pozycja:", round(movement.position, 4))
    print("Impulsy DNg103:", movement.total_spikes)
    print("Liczba zapisanych kroków:", len(rows))
    print("Zapisano:", output)


if __name__ == "__main__":
    main()
