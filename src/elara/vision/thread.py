"""Owns the camera + landmarker + engine on their own QThread (ADR-007), so
the Qt main thread stays free for UI. The engine (and camera) are built
lazily inside run() — not in __init__ — so the camera is only ever opened
once the thread actually starts, which only happens while armed. Stopping
the thread releases the camera, so the hardware LED reflects real state.
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from PySide6.QtCore import QThread

logger = logging.getLogger(__name__)


class VisionThread(QThread):
    def __init__(self, engine_factory: Callable[[], object], parent=None) -> None:
        super().__init__(parent)
        self._engine_factory = engine_factory
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:  # noqa: N802 (Qt override)
        engine = self._engine_factory()
        try:
            self._loop(engine)
        except Exception:  # noqa: BLE001 — the vision thread must never crash the app
            logger.exception("vision thread crashed")
        finally:
            try:
                engine.source.close()
            except Exception:  # noqa: BLE001
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
            except Exception:  # noqa: BLE001
                return False

        return _check
