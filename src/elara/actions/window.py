"""window.* and desktop.* — thin wrappers over the platform adapter's
window-management methods. Virtual-desktop switching has no stable public
Win32 API (the shell interfaces involved are undocumented COM), so
desktop.next/prev fall back to the well-known Ctrl+Win+Arrow shortcut via
the keyboard adapter, which works identically to a native call."""

from __future__ import annotations

from elara.actions._keys import press_combo
from elara.actions.registry import ActionRegistry, ActionSpec


def _switch_next(ctx) -> None:
    ctx.platform.window_switch_next()


def _switch_prev(ctx) -> None:
    ctx.platform.window_switch_prev()


def _minimize(ctx) -> None:
    ctx.platform.window_minimize()


def _maximize(ctx) -> None:
    ctx.platform.window_maximize()


def _close(ctx) -> None:
    ctx.platform.window_close()


def _snap_left(ctx) -> None:
    ctx.platform.window_snap_left()


def _snap_right(ctx) -> None:
    ctx.platform.window_snap_right()


def _show_desktop(ctx) -> None:
    ctx.platform.show_desktop()


def _desktop_next(ctx) -> None:
    from pynput.keyboard import Key

    press_combo(Key.ctrl, Key.cmd, Key.right)


def _desktop_prev(ctx) -> None:
    from pynput.keyboard import Key

    press_combo(Key.ctrl, Key.cmd, Key.left)


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("window.switch_next", "Next window", "window", _switch_next))
    registry.register(ActionSpec("window.switch_prev", "Previous window", "window", _switch_prev))
    registry.register(ActionSpec("window.minimize", "Minimize window", "window", _minimize))
    registry.register(ActionSpec("window.maximize", "Maximize window", "window", _maximize))
    registry.register(ActionSpec("window.close", "Close window", "window", _close))
    registry.register(ActionSpec("window.snap_left", "Snap window left", "window", _snap_left))
    registry.register(ActionSpec("window.snap_right", "Snap window right", "window", _snap_right))
    registry.register(ActionSpec("window.show_desktop", "Show desktop", "window", _show_desktop))
    registry.register(ActionSpec("desktop.next", "Next virtual desktop", "window", _desktop_next))
    registry.register(ActionSpec("desktop.prev", "Previous virtual desktop", "window", _desktop_prev))
