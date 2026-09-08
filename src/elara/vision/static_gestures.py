"""Rule-based static pose classifier over HandFeatures (ADR-005). Returns the
highest-priority matching pose with a graded confidence — not a flat 1.0 —
so the arming gate (T027) has something to work with. Ambiguity is resolved
by an explicit priority order: most specific pose wins (e.g. ok_sign before
pinch, l_shape before point)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from elara.vision.features import HandFeatures

# Priority order matters: first match in this list wins.
_PRIORITY = (
    "ok_sign",
    "l_shape",
    "rock",
    "peace",
    "three",
    "point",
    "thumbs_up",
    "thumbs_down",
    "pinch",
    "palm_away",
    "open_palm",
    "fist",
)

_ANGLE_L_SHAPE_MIN = 60.0
_ANGLE_L_SHAPE_MAX = 120.0


@dataclass
class PoseResult:
    id: str
    confidence: float


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


def _margin_confidence(value: float, threshold: float, direction: str, softness: float) -> float:
    """Confidence derived from how far `value` sits past `threshold`, in the
    direction that indicates a match ("above" or "below"), squashed to
    0..1 over a `softness`-wide band around the threshold."""
    if direction == "above":
        return _clip01((value - threshold) / softness + 0.5)
    return _clip01((threshold - value) / softness + 0.5)


def _thumb_up_down(pts: np.ndarray) -> str | None:
    tip = pts[4]
    mcp = pts[2]
    if tip[1] - mcp[1] > 0.3:
        return "up"
    if mcp[1] - tip[1] > 0.3:
        return "down"
    return None


def _thumb_index_angle_deg(pts: np.ndarray) -> float:
    tip4, tip8, wrist = pts[4], pts[8], pts[0]
    v1 = tip4 - wrist
    v2 = tip8 - wrist
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 0.0
    cos_theta = float(np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0))
    return float(np.degrees(np.arccos(cos_theta)))


def classify_static(features: HandFeatures, config) -> PoseResult | None:
    ext = features.finger_extended
    pinch_on = config.pinch_on
    pinch_off = config.pinch_off
    pinching = features.pinch_distance < pinch_on

    candidates: dict[str, float] = {}

    if pinching and ext["middle"] and ext["ring"] and ext["pinky"]:
        candidates["ok_sign"] = _margin_confidence(features.pinch_distance, pinch_on, "below", 0.02)

    if ext["thumb"] and ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]:
        angle = _thumb_index_angle_deg(features.landmarks_norm)
        if _ANGLE_L_SHAPE_MIN <= angle <= _ANGLE_L_SHAPE_MAX:
            candidates["l_shape"] = _margin_confidence(angle, 90.0, "above", 30.0)

    if ext["thumb"] and ext["index"] and not ext["middle"] and not ext["ring"] and ext["pinky"]:
        candidates["rock"] = 0.85

    if ext["index"] and ext["middle"] and not ext["ring"] and not ext["pinky"]:
        candidates["peace"] = 0.85

    if ext["index"] and ext["middle"] and ext["ring"] and not ext["pinky"]:
        candidates["three"] = 0.8

    if ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"] and not pinching:
        candidates["point"] = 0.85

    if ext["thumb"] and not ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]:
        direction = _thumb_up_down(features.landmarks_norm)
        if direction == "up":
            candidates["thumbs_up"] = 0.85
        elif direction == "down":
            candidates["thumbs_down"] = 0.85

    if pinching and not (ext["middle"] and ext["ring"] and ext["pinky"]):
        candidates["pinch"] = _margin_confidence(features.pinch_distance, pinch_off, "below", 0.03)

    all_extended = all(ext.values())
    if all_extended:
        facing_away = float(features.palm_normal[2]) > 0.3
        span_conf = _clip01(features.hand_span / 1.2)
        if facing_away:
            candidates["palm_away"] = span_conf
        else:
            candidates["open_palm"] = span_conf

    if not any(ext.values()):
        candidates["fist"] = 0.85

    for pose_id in _PRIORITY:
        if pose_id in candidates:
            return PoseResult(id=pose_id, confidence=candidates[pose_id])

    return None
