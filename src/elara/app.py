"""App shell: the QApplication wrapper, the shared AppContext, and arm/disarm
state. Disarmed on launch and the camera is never opened at startup — the
vision engine (Phase 1) only opens it once armed, so the hardware LED is an
honest signal of whether Elara is watching."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from elara.actions.registry import ActionRegistry
from elara.config import Config
from elara.events import EventBus, StateChanged
from elara.platform_adapters.base import PlatformAdapter

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    config: Config
    event_bus: EventBus
    dry_run: bool = True
    armed: bool = False
    stats: dict[str, Any] = field(default_factory=dict)
    registry: ActionRegistry | None = None
    platform: PlatformAdapter | None = None
    executor: Any = None
    router: Any = None
    cursor_controller: Any = None
    pinch_scrub_controller: Any = None
    set_armed_callback: Callable[[bool], None] | None = None
    _notify_subscribers: list[Callable[[str], None]] = field(default_factory=list)

    def notify(self, message: str) -> None:
        """The one feedback channel both built-in actions and plugins use
        (docs/ARCHITECTURE.md plugin contract: `ctx.notify("hello")`). The
        toast UI (Phase 3) subscribes here; until then this just logs."""
        logger.info("notify: %s", message)
        for subscriber in self._notify_subscribers:
            subscriber(message)

    def on_notify(self, subscriber: Callable[[str], None]) -> None:
        self._notify_subscribers.append(subscriber)


class ElaraApp(QObject):
    """Owns arm/disarm state and wires it to the event bus. UI pieces (tray,
    overlay) subscribe to event_bus.state_changed rather than polling."""

    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        ctx.set_armed_callback = self.set_armed

    def set_armed(self, armed: bool) -> None:
        if armed == self.ctx.armed:
            return
        self.ctx.armed = armed
        self.ctx.event_bus.state_changed.emit(StateChanged(armed=armed))

    def toggle_armed(self) -> None:
        self.set_armed(not self.ctx.armed)


def build_qapplication(argv: list[str] | None = None) -> QApplication:
    app = QApplication(argv or [])
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Elara")
    app.setOrganizationName("Elara")
    return app


def build_context(config: Config, dry_run: bool = True) -> AppContext:
    return AppContext(config=config, event_bus=EventBus(), dry_run=dry_run, armed=False)
