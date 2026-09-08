"""One Euro filter (Casiez, Roussel, Vogel 2012). Adapts its cutoff frequency
to the signal's speed: heavy smoothing when nearly still (kills jitter for
precision work), light smoothing when moving fast (keeps latency low so the
cursor doesn't lag). This is what makes cursor mode feel responsive instead
of laggy or twitchy — see ADR-008."""

from __future__ import annotations

import math


class _LowPassFilter:
    def __init__(self, alpha: float) -> None:
        self._alpha = alpha
        self._y: float | None = None
        self._s: float | None = None

    def set_alpha(self, alpha: float) -> None:
        if not (0.0 < alpha <= 1.0):
            raise ValueError(f"alpha must be in (0, 1], got {alpha}")
        self._alpha = alpha

    def __call__(self, value: float, alpha: float | None = None) -> float:
        if alpha is not None:
            self.set_alpha(alpha)
        s = value if self._y is None else self._alpha * value + (1.0 - self._alpha) * self._s
        self._y = value
        self._s = s
        return s

    def last_value(self) -> float | None:
        return self._y


class OneEuroFilter:
    def __init__(
        self,
        freq: float,
        mincutoff: float = 1.0,
        beta: float = 0.007,
        dcutoff: float = 1.0,
    ) -> None:
        if freq <= 0:
            raise ValueError("freq must be positive")
        self.freq = freq
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff
        self._x_filt = _LowPassFilter(self._alpha(mincutoff))
        self._dx_filt = _LowPassFilter(self._alpha(dcutoff))
        self._last_timestamp: float | None = None

    def _alpha(self, cutoff: float) -> float:
        te = 1.0 / self.freq
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def __call__(self, x: float, timestamp: float | None = None) -> float:
        if timestamp is not None and self._last_timestamp is not None:
            dt = timestamp - self._last_timestamp
            if dt > 0:
                self.freq = 1.0 / dt
        if timestamp is not None:
            self._last_timestamp = timestamp

        prev_x = self._x_filt.last_value()
        dx = 0.0 if prev_x is None else (x - prev_x) * self.freq
        edx = self._dx_filt(dx, alpha=self._alpha(self.dcutoff))

        cutoff = self.mincutoff + self.beta * abs(edx)
        return self._x_filt(x, alpha=self._alpha(cutoff))


class Vec2Filter:
    """Wraps two OneEuroFilter instances for (x, y) points."""

    def __init__(
        self,
        freq: float,
        mincutoff: float = 1.0,
        beta: float = 0.007,
        dcutoff: float = 1.0,
    ) -> None:
        self._fx = OneEuroFilter(freq, mincutoff, beta, dcutoff)
        self._fy = OneEuroFilter(freq, mincutoff, beta, dcutoff)

    def __call__(self, point: tuple[float, float], timestamp: float | None = None) -> tuple[float, float]:
        x, y = point
        return self._fx(x, timestamp), self._fy(y, timestamp)
