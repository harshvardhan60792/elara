from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from elara.vision.camera import SynthSource, VideoFileSource

cv2 = pytest.importorskip("cv2")


@pytest.fixture
def ten_frame_video(tmp_path: Path) -> Path:
    path = tmp_path / "clip.avi"
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"MJPG"), 30.0, (16, 16)
    )
    for i in range(10):
        frame = np.full((16, 16, 3), i * 20, dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return path


def test_video_file_source_returns_ten_frames_then_loops(ten_frame_video: Path):
    src = VideoFileSource(ten_frame_video, loop=True, realtime=False)
    frames = [src.read() for _ in range(10)]
    assert all(f is not None for f in frames)
    assert len(frames) == 10

    looped = src.read()
    assert looped is not None
    src.close()


def test_video_file_source_no_loop_returns_none_at_end(ten_frame_video: Path):
    src = VideoFileSource(ten_frame_video, loop=False, realtime=False)
    for _ in range(10):
        assert src.read() is not None
    assert src.read() is None
    src.close()


def test_synth_source_single_pose(tmp_path: Path):
    path = tmp_path / "fist.json"
    path.write_text(json.dumps(np.zeros((21, 3)).tolist()))
    src = SynthSource(path)
    ts, landmarks = src.read_landmarks()
    assert ts == 0.0
    assert landmarks.shape == (21, 3)
    assert src.read_landmarks() is None


def test_synth_source_motion_sequence_with_gaps(tmp_path: Path):
    path = tmp_path / "motion.json"
    path.write_text(
        json.dumps(
            [
                {"t": 0.0, "landmarks": np.zeros((21, 3)).tolist()},
                {"t": 0.033, "landmarks": None},
                {"t": 0.066, "landmarks": np.ones((21, 3)).tolist()},
            ]
        )
    )
    src = SynthSource(path)
    assert len(src) == 3
    _, first = src.read_landmarks()
    assert first is not None
    _, second = src.read_landmarks()
    assert second is None
    _, third = src.read_landmarks()
    assert third is not None
