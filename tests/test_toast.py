from __future__ import annotations

from elara.ui.toast import ToastManager


def test_three_toasts_stack_and_dismiss_in_order(qapp, qtbot):
    manager = ToastManager(duration_ms=20)

    manager.show("first")
    manager.show("second")
    manager.show("third")

    assert manager.active_count() == 3

    qtbot.waitUntil(lambda: manager.active_count() == 0, timeout=2000)
    assert manager._active == []
