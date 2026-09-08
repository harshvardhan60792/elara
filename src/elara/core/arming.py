"""The four-filter arming stack (ADR-009): confidence floor -> N-of-M vote
-> dwell -> per-action cooldown, plus an optional active zone. An
always-watching camera that misfires is worse than no product at all, so
every filter here exists to kill a specific false-positive: the floor kills
low-confidence noise, the vote kills single-frame flicker, dwell kills
brush-past poses, cooldown kills rapid re-fire, and the zone (if set)
confines a pose to a screen region.

Pure logic over (pose_id, confidence, timestamp_ms, position) — no Qt, no
threads, no I/O. This is what makes it table-driven-testable.

Re-arming: a pose that fires stays disarmed as long as it is continuously
re-acquired (the same dwell segment) — a pose held indefinitely fires
exactly once, never again on a cooldown timer alone. It only re-arms when
released (drops below the floor/vote/zone) and is then re-acquired; cooldown
then additionally blocks a too-quick release/re-acquire cycle.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable


@dataclass
class _PoseState:
    armed: bool = True
    last_fired_ms: float | None = None


class ArmingGate:
    def __init__(
        self,
        confidence_floor: float = 0.72,
        vote_n: int = 4,
        vote_m: int = 6,
        dwell_ms: float = 250,
        cooldown_ms: float = 800,
        active_zone: Callable[[tuple[float, float]], bool] | None = None,
    ) -> None:
        self.confidence_floor = confidence_floor
        self.vote_n = vote_n
        self.vote_m = vote_m
        self.dwell_ms = dwell_ms
        self.cooldown_ms = cooldown_ms
        self.active_zone = active_zone

        self._vote_window: deque[str | None] = deque(maxlen=vote_m)
        self._dwell_pose: str | None = None
        self._dwell_start_ms: float | None = None
        self._states: dict[str, _PoseState] = {}

    def _state(self, pose_id: str) -> _PoseState:
        return self._states.setdefault(pose_id, _PoseState())

    def update(
        self,
        pose_id: str | None,
        confidence: float,
        timestamp_ms: float,
        position: tuple[float, float] | None = None,
    ) -> str | None:
        passed = pose_id is not None and confidence >= self.confidence_floor
        if passed and self.active_zone is not None and position is not None:
            passed = self.active_zone(position)

        self._vote_window.append(pose_id if passed else None)

        if not passed:
            self._dwell_pose = None
            self._dwell_start_ms = None
            return None

        votes = sum(1 for p in self._vote_window if p == pose_id)
        if votes < self.vote_n:
            self._dwell_pose = None
            self._dwell_start_ms = None
            return None

        if self._dwell_pose != pose_id:
            self._dwell_pose = pose_id
            self._dwell_start_ms = timestamp_ms
            self._state(pose_id).armed = True

        held_ms = timestamp_ms - self._dwell_start_ms
        if held_ms < self.dwell_ms:
            return None

        state = self._state(pose_id)
        if not state.armed:
            return None
        if state.last_fired_ms is not None and (timestamp_ms - state.last_fired_ms) < self.cooldown_ms:
            return None

        state.armed = False
        state.last_fired_ms = timestamp_ms
        return pose_id

    def reset(self) -> None:
        self._vote_window.clear()
        self._dwell_pose = None
        self._dwell_start_ms = None
        self._states.clear()
