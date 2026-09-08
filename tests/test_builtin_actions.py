from __future__ import annotations

import pytest

from elara.actions.builtin import register_all
from elara.actions.executor import ActionExecutor
from elara.actions.registry import ActionRegistry
from elara.app import build_context
from elara.config import Config

_DUMMY_VALUES = {
    "name": "notepad",
    "text": "hello",
    "query": "elara gesture control",
    "percent": 50,
    "value": 0.5,
    "x": 0,
    "y": 0,
    "x0": 0,
    "y0": 0,
    "x1": 100,
    "y1": 100,
    "width": 400,
    "height": 300,
}


@pytest.fixture(scope="module")
def registry() -> ActionRegistry:
    registry = ActionRegistry()
    register_all(registry)
    return registry


def test_registry_has_every_documented_action_id(registry: ActionRegistry):
    expected_prefixes = {
        "media", "volume", "system", "window", "desktop", "cursor", "apps",
        "capture", "meeting", "browser", "text", "slides", "elara",
    }
    seen_prefixes = {spec.id.split(".")[0] for spec in registry.all()}
    assert expected_prefixes <= seen_prefixes
    assert len(registry.all()) >= 60


def _all_action_ids() -> list[str]:
    registry = ActionRegistry()
    register_all(registry)
    return sorted(spec.id for spec in registry.all())


@pytest.mark.parametrize("action_id", _all_action_ids())
def test_every_action_dry_run_logs_exactly_once(action_id: str):
    registry = ActionRegistry()
    register_all(registry)
    spec = registry.get(action_id)

    slots = {name: _DUMMY_VALUES.get(name, "x") for name in spec.slots}

    ctx = build_context(Config(), dry_run=True)
    executor = ActionExecutor(registry, ctx)

    record = executor.execute(action_id, slots)

    assert record.ok is True
    assert len(executor.dry_run_log) == 1
    assert executor.dry_run_log[0].action_id == action_id
    assert executor.dry_run_log[0].slots == slots
