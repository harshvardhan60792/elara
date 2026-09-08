"""Registers every built-in action module. Called once at startup, before
plugins load (plugins get the same registry front door, ARCHITECTURE.md)."""

from __future__ import annotations

from elara.actions import (
    apps,
    browser,
    capture,
    media,
    meeting,
    mouse,
    self_actions,
    slides,
    system,
    text,
    volume,
    window,
)
from elara.actions.registry import ActionRegistry

_MODULES = (
    media,
    volume,
    system,
    window,
    mouse,
    apps,
    capture,
    meeting,
    browser,
    text,
    slides,
    self_actions,
)


def register_all(registry: ActionRegistry) -> None:
    for module in _MODULES:
        module.register(registry)
