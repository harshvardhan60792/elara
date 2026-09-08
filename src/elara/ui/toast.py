"""Toast notifications: a small card near a screen corner, fade in/out,
stacked queue, auto-dismiss. Used for every executed action, gesture
rejections in learning mode, and voice transcripts (docs/GESTURES.md)."""

from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, QRect, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel

from elara.ui.overlay import OverlayWindow

FADE_MS = 200
DEFAULT_DURATION_MS = 1400
TOAST_WIDTH = 280
TOAST_HEIGHT = 48
MARGIN = 16
SPACING = 8


class Toast(OverlayWindow):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self.resize(TOAST_WIDTH, TOAST_HEIGHT)

        self._label = QLabel(text, self)
        self._label.setGeometry(0, 0, TOAST_WIDTH, TOAST_HEIGHT)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet(
            "background-color: rgba(30, 30, 34, 220); color: white;"
            "border-radius: 10px; padding: 8px; font-size: 13px;"
        )

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

    def play_in(self) -> QPropertyAnimation:
        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(FADE_MS)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start(QPropertyAnimation.DeletionPolicy.KeepWhenStopped)
        return anim

    def play_out(self) -> QPropertyAnimation:
        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(FADE_MS)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.start(QPropertyAnimation.DeletionPolicy.KeepWhenStopped)
        return anim


class ToastManager:
    """Owns the stacked queue of on-screen toasts, positioned bottom-right
    of the primary screen and shifted up as more stack."""

    def __init__(self, duration_ms: int = DEFAULT_DURATION_MS) -> None:
        self.duration_ms = duration_ms
        self._active: list[Toast] = []
        self._anims: list[QPropertyAnimation] = []  # keep references alive

    def show(self, text: str) -> Toast:
        from PySide6.QtGui import QGuiApplication

        toast = Toast(text)
        screen = QGuiApplication.primaryScreen()
        geometry = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

        index = len(self._active)
        x = geometry.right() - TOAST_WIDTH - MARGIN
        y = geometry.bottom() - MARGIN - (TOAST_HEIGHT + SPACING) * (index + 1)
        toast.move(x, y)

        self._active.append(toast)
        toast.show()
        self._anims.append(toast.play_in())

        QTimer.singleShot(self.duration_ms, lambda: self._dismiss(toast))
        return toast

    def _dismiss(self, toast: Toast) -> None:
        if toast not in self._active:
            return
        anim = toast.play_out()
        self._anims.append(anim)
        anim.finished.connect(lambda: self._remove(toast))

    def _remove(self, toast: Toast) -> None:
        if toast in self._active:
            self._active.remove(toast)
        toast.close()
        toast.deleteLater()

    def active_count(self) -> int:
        return len(self._active)
