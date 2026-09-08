from __future__ import annotations

import numpy as np

from elara.ui.preview import PreviewWidget


def test_preview_renders_one_frame_without_exception(qapp):
    widget = PreviewWidget()
    widget.resize(320, 240)

    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    landmarks_px = np.array([[160 + i, 120 + i] for i in range(21)], dtype=np.float64)

    widget.update_frame(frame, landmarks_px, pose_name="fist", confidence=0.9, fps=29.5, cpu_percent=12.0)
    widget.grab()  # forces a real paintEvent


def test_preview_renders_with_no_frame_yet(qapp):
    widget = PreviewWidget()
    widget.resize(320, 240)
    widget.grab()
