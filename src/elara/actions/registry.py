"""One registry, four front-ends: gestures, voice, the radial menu, and
plugins all resolve an action_id through the same ActionRegistry
(docs/ARCHITECTURE.md)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from rapidfuzz import process as fuzz_process


@dataclass
class ActionSpec:
    id: str
    label: str
    category: str
    run: Callable[..., Any]
    icon: str | None = None
    profiles: tuple[str, ...] | None = None  # None == all profiles
    needs_confirm: bool = False
    slots: tuple[str, ...] = field(default_factory=tuple)


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, ActionSpec] = {}

    def register(self, spec: ActionSpec) -> None:
        if spec.id in self._actions:
            raise ValueError(f"action already registered: {spec.id}")
        self._actions[spec.id] = spec

    def get(self, action_id: str) -> ActionSpec | None:
        return self._actions.get(action_id)

    def by_category(self, category: str) -> list[ActionSpec]:
        return [a for a in self._actions.values() if a.category == category]

    def search(self, query: str, limit: int = 10) -> list[ActionSpec]:
        if not query:
            return list(self._actions.values())[:limit]
        labels = {spec.id: spec.label for spec in self._actions.values()}
        matches = fuzz_process.extract(query, labels, limit=limit)
        return [self._actions[action_id] for _label, _score, action_id in matches]

    def all(self) -> list[ActionSpec]:
        return list(self._actions.values())

    def __contains__(self, action_id: str) -> bool:
        return action_id in self._actions
