from __future__ import annotations

import math

from PySide6.QtCore import QPoint

from elara.ui.radial_menu import RadialMenu, RadialSegment, hover_for_offset


def test_dead_zone_returns_none():
    assert hover_for_offset(2, 2, n_segments=4, dead_zone_radius=30) is None


def test_straight_up_selects_segment_zero():
    assert hover_for_offset(0, -100, n_segments=4, dead_zone_radius=30) == 0


def test_straight_right_selects_expected_segment_for_four_segments():
    # 4 segments of 90 deg each, segment 0 centered on "up" (-90..0..90
    # relative)... straight right (angle=90 from up) falls in segment 1.
    assert hover_for_offset(100, 0, n_segments=4, dead_zone_radius=30) == 1


def test_straight_down_selects_segment_two_of_four():
    assert hover_for_offset(0, 100, n_segments=4, dead_zone_radius=30) == 2


def test_straight_left_selects_segment_three_of_four():
    assert hover_for_offset(-100, 0, n_segments=4, dead_zone_radius=30) == 3


def test_all_directions_around_a_ring_map_to_a_valid_segment():
    n = 6
    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        dx, dy = 100 * math.sin(rad), -100 * math.cos(rad)
        result = hover_for_offset(dx, dy, n_segments=n, dead_zone_radius=30)
        assert result is not None and 0 <= result < n


def test_radial_menu_open_hover_confirm(qapp, qtbot):
    segments = [RadialSegment(f"action.{i}", f"Action {i}") for i in range(6)]
    menu = RadialMenu(segments, timeout_ms=5000)

    menu.open_at(QPoint(400, 300))
    assert menu.isVisible()

    menu.update_hover(0, -100)  # straight up -> segment 0
    assert menu._hovered_index == 0

    selected = []
    menu.selected.connect(selected.append)
    action_id = menu.confirm()

    assert action_id == "action.0"
    assert selected == ["action.0"]
    assert not menu.isVisible()


def test_radial_menu_dismisses_on_timeout(qapp, qtbot):
    segments = [RadialSegment("a", "A"), RadialSegment("b", "B")]
    menu = RadialMenu(segments, timeout_ms=30)

    dismissed = []
    menu.dismissed.connect(lambda: dismissed.append(True))

    menu.open_at(QPoint(200, 200))
    qtbot.waitUntil(lambda: dismissed == [True], timeout=2000)
    assert not menu.isVisible()


def test_confirm_with_no_hover_dismisses_without_selecting(qapp, qtbot):
    segments = [RadialSegment("a", "A")]
    menu = RadialMenu(segments, timeout_ms=5000)
    menu.open_at(QPoint(100, 100))

    selected = []
    menu.selected.connect(selected.append)

    result = menu.confirm()

    assert result is None
    assert selected == []
    assert not menu.isVisible()
