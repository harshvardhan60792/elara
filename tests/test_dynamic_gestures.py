"""Drives DynamicGestureDetector frame-by-frame against the motion fixtures
from scripts/synth_landmarks.py (docs/PLAN.md T016 accept criteria)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from elara.vision.dynamic_gestures import DynamicGestureDetector
from elara.vision.features import raw_hand_span, raw_palm_center

FIXTURES = Path(__file__).parent / "fixtures" / "landmarks"

pytestmark = pytest.mark.skipif(not FIXTURES.exists(), reason="run scripts/synth_landmarks.py first")


def _drive(fixture_name: str, detector: DynamicGestureDetector | None = None) -> list[str]:
    detector = detector or DynamicGestureDetector()
    frames = json.loads((FIXTURES / f"{fixture_name}.json").read_text())
    results = []
    for frame in frames:
        landmarks = frame["landmarks"]
        if landmarks is None:
            continue
        landmarks = np.array(landmarks)
        center = raw_palm_center(landmarks)
        span = raw_hand_span(landmarks)
        result = detector.update(frame["t"], center, span)
        if result:
            results.append(result)
    return results


@pytest.mark.parametrize(
    "fixture_name,expected",
    [
        ("swipe_left", "swipe_left"),
        ("swipe_right", "swipe_right"),
        ("swipe_up", "swipe_up"),
        ("swipe_down", "swipe_down"),
        ("circle_cw", "circle_cw"),
        ("circle_ccw", "circle_ccw"),
        ("push", "push"),
    ],
)
def test_motion_fixture_classifies_correctly(fixture_name: str, expected: str):
    results = _drive(fixture_name)
    assert results == [expected], f"{fixture_name} -> {results}, expected [{expected}]"


def test_swipe_left_and_swipe_right_are_opposite_directions():
    left = _drive("swipe_left")
    right = _drive("swipe_right")
    assert left == ["swipe_left"]
    assert right == ["swipe_right"]
    assert left != right


def test_slow_drift_negative_classifies_as_nothing():
    results = _drive("neg_slow_drift")
    assert results == []


def test_one_physical_swipe_never_fires_twice():
    # Continue feeding the fixture's final (stationary) frame after the
    # swipe completes — a real re-detection race would double-fire here.
    detector = DynamicGestureDetector()
    results = _drive("swipe_left", detector)
    frames = json.loads((FIXTURES / "swipe_left.json").read_text())
    last = frames[-1]
    last_landmarks = np.array(last["landmarks"])
    center = raw_palm_center(last_landmarks)
    span = raw_hand_span(last_landmarks)
    for i in range(10):
        extra = detector.update(last["t"] + 0.05 * (i + 1), center, span)
        if extra:
            results.append(extra)
    assert results == ["swipe_left"]
