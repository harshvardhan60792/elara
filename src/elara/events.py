"""Cross-thread event types. GestureEvent/ContinuousUpdate/etc. are frozen
dataclasses (plain data, safe to pass across threads); EventBus is the only
sanctioned crossing point, via Qt signals, per ADR-007 (single process,
three threads, no shared mutable state)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PySide6.QtCore import QObject, Signal


@dataclass(frozen=True)
class GestureEvent:
    id: str
    hand: str  # "left" | "right"
    confidence: float
    position: tuple[float, float]
    timestamp: float


@dataclass(frozen=True)
class ContinuousUpdate:
    channel: str
    value: float
    position: tuple[float, float] | None = None


@dataclass(frozen=True)
class VoiceCommand:
    intent: str
    raw_text: str
    confidence: float
    slots: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PresenceEvent:
    state: str  # "present" | "away"


@dataclass(frozen=True)
class ProfileChanged:
    name: str


@dataclass(frozen=True)
class StateChanged:
    armed: bool


class EventBus(QObject):
    gesture = Signal(GestureEvent)
    continuous_update = Signal(ContinuousUpdate)
    voice_command = Signal(VoiceCommand)
    presence = Signal(PresenceEvent)
    profile_changed = Signal(ProfileChanged)
    state_changed = Signal(StateChanged)
