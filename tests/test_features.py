from __future__ import annotations

import numpy as np
import pytest

from elara.vision.features import extract_features, normalize_landmarks


def _open_hand() -> np.ndarray:
    """A rough open-palm skeleton: wrist at origin, fingers splayed and
    fully extended along +Y with increasing spread by finger."""
    pts = np.zeros((21, 3), dtype=np.float64)
    pts[0] = (0.0, 0.0, 0.0)  # wrist

    finger_specs = {
        "thumb": (1, 2, 3, 4, -0.35),
        "index": (5, 6, 7, 8, -0.12),
        "middle": (9, 10, 11, 12, 0.0),
        "ring": (13, 14, 15, 16, 0.12),
        "pinky": (17, 18, 19, 20, 0.24),
    }
    for _name, (mcp, pip, dip, tip, x_off) in finger_specs.items():
        pts[mcp] = (x_off, 0.5, 0.0)
        pts[pip] = (x_off, 0.75, 0.0)
        pts[dip] = (x_off, 0.9, 0.0)
        pts[tip] = (x_off, 1.05, 0.0)

    return pts


def _fist() -> np.ndarray:
    pts = _open_hand()
    # Fold every tip/dip/pip back toward its MCP.
    for mcp, pip, dip, tip in [(2, 3, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
        target = pts[mcp] + np.array([0.0, 0.05, 0.02])
        pts[pip] = target
        pts[dip] = target
        pts[tip] = target
    return pts


def test_scale_invariance():
    base = _open_hand()
    scaled = base * 2.0

    norm_base = normalize_landmarks(base)
    norm_scaled = normalize_landmarks(scaled)

    assert np.allclose(norm_base, norm_scaled, atol=1e-9)


def test_translation_invariance():
    base = _open_hand()
    translated = base + np.array([5.0, -3.0, 1.0])

    norm_base = normalize_landmarks(base)
    norm_translated = normalize_landmarks(translated)

    assert np.allclose(norm_base, norm_translated, atol=1e-9)


def test_wrist_maps_to_origin():
    norm = normalize_landmarks(_open_hand())
    assert np.allclose(norm[0], (0.0, 0.0, 0.0), atol=1e-9)


def test_open_hand_all_fingers_extended():
    feats = extract_features(_open_hand())
    assert all(feats.finger_extended.values())


def test_fist_no_fingers_extended():
    feats = extract_features(_fist())
    assert not any(
        feats.finger_extended[name] for name in ("index", "middle", "ring", "pinky")
    )


def test_curl_is_monotonic_between_open_and_fist():
    open_feats = extract_features(_open_hand())
    fist_feats = extract_features(_fist())
    for name in ("index", "middle", "ring", "pinky"):
        assert fist_feats.finger_curl[name] > open_feats.finger_curl[name]


def test_bad_shape_raises():
    with pytest.raises(AssertionError):
        normalize_landmarks(np.zeros((5, 3)))
