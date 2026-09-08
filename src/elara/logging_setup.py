"""Rotating file logging plus console output. Transcripts and frame data are
DEBUG-only by convention (enforced by callers, not this module) so a default
INFO run never writes what the user said or saw to disk."""

from __future__ import annotations

import logging
import logging.handlers

from elara.paths import logs_dir

_CONFIGURED = False


class DryRunFilter(logging.Filter):
    """Tags every record with whether it was emitted while dry_run was active."""

    def __init__(self, dry_run: bool) -> None:
        super().__init__()
        self.dry_run = dry_run

    def filter(self, record: logging.LogRecord) -> bool:
        record.dry_run = self.dry_run
        return True


def setup(level: str = "INFO", dry_run: bool = True) -> logging.Logger:
    global _CONFIGURED
    root = logging.getLogger("elara")

    if _CONFIGURED:
        root.setLevel(level)
        for f in root.filters:
            if isinstance(f, DryRunFilter):
                f.dry_run = dry_run
        return root

    root.setLevel(level)
    root.addFilter(DryRunFilter(dry_run))

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s", datefmt="%H:%M:%S"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir() / "elara.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    root.propagate = False
    _CONFIGURED = True
    return root
