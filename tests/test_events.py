from __future__ import annotations

import threading

from elara.events import EventBus, GestureEvent, StateChanged


def test_gesture_signal_crosses_thread(qapp, qtbot):
    bus = EventBus()
    received = []
    bus.gesture.connect(received.append)

    event = GestureEvent(id="fist", hand="right", confidence=0.9, position=(0.5, 0.5), timestamp=1.0)

    def emit_from_worker():
        bus.gesture.emit(event)

    with qtbot.waitSignal(bus.gesture, timeout=1000):
        t = threading.Thread(target=emit_from_worker)
        t.start()
        t.join()

    assert received == [event]


def test_state_changed_signal_crosses_thread(qapp, qtbot):
    bus = EventBus()
    received = []
    bus.state_changed.connect(received.append)

    def emit_from_worker():
        bus.state_changed.emit(StateChanged(armed=True))

    with qtbot.waitSignal(bus.state_changed, timeout=1000):
        t = threading.Thread(target=emit_from_worker)
        t.start()
        t.join()

    assert received == [StateChanged(armed=True)]
