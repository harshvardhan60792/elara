from __future__ import annotations

from elara.core.cursor import CursorMapper


def test_center_of_active_rect_maps_to_center_of_screen():
    mapper = CursorMapper(active_rect=(0.0, 0.0, 1.0, 1.0), freq=30.0, mincutoff=1.0, beta=100.0)
    screen = (0.0, 0.0, 1920.0, 1080.0)

    # High beta minimizes smoothing lag so a single call converges close
    # enough to the raw mapped position for this test's tolerance.
    x, y = 0, 0
    for i in range(5):
        x, y = mapper.map_to_screen(0.5, 0.5, i * (1 / 30.0), screen)

    assert abs(x - 960) < 50
    assert abs(y - 540) < 50


def test_position_outside_active_rect_clamps_to_screen_edge():
    mapper = CursorMapper(active_rect=(0.2, 0.2, 0.8, 0.8), freq=30.0, beta=100.0)
    screen = (0.0, 0.0, 1000.0, 1000.0)

    x, y = 0, 0
    for i in range(10):
        x, y = mapper.map_to_screen(0.0, 0.0, i * (1 / 30.0), screen)  # far outside active_rect
    assert x <= 5
    assert y <= 5

    x, y = 0, 0
    for i in range(10):
        x, y = mapper.map_to_screen(1.0, 1.0, i * (1 / 30.0), screen)
    assert x >= 995
    assert y >= 995


def test_screen_bounds_offset_is_respected():
    mapper = CursorMapper(active_rect=(0.0, 0.0, 1.0, 1.0), beta=100.0)
    screen = (1920.0, 0.0, 1920.0, 1080.0)  # a second monitor to the right

    x = 0
    for i in range(5):
        x, _y = mapper.map_to_screen(0.0, 0.0, i * (1 / 30.0), screen)
    assert x >= 1920
