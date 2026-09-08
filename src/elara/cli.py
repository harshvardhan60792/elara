"""Argument parsing. dry_run defaults True; --live is the only way off, so an
unattended run (or a slipped invocation) can never touch the real OS."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from elara import __version__


@dataclass
class Args:
    dry_run: bool
    source: str | None
    headless: bool
    log_level: str
    config: str | None
    profile: str | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="elara", description="Elara desktop control")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Disable dry-run and let actions actually touch the OS.",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="camera:N | video:PATH | synth:PATH",
    )
    parser.add_argument("--headless", action="store_true", help="No tray icon, no windows.")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--config", default=None, help="Override config file path.")
    parser.add_argument("--profile", default=None, help="Force a starting profile.")
    parser.add_argument(
        "--version", action="version", version=f"elara {__version__}"
    )
    return parser


def parse_args(argv: list[str] | None = None) -> Args:
    parser = build_parser()
    ns = parser.parse_args(argv)
    return Args(
        dry_run=not ns.live,
        source=ns.source,
        headless=ns.headless,
        log_level=ns.log_level,
        config=ns.config,
        profile=ns.profile,
    )
