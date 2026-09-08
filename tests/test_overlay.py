from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtCore import QPoint, QRect

from elara.ui.overlay import OverlayWindow


def _fake_screen(rect: QRect) -> MagicMock:
    screen = MagicMock()
    screen.availableGeometry.return_value = rect
    return screen


def test_overlay_constructs_and_shows_without_stealing_focus(qapp):
    overlay = OverlayWindow()
    overlay.resize(200, 100)
    overlay.show()
    assert overlay.isVisible()
    overlay.close()


def test_move_to_point_clamps_within_screen_geometry(qapp, monkeypatch):
    overlay = OverlayWindow()
    overlay.resize(50, 50)

    screen_a = _fake_screen(QRect(0, 0, 1000, 800))
    monkeypatch.setattr("elara.ui.overlay.QGuiApplication.screenAt", lambda pt: screen_a)

    overlay.move_to_point(QPoint(10, 10), center=True)
    pos = overlay.pos()
    assert pos.x() >= 0 and pos.y() >= 0


def test_move_to_point_uses_screen_under_the_given_point(qapp, monkeypatch):
    overlay = OverlayWindow()
    overlay.resize(50, 50)

    screen_left = _fake_screen(QRect(0, 0, 1000, 800))
    screen_right = _fake_screen(QRect(1000, 0, 1000, 800))

    def screen_at(pt):
        return screen_right if pt.x() >= 1000 else screen_left

    monkeypatch.setattr("elara.ui.overlay.QGuiApplication.screenAt", screen_at)

    overlay.move_to_point(QPoint(1500, 400), center=True)
    pos = overlay.pos()
    assert pos.x() >= 1000

    overlay.move_to_point(QPoint(200, 400), center=True)
    pos = overlay.pos()
    assert pos.x() < 1000
