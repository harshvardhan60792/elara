"""Owns the camera + landmarker + engine on their own QThread (ADR-007), so
the Qt main thread stays free for UI. The engine (and camera) are built
lazily inside run() — not in __init__ — so the camera is only ever opened
once the thread actually starts, which only happens while armed. Stopping
the thread releases the camera, so the hardware LED reflects real state.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from PySide6.QtCore import QThread

logger = logging.getLogger(__name__)


class VisionThread(QThread):
    def __init__(self, engine_factory: Callable[[], object], parent=None) -> None:
        super().__init__(parent)
        self._engine_factory = engine_factory
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        engine = self._engine_factory()
        try:
            self._loop(engine)
        except Exception:
            logger.exception("vision thread crashed")
        finally:
            try:
                engine.source.close()
            except Exception:
                logger.exception("error closing frame source")

    def _loop(self, engine) -> None:
        on_battery = self._battery_check()
        while not self._stop_requested:
            t0 = time.monotonic()
            if not engine.step():
                break

            target_fps = engine.fps_controller.target_fps(t0 * 1000.0, on_battery())
            budget = 1.0 / target_fps
            elapsed = time.monotonic() - t0
            remaining = budget - elapsed
            if remaining > 0:
                self.msleep(int(remaining * 1000))

    @staticmethod
    def _battery_check() -> Callable[[], bool]:
        def _check() -> bool:
            try:
                import psutil

                battery = psutil.sensors_battery()
                return bool(battery and not battery.power_plugged)
            except Exception:
                return False

        return _check


def make_source(spec: str):
    """Parses --source camera:N | video:PATH | synth:PATH into a frame
    source instance. Shared by __main__.py and scripts/bench.py."""
    from elara.vision.camera import CameraSource, SynthSource, VideoFileSource

    kind, _, value = spec.partition(":")
    if kind == "camera":
        return CameraSource(device_index=int(value or 0))
    if kind == "video":
        return VideoFileSource(value)
    if kind == "synth":
        return SynthSource(value)
    raise ValueError(f"unsupported --source spec: {spec!r}")


class VisionSupervisor:
    """Starts/stops the VisionThread on StateChanged. A fresh VisionEngine
    (and, for a real camera, a fresh HandLandmarkerWrapper) is built each
    time arming happens — nothing about the camera or model is held open
    while disarmed."""

    def __init__(self, ctx, source_spec: str = "camera:0") -> None:
        self.ctx = ctx
        self.source_spec = source_spec
        self._thread: VisionThread | None = None

    def _build_engine(self):
        from elara.vision.engine import VisionEngine

        source = make_source(self.source_spec)
        landmarker = None
        if self.source_spec.startswith("camera:") or self.source_spec.startswith("video:"):
            from elara.vision.landmarker import HandLandmarkerWrapper

            try:
                landmarker = HandLandmarkerWrapper(
                    min_hand_detection_confidence=self.ctx.config.vision.min_hand_detection_confidence,
                    min_hand_presence_confidence=self.ctx.config.vision.min_hand_presence_confidence,
                    min_tracking_confidence=self.ctx.config.vision.min_tracking_confidence,
                )
            except FileNotFoundError:
                logger.warning("hand landmarker model missing; run scripts/fetch_models.py")

        return VisionEngine(source, self.ctx.config, self.ctx.event_bus, landmarker=landmarker)

    def on_state_changed(self, event) -> None:
        if event.armed:
            self.start()
        else:
            self.stop()

    def start(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return
        self._thread = VisionThread(self._build_engine)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._thread.stop()
        self._thread.wait(2000)
        self._thread = None
