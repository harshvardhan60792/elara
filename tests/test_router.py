from __future__ import annotations

from elara.actions.executor import ActionExecutor
from elara.actions.registry import ActionRegistry, ActionSpec
from elara.app import build_context
from elara.config import Config
from elara.core.router import Router
from elara.events import GestureEvent


def _swipe_left_event() -> GestureEvent:
    return GestureEvent(id="swipe_left", hand="right", confidence=1.0, position=(0.1, 0.5), timestamp=1.0)


def test_bound_gesture_fires_exactly_one_action_when_armed():
    registry = ActionRegistry()
    registry.register(ActionSpec("media.prev", "Previous track", "media", lambda ctx: None))

    ctx = build_context(Config(), dry_run=True)
    ctx.armed = True
    executor = ActionExecutor(registry, ctx)
    router = Router(registry, executor, ctx, bindings={"swipe_left": "media.prev"})

    router.handle_gesture(_swipe_left_event())

    assert len(executor.dry_run_log) == 1
    assert executor.dry_run_log[0].action_id == "media.prev"


def test_bound_gesture_fires_nothing_when_disarmed():
    registry = ActionRegistry()
    registry.register(ActionSpec("media.prev", "Previous track", "media", lambda ctx: None))

    ctx = build_context(Config(), dry_run=True)
    ctx.armed = False
    executor = ActionExecutor(registry, ctx)
    router = Router(registry, executor, ctx, bindings={"swipe_left": "media.prev"})

    router.handle_gesture(_swipe_left_event())

    assert executor.dry_run_log == []


def test_unbound_gesture_is_ignored():
    registry = ActionRegistry()
    ctx = build_context(Config(), dry_run=True)
    ctx.armed = True
    executor = ActionExecutor(registry, ctx)
    router = Router(registry, executor, ctx, bindings={})

    router.handle_gesture(_swipe_left_event())

    assert executor.dry_run_log == []
