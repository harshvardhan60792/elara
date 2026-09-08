from __future__ import annotations

import signal

from elara.__main__ import install_sigint_handler
from elara.app import ElaraApp, build_context
from elara.config import Config


def test_toggle_armed_emits_state_changed_twice(qapp):
    ctx = build_context(Config(), dry_run=True)
    app = ElaraApp(ctx)
    received = []
    ctx.event_bus.state_changed.connect(lambda e: received.append(e.armed))

    app.toggle_armed()
    app.toggle_armed()

    assert received == [True, False]


def test_toggle_armed_noop_when_state_unchanged(qapp):
    ctx = build_context(Config(), dry_run=True)
    app = ElaraApp(ctx)
    received = []
    ctx.event_bus.state_changed.connect(lambda e: received.append(e.armed))

    app.set_armed(False)  # already disarmed, must not emit

    assert received == []


def test_sigint_handler_quits_qapp(qapp):
    """`install_sigint_handler` wires SIGINT -> qapp.quit(). Verified by
    raising SIGINT in-process (signal.raise_signal), which invokes the
    real registered Python handler synchronously — reliable cross-platform
    and independent of whether this process has a real console attached.

    A full subprocess-level "send a genuine Ctrl+C to a child console
    process group" test was tried and does not work in this sandboxed
    environment: GenerateConsoleCtrlEvent needs the *sender* attached to a
    real console, which an automated agent session does not have. That
    full end-to-end path is HUMAN QA (docs/TESTING.md) — do not re-add an
    automated subprocess+CTRL_C_EVENT test without first confirming the
    harness actually has a console.
    """
    quit_calls = []

    class _FakeApp:
        def quit(self) -> None:
            quit_calls.append(True)

    original_handler = signal.getsignal(signal.SIGINT)
    keepalive = install_sigint_handler(_FakeApp())
    try:
        signal.raise_signal(signal.SIGINT)
    finally:
        signal.signal(signal.SIGINT, original_handler)
        keepalive.stop()

    assert quit_calls == [True]
