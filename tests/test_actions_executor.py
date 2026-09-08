from __future__ import annotations

from elara.actions.executor import ActionExecutor
from elara.actions.registry import ActionRegistry, ActionSpec
from elara.app import build_context
from elara.config import Config


def test_dry_run_execute_never_touches_os_and_logs_once():
    os_touched = False

    def fake_run(ctx, **slots):
        nonlocal os_touched
        os_touched = True  # would only happen if dry_run were bypassed

    registry = ActionRegistry()
    registry.register(ActionSpec(id="test.fake", label="Fake", category="test", run=fake_run))

    ctx = build_context(Config(), dry_run=True)
    executor = ActionExecutor(registry, ctx)

    record = executor.execute("test.fake", {"foo": "bar"})

    assert os_touched is False
    assert record.ok is True
    assert len(executor.dry_run_log) == 1
    assert executor.dry_run_log[0].action_id == "test.fake"
    assert executor.dry_run_log[0].slots == {"foo": "bar"}


def test_live_execute_calls_run_and_survives_exceptions():
    calls = []

    def failing_run(ctx, **slots):
        calls.append(slots)
        raise RuntimeError("boom")

    registry = ActionRegistry()
    registry.register(ActionSpec(id="test.fails", label="Fails", category="test", run=failing_run))

    ctx = build_context(Config(), dry_run=False)
    executor = ActionExecutor(registry, ctx)

    record = executor.execute("test.fails")

    assert calls == [{}]
    assert record.ok is False
    assert record.error == "boom"
    assert executor.stats["test.fails"] == 1


def test_unknown_action_id_does_not_raise():
    registry = ActionRegistry()
    ctx = build_context(Config(), dry_run=True)
    executor = ActionExecutor(registry, ctx)

    record = executor.execute("nonexistent.action")

    assert record.ok is False
    assert record.error == "unknown action_id"
