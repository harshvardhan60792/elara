"""cursor.* — discrete mouse actions. The continuous cursor *position*
(index fingertip -> screen coords, One Euro filtered) is driven directly
from ContinuousUpdate in Phase 4 (T040), bypassing the action registry
entirely since it's per-frame state, not a discrete event; these are just
the click/scroll/drag verbs a gesture or voice command can fire."""

from __future__ import annotations

from elara.actions.registry import ActionRegistry, ActionSpec


def _toggle(ctx) -> None:
    active = not ctx.stats.get("cursor_active", False)
    ctx.stats["cursor_active"] = active
    ctx.notify("Cursor mode " + ("on" if active else "off"))


def _left_click(ctx) -> None:
    from pynput.mouse import Button, Controller

    Controller().click(Button.left)


def _right_click(ctx) -> None:
    from pynput.mouse import Button, Controller

    Controller().click(Button.right)


def _double_click(ctx) -> None:
    from pynput.mouse import Button, Controller

    Controller().click(Button.left, 2)


def _drag_toggle(ctx) -> None:
    from pynput.mouse import Button, Controller

    mouse = Controller()
    dragging = not ctx.stats.get("cursor_dragging", False)
    ctx.stats["cursor_dragging"] = dragging
    if dragging:
        mouse.press(Button.left)
    else:
        mouse.release(Button.left)


def _scroll_up(ctx) -> None:
    from pynput.mouse import Controller

    Controller().scroll(0, 2)


def _scroll_down(ctx) -> None:
    from pynput.mouse import Controller

    Controller().scroll(0, -2)


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("cursor.toggle", "Cursor mode toggle", "cursor", _toggle))
    registry.register(ActionSpec("cursor.left_click", "Left click", "cursor", _left_click))
    registry.register(ActionSpec("cursor.right_click", "Right click", "cursor", _right_click))
    registry.register(ActionSpec("cursor.double_click", "Double click", "cursor", _double_click))
    registry.register(ActionSpec("cursor.drag_toggle", "Drag toggle", "cursor", _drag_toggle))
    registry.register(ActionSpec("cursor.scroll_up", "Scroll up", "cursor", _scroll_up))
    registry.register(ActionSpec("cursor.scroll_down", "Scroll down", "cursor", _scroll_down))
