"""meeting.* — per-app hotkey maps, keyed by the foreground app's process
name. Each meeting app picks its own mute/camera/hand/leave shortcuts, so
there's no single OS-level hotkey to hook; we read the foreground app via
the platform adapter and dispatch accordingly."""

from __future__ import annotations

from elara.actions._keys import press_combo
from elara.actions.registry import ActionRegistry, ActionSpec

# process name (lowercase, no .exe) -> {intent: (modifiers, key)}
_HOTKEYS: dict[str, dict[str, tuple[tuple[str, ...], str]]] = {
    "zoom": {
        "mute_toggle": (("alt",), "a"),
        "camera_toggle": (("alt",), "v"),
        "raise_hand": (("alt",), "y"),
        "leave": (("alt",), "q"),
        "share_screen": (("alt",), "s"),
    },
    "teams": {
        "mute_toggle": (("ctrl", "shift"), "m"),
        "camera_toggle": (("ctrl", "shift"), "o"),
        "raise_hand": (("ctrl", "shift"), "k"),
        "leave": (("ctrl", "shift"), "h"),
        "share_screen": (("ctrl", "shift"), "e"),
    },
    "chrome": {  # covers Google Meet running in Chrome
        "mute_toggle": (("ctrl",), "d"),
        "camera_toggle": (("ctrl",), "e"),
        "leave": (("ctrl",), "h"),
    },
}


def _dispatch(ctx, intent: str) -> None:
    app = ctx.platform.get_foreground_app()
    proc = (app.name or "").lower().removesuffix(".exe")
    hotkeys = _HOTKEYS.get(proc)
    if hotkeys is None or intent not in hotkeys:
        ctx.notify(f"No {intent} hotkey known for {app.name}")
        return

    from pynput.keyboard import Key

    modifier_keys = {"alt": Key.alt, "ctrl": Key.ctrl, "shift": Key.shift, "cmd": Key.cmd}
    modifiers, key = hotkeys[intent]
    press_combo(*(modifier_keys[m] for m in modifiers), key)


def _mute_toggle(ctx) -> None:
    _dispatch(ctx, "mute_toggle")


def _camera_toggle(ctx) -> None:
    _dispatch(ctx, "camera_toggle")


def _raise_hand(ctx) -> None:
    _dispatch(ctx, "raise_hand")


def _leave(ctx) -> None:
    _dispatch(ctx, "leave")


def _share_screen(ctx) -> None:
    _dispatch(ctx, "share_screen")


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("meeting.mute_toggle", "Mute / unmute mic", "meeting", _mute_toggle))
    registry.register(ActionSpec("meeting.camera_toggle", "Camera on / off", "meeting", _camera_toggle))
    registry.register(ActionSpec("meeting.raise_hand", "Raise hand", "meeting", _raise_hand))
    registry.register(
        ActionSpec("meeting.leave", "Leave meeting", "meeting", _leave, needs_confirm=True)
    )
    registry.register(ActionSpec("meeting.share_screen", "Share screen", "meeting", _share_screen))
