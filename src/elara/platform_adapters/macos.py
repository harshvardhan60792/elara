"""macOS stub. Imports cleanly and reports `supported = False` so the app
still runs; every capability falls back to the base class's NotImplementedError.
Real implementation (osascript for volume/brightness/DND, pmset for sleep,
NSWorkspace via pyobjc for foreground app) is future work — v1 targets
Windows only.
"""

from __future__ import annotations

from elara.platform_adapters.base import PlatformAdapter


class MacOSAdapter(PlatformAdapter):
    supported = False
