"""Choose stimulation frequency from the current position."""

import math


class TargetController:
    def __init__(self, target=1.0, max_rate_hz=100.0, mode="decreasing", min_rate_hz=0.0):
        self.target = float(target)
        self.max_rate_hz = float(max_rate_hz)
        self.mode = mode

        if not math.isfinite(self.target) or self.target <= 0:
            raise ValueError("Target must be positive and finite.")
        if not math.isfinite(self.max_rate_hz) or self.max_rate_hz < 0:
            raise ValueError("Maximum rate must be nonnegative and finite.")
        self.min_rate_hz = float(min_rate_hz)
        if (
            not math.isfinite(self.min_rate_hz)
            or not 0 <= self.min_rate_hz <= self.max_rate_hz
        ):
            raise ValueError("Minimum rate must be between zero and maximum.")

        if mode not in ("constant", "decreasing"):
            raise ValueError("Mode must be constant or decreasing.")

    def stimulus(self, position):
        position = float(position)
        if not math.isfinite(position):
            raise ValueError("Position must be finite.")

        remaining = self.target - position
        if remaining <= 1e-9:
            return 0.0

        if self.mode == "constant":
            return self.max_rate_hz

        fraction = min(1.0, remaining / self.target)
        return max(self.min_rate_hz, self.max_rate_hz * fraction)
