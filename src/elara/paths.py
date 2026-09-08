"""Filesystem locations, resolved so they work both from source and from a
PyInstaller-frozen build. Never resolve anything relative to C: implicitly —
platformdirs picks the OS app-data location, which on this machine is fine
(kilobytes of config/logs), but nothing here downloads or caches large files
outside of what the caller explicitly points at models_dir()/data_dir()."""

from __future__ import annotations

import sys
from pathlib import Path

import platformdirs

_APP_NAME = "Elara"


def resource_root() -> Path:
    """Root for bundled read-only resources (icons, default configs).

    Under PyInstaller, sys._MEIPASS points at the unpacked bundle. From
    source, it's the repository root (three levels up from this file:
    src/elara/paths.py -> src/elara -> src -> repo root).
    """
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root is not None:
        return Path(frozen_root)
    return Path(__file__).resolve().parents[2]


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    return _ensure(Path(platformdirs.user_config_dir(_APP_NAME, appauthor=False)))


def models_dir() -> Path:
    return _ensure(Path(platformdirs.user_data_dir(_APP_NAME, appauthor=False)) / "models")


def logs_dir() -> Path:
    return _ensure(Path(platformdirs.user_log_dir(_APP_NAME, appauthor=False)))


def plugins_dir() -> Path:
    return _ensure(Path(platformdirs.user_data_dir(_APP_NAME, appauthor=False)) / "plugins")


def data_dir() -> Path:
    return _ensure(Path(platformdirs.user_data_dir(_APP_NAME, appauthor=False)))


def config_file() -> Path:
    return config_dir() / "config.json"
