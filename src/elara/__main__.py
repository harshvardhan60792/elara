"""Entry point. `python -m elara` / the `elara` console script both land here.

Signal handling note: Qt's event loop is native C++ and doesn't poll for
Python signals by default, so SIGINT would otherwise be swallowed until a Qt
event fires. A short-interval QTimer keeps the Python interpreter running
often enough for signal.signal's handler to actually get invoked.
"""

from __future__ import annotations

import signal
import sys

from PySide6.QtCore import QTimer

from elara import config as config_module
from elara import logging_setup
from elara.app import ElaraApp, build_qapplication
from elara.bootstrap import build_full_context
from elara.cli import parse_args


def install_sigint_handler(qapp) -> QTimer:
    """Wires SIGINT -> qapp.quit(). Returns the keepalive QTimer (caller
    must keep a reference — a QTimer with no Python owner gets garbage
    collected and stops firing)."""

    def _sigint_handler(*_: object) -> None:
        qapp.quit()

    signal.signal(signal.SIGINT, _sigint_handler)
    keepalive = QTimer()
    keepalive.timeout.connect(lambda: None)
    keepalive.start(200)
    return keepalive


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging_setup.setup(level=args.log_level, dry_run=args.dry_run)

    from pathlib import Path

    cfg = config_module.load(Path(args.config)) if args.config else config_module.load()
    if args.profile:
        cfg.general.active_profile = args.profile

    qapp = build_qapplication(sys.argv[:1])
    ctx, _router = build_full_context(cfg, dry_run=args.dry_run)
    elara_app = ElaraApp(ctx)

    from elara.vision.thread import VisionSupervisor

    supervisor = VisionSupervisor(ctx, source_spec=args.source or "camera:0")
    ctx.event_bus.state_changed.connect(supervisor.on_state_changed)

    tray = None
    toast_manager = None
    if not args.headless:
        from elara.ui.tray import TrayIcon
        from elara.ui.toast import ToastManager

        tray = TrayIcon(elara_app)
        tray.show()

        toast_manager = ToastManager(duration_ms=ctx.config.ui.toast_duration_ms)
        ctx.on_notify(lambda message: toast_manager.show(message))

    keepalive = install_sigint_handler(qapp)

    if cfg.general.start_armed:
        elara_app.set_armed(True)

    exit_code = qapp.exec()
    supervisor.stop()
    del tray, toast_manager  # keep referenced until after exec() so they aren't GC'd early
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
