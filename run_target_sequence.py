"""Run two successive targets without resetting brain or position."""

import csv
from datetime import datetime, timezone
from pathlib import Path

from brain_session import BrainSession
from movement_controller import MovementController
from target_controller import TargetController


def main():
    brain = BrainSession(experiment="p9", seed=45)
    movement = MovementController(brain.input_indices)
    rows = []

    for target in (1.0, 2.0):
        controller = TargetController(target=target, mode="decreasing")
        stage_start = brain.time_ms
        reached_ms = None

        for _ in range(100):
            start = brain.time_ms
            rate = controller.stimulus(movement.position)
            brain.set_stimulus(rate)
            counts = brain.advance(10)
            displacement = movement.update(counts)

            if reached_ms is None and movement.position >= target - 1e-9:
                reached_ms = brain.time_ms

            rows.append({
                "seed": 45,
                "target": target,
                "start_ms": start,
                "end_ms": brain.time_ms,
                "stimulus_hz": rate,
                "p9_spikes": sum(
                    int(counts[i]) for i in movement.neuron_indices
                ),
                "displacement": displacement,
                "position": movement.position,
            })

        duration = (
            reached_ms - stage_start
            if reached_ms is not None else None
        )
        print(
            f"Cel: {target:.2f} | "
            f"Czas dojścia: {duration} ms | "
            f"Pozycja: {movement.position:.2f}",
            flush=True,
        )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = (
        Path(__file__).resolve().parent
        / "data/results/target"
        / f"sequence-seed45-{stamp}.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("x", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print("Zapisano:", output)


if __name__ == "__main__":
    main()
