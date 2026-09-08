"""Generates deterministic synthetic 21-landmark hand fixtures — the 12
static poses from docs/GESTURES.md plus motion sequences (swipes, circles,
push) — so the classifier and dynamic gesture detector are testable without
a camera (ADR-015). Coordinates use the same "+Y = up" canonical convention
as src/elara/vision/features.py and dynamic_gestures.py.

Run with --all to regenerate every fixture; must be deterministic (fixed
seed) so `git diff` is empty after a re-run with the same --noise value.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

FINGER_X = {"index": -0.12, "middle": 0.0, "ring": 0.12, "pinky": 0.24}
THUMB_X = -0.35
SEED = 1234


def _straight_finger(x_off: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mcp = np.array([x_off, 0.5, 0.0])
    pip = np.array([x_off, 0.75, 0.0])
    dip = np.array([x_off, 0.9, 0.0])
    tip = np.array([x_off, 1.05, 0.0])
    return mcp, pip, dip, tip


def _curled_finger(x_off: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mcp = np.array([x_off, 0.5, 0.0])
    fold = mcp + np.array([0.0, 0.05, 0.03])
    return mcp, fold, fold.copy(), fold.copy()


def _finger_points(x_off: float, curl: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mcp, s_pip, s_dip, s_tip = _straight_finger(x_off)
    _, c_pip, c_dip, c_tip = _curled_finger(x_off)
    pip = s_pip + curl * (c_pip - s_pip)
    dip = s_dip + curl * (c_dip - s_dip)
    tip = s_tip + curl * (c_tip - s_tip)
    return mcp, pip, dip, tip


_THUMB_STATES = {
    # tip placed so wrist->tip is exactly perpendicular to a straight
    # index's wrist->tip (docs/GESTURES.md: "thumb+index at ~90 deg"),
    # ip at the midpoint of mcp->tip so the thumb reads as extended
    # (straight) rather than curled.
    "straight_side": {
        "mcp": np.array([THUMB_X, 0.5, 0.0]),
        "ip": np.array([-0.39375, 0.225, 0.0]),
        "tip": np.array([-0.4375, -0.05, 0.0]),
    },
    "up": {
        "mcp": np.array([THUMB_X, 0.5, 0.0]),
        "ip": np.array([THUMB_X, 0.65, 0.0]),
        "tip": np.array([THUMB_X, 0.8, 0.0]),
    },
    "down": {
        "mcp": np.array([THUMB_X, 0.5, 0.0]),
        "ip": np.array([THUMB_X, 0.35, 0.0]),
        "tip": np.array([THUMB_X, 0.2, 0.0]),
    },
    # A genuine fold: ip juts to one side of the mcp->tip line rather than
    # just being a short straight segment — a short-but-straight segment
    # still measures as extended by the tip-ip-mcp angle test (angle only
    # cares about direction, not length), which is what real folding needs
    # to defeat.
    "folded": {
        "mcp": np.array([THUMB_X, 0.5, 0.0]),
        "ip": np.array([THUMB_X + 0.05, 0.48, 0.02]),
        "tip": np.array([THUMB_X + 0.01, 0.53, 0.04]),
    },
    "pinch": {
        "mcp": np.array([THUMB_X, 0.5, 0.0]),
        "ip": np.array([FINGER_X["index"] - 0.06, 0.87, 0.0]),
        "tip": np.array([FINGER_X["index"] + 0.01, 1.03, 0.0]),
    },
}

# name -> (thumb_state, index_curl, middle_curl, ring_curl, pinky_curl, mirror_x)
_POSES: dict[str, tuple[str, float, float, float, float, bool]] = {
    "open_palm": ("straight_side", 0.0, 0.0, 0.0, 0.0, False),
    "fist": ("folded", 1.0, 1.0, 1.0, 1.0, False),
    "point": ("folded", 0.0, 1.0, 1.0, 1.0, False),
    "peace": ("straight_side", 0.0, 0.0, 1.0, 1.0, False),
    "three": ("folded", 0.0, 0.0, 0.0, 1.0, False),
    "thumbs_up": ("up", 1.0, 1.0, 1.0, 1.0, False),
    "thumbs_down": ("down", 1.0, 1.0, 1.0, 1.0, False),
    "pinch": ("pinch", 0.0, 1.0, 1.0, 1.0, False),
    "ok_sign": ("pinch", 0.0, 0.0, 0.0, 0.0, False),
    "l_shape": ("straight_side", 0.0, 1.0, 1.0, 1.0, False),
    "rock": ("straight_side", 0.0, 1.0, 1.0, 0.0, False),
    "palm_away": ("straight_side", 0.0, 0.0, 0.0, 0.0, True),
}


def build_pose(name: str) -> np.ndarray:
    thumb_state, ic, mc, rc, pc, mirror = _POSES[name]
    pts = np.zeros((21, 3), dtype=np.float64)
    pts[0] = (0.0, 0.0, 0.0)

    thumb = _THUMB_STATES[thumb_state]
    pts[1] = thumb["mcp"] * 0.6  # a rough CMC placement between wrist and MCP
    pts[2] = thumb["mcp"]
    pts[3] = thumb["ip"]
    pts[4] = thumb["tip"]

    for finger, curl in (("index", ic), ("middle", mc), ("ring", rc), ("pinky", pc)):
        mcp_i, pip_i, dip_i, tip_i = {"index": (5, 6, 7, 8), "middle": (9, 10, 11, 12), "ring": (13, 14, 15, 16), "pinky": (17, 18, 19, 20)}[finger]
        mcp, pip, dip, tip = _finger_points(FINGER_X[finger], curl)
        pts[mcp_i] = mcp
        pts[pip_i] = pip
        pts[dip_i] = dip
        pts[tip_i] = tip

    if mirror:
        pts[:, 0] *= -1

    return pts


def add_noise(pts: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    if sigma <= 0:
        return pts
    return pts + rng.normal(0, sigma, size=pts.shape)


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def build_swipe(direction: str, duration_s: float = 0.35, fps: float = 60.0, distance: float = 0.6) -> list[dict]:
    base = build_pose("open_palm")
    deltas = {
        "swipe_left": np.array([-distance, 0.0, 0.0]),
        "swipe_right": np.array([distance, 0.0, 0.0]),
        "swipe_up": np.array([0.0, distance, 0.0]),
        "swipe_down": np.array([0.0, -distance, 0.0]),
    }[direction]

    n_frames = max(3, int(duration_s * fps))
    frames = []
    for i in range(n_frames + 1):
        t = i / n_frames
        offset = deltas * _smoothstep(t)
        frames.append({"t": round(t * duration_s, 6), "landmarks": (base + offset).tolist()})
    return frames


def build_circle(direction: str, radius: float = 0.5, duration_s: float = 0.8, fps: float = 60.0) -> list[dict]:
    base = build_pose("point")
    n_frames = max(5, int(duration_s * fps))
    sign = 1.0 if direction == "circle_ccw" else -1.0
    frames = []
    for i in range(n_frames + 1):
        t = i / n_frames
        angle = sign * _smoothstep(t) * 2 * np.pi
        offset = np.array([radius * np.cos(angle) - radius, radius * np.sin(angle), 0.0])
        frames.append({"t": round(t * duration_s, 6), "landmarks": (base + offset).tolist()})
    return frames


def build_held_pose(name: str, duration_s: float = 1.0, fps: float = 30.0) -> list[dict]:
    """A static pose repeated across frames at a fixed position — the
    ArmingGate needs a genuine hold (N-of-M vote + dwell) to fire, which a
    single-frame pose fixture can never satisfy. This is what an e2e test
    of "hold open_palm -> action fires" actually needs to drive."""
    base = build_pose(name)
    n_frames = max(1, int(duration_s * fps))
    return [{"t": round(i / fps, 6), "landmarks": base.tolist()} for i in range(n_frames)]


def build_push(duration_s: float = 0.3, fps: float = 60.0, growth: float = 1.8) -> list[dict]:
    """Palm thrusts toward the camera: hand_span grows while the palm
    centre stays put, so scaling happens about the palm centre (mean of
    landmarks 0, 5, 9, 13, 17) rather than about the wrist/origin — scaling
    about the origin would drag the whole hand away from its own centroid
    and fail the "centre stays put" check."""
    base = build_pose("open_palm")
    palm_center0 = base[[0, 5, 9, 13, 17]].mean(axis=0)
    n_frames = max(3, int(duration_s * fps))
    frames = []
    for i in range(n_frames + 1):
        t = i / n_frames
        scale = 1.0 + (growth - 1.0) * _smoothstep(t)
        scaled = palm_center0 + scale * (base - palm_center0)
        frames.append({"t": round(t * duration_s, 6), "landmarks": scaled.tolist()})
    return frames


def build_slow_drift(duration_s: float = 2.0, fps: float = 30.0, distance: float = 0.5) -> list[dict]:
    """Negative fixture: the same net displacement as a swipe, but spread
    over seconds instead of ~350ms, so peak velocity never crosses the
    floor. Must classify as nothing."""
    base = build_pose("open_palm")
    n_frames = max(3, int(duration_s * fps))
    frames = []
    for i in range(n_frames + 1):
        t = i / n_frames
        offset = np.array([distance * t, 0.0, 0.0])
        frames.append({"t": round(t * duration_s, 6), "landmarks": (base + offset).tolist()})
    return frames


def build_hand_enter_exit(fps: float = 30.0) -> list[dict]:
    """Negative fixture: hand is absent (None) for several frames, appears,
    lingers, then disappears again. Exercises engine-level presence
    handling (T017), not the dynamic gesture detector directly."""
    base = build_pose("open_palm")
    frames: list[dict] = []
    dt = 1.0 / fps
    t = 0.0
    for _ in range(5):
        frames.append({"t": round(t, 6), "landmarks": None})
        t += dt
    for _ in range(15):
        frames.append({"t": round(t, 6), "landmarks": base.tolist()})
        t += dt
    for _ in range(5):
        frames.append({"t": round(t, 6), "landmarks": None})
        t += dt
    return frames


def build_partial_occlusion(fps: float = 30.0, sigma: float = 0.15, rng: np.random.Generator | None = None) -> list[dict]:
    """Negative fixture: fingertip landmarks are heavily perturbed (as if
    occluded/guessed by the model) while the palm stays put. Must not fire
    a static pose or a dynamic gesture."""
    rng = rng or np.random.default_rng(SEED)
    base = build_pose("open_palm")
    frames = []
    dt = 1.0 / fps
    tip_indices = [4, 8, 12, 16, 20]
    for i in range(20):
        pts = base.copy()
        pts[tip_indices] += rng.normal(0, sigma, size=(5, 3))
        frames.append({"t": round(i * dt, 6), "landmarks": pts.tolist()})
    return frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--out", default="tests/fixtures/landmarks")
    parser.add_argument("--noise", type=float, default=0.0)
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    for name in _POSES:
        pts = build_pose(name)
        pts = add_noise(pts, args.noise, rng)
        (out_dir / f"{name}.json").write_text(json.dumps(pts.tolist(), indent=2))

    (out_dir / "held_open_palm.json").write_text(json.dumps(build_held_pose("open_palm"), indent=2))
    (out_dir / "held_fist.json").write_text(json.dumps(build_held_pose("fist"), indent=2))

    for direction in ("swipe_left", "swipe_right", "swipe_up", "swipe_down"):
        (out_dir / f"{direction}.json").write_text(json.dumps(build_swipe(direction), indent=2))

    for direction in ("circle_cw", "circle_ccw"):
        (out_dir / f"{direction}.json").write_text(json.dumps(build_circle(direction), indent=2))

    (out_dir / "push.json").write_text(json.dumps(build_push(), indent=2))

    (out_dir / "neg_slow_drift.json").write_text(json.dumps(build_slow_drift(), indent=2))
    (out_dir / "neg_hand_enter_exit.json").write_text(json.dumps(build_hand_enter_exit(), indent=2))
    (out_dir / "neg_partial_occlusion.json").write_text(
        json.dumps(build_partial_occlusion(rng=rng), indent=2)
    )

    print(f"wrote fixtures to {out_dir}")


if __name__ == "__main__":
    main()
