from __future__ import annotations

from pathlib import Path

import pytest

from elara.app import build_context
from elara.config import Config
from elara.events import StateChanged
from elara.vision.thread import VisionSupervisor

FIXTURES = Path(__file__).parent / "fixtures" / "landmarks"


@pytest.mark.skipif(not FIXTURES.exists(), reason="run scripts/synth_landmarks.py first")
def test_supervisor_starts_and_stops_on_state_changed(qapp, qtbot):
    ctx = build_context(Config(), dry_run=True)
    supervisor = VisionSupervisor(ctx, source_spec=f"synth:{FIXTURES / 'held_open_palm.json'}")

    supervisor.on_state_changed(StateChanged(armed=True))
    assert supervisor._thread is not None
    assert supervisor._thread.isRunning()

    supervisor.on_state_changed(StateChanged(armed=False))
    assert supervisor._thread is None


def test_start_is_idempotent_while_running(qapp, qtbot):
    ctx = build_context(Config(), dry_run=True)
    supervisor = VisionSupervisor(ctx, source_spec="synth:" + str(FIXTURES / "swipe_left.json"))

    supervisor.start()
    first_thread = supervisor._thread
    supervisor.start()
    assert supervisor._thread is first_thread

    supervisor.stop()
