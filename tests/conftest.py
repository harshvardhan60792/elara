"""Shared test fixtures. QT_QPA_PLATFORM=offscreen is set before Qt is
imported anywhere else, so the whole suite runs with no display and no
window ever actually shown — required for an unattended CI/agent run."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import logging
from pathlib import Path

import pytest

from elara.app import AppContext, build_context
from elara.config import Config


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def app_context(tmp_path: Path) -> AppContext:
    cfg = Config()
    ctx = build_context(cfg, dry_run=True)
    return ctx


@pytest.fixture
def caplog_actions(caplog):
    caplog.set_level(logging.INFO, logger="elara")
    yield caplog
