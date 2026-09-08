"""Feature extraction over raw 21-landmark hand arrays. Pure functions over
np.ndarray only — no MediaPipe import here (ADR-005), which is what makes
this module unit-testable with synthetic arrays and safe for an unattended
agent to validate without a camera.

Landmark indices follow MediaPipe's hand model (see docs/GESTURES.md):
0 wrist; 1-4 thumb; 5-8 index; 9-12 middle; 13-16 ring; 17-20 pinky.
Tip indices are 4, 8, 12, 16, 20. PIP joints are 6, 10, 14, 18 (thumb has
no PIP; it uses IP = 3). MCP joints are 2, 5, 9, 13, 17.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

WRIST = 0
MIDDLE_MCP = 9

FINGER_NAMES = ("thumb", "index", "middle", "ring", "pinky")
TIP = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}
PIP = {"index": 6, "middle": 10, "ring": 14, "pinky": 18}
MCP = {"thumb": 2, "index": 5, "middle": 9, "ring": 13, "pinky": 17}
THUMB_IP = 3

PALM_LANDMARKS = (0, 5, 9, 13, 17)

_EPS = 1e-9


def raw_palm_center(landmarks: np.ndarray) -> np.ndarray:
    """Palm centre in the caller's original coordinate space (raw image or
    world coordinates) — used for trajectory/direction tracking, which cares
    about actual movement, unlike the orientation-normalized HandFeatures
    fields used for static pose classification."""
    raw = np.asarray(landmarks, dtype=np.float64)
    return raw[list(PALM_LANDMARKS)].mean(axis=0)


def raw_hand_span(landmarks: np.ndarray) -> float:
    """Bounding-box diagonal in the caller's original coordinate space — a
    proxy for distance from camera. Deliberately NOT computed on normalized
    landmarks: normalization fixes scale to wrist->middle-MCP == 1, which
    would make this constant and useless."""
    raw = np.asarray(landmarks, dtype=np.float64)
    return float(np.linalg.norm(raw.max(axis=0) - raw.min(axis=0)))


def normalize_landmarks(landmarks: np.ndarray) -> np.ndarray:
    """Translate wrist to origin, scale wrist->middle-MCP to length 1, then
    rotate in the XY plane so that vector points "up" (+Y). Order matters:
    translate, then scale, then rotate — see docs/GESTURES.md."""
    pts = np.asarray(landmarks, dtype=np.float64).copy()
    assert pts.shape == (21, 3), f"expected (21, 3), got {pts.shape}"

    pts -= pts[WRIST]

    scale = float(np.linalg.norm(pts[MIDDLE_MCP][:2])) or 1.0
    pts /= max(scale, _EPS)

    ref = pts[MIDDLE_MCP][:2]
    angle_to_up = np.arctan2(ref[0], ref[1])  # rotate ref onto (0, 1)
    cos_a, sin_a = np.cos(angle_to_up), np.sin(angle_to_up)
    rot = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
    pts[:, :2] = pts[:, :2] @ rot.T

    return pts


def _angle_deg(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """Angle at vertex b, formed by rays b->a and b->c, in degrees."""
    v1 = a - b
    v2 = c - b
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < _EPS or n2 < _EPS:
        return 180.0
    cos_theta = float(np.dot(v1, v2) / (n1 * n2))
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return float(np.degrees(np.arccos(cos_theta)))


def _finger_extended(pts: np.ndarray, name: str, thumb_angle_threshold: float = 150.0) -> bool:
    if name == "thumb":
        angle = _angle_deg(pts[TIP["thumb"]], pts[THUMB_IP], pts[MCP["thumb"]])
        return angle > thumb_angle_threshold
    tip_dist = float(np.linalg.norm(pts[TIP[name]] - pts[WRIST]))
    pip_dist = float(np.linalg.norm(pts[PIP[name]] - pts[WRIST]))
    return tip_dist > pip_dist


def _finger_curl(pts: np.ndarray, name: str) -> float:
    """0 = fully straight, 1 = fully curled. Heuristic ratio of tip reach
    beyond the MCP against the PIP's reach beyond the MCP — a straight
    finger's tip reaches well past its PIP; a curled finger's tip folds
    back toward (or past) the MCP."""
    if name == "thumb":
        angle = _angle_deg(pts[TIP["thumb"]], pts[THUMB_IP], pts[MCP["thumb"]])
        return float(np.clip((180.0 - angle) / 90.0, 0.0, 1.0))

    mcp_dist = float(np.linalg.norm(pts[MCP[name]] - pts[WRIST]))
    pip_dist = float(np.linalg.norm(pts[PIP[name]] - pts[WRIST]))
    tip_dist = float(np.linalg.norm(pts[TIP[name]] - pts[WRIST]))
    span = (pip_dist - mcp_dist) * 1.5
    if span < _EPS:
        return 0.0
    extension = (tip_dist - mcp_dist) / span
    return float(np.clip(1.0 - extension, 0.0, 1.0))


@dataclass
class HandFeatures:
    landmarks_norm: np.ndarray
    finger_extended: dict[str, bool]
    finger_curl: dict[str, float]
    pinch_distance: float
    palm_center: np.ndarray
    palm_normal: np.ndarray
    hand_span: float
    handedness: str | None = None
    visibility_score: float | None = None
    velocity: np.ndarray | None = None


def extract_features(
    landmarks: np.ndarray,
    handedness: str | None = None,
    visibility_score: float | None = None,
    velocity: np.ndarray | None = None,
) -> HandFeatures:
    pts = normalize_landmarks(landmarks)

    extended = {name: _finger_extended(pts, name) for name in FINGER_NAMES}
    curl = {name: _finger_curl(pts, name) for name in FINGER_NAMES}

    pinch_distance = float(np.linalg.norm(pts[TIP["thumb"]] - pts[TIP["index"]]))

    palm_center = pts[list(PALM_LANDMARKS)].mean(axis=0)

    v1 = pts[5] - pts[0]
    v2 = pts[17] - pts[0]
    normal = np.cross(v1, v2)
    norm_len = np.linalg.norm(normal)
    palm_normal = normal / norm_len if norm_len > _EPS else np.array([0.0, 0.0, 1.0])

    hand_span = raw_hand_span(landmarks)

    return HandFeatures(
        landmarks_norm=pts,
        finger_extended=extended,
        finger_curl=curl,
        pinch_distance=pinch_distance,
        palm_center=palm_center,
        palm_normal=palm_normal,
        hand_span=hand_span,
        handedness=handedness,
        visibility_score=visibility_score,
        velocity=velocity,
    )
