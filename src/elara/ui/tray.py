"""System tray icon: Arm/Disarm toggle, profile submenu (stub until
Phase 5), Settings (stub until later in Phase 3), Quit. Icon swaps on armed
state so the tray itself is a second honest signal alongside the camera LED."""

from __future__ import annotations

from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from elara.app import ElaraApp
from elara.paths import resource_root


def _icon_path(name: str) -> str:
    return str(resource_root() / "assets" / name)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, app: ElaraApp, parent=None) -> None:
        self._icon_idle = QIcon(_icon_path("icon_idle.png"))
        self._icon_armed = QIcon(_icon_path("icon_armed.png"))
        super().__init__(self._icon_idle, parent)
        self.app = app

        self.setToolTip("Elara — disarmed")

        menu = QMenu()

        self.arm_action = QAction("Armed", menu, checkable=True)
        self.arm_action.setChecked(app.ctx.armed)
        self.arm_action.toggled.connect(self._on_arm_toggled)
        menu.addAction(self.arm_action)

        self.profile_menu = QMenu("Profile", menu)
        self._profile_group = QActionGroup(self.profile_menu)
        self._profile_group.setExclusive(True)
        for name in ("Desktop", "Media", "Presentation", "Meeting", "Browser", "Reading"):
            action = QAction(name, self.profile_menu, checkable=True)
            action.setChecked(name == "Desktop")
            self._profile_group.addAction(action)
            self.profile_menu.addAction(action)
        menu.addMenu(self.profile_menu)

        settings_action = QAction("Settings…", menu)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

        app.ctx.event_bus.state_changed.connect(self._on_state_changed)

    def _on_arm_toggled(self, checked: bool) -> None:
        self.app.set_armed(checked)

    def _on_state_changed(self, event) -> None:
        armed = event.armed
        if self.arm_action.isChecked() != armed:
            self.arm_action.setChecked(armed)
        self.setIcon(self._icon_armed if armed else self._icon_idle)
        self.setToolTip(f"Elara — {'armed' if armed else 'disarmed'}")

    def _open_settings(self) -> None:
        # Settings window lands in a later Phase 3 task; stub for now.
        pass
