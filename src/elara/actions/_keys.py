"""Shared key-combo helper for action modules that send hotkeys (browser,
slides, media seek, window desktop-switch). Not a public API — leading
underscore is deliberate."""

from __future__ import annotations


def press_combo(*keys) -> None:
    from pynput.keyboard import Controller

    kb = Controller()

    def _press_rest(remaining: list) -> None:
        if len(remaining) == 1:
            kb.tap(remaining[0])
            return
        with kb.pressed(remaining[0]):
            _press_rest(remaining[1:])

    _press_rest(list(keys))
