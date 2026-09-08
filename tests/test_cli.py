from __future__ import annotations

import subprocess
import sys

from elara import __version__
from elara.cli import parse_args


def test_default_parse_is_dry_run():
    args = parse_args([])
    assert args.dry_run is True


def test_live_flag_disables_dry_run():
    args = parse_args(["--live"])
    assert args.dry_run is False


def test_source_and_headless_parse():
    args = parse_args(["--source", "synth:tests/fixtures/landmarks/swipe_left.json", "--headless"])
    assert args.source == "synth:tests/fixtures/landmarks/swipe_left.json"
    assert args.headless is True


def test_version_flag_prints_version():
    result = subprocess.run(
        [sys.executable, "-m", "elara", "--version"],
        capture_output=True,
        text=True,
    )
    assert __version__ in result.stdout
    assert result.returncode == 0
