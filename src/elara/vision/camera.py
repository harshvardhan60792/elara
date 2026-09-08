"""Frame sources. CameraSource and VideoFileSource yield raw BGR frames for
the landmarker to process. SynthSource is different in kind, not just
implementation: it has no image, so it skips inference entirely and hands
pre-baked landmarks straight to the engine (ADR-015) — that's what makes the
whole pipeline testable without a camera.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Protocol

import numpy as np


class FrameSource(Protocol):
    def read(self) -> np.ndarray | None: ...
    def close(self) -> None: ...
    def set_fps(self, fps: int) -> None: ...


class CameraSource:
    def __init__(self, device_index: int = 0, width: int = 640, height: int = 480) -> None:
        import cv2

        self._cv2 = cv2
        backend = cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else cv2.CAP_ANY
        self._cap = cv2.VideoCapture(device_index, backend)
        self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self) -> np.ndarray | None:
        ok, frame = self._cap.read()
        return frame if ok else None

    def close(self) -> None:
        self._cap.release()

    def set_fps(self, fps: int) -> None:
        self._cap.set(self._cv2.CAP_PROP_FPS, fps)

    @staticmethod
    def enumerate_devices(max_index: int = 6) -> list[int]:
        import cv2

        found = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else cv2.CAP_ANY)
            if cap.isOpened():
                found.append(i)
            cap.release()
        return found


class VideoFileSource:
    def __init__(self, path: str | Path, loop: bool = True, realtime: bool = True) -> None:
        import cv2

        self._cv2 = cv2
        self._path = str(path)
        self._loop = loop
        self._realtime = realtime
        self._cap = cv2.VideoCapture(self._path)
        fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._frame_interval = 1.0 / fps
        self._last_read_time: float | None = None

    def read(self) -> np.ndarray | None:
        if self._realtime and self._last_read_time is not None:
            elapsed = time.monotonic() - self._last_read_time
            remaining = self._frame_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)

        ok, frame = self._cap.read()
        if not ok:
            if self._loop:
                self._cap.set(self._cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self._cap.read()
            if not ok:
                return None

        self._last_read_time = time.monotonic()
        return frame

    def close(self) -> None:
        self._cap.release()

    def set_fps(self, fps: int) -> None:
        self._frame_interval = 1.0 / fps


class SynthSource:
    """Replays a JSON fixture produced by scripts/synth_landmarks.py.

    Two shapes are accepted: a single-frame fixture (a bare 21x3 list, for
    static poses) and a multi-frame fixture (a list of {"t", "landmarks"}
    dicts, for motion sequences). `landmarks` may be null on a frame to
    represent no hand present.
    """

    def __init__(self, path: str | Path) -> None:
        raw = json.loads(Path(path).read_text())
        if raw and isinstance(raw[0], dict):
            self._frames: list[tuple[float, np.ndarray | None]] = [
                (float(f["t"]), np.array(f["landmarks"], dtype=np.float64) if f["landmarks"] is not None else None)
                for f in raw
            ]
        else:
            self._frames = [(0.0, np.array(raw, dtype=np.float64))]
        self._index = 0

    def read_landmarks(self) -> tuple[float, np.ndarray | None] | None:
        if self._index >= len(self._frames):
            return None
        item = self._frames[self._index]
        self._index += 1
        return item

    def close(self) -> None:
        pass

    def set_fps(self, fps: int) -> None:
        pass

    def __len__(self) -> int:
        return len(self._frames)
