"""Wires everything the startup sequence needs (docs/ARCHITECTURE.md):
config, registry + built-in actions, platform adapter, executor, router
with default bindings, and (once armed) the vision engine. Kept separate
from __main__.py so tests can build a full context without going through
argv parsing or QApplication.
"""

from __future__ import annotations

from elara.actions.builtin import register_all
from elara.actions.executor import ActionExecutor
from elara.actions.registry import ActionRegistry
from elara.app import AppContext, build_context
from elara.config import Config
from elara.core.cursor import CursorController
from elara.core.pinch_scrub import PinchScrubController
from elara.core.router import Router
from elara.platform_adapters import get_adapter

# The Desktop profile's default bindings (docs/GESTURES.md). Real
# per-profile switching lands in Phase 5 (ProfileManager); until then this
# is the single active binding set.
DEFAULT_BINDINGS: dict[str, str] = {
    "swipe_left": "window.switch_prev",
    "swipe_right": "window.switch_next",
    "point": "cursor.toggle",
    "fist": "volume.mute_toggle",
    "thumbs_up": "volume.up",
    "thumbs_down": "volume.down",
    "push": "elara.panic_disarm",
}


def build_full_context(config: Config | None = None, dry_run: bool = True) -> tuple[AppContext, Router]:
    ctx = build_context(config or Config(), dry_run=dry_run)

    registry = ActionRegistry()
    register_all(registry)
    ctx.registry = registry

    try:
        ctx.platform = get_adapter()
    except Exception:  # noqa: BLE001 — platform construction touches real OS/COM state
        ctx.platform = None

    executor = ActionExecutor(registry, ctx)
    ctx.executor = executor

    router = Router(registry, executor, ctx, bindings=dict(DEFAULT_BINDINGS))
    router.connect(ctx.event_bus)

    cursor_controller = CursorController(ctx)
    pinch_scrub_controller = PinchScrubController(ctx)
    ctx.event_bus.continuous_update.connect(cursor_controller.handle_continuous)
    ctx.event_bus.continuous_update.connect(pinch_scrub_controller.handle_continuous)
    # Continuous consumers bypass the arming gate entirely (ADR per
    # ARCHITECTURE.md) and aren't reachable through ctx alone otherwise —
    # anchor them the same way Router anchors itself, or they'd be GC'd.
    ctx.cursor_controller = cursor_controller
    ctx.pinch_scrub_controller = pinch_scrub_controller

    return ctx, router
