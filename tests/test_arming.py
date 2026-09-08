from __future__ import annotations

from elara.core.arming import ArmingGate


def _hold(gate: ArmingGate, pose_id: str, confidence: float, n_frames: int, dt_ms: float, start_ms: float = 0.0):
    """Feeds n_frames of the same pose at dt_ms spacing; returns the list of
    non-None fire results (in order)."""
    fires = []
    t = start_ms
    for _ in range(n_frames):
        result = gate.update(pose_id, confidence, t)
        if result is not None:
            fires.append(result)
        t += dt_ms
    return fires


def test_flickering_below_vote_threshold_never_fires():
    gate = ArmingGate(confidence_floor=0.7, vote_n=4, vote_m=6, dwell_ms=100, cooldown_ms=500)
    t = 0.0
    fires = []
    for i in range(30):
        pose = "fist" if i % 2 == 0 else None  # alternates every frame: 3/6 votes, below vote_n=4
        conf = 0.9 if pose else 0.0
        result = gate.update(pose, conf, t)
        if result:
            fires.append(result)
        t += 33.0
    assert fires == []


def test_stable_pose_fires_once_and_not_again_until_cooldown_elapses():
    gate = ArmingGate(confidence_floor=0.7, vote_n=4, vote_m=6, dwell_ms=100, cooldown_ms=500)

    # Hold long enough to pass vote + dwell -> exactly one fire.
    fires = _hold(gate, "fist", 0.9, n_frames=10, dt_ms=33.0, start_ms=0.0)
    assert fires == ["fist"]

    # Release (drop below floor) then immediately re-acquire, well within
    # the 500ms cooldown -> must not fire again.
    gate.update(None, 0.0, 330.0)
    fires_again = _hold(gate, "fist", 0.9, n_frames=6, dt_ms=10.0, start_ms=340.0)
    assert fires_again == []

    # Release, wait past cooldown, then re-acquire -> fires again.
    gate.update(None, 0.0, 900.0)
    fires_after_cooldown = _hold(gate, "fist", 0.9, n_frames=10, dt_ms=33.0, start_ms=1000.0)
    assert fires_after_cooldown == ["fist"]


def test_continuous_hold_fires_at_most_once_even_past_cooldown():
    """The scenario T017's engine test relies on: 200 synth frames of a
    stationary held pose must emit at most one event, even though 200
    frames at 30fps (~6.7s) is far longer than an 800ms cooldown."""
    gate = ArmingGate(confidence_floor=0.72, vote_n=4, vote_m=6, dwell_ms=250, cooldown_ms=800)
    fires = _hold(gate, "open_palm", 0.95, n_frames=200, dt_ms=33.0)
    assert len(fires) <= 1


def test_active_zone_fires_only_inside():
    def in_right_half(position: tuple[float, float]) -> bool:
        return position[0] >= 0.5

    gate = ArmingGate(confidence_floor=0.7, vote_n=2, vote_m=3, dwell_ms=50, cooldown_ms=200, active_zone=in_right_half)

    t = 0.0
    fires_outside = []
    for _ in range(10):
        result = gate.update("point", 0.9, t, position=(0.1, 0.5))
        if result:
            fires_outside.append(result)
        t += 20.0
    assert fires_outside == []

    fires_inside = []
    for _ in range(10):
        result = gate.update("point", 0.9, t, position=(0.9, 0.5))
        if result:
            fires_inside.append(result)
        t += 20.0
    assert fires_inside == ["point"]


def test_low_confidence_never_passes_floor():
    gate = ArmingGate(confidence_floor=0.7, vote_n=2, vote_m=3, dwell_ms=50, cooldown_ms=200)
    fires = _hold(gate, "fist", 0.5, n_frames=20, dt_ms=20.0)
    assert fires == []
