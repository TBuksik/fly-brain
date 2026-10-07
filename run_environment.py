"""Run a prototype sugar-region environment with DNg103 readout."""

import argparse
import csv
import math
from datetime import datetime, timezone
from pathlib import Path

from environment_session import EnvironmentSession


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duration-ms", type=int, default=300)
    parser.add_argument("--region-start", type=float, default=0.0)
    parser.add_argument("--region-end", type=float, default=1.0)
    parser.add_argument("--region-rate", type=float, default=200.0)
    parser.add_argument("--start-position", type=float, default=0.0)
    args = parser.parse_args()
    if args.duration_ms <= 0 or args.duration_ms % 10 != 0:
        parser.error("--duration-ms must be positive and a multiple of 10")
    if not math.isfinite(args.start_position):
        parser.error("--start-position must be finite")

    session = EnvironmentSession(
        seed=args.seed,
        region_start=args.region_start,
        region_end=args.region_end,
        region_rate=args.region_rate,
        start_position=args.start_position,
    )
    rows = [
        session.step()
        for _ in range(args.duration_ms // session.STEP_MS)
    ]
    movement = session.movement
    exit_ms = session.exit_ms

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
