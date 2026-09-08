"""Trajectory-based dynamic gesture detection: swipes, circles, push. Pure
logic over a ring buffer of (timestamp, palm_center, hand_span) samples — no
MediaPipe import, testable with synthetic sequences (ADR-015).

Coordinate convention: callers must supply palm_center with +Y = up, +X =
right (matching the canonical frame used elsewhere in vision/). MediaPipe's
image-normalized landmarks have +Y = down, so the caller (the vision engine,
T017) is responsible for negating Y before calling update().

Swipe/circle detection uses a simple motion state machine: samples
accumulate into a "stroke" while tail speed stays at or above
`velocity_floor`; the stroke is classified only once speed drops back below
the floor. This is what stops one physical swipe firing more than once
(docs/GESTURES.md) — re-evaluation only happens at the end of a motion
segment, never mid-motion.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

_EPS = 1e-9


@dataclass
class _Sample:
    t: float
    center: np.ndarray
    span: float


class DynamicGestureDetector:
    def __init__(
        self,
        buffer_seconds: float = 1.0,
        velocity_floor: float = 0.8,
        min_displacement: float = 0.4,
        axis_dominance_ratio: float = 2.0,
        max_stroke_s: float = 0.6,
        circle_min_turns: float = 0.8,
        circle_radius_cv_max: float = 0.5,
        push_span_growth_ratio: float = 1.3,
        push_window_s: float = 0.35,
        push_center_still_ratio: float = 0.15,
    ) -> None:
        self.buffer_seconds = buffer_seconds
        self.velocity_floor = velocity_floor
        self.min_displacement = min_displacement
        self.axis_dominance_ratio = axis_dominance_ratio
        self.max_stroke_s = max_stroke_s
        self.circle_min_turns = circle_min_turns
        self.circle_radius_cv_max = circle_radius_cv_max
        self.push_span_growth_ratio = push_span_growth_ratio
        self.push_window_s = push_window_s
        self.push_center_still_ratio = push_center_still_ratio

        self._samples: deque[_Sample] = deque()
        self._moving = False
        self._stroke_samples: list[_Sample] = []
        self._push_armed = True

    def reset(self) -> None:
        self._samples.clear()
        self._moving = False
        self._stroke_samples = []
        self._push_armed = True

    def update(self, timestamp: float, palm_center, hand_span: float) -> str | None:
        center = np.asarray(palm_center, dtype=np.float64)[:2]
        sample = _Sample(t=timestamp, center=center, span=float(hand_span))
        self._samples.append(sample)

        cutoff = timestamp - self.buffer_seconds
        while len(self._samples) > 1 and self._samples[0].t < cutoff:
            self._samples.popleft()

        result = self._update_swipe_or_circle(sample)
        if result is None:
            result = self._update_push(timestamp)
        return result

    def _speed_at_tail(self) -> float:
        if len(self._samples) < 2:
            return 0.0
        a, b = self._samples[-2], self._samples[-1]
        dt = b.t - a.t
        if dt <= 0:
            return 0.0
        return float(np.linalg.norm(b.center - a.center) / dt)

    def _update_swipe_or_circle(self, tail: _Sample) -> str | None:
        speed = self._speed_at_tail()

        if speed >= self.velocity_floor:
            if not self._moving:
                self._moving = True
                self._stroke_samples = list(self._samples)[-2:-1]
            self._stroke_samples.append(tail)
            return None

        if self._moving:
            self._moving = False
            stroke = self._stroke_samples
            self._stroke_samples = []
            return self._classify_stroke(stroke)

        return None

    def _classify_stroke(self, stroke: list[_Sample]) -> str | None:
        if len(stroke) < 3:
            return None
        duration = stroke[-1].t - stroke[0].t
        if duration <= 0:
            return None

        disp = stroke[-1].center - stroke[0].center
        dist = float(np.linalg.norm(disp))
        dx, dy = float(disp[0]), float(disp[1])

        # max_stroke_s ("completed within a time window", docs/GESTURES.md)
        # is a swipe-specific completion-time requirement, not a general
        # motion-duration cap — a circle legitimately takes longer than a
        # quick linear swipe and must not be rejected by it.
        if dist >= self.min_displacement and duration <= self.max_stroke_s:
            if abs(dx) >= self.axis_dominance_ratio * max(abs(dy), _EPS):
                return "swipe_right" if dx > 0 else "swipe_left"
            if abs(dy) >= self.axis_dominance_ratio * max(abs(dx), _EPS):
                return "swipe_up" if dy > 0 else "swipe_down"

        return self._classify_circle(stroke)

    def _classify_circle(self, stroke: list[_Sample]) -> str | None:
        if len(stroke) < 5:
            return None
        centers = np.array([s.center for s in stroke])
        centroid = centers.mean(axis=0)
        rel = centers - centroid
        radii = np.linalg.norm(rel, axis=1)
        if radii.mean() < 1e-6:
            return None
        radius_cv = float(radii.std() / radii.mean())
        if radius_cv > self.circle_radius_cv_max:
            return None

        angles = np.arctan2(rel[:, 1], rel[:, 0])
        dangles = np.diff(angles)
        dangles = (dangles + np.pi) % (2 * np.pi) - np.pi
        total = float(np.sum(dangles))
        if abs(total) < self.circle_min_turns * 2 * np.pi:
            return None
        return "circle_ccw" if total > 0 else "circle_cw"

    def _update_push(self, timestamp: float) -> str | None:
        window = [s for s in self._samples if timestamp - s.t <= self.push_window_s]
        if len(window) < 3:
            return None

        span0, span1 = window[0].span, window[-1].span
        if span0 <= 1e-6:
            return None
        growth = span1 / span0
        center_disp = float(np.linalg.norm(window[-1].center - window[0].center))

        if growth >= self.push_span_growth_ratio and center_disp <= self.push_center_still_ratio * span0:
            if self._push_armed:
                self._push_armed = False
                return "push"
            return None

        if growth < 1.05:
            self._push_armed = True
        return None
