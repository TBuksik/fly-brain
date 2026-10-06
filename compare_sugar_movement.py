from brain_session import BrainSession
from movement_controller import MovementController
from target_controller import TargetController

brain = BrainSession(input_groups=("sugar", "p9"))
sugar_ids = brain.input_groups["sugar"]
p9_ids = brain.input_groups["p9"]
p9_indices = [brain.id_to_index[n] for n in p9_ids]

print("Seed | Cukier [Hz] | Czas dojścia [ms] | Pozycja")

for seed in (42, 43, 44, 45, 46):
    for sugar_rate in (0, 200):
        brain.reset(seed=seed)
        movement = MovementController(p9_indices)
        controller = TargetController(target=1.0, mode="decreasing")
        reached_ms = None

        for _ in range(100):
            p9_rate = controller.stimulus(movement.position)
            rates = {n: sugar_rate for n in sugar_ids}
            rates.update({n: p9_rate for n in p9_ids})
            brain.set_stimuli(rates)

            movement.update(brain.advance(10))

            if reached_ms is None and movement.position >= 1.0 - 1e-9:
                reached_ms = brain.time_ms

        time_text = (
            f"{reached_ms:.0f}" if reached_ms is not None else "brak"
        )
        print(
            f"{seed:4} | {sugar_rate:11} | "
            f"{time_text:17} | {movement.position:.2f}",
            flush=True,
        )
