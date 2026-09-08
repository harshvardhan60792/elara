"""text.* — clipboard/edit hotkeys, typed dictation slot, and optional
text-to-speech for the current selection. TTS degrades gracefully: pyttsx3
lives in requirements-voice.txt, not the base install, so voice-off users
never pull it in."""

from __future__ import annotations

import time

from elara.actions.registry import ActionRegistry, ActionSpec


def _copy(ctx) -> None:
    from pynput.keyboard import Controller, Key

    kb = Controller()
    with kb.pressed(Key.ctrl):
        kb.tap("c")


def _paste(ctx) -> None:
    from pynput.keyboard import Controller, Key

    kb = Controller()
    with kb.pressed(Key.ctrl):
        kb.tap("v")


def _cut(ctx) -> None:
    from pynput.keyboard import Controller, Key

    kb = Controller()
    with kb.pressed(Key.ctrl):
        kb.tap("x")


def _undo(ctx) -> None:
    from pynput.keyboard import Controller, Key

    kb = Controller()
    with kb.pressed(Key.ctrl):
        kb.tap("z")


def _type(ctx, text: str = "") -> None:
    from pynput.keyboard import Controller

    Controller().type(text)


def _dictation_toggle(ctx) -> None:
    active = not ctx.stats.get("dictation_active", False)
    ctx.stats["dictation_active"] = active
    ctx.notify("Dictation " + ("on" if active else "off"))


def _read_selection_aloud(ctx) -> None:
    from pynput.keyboard import Controller, Key

    kb = Controller()
    with kb.pressed(Key.ctrl):
        kb.tap("c")
    time.sleep(0.05)  # give the OS clipboard time to update before reading it back

    try:
        import win32clipboard  # pywin32 — already a base dependency on Windows

        win32clipboard.OpenClipboard()
        try:
            selection = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        finally:
            win32clipboard.CloseClipboard()
    except ImportError:
        ctx.notify("Read-aloud needs pywin32 (Windows only)")
        return

    try:
        import pyttsx3
    except ImportError:
        ctx.notify("Read-aloud needs pyttsx3 (requirements-voice.txt)")
        return

    engine = pyttsx3.init()
    engine.say(selection)
    engine.runAndWait()


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("text.copy", "Copy", "text", _copy))
    registry.register(ActionSpec("text.paste", "Paste", "text", _paste))
    registry.register(ActionSpec("text.cut", "Cut", "text", _cut))
    registry.register(ActionSpec("text.undo", "Undo", "text", _undo))
    registry.register(ActionSpec("text.type", "Type text", "text", _type, slots=("text",)))
    registry.register(ActionSpec("text.dictation_toggle", "Dictation toggle", "text", _dictation_toggle))
    registry.register(
        ActionSpec("text.read_selection_aloud", "Read selection aloud", "text", _read_selection_aloud)
    )
