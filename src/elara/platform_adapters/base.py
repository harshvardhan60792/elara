"""Platform adapter interface (docs/ARCHITECTURE.md capability matrix).
Every method raises NotImplementedError by default; a concrete adapter only
overrides what it actually implements. `supported` is a single per-adapter
flag (not per-method) — macOS/Linux stubs import cleanly and report
`supported = False` so the app still runs; Windows is the v1 target.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AppInfo:
    name: str
    pid: int | None
    exe_path: str | None


class PlatformAdapter:
    supported: bool = False

    # -- Volume --
    def volume_up(self, step: int = 5) -> None:
        raise NotImplementedError

    def volume_down(self, step: int = 5) -> None:
        raise NotImplementedError

    def volume_set(self, percent: int) -> None:
        raise NotImplementedError

    def volume_get(self) -> float:
        raise NotImplementedError

    def volume_mute_toggle(self) -> None:
        raise NotImplementedError

    # -- Media keys --
    def media_play_pause(self) -> None:
        raise NotImplementedError

    def media_next(self) -> None:
        raise NotImplementedError

    def media_prev(self) -> None:
        raise NotImplementedError

    def media_stop(self) -> None:
        raise NotImplementedError

    # -- Brightness --
    def brightness_up(self, step: int = 10) -> None:
        raise NotImplementedError

    def brightness_down(self, step: int = 10) -> None:
        raise NotImplementedError

    def brightness_set(self, percent: int) -> None:
        raise NotImplementedError

    def brightness_get(self) -> float:
        raise NotImplementedError

    # -- Lock / sleep --
    def lock(self) -> None:
        raise NotImplementedError

    def sleep_display(self) -> None:
        raise NotImplementedError

    # -- Foreground app / windows --
    def get_foreground_app(self) -> AppInfo:
        raise NotImplementedError

    def window_minimize(self) -> None:
        raise NotImplementedError

    def window_maximize(self) -> None:
        raise NotImplementedError

    def window_close(self) -> None:
        raise NotImplementedError

    def window_snap_left(self) -> None:
        raise NotImplementedError

    def window_snap_right(self) -> None:
        raise NotImplementedError

    def window_switch_next(self) -> None:
        raise NotImplementedError

    def window_switch_prev(self) -> None:
        raise NotImplementedError

    def show_desktop(self) -> None:
        raise NotImplementedError

    # -- Do not disturb --
    def dnd_set(self, enabled: bool) -> None:
        raise NotImplementedError

    def dnd_get(self) -> bool:
        raise NotImplementedError
