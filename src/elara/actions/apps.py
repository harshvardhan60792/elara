"""apps.* — a fuzzy-matched name -> path index built by scanning Start Menu
.lnk shortcuts once at startup (cached to the data dir), so "open vs code"
resolves to whatever the shortcut is actually named without an exact match.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from elara.actions.registry import ActionRegistry, ActionSpec
from elara.paths import data_dir

_START_MENU_DIRS = [
    Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs",
]


def _index_path() -> Path:
    return data_dir() / "app_index.json"


def build_app_index(force: bool = False) -> dict[str, str]:
    cache = _index_path()
    if cache.exists() and not force:
        return json.loads(cache.read_text())

    index: dict[str, str] = {}
    for start_dir in _START_MENU_DIRS:
        if not start_dir.exists():
            continue
        for lnk in start_dir.rglob("*.lnk"):
            name = lnk.stem
            index[name] = str(lnk)

    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(index, indent=2))
    return index


def _resolve(name: str) -> str | None:
    from rapidfuzz import process

    index = build_app_index()
    if not index:
        return None
    match = process.extractOne(name, list(index.keys()))
    if match is None:
        return None
    best_name, score, _idx = match
    if score < 60:
        return None
    return index[best_name]


def _launch(ctx, name: str = "") -> None:
    path = _resolve(name)
    if path is None:
        ctx.notify(f"No app matching '{name}'")
        return
    os.startfile(path)
    ctx.notify(f"Launching {name}")


def _switch_to(ctx, name: str = "") -> None:
    # Best-effort: launching the shortcut also focuses an already-running
    # instance for most apps (Windows' single-instance activation), so this
    # reuses _launch rather than duplicating window-enumeration logic.
    _launch(ctx, name)


def _close_active(ctx) -> None:
    ctx.platform.window_close()


def _radial_launcher(ctx) -> None:
    ctx.notify("App launcher radial menu is a Phase 3 UI feature")


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("apps.launch", "Launch app", "apps", _launch, slots=("name",)))
    registry.register(ActionSpec("apps.switch_to", "Switch to app", "apps", _switch_to, slots=("name",)))
    registry.register(ActionSpec("apps.close_active", "Close active app", "apps", _close_active))
    registry.register(ActionSpec("apps.radial_launcher", "App launcher", "apps", _radial_launcher))
