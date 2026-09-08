from __future__ import annotations

import numpy as np

from elara.vision.smoothing import OneEuroFilter, Vec2Filter


def test_step_input_converges():
    f = OneEuroFilter(freq=30.0, mincutoff=1.0, beta=0.007)
    t = 0.0
    dt = 1.0 / 30.0
    out = 0.0
    for _ in range(60):
        out = f(1.0, t)
        t += dt
    assert abs(out - 1.0) < 0.02


def test_noisy_stationary_signal_variance_reduced():
    rng = np.random.default_rng(42)
    signal = 5.0 + rng.normal(0, 0.05, size=200)

    f = OneEuroFilter(freq=30.0, mincutoff=1.0, beta=0.007)
    t = 0.0
    dt = 1.0 / 30.0
    out = []
    for x in signal:
        out.append(f(float(x), t))
        t += dt

    assert np.var(out) < np.var(signal)


def test_fast_ramp_lags_within_budget():
    freq = 60.0
    dt = 1.0 / freq
    f = OneEuroFilter(freq=freq, mincutoff=1.0, beta=0.5)

    t = 0.0
    true_value = 0.0
    filtered = 0.0
    for _ in range(120):
        true_value += 0.05  # fast ramp
        filtered = f(true_value, t)
        t += dt

    lag = true_value - filtered
    assert lag < 0.5, f"lag too large: {lag}"


def test_vec2_filter_tracks_point():
    f = Vec2Filter(freq=30.0)
    t = 0.0
    dt = 1.0 / 30.0
    out = (0.0, 0.0)
    for _ in range(60):
        out = f((2.0, -3.0), t)
        t += dt
    assert abs(out[0] - 2.0) < 0.02
    assert abs(out[1] - (-3.0)) < 0.02
