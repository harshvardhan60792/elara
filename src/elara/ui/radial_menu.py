"""The primary interaction (docs/GESTURES.md): hold open_palm to open this
centered on the hand, move to highlight a segment by angle, pinch/fist to
confirm. Solves discoverability (nobody memorizes 15 gestures) and misfires
(nothing fires outside command mode unless directly bound) at once.

Hover selection is pure geometry (`hover_for_offset`), kept separate from
painting so it's testable without a real paint cycle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from PySide6.QtCore import QPropertyAnimation, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsOpacityEffect

from elara.ui.overlay import OverlayWindow

DEFAULT_RADIUS = 120
DEFAULT_DEAD_ZONE = 28
DEFAULT_TIMEOUT_MS = 3000
DEFAULT_OPEN_MS = 180


@dataclass
class RadialSegment:
    action_id: str
    label: str


def hover_for_offset(
    dx: float, dy: float, n_segments: int, dead_zone_radius: float
) -> int | None:
    """Returns the segment index under a point offset (dx, dy) from the
    menu's center (+X right, +Y down, matching Qt/screen coordinates), or
    None if the point is inside the dead zone (a stationary hand selects
    nothing — that's what stops the menu firing the instant it opens)."""
    if n_segments <= 0:
        return None
    radius = math.hypot(dx, dy)
    if radius < dead_zone_radius:
        return None

    # Segment 0 is centered on "up" (12 o'clock), proceeding clockwise —
    # matches how the menu is drawn.
    angle = math.atan2(dx, -dy)  # 0 at top, +pi/2 at right
    if angle < 0:
        angle += 2 * math.pi

    segment_width = 2 * math.pi / n_segments
    return int(angle // segment_width) % n_segments


class RadialMenu(OverlayWindow):
    selected = Signal(str)  # emits the chosen action_id
    dismissed = Signal()

    def __init__(
        self,
        segments: list[RadialSegment],
        radius: int = DEFAULT_RADIUS,
        dead_zone_radius: int = DEFAULT_DEAD_ZONE,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.segments = segments
        self.radius = radius
        self.dead_zone_radius = dead_zone_radius
        self.timeout_ms = timeout_ms

        size = radius * 2 + 20
        self.resize(size, size)

        self._hovered_index: int | None = None
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self.dismiss)

        self._anim: QPropertyAnimation | None = None

    def open_at(self, point) -> None:
        self.move_to_point(point, center=True)
        self.show()
        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._anim.setDuration(DEFAULT_OPEN_MS)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start(QPropertyAnimation.DeletionPolicy.KeepWhenStopped)
        self._timeout_timer.start(self.timeout_ms)

    def update_hover(self, dx: float, dy: float) -> None:
        self._timeout_timer.start(self.timeout_ms)  # activity resets the auto-dismiss clock
        new_index = hover_for_offset(dx, dy, len(self.segments), self.dead_zone_radius)
        if new_index != self._hovered_index:
            self._hovered_index = new_index
            self.update()

    def confirm(self) -> str | None:
        if self._hovered_index is None:
            self.dismiss()
            return None
        action_id = self.segments[self._hovered_index].action_id
        self.selected.emit(action_id)
        self._close()
        return action_id

    def dismiss(self) -> None:
        self.dismissed.emit()
        self._close()

    def _close(self) -> None:
        self._timeout_timer.stop()
        self.hide()

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        try:
            self._draw(painter)
        finally:
            painter.end()

    def _draw(self, painter: QPainter) -> None:
        n = len(self.segments)
        if n == 0:
            return
        center = self.rect().center()
        segment_deg = 360.0 / n
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        outer = QRect(
            center.x() - self.radius, center.y() - self.radius, self.radius * 2, self.radius * 2
        )
        for i, seg in enumerate(self.segments):
            start_angle_deg = 90 - (i * segment_deg) - segment_deg / 2  # Qt angles are CCW from 3 o'clock
            fill = QColor(108, 99, 255, 200 if i == self._hovered_index else 90)
            painter.setBrush(fill)
            painter.setPen(QPen(QColor(255, 255, 255, 60), 1))
            painter.drawPie(outer, int(start_angle_deg * 16), int(-segment_deg * 16))

        painter.setPen(QColor(255, 255, 255))
        painter.drawEllipse(center, self.dead_zone_radius, self.dead_zone_radius)
