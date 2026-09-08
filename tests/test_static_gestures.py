"""Classifies every fixture from scripts/synth_landmarks.py and checks it
against its expected pose id — the single most important test file in the
project (docs/PLAN.md T014)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from elara.config import VisionConfig
from elara.vision.features import extract_features
from elara.vision.static_gestures import classify_static

FIXTURES = Path(__file__).parent / "fixtures" / "landmarks"

EXPECTED_POSES = [
    "open_palm",
    "fist",
    "point",
    "peace",
    "three",
    "thumbs_up",
    "thumbs_down",
    "pinch",
    "ok_sign",
    "l_shape",
    "rock",
    "palm_away",
]

pytestmark = pytest.mark.skipif(not FIXTURES.exists(), reason="run scripts/synth_landmarks.py first")


def _classify_fixture(name: str):
    landmarks = np.array(json.loads((FIXTURES / f"{name}.json").read_text()))
    features = extract_features(landmarks)
    return classify_static(features, VisionConfig())


@pytest.mark.parametrize("pose_name", EXPECTED_POSES)
def test_fixture_classifies_to_expected_pose(pose_name: str):
    result = _classify_fixture(pose_name)
    assert result is not None, f"{pose_name}.json classified to nothing"
    assert result.id == pose_name, f"{pose_name}.json classified as {result.id}"


def test_all_twelve_poses_are_covered():
    assert len(EXPECTED_POSES) == 12


def test_confidence_is_never_a_flat_one():
    # ADR-005: confidence must be graded, not boolean, so the arming gate
    # has something to work with.
    seen_non_unity = False
    for pose_name in EXPECTED_POSES:
        result = _classify_fixture(pose_name)
        if result is not None and result.confidence < 0.999:
            seen_non_unity = True
    assert seen_non_unity
