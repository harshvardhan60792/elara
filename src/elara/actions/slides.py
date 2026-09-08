"""slides.* — PowerPoint's own slideshow keyboard shortcuts, which fire
identically whether the slideshow window has native or borrowed focus.
Google Slides / Keynote support is the same shortcut set for next/prev/
start/end, which is why this isn't PowerPoint-specific despite the module
name matching the profile."""

from __future__ import annotations

from elara.actions._keys import press_combo as _key
from elara.actions.registry import ActionRegistry, ActionSpec


def _next(ctx) -> None:
    from pynput.keyboard import Key

    _key(Key.right)


def _prev(ctx) -> None:
    from pynput.keyboard import Key

    _key(Key.left)


def _start(ctx) -> None:
    from pynput.keyboard import Key

    _key(Key.f5)


def _end(ctx) -> None:
    from pynput.keyboard import Key

    _key(Key.esc)


def _black_screen(ctx) -> None:
    _key("b")


def _laser_toggle(ctx) -> None:
    from pynput.keyboard import Key

    _key(Key.ctrl, "l")


def _annotate_toggle(ctx) -> None:
    from pynput.keyboard import Key

    _key(Key.ctrl, "p")


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("slides.next", "Next slide", "slides", _next))
    registry.register(ActionSpec("slides.prev", "Previous slide", "slides", _prev))
    registry.register(ActionSpec("slides.start", "Start slideshow", "slides", _start))
    registry.register(ActionSpec("slides.end", "End slideshow", "slides", _end))
    registry.register(ActionSpec("slides.black_screen", "Black screen", "slides", _black_screen))
    registry.register(ActionSpec("slides.laser_toggle", "Laser pointer toggle", "slides", _laser_toggle))
    registry.register(ActionSpec("slides.annotate_toggle", "Annotate toggle", "slides", _annotate_toggle))
