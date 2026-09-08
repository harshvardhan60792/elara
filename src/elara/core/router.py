"""Resolves GestureEvent/VoiceCommand/ContinuousUpdate into action_ids via
the active profile's bindings and dispatches through the executor. Honours
global armed state — nothing fires while disarmed.

`bindings` is a plain gesture_id -> action_id dict for now; ProfileManager
(Phase 5) becomes the real source of truth and just swaps this dict out
when the active profile changes, so Router's shape doesn't need to change.

needs_confirm actions execute immediately for now — the confirmation toast
UI is Phase 3 (T031); see docs/DECISIONS.md.
"""

from __future__ import annotations

import logging

from elara.actions.executor import ActionExecutor
from elara.actions.registry import ActionRegistry
from elara.events import ContinuousUpdate, EventBus, GestureEvent, VoiceCommand

logger = logging.getLogger(__name__)


class Router:
    def __init__(
        self,
        registry: ActionRegistry,
        executor: ActionExecutor,
        ctx,
        bindings: dict[str, str] | None = None,
    ) -> None:
        self.registry = registry
        self.executor = executor
        self.ctx = ctx
        self.bindings = bindings or {}

        # PySide6 connects a plain bound method without keeping the
        # underlying object's Python refcount up — if nothing else holds a
        # strong reference to this Router, it gets GC'd and the connection
        # silently stops delivering (no error, events just vanish). ctx
        # outlives the router in every real caller, so anchoring it here is
        # what actually keeps the connection alive; it's also how later
        # code (e.g. a profile switch) can reach the router via ctx.router.
        ctx.router = self

    def connect(self, event_bus: EventBus) -> None:
        event_bus.gesture.connect(self.handle_gesture)
        event_bus.voice_command.connect(self.handle_voice)

    def handle_gesture(self, event: GestureEvent) -> None:
        if not self.ctx.armed:
            return
        action_id = self.bindings.get(event.id)
        if action_id is None:
            return
        self.executor.execute(action_id)

    def handle_voice(self, command: VoiceCommand) -> None:
        if not self.ctx.armed:
            return
        action_id = self.bindings.get(command.intent, command.intent)
        if action_id not in self.registry:
            logger.info("voice intent %s has no bound action", command.intent)
            return
        self.executor.execute(action_id, dict(command.slots))

    def handle_continuous(self, update: ContinuousUpdate) -> None:
        # Continuous channels (cursor, pinch-scrub) bypass the action
        # registry entirely and are consumed directly by their owning mode
        # (T040/T041) — this hook exists so Router stays the single place
        # that knows about armed state gating, even for continuous input.
        if not self.ctx.armed:
            return
