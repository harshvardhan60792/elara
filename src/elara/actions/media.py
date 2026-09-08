"""media.* — thin wrappers over the platform adapter's media-key methods,
plus seek (no OS-level seek key exists, so it's approximated as a
scrub-sized jump via the keyboard adapter's focused-player hotkeys, which
most players — Spotify, VLC, browsers — honour on the currently focused
window). Actions never run in dry-run (ActionExecutor gates that), so these
call the adapter directly with no internal dry-run branching of their own.
"""

from __future__ import annotations

from elara.actions.registry import ActionRegistry, ActionSpec


def _play_pause(ctx) -> None:
    ctx.platform.media_play_pause()


def _next(ctx) -> None:
    ctx.platform.media_next()


def _prev(ctx) -> None:
    ctx.platform.media_prev()


def _stop(ctx) -> None:
    ctx.platform.media_stop()


def _seek_forward(ctx) -> None:
    from pynput.keyboard import Controller, Key

    Controller().tap(Key.right)


def _seek_back(ctx) -> None:
    from pynput.keyboard import Controller, Key

    Controller().tap(Key.left)


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("media.play_pause", "Play / Pause", "media", _play_pause))
    registry.register(ActionSpec("media.next", "Next track", "media", _next))
    registry.register(ActionSpec("media.prev", "Previous track", "media", _prev))
    registry.register(ActionSpec("media.stop", "Stop", "media", _stop))
    registry.register(ActionSpec("media.seek_forward", "Seek forward", "media", _seek_forward))
    registry.register(ActionSpec("media.seek_back", "Seek back", "media", _seek_back))
