"""Run two sugar stimulation pulses with continuous brain state."""

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path

from environment_session import EnvironmentSession


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    session = EnvironmentSession(
        seed=args.seed,
        region_end=2.0,
    )
    rows = []

    print("Czas [ms] | Cukier [Hz] | DNg103 lewy | DNg103 prawy | Pozycja")

    for rate in (200.0, 0.0, 200.0):
        session.environment.rate_hz = rate

        for _ in range(3):
            row = session.step()
            rows.append(row)
            print(
                f"{row['start_ms']:5.0f}–{row['end_ms']:5.0f} | "
                f"{row['sugar_hz']:11.0f} | "
                f"{row['dng103_left_spikes']:11} | "
                f"{row['dng103_right_spikes']:12} | "
                f"{row['position']:7.2f}",
                flush=True,
            )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (
        Path(__file__).resolve().parent
        / "data/results/environment"
        / f"pulses-seed{args.seed}-{stamp}.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("\nCzas:", session.brain.time_ms, "ms")
    print("Impulsy DNg103:", session.movement.total_spikes)
    print("Końcowa pozycja:", round(session.movement.position, 4))
    print("Zapisano:", output)


if __name__ == "__main__":
    main()
