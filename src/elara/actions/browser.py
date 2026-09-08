"""browser.* — standard browser hotkeys via the keyboard adapter, plus
`browser.search` which opens the system default browser directly rather
than relying on the foreground window being a browser at all."""

from __future__ import annotations

from elara.actions._keys import press_combo as _hotkey
from elara.actions.registry import ActionRegistry, ActionSpec


def _new_tab(ctx) -> None:
    from pynput.keyboard import Key

    _hotkey(Key.ctrl, "t")


def _close_tab(ctx) -> None:
    from pynput.keyboard import Key

    _hotkey(Key.ctrl, "w")


def _next_tab(ctx) -> None:
    from pynput.keyboard import Key

    _hotkey(Key.ctrl, Key.tab)


def _prev_tab(ctx) -> None:
    from pynput.keyboard import Key

    _hotkey(Key.ctrl, Key.shift, Key.tab)


def _back(ctx) -> None:
    from pynput.keyboard import Key

    _hotkey(Key.alt, Key.left)


def _forward(ctx) -> None:
    from pynput.keyboard import Key

    _hotkey(Key.alt, Key.right)


def _reload(ctx) -> None:
    from pynput.keyboard import Key

    _hotkey(Key.f5)


def _search(ctx, query: str = "") -> None:
    import urllib.parse
    import webbrowser

    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("browser.new_tab", "New tab", "browser", _new_tab))
    registry.register(ActionSpec("browser.close_tab", "Close tab", "browser", _close_tab))
    registry.register(ActionSpec("browser.next_tab", "Next tab", "browser", _next_tab))
    registry.register(ActionSpec("browser.prev_tab", "Previous tab", "browser", _prev_tab))
    registry.register(ActionSpec("browser.back", "Back", "browser", _back))
    registry.register(ActionSpec("browser.forward", "Forward", "browser", _forward))
    registry.register(ActionSpec("browser.reload", "Reload", "browser", _reload))
    registry.register(ActionSpec("browser.search", "Search the web", "browser", _search, slots=("query",)))
