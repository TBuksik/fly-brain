"""Simple one-dimensional movement driven by observed spikes."""

import math


class MovementController:
    def __init__(self, neuron_indices, distance_per_spike=0.1):
        self.neuron_indices = tuple(neuron_indices)
        self.distance_per_spike = float(distance_per_spike)

        if not self.neuron_indices:
            raise ValueError("At least one neuron is required.")
        if not math.isfinite(self.distance_per_spike):
            raise ValueError("Distance per spike must be finite.")

        self.reset()

    def reset(self):
        self.position = 0.0
        self.total_spikes = 0

    def update(self, counts):
        spikes = sum(int(counts[i]) for i in self.neuron_indices)
        movement = spikes * self.distance_per_spike

        self.total_spikes += spikes
        self.position += movement
        return movement
