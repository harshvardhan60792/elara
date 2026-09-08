"""Wraps mp.tasks.vision.HandLandmarker in LIVE_STREAM mode (ADR-004): the
model tracks hands between frames instead of re-running palm detection every
frame, which is materially cheaper. The result callback is async and must
never block, so it pushes onto a small bounded queue and drops the oldest
entry on overflow rather than stalling MediaPipe's worker thread.

Timestamps passed to detect_async must be monotonically increasing integer
milliseconds or MediaPipe raises — callers must derive them from a frame
counter, never wall-clock reads that could go backwards or repeat.
"""

from __future__ import annotations

import contextlib
import queue
from pathlib import Path

import numpy as np

from elara.paths import models_dir

DEFAULT_MODEL_NAME = "hand_landmarker.task"


class HandLandmarkerWrapper:
    def __init__(
        self,
        model_path: str | Path | None = None,
        num_hands: int = 2,
        min_hand_detection_confidence: float = 0.5,
        min_hand_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        import mediapipe as mp

        self._mp = mp
        resolved = Path(model_path) if model_path else models_dir() / DEFAULT_MODEL_NAME
        if not resolved.exists():
            raise FileNotFoundError(
                f"hand landmarker model not found at {resolved}; run scripts/fetch_models.py"
            )

        self._results: queue.Queue = queue.Queue(maxsize=2)

        base = mp.tasks.BaseOptions(model_asset_path=str(resolved))
        opts = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base,
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=num_hands,
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_hand_presence_confidence=min_hand_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
            result_callback=self._on_result,
        )
        self._landmarker = mp.tasks.vision.HandLandmarker.create_from_options(opts)
        self._frame_counter = 0

    def _on_result(self, result, output_image, timestamp_ms: int) -> None:
        try:
            self._results.put_nowait((timestamp_ms, result))
        except queue.Full:
            with contextlib.suppress(queue.Empty):
                self._results.get_nowait()
            with contextlib.suppress(queue.Full):
                self._results.put_nowait((timestamp_ms, result))

    def submit(self, frame_bgr: np.ndarray) -> int:
        mp = self._mp
        rgb = frame_bgr[:, :, ::-1]
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        timestamp_ms = self._frame_counter
        self._frame_counter += 1
        self._landmarker.detect_async(mp_image, timestamp_ms)
        return timestamp_ms

    def poll(self):
        try:
            return self._results.get_nowait()
        except queue.Empty:
            return None

    def close(self) -> None:
        self._landmarker.close()


def result_to_landmark_arrays(result) -> list[np.ndarray]:
    """Converts a HandLandmarkerResult into a list of (21, 3) arrays, one
    per detected hand, in the order MediaPipe returned them."""
    arrays = []
    for hand in result.hand_landmarks:
        arrays.append(np.array([[lm.x, lm.y, lm.z] for lm in hand], dtype=np.float64))
    return arrays
