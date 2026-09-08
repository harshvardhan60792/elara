"""SynthSource -> VisionEngine -> ArmingGate -> Router -> ActionExecutor,
wired end to end and driven by real fixture files from
scripts/synth_landmarks.py. This is the regression net (ADR-015): it must
stay green for the rest of the project, since it's the only test that
proves the whole discrete-gesture pipeline actually works together.

Every test here takes the `qapp` fixture even though none of them touch a
widget: EventBus signal delivery silently no-ops without a live
QApplication instance (PySide6 falls back to a connection type that needs
a running event loop to flush), so a test with no QApplication anywhere in
the session passes the emit() call but the connected slot never runs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from elara.actions.executor import ActionExecutor
from elara.actions.registry import ActionRegistry, ActionSpec
from elara.app import build_context
from elara.config import Config
from elara.core.router import Router
from elara.vision.camera import SynthSource
from elara.vision.engine import VisionEngine

FIXTURES = Path(__file__).parent / "fixtures" / "landmarks"


def _build_pipeline(bindings: dict[str, str]):
    registry = ActionRegistry()
    for action_id in set(bindings.values()):
        registry.register(ActionSpec(action_id, action_id, "test", lambda ctx: None))

    ctx = build_context(Config(), dry_run=True)
    ctx.armed = True
    executor = ActionExecutor(registry, ctx)
    router = Router(registry, executor, ctx, bindings=bindings)
    router.connect(ctx.event_bus)

    source = SynthSource(FIXTURES / "swipe_left.json")
    engine = VisionEngine(source, ctx.config, ctx.event_bus)
    return engine, executor


@pytest.mark.skipif(not FIXTURES.exists(), reason="run scripts/synth_landmarks.py first")
def test_swipe_left_fixture_fires_bound_action_exactly_once(qapp):
    engine, executor = _build_pipeline({"swipe_left": "media.prev"})
    engine.run_to_completion()

    fired = [r.action_id for r in executor.dry_run_log]
    assert fired == ["media.prev"]


@pytest.mark.skipif(not FIXTURES.exists(), reason="run scripts/synth_landmarks.py first")
def test_open_palm_static_pose_fires_bound_action_once(qapp):
    registry = ActionRegistry()
    registry.register(ActionSpec("elara.show_help", "Help", "test", lambda ctx: None))

    ctx = build_context(Config(), dry_run=True)
    ctx.armed = True
    executor = ActionExecutor(registry, ctx)
    router = Router(registry, executor, ctx, bindings={"open_palm": "elara.show_help"})
    router.connect(ctx.event_bus)

    source = SynthSource(FIXTURES / "held_open_palm.json")
    engine = VisionEngine(source, ctx.config, ctx.event_bus)
    engine.run_to_completion()

    fired = [r.action_id for r in executor.dry_run_log]
    assert fired == ["elara.show_help"]


@pytest.mark.skipif(not FIXTURES.exists(), reason="run scripts/synth_landmarks.py first")
def test_slow_drift_negative_fires_nothing(qapp):
    engine, executor = _build_pipeline({"swipe_left": "media.prev", "swipe_right": "media.next"})
    engine.source = SynthSource(FIXTURES / "neg_slow_drift.json")
    engine.run_to_completion()

    assert executor.dry_run_log == []


@pytest.mark.skipif(not FIXTURES.exists(), reason="run scripts/synth_landmarks.py first")
def test_disarmed_fires_nothing_even_for_a_real_swipe(qapp):
    engine, executor = _build_pipeline({"swipe_left": "media.prev"})
    executor.ctx.armed = False

    engine.run_to_completion()

    assert executor.dry_run_log == []
