"""A one-dimensional sugar region for the prototype environment."""

import math


class SugarEnvironment:
    def __init__(self, start=0.0, end=1.0, rate_hz=200.0):
        self.start = float(start)
        self.end = float(end)
        self.rate_hz = float(rate_hz)

        if not all(math.isfinite(v) for v in (
            self.start, self.end, self.rate_hz
        )):
            raise ValueError("Parameters must be finite.")
        if self.end <= self.start or self.rate_hz < 0:
            raise ValueError("Invalid region or stimulation rate.")

    def stimulus(self, position):
        position = float(position)
        if not math.isfinite(position):
            raise ValueError("Position must be finite.")

        return (
            self.rate_hz
            if self.start - 1e-9 <= position < self.end - 1e-9
            else 0.0
        )
