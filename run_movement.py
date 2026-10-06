"""Run a P9 stimulation experiment and save movement measurements."""

import csv
from pathlib import Path

from brain_session import BrainSession
from movement_controller import MovementController


def main():
    brain = BrainSession(experiment="p9", seed=42)
    movement = MovementController(brain.input_indices)
    rows = []

    print("Czas [ms] | Bodziec [Hz] | Impulsy P9 | Pozycja")

    for duration, rate in ((50, 0), (100, 100), (200, 0)):
        brain.set_stimulus(rate)

        for _ in range(duration // 25):
            start = brain.time_ms
            counts = brain.advance(25)
            displacement = movement.update(counts)

            rows.append({
                "start_ms": start,
                "end_ms": brain.time_ms,
                "stimulus_hz": rate,
                "p9_spikes": sum(
                    int(counts[i]) for i in movement.neuron_indices
                ),
                "displacement": displacement,
                "position": movement.position,
            })

            print(
                f"{start:5.0f}–{brain.time_ms:5.0f} | "
                f"{rate:12} | "
                f"{rows[-1]['p9_spikes']:10} | "
                f"{movement.position:7.2f}",
                flush=True,
            )

    output = (
        Path(__file__).resolve().parent
        / "data/results/movement/p9-seed42.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("\nZapisano:", output)
    print("Łącznie impulsów P9:", movement.total_spikes)
    print("Końcowa pozycja:", round(movement.position, 2))


if __name__ == "__main__":
    main()
