"""Executes actions through the dry-run gate (ADR-014): every automated run
defaults to dry-run, which logs a structured record instead of touching the
OS. This is the safety net an unattended agent depends on — it must be
impossible for a test or an autonomous build session to actually mute the
machine, lock the screen, or type into whatever window has focus.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from elara.actions.registry import ActionRegistry

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRecord:
    action_id: str
    slots: dict[str, Any]
    ts: float
    ok: bool
    error: str | None = None


class ActionExecutor:
    def __init__(self, registry: ActionRegistry, ctx: Any) -> None:
        self.registry = registry
        self.ctx = ctx
        self.dry_run_log: list[ExecutionRecord] = []
        self.stats: dict[str, int] = {}

    def execute(self, action_id: str, slots: dict[str, Any] | None = None) -> ExecutionRecord:
        slots = slots or {}
        spec = self.registry.get(action_id)
        ts = time.time()

        if spec is None:
            record = ExecutionRecord(action_id, slots, ts, ok=False, error="unknown action_id")
            logger.warning("DRYRUN unknown action_id=%s", action_id)
            self.dry_run_log.append(record)
            return record

        if self.ctx.dry_run:
            record = ExecutionRecord(action_id, slots, ts, ok=True)
            logger.info("DRYRUN action_id=%s slots=%s", action_id, slots)
            self.dry_run_log.append(record)
            self._bump_stats(action_id)
            return record

        try:
            spec.run(self.ctx, **slots)
            record = ExecutionRecord(action_id, slots, ts, ok=True)
        except Exception as exc:  # noqa: BLE001 — a failing action must never kill the app
            logger.exception("action %s raised", action_id)
            record = ExecutionRecord(action_id, slots, ts, ok=False, error=str(exc))

        self._bump_stats(action_id)
        self.ctx.notify(spec.label)
        return record

    def _bump_stats(self, action_id: str) -> None:
        self.stats[action_id] = self.stats.get(action_id, 0) + 1
