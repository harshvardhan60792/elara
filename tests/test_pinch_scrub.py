from __future__ import annotations

from elara.actions.executor import ActionExecutor
from elara.actions.registry import ActionRegistry, ActionSpec
from elara.app import build_context
from elara.config import Config
from elara.core.pinch_scrub import PinchScrubController
from elara.events import ContinuousUpdate


def _make_ctx_with_executor():
    registry = ActionRegistry()
    registry.register(ActionSpec("volume.scrub", "Volume scrub", "volume", lambda ctx, value=0.5: None))
    ctx = build_context(Config(), dry_run=True)
    ctx.armed = True
    ctx.executor = ActionExecutor(registry, ctx)
    return ctx


def test_does_not_engage_below_threshold():
    ctx = _make_ctx_with_executor()
    controller = PinchScrubController(ctx)
    controller.handle_continuous(ContinuousUpdate(channel="pinch_scrub", value=0.3, position=(0.5, 0.5)))
    assert ctx.executor.dry_run_log == []


def test_engages_above_threshold_and_executes():
    ctx = _make_ctx_with_executor()
    controller = PinchScrubController(ctx)
    controller.handle_continuous(ContinuousUpdate(channel="pinch_scrub", value=0.9, position=(0.5, 0.5)))
    assert len(ctx.executor.dry_run_log) == 1
    assert ctx.executor.dry_run_log[0].action_id == "volume.scrub"


def test_stays_engaged_through_hysteresis_band():
    ctx = _make_ctx_with_executor()
    controller = PinchScrubController(ctx)
    controller.handle_continuous(ContinuousUpdate(channel="pinch_scrub", value=0.9, position=(0.5, 0.5)))
    controller.handle_continuous(ContinuousUpdate(channel="pinch_scrub", value=0.4, position=(0.5, 0.5)))
    controller.handle_continuous(ContinuousUpdate(channel="pinch_scrub", value=0.9, position=(0.5, 0.5)))
    assert len(ctx.executor.dry_run_log) == 3  # engaged the whole time, fires every update


def test_releases_below_release_threshold():
    ctx = _make_ctx_with_executor()
    controller = PinchScrubController(ctx)
    controller.handle_continuous(ContinuousUpdate(channel="pinch_scrub", value=0.9, position=(0.5, 0.5)))
    controller.handle_continuous(ContinuousUpdate(channel="pinch_scrub", value=0.1, position=(0.5, 0.5)))
    controller.handle_continuous(ContinuousUpdate(channel="pinch_scrub", value=0.5, position=(0.5, 0.5)))
    # 0.5 is between release(0.2) and engage(0.7), so once released it must
    # not re-engage until crossing the engage threshold again.
    assert len(ctx.executor.dry_run_log) == 1


def test_ignores_other_channels():
    ctx = _make_ctx_with_executor()
    controller = PinchScrubController(ctx)
    controller.handle_continuous(ContinuousUpdate(channel="cursor", value=0.9, position=(0.5, 0.5)))
    assert ctx.executor.dry_run_log == []


def test_disarmed_never_engages():
    ctx = _make_ctx_with_executor()
    ctx.armed = False
    controller = PinchScrubController(ctx)
    controller.handle_continuous(ContinuousUpdate(channel="pinch_scrub", value=0.95, position=(0.5, 0.5)))
    assert ctx.executor.dry_run_log == []
