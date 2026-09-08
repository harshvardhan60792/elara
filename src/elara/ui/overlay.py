"""Frameless, translucent, always-on-top, click-through overlay base.
Everything drawn over the user's other windows (toasts, radial menu) is a
child of this. `Qt.WindowTransparentForInput` + `Qt.Tool` are what make it
never steal focus or appear in alt-tab — critical, since stealing focus
would break the entire pitch (you couldn't swipe to change a PowerPoint
slide if the overlay stole focus from the slideshow)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


class OverlayWindow(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

    def screen_for_point(self, point) -> object:
        screen = QGuiApplication.screenAt(point)
        return screen or QGuiApplication.primaryScreen()

    def move_to_point(self, point, center: bool = True) -> None:
        screen = self.screen_for_point(point)
        geometry = screen.availableGeometry()

        x, y = point.x(), point.y()
        if center:
            x -= self.width() // 2
            y -= self.height() // 2

        x = max(geometry.left(), min(x, geometry.right() - self.width()))
        y = max(geometry.top(), min(y, geometry.bottom() - self.height()))
        self.move(x, y)
