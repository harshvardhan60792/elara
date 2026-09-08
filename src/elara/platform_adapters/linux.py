"""Linux stub. Imports cleanly and reports `supported = False` so the app
still runs; every capability falls back to the base class's NotImplementedError.
Real implementation (pactl for volume, brightnessctl, loginctl, xdotool/wmctrl,
playerctl for MPRIS2 media keys) is future work — v1 targets Windows only.
"""

from __future__ import annotations

from elara.platform_adapters.base import PlatformAdapter


class LinuxAdapter(PlatformAdapter):
    supported = False
