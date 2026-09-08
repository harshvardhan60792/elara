"""The vision pipeline: reads frames (or, for tests, pre-baked landmarks),
extracts features, classifies poses, feeds the arming gate and the dynamic
gesture detector, and emits events. A SynthSource skips capture and
inference entirely (ADR-015) — `step()` is the same call either way, which
is what makes the whole pipeline testable end to end without a camera.

Threading: production use wraps this in a QThread (see app wiring) so the
Qt main thread stays free for UI. Tests drive `step()`/`run_to_completion()`
directly and never touch Qt.
"""

from __future__ import annotations

from dataclasses import dataclass

from elara.core.arming import ArmingGate
from elara.events import ContinuousUpdate, EventBus, GestureEvent
from elara.vision.camera import SynthSource
from elara.vision.dynamic_gestures import DynamicGestureDetector
from elara.vision.features import extract_features, raw_hand_span, raw_palm_center
from elara.vision.static_gestures import classify_static


@dataclass
class AdaptiveFpsController:
    """ADR-016: 8 FPS scanning for a hand, 30 FPS once one is present,
    capped at 15 on battery. Pure logic — the caller owns the actual sleep
    timing so this stays trivially testable."""

    fps_idle: int = 8
    fps_active: int = 30
    fps_battery_cap: int = 15
    idle_after_ms: float = 1500

    _last_hand_seen_ms: float | None = None

    def observe(self, hand_present: bool, timestamp_ms: float) -> None:
        if hand_present:
            self._last_hand_seen_ms = timestamp_ms

    def target_fps(self, timestamp_ms: float, on_battery: bool) -> float:
        if self._last_hand_seen_ms is None:
            fps = self.fps_idle
        else:
            idle_for = timestamp_ms - self._last_hand_seen_ms
            fps = self.fps_idle if idle_for > self.idle_after_ms else self.fps_active
        if on_battery:
            fps = min(fps, self.fps_battery_cap)
        return fps


class VisionEngine:
    def __init__(self, source, config, event_bus: EventBus, landmarker=None, hand_label: str = "right") -> None:
        self.source = source
        self.config = config
        self.event_bus = event_bus
        self.landmarker = landmarker
        self.hand_label = hand_label

        arming_cfg = config.arming
        self._arming = ArmingGate(
            confidence_floor=arming_cfg.confidence_floor,
            vote_n=arming_cfg.vote_n,
            vote_m=arming_cfg.vote_m,
            dwell_ms=arming_cfg.dwell_ms,
            cooldown_ms=arming_cfg.cooldown_ms,
        )
        self._dynamic = DynamicGestureDetector(buffer_seconds=config.vision.trajectory_buffer_s)
        self.fps_controller = AdaptiveFpsController(
            fps_idle=config.performance.fps_idle,
            fps_active=config.performance.fps_active,
            fps_battery_cap=config.performance.fps_battery_cap,
            idle_after_ms=config.performance.idle_after_ms,
        )

    def is_synth(self) -> bool:
        return isinstance(self.source, SynthSource)

    def step(self) -> bool:
        if self.is_synth():
            item = self.source.read_landmarks()
            if item is None:
                return False
            timestamp_s, landmarks = item
            self._process_landmarks(landmarks, timestamp_s * 1000.0)
            return True

        frame = self.source.read()
        if frame is None:
            return False
        if self.landmarker is not None:
            self.landmarker.submit(frame)
            polled = self.landmarker.poll()
            if polled is not None:
                _timestamp_ms, mp_result = polled
                from elara.vision.landmarker import result_to_landmark_arrays

                arrays = result_to_landmark_arrays(mp_result)
                landmarks = arrays[0] if arrays else None
                self._process_landmarks(landmarks, _timestamp_ms)
        return True

    def _process_landmarks(self, landmarks, timestamp_ms: float) -> None:
        self.fps_controller.observe(landmarks is not None, timestamp_ms)

        if landmarks is None:
            self._arming.update(None, 0.0, timestamp_ms)
            return

        feats = extract_features(landmarks)
        raw_center = raw_palm_center(landmarks)
        raw_span = raw_hand_span(landmarks)
        position = (float(raw_center[0]), float(raw_center[1]))

        pose = classify_static(feats, self.config.vision)
        pose_id = pose.id if pose else None
        confidence = pose.confidence if pose else 0.0

        fired = self._arming.update(pose_id, confidence, timestamp_ms, position=position)
        if fired:
            self.event_bus.gesture.emit(
                GestureEvent(
                    id=fired,
                    hand=self.hand_label,
                    confidence=confidence,
                    position=position,
                    timestamp=timestamp_ms / 1000.0,
                )
            )

        dynamic_id = self._dynamic.update(timestamp_ms / 1000.0, raw_center, raw_span)
        if dynamic_id:
            self.event_bus.gesture.emit(
                GestureEvent(
                    id=dynamic_id,
                    hand=self.hand_label,
                    confidence=1.0,
                    position=position,
                    timestamp=timestamp_ms / 1000.0,
                )
            )

        index_tip = landmarks[8]
        self.event_bus.continuous_update.emit(
            ContinuousUpdate(
                channel="cursor", value=0.0, position=(float(index_tip[0]), float(index_tip[1]))
            )
        )

        pinch_channel_value = 1.0 - min(1.0, feats.pinch_distance / max(self.config.vision.pinch_off, 1e-6))
        self.event_bus.continuous_update.emit(
            ContinuousUpdate(channel="pinch_scrub", value=pinch_channel_value, position=position)
        )

    def run_to_completion(self, max_steps: int | None = None) -> int:
        count = 0
        while (max_steps is None or count < max_steps) and self.step():
            count += 1
        return count
