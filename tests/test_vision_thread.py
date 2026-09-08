from __future__ import annotations

from pathlib import Path

import pytest

from elara.app import build_context
from elara.config import Config
from elara.vision.camera import SynthSource
from elara.vision.engine import VisionEngine
from elara.vision.thread import VisionThread

FIXTURES = Path(__file__).parent / "fixtures" / "landmarks"


@pytest.mark.skipif(not FIXTURES.exists(), reason="run scripts/synth_landmarks.py first")
def test_vision_thread_runs_synth_source_to_completion_and_emits_events(qapp, qtbot):
    ctx = build_context(Config(), dry_run=True)
    received = []
    ctx.event_bus.gesture.connect(lambda e: received.append(e.id))

    def make_engine():
        source = SynthSource(FIXTURES / "swipe_left.json")
        return VisionEngine(source, ctx.config, ctx.event_bus)

    thread = VisionThread(make_engine)
    thread.start()

    qtbot.waitUntil(lambda: not thread.isRunning(), timeout=5000)

    assert "swipe_left" in received
