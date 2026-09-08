"""Picks the concrete PlatformAdapter for the running OS."""

from __future__ import annotations

import sys

from elara.platform_adapters.base import AppInfo, PlatformAdapter

__all__ = ["AppInfo", "PlatformAdapter", "get_adapter"]


def get_adapter() -> PlatformAdapter:
    if sys.platform == "win32":
        from elara.platform_adapters.windows import WindowsAdapter

        return WindowsAdapter()
    if sys.platform == "darwin":
        from elara.platform_adapters.macos import MacOSAdapter

        return MacOSAdapter()

    from elara.platform_adapters.linux import LinuxAdapter

    return LinuxAdapter()
