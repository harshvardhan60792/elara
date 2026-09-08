"""Camera preview widget: draws the raw frame with the hand skeleton, pose
name, confidence, FPS and CPU% overlaid. Used in onboarding and settings.
Wraps the numpy BGR buffer directly in a QImage rather than round-tripping
through PIL per frame — that conversion is cheap enough to matter at 30 FPS.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

# MediaPipe hand connections: (start_index, end_index) pairs.
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
)


class PreviewWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._frame_bgr: np.ndarray | None = None
        self._landmarks_px: np.ndarray | None = None
        self._pose_name: str = ""
        self._confidence: float = 0.0
        self._fps: float = 0.0
        self._cpu_percent: float = 0.0
        self.setMinimumSize(320, 240)

    def update_frame(
        self,
        frame_bgr: np.ndarray,
        landmarks_px: np.ndarray | None = None,
        pose_name: str = "",
        confidence: float = 0.0,
        fps: float = 0.0,
        cpu_percent: float = 0.0,
    ) -> None:
        self._frame_bgr = frame_bgr
        self._landmarks_px = landmarks_px
        self._pose_name = pose_name
        self._confidence = confidence
        self._fps = fps
        self._cpu_percent = cpu_percent
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        try:
            if self._frame_bgr is not None:
                self._draw_frame(painter)
                if self._landmarks_px is not None:
                    self._draw_skeleton(painter)
            else:
                painter.fillRect(self.rect(), QColor(20, 20, 20))
            self._draw_hud(painter)
        finally:
            painter.end()

    def _draw_frame(self, painter: QPainter) -> None:
        frame = self._frame_bgr
        h, w = frame.shape[:2]
        rgb = np.ascontiguousarray(frame[:, :, ::-1])
        image = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888)
        target = self.rect()
        painter.drawImage(target, image, image.rect())

    def _draw_skeleton(self, painter: QPainter) -> None:
        pts = self._landmarks_px
        pen = QPen(QColor(108, 99, 255))
        pen.setWidth(2)
        painter.setPen(pen)
        for a, b in HAND_CONNECTIONS:
            painter.drawLine(int(pts[a][0]), int(pts[a][1]), int(pts[b][0]), int(pts[b][1]))
        painter.setBrush(QColor(255, 255, 255))
        for x, y in pts:
            painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)

    def _draw_hud(self, painter: QPainter) -> None:
        painter.setPen(QColor(255, 255, 255))
        lines = [
            f"{self._pose_name or '—'}  ({self._confidence:.2f})",
            f"{self._fps:.1f} FPS  ·  {self._cpu_percent:.0f}% CPU",
        ]
        for i, line in enumerate(lines):
            painter.drawText(8, 18 + i * 16, line)
