from __future__ import annotations

import pytest

from elara.actions.registry import ActionRegistry, ActionSpec


def _spec(action_id: str, label: str, category: str = "test") -> ActionSpec:
    return ActionSpec(id=action_id, label=label, category=category, run=lambda ctx: None)


def test_register_and_get():
    registry = ActionRegistry()
    registry.register(_spec("media.play_pause", "Play/Pause"))
    assert registry.get("media.play_pause").label == "Play/Pause"
    assert registry.get("does.not.exist") is None


def test_duplicate_registration_raises():
    registry = ActionRegistry()
    registry.register(_spec("a.b", "AB"))
    with pytest.raises(ValueError):
        registry.register(_spec("a.b", "AB again"))


def test_by_category():
    registry = ActionRegistry()
    registry.register(_spec("media.next", "Next", category="media"))
    registry.register(_spec("media.prev", "Prev", category="media"))
    registry.register(_spec("volume.up", "Volume up", category="volume"))

    media_actions = registry.by_category("media")
    assert {a.id for a in media_actions} == {"media.next", "media.prev"}


def test_search_fuzzy_match():
    registry = ActionRegistry()
    registry.register(_spec("apps.launch", "Launch Visual Studio Code"))
    registry.register(_spec("media.play_pause", "Play/Pause"))

    results = registry.search("vs code", limit=5)
    assert any(a.id == "apps.launch" for a in results)


def test_contains():
    registry = ActionRegistry()
    registry.register(_spec("system.lock", "Lock"))
    assert "system.lock" in registry
    assert "system.unlock" not in registry
