from __future__ import annotations

import time

import numpy as np
import pytest

from elara.paths import models_dir
from elara.vision.landmarker import (
    DEFAULT_MODEL_NAME,
    HandLandmarkerWrapper,
    result_to_landmark_arrays,
)

_MODEL_PATH = models_dir() / DEFAULT_MODEL_NAME

pytestmark = pytest.mark.skipif(
    not _MODEL_PATH.exists(),
    reason=f"hand landmarker model not present at {_MODEL_PATH}; run scripts/fetch_models.py",
)


def test_solid_color_frame_produces_zero_hands():
    wrapper = HandLandmarkerWrapper()
    try:
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        wrapper.submit(frame)

        result = None
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            polled = wrapper.poll()
            if polled is not None:
                result = polled
                break
            time.sleep(0.05)

        assert result is not None, "no result arrived from the async callback within 5s"
        _timestamp_ms, mp_result = result
        arrays = result_to_landmark_arrays(mp_result)
        assert arrays == []
    finally:
        wrapper.close()


def test_missing_model_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        HandLandmarkerWrapper(model_path=tmp_path / "does_not_exist.task")
