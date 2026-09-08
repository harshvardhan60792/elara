"""Maps the index fingertip's raw (0..1 image-normalized) position through
an active rectangle to screen coordinates, One Euro filtered. Pure mapping
logic (`CursorMapper`) is Qt-independent and takes screen bounds as a plain
tuple, so it's testable without a display. `CursorController` is the thin
Qt-facing piece that actually moves the OS cursor.
"""

from __future__ import annotations

from elara.vision.smoothing import Vec2Filter


class CursorMapper:
    def __init__(
        self,
        active_rect: tuple[float, float, float, float] = (0.15, 0.15, 0.85, 0.85),
        freq: float = 30.0,
        mincutoff: float = 1.0,
        beta: float = 0.007,
    ) -> None:
        self.active_rect = active_rect
        self._filter = Vec2Filter(freq=freq, mincutoff=mincutoff, beta=beta)

    def map_to_screen(
        self,
        norm_x: float,
        norm_y: float,
        timestamp: float,
        screen_bounds: tuple[float, float, float, float],
    ) -> tuple[int, int]:
        """screen_bounds is (left, top, width, height)."""
        x0, y0, x1, y1 = self.active_rect
        u = (norm_x - x0) / (x1 - x0) if x1 != x0 else 0.5
        v = (norm_y - y0) / (y1 - y0) if y1 != y0 else 0.5
        u = max(0.0, min(1.0, u))
        v = max(0.0, min(1.0, v))

        fx, fy = self._filter((u, v), timestamp)
        fx = max(0.0, min(1.0, fx))
        fy = max(0.0, min(1.0, fy))

        left, top, width, height = screen_bounds
        return int(left + fx * width), int(top + fy * height)


class CursorController:
    """Subscribes to ContinuousUpdate(channel="cursor") and moves the real
    OS mouse while cursor mode is active and Elara is armed. Screen bounds
    are read from Qt at move time (multi-monitor aware via the virtual
    desktop's combined geometry) rather than cached, since monitors can be
    hot-plugged while the app runs."""

    def __init__(self, ctx, mapper: CursorMapper | None = None) -> None:
        self.ctx = ctx
        self.mapper = mapper or CursorMapper()

    def _screen_bounds(self) -> tuple[float, float, float, float]:
        from PySide6.QtGui import QGuiApplication

        geometry = QGuiApplication.primaryScreen().virtualGeometry()
        return (geometry.left(), geometry.top(), geometry.width(), geometry.height())

    def handle_continuous(self, update) -> None:
        if update.channel != "cursor":
            return
        if not self.ctx.armed or not self.ctx.stats.get("cursor_active", False):
            return
        if update.position is None:
            return

        import time

        from pynput.mouse import Controller

        x, y = self.mapper.map_to_screen(
            update.position[0], update.position[1], time.monotonic(), self._screen_bounds()
        )
        Controller().position = (x, y)
