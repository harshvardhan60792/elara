"""capture.* — screenshots and screen recording via mss (fast, cross-platform
grab; no extra native deps beyond what's already required). Screenshots
land in the user's Pictures folder and the clipboard; recording is a
convenience capped at 15 FPS / 1080p — it is not meant to compete with OBS.
"""

from __future__ import annotations

import datetime as dt
import io
import threading
import time
from pathlib import Path

from elara.actions.registry import ActionRegistry, ActionSpec


def _pictures_dir() -> Path:
    pictures = Path.home() / "Pictures" / "Elara"
    pictures.mkdir(parents=True, exist_ok=True)
    return pictures


def _timestamped_name(prefix: str) -> str:
    return f"{prefix}_{dt.datetime.now():%Y%m%d_%H%M%S}.png"


def _copy_image_to_clipboard(png_bytes: bytes) -> None:
    import win32clipboard
    from PIL import Image

    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    buf = io.BytesIO()
    image.save(buf, "BMP")
    bmp_data = buf.getvalue()[14:]  # strip the 14-byte BMP file header; DIB only

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
    finally:
        win32clipboard.CloseClipboard()


def _screenshot_full(ctx) -> None:
    import mss
    import mss.tools

    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[0])
        png_bytes = mss.tools.to_png(shot.rgb, shot.size)

    path = _pictures_dir() / _timestamped_name("screenshot")
    path.write_bytes(png_bytes)
    _copy_image_to_clipboard(png_bytes)
    ctx.notify(f"Screenshot saved: {path.name}")


def _screenshot_region(ctx, x: int = 0, y: int = 0, width: int = 800, height: int = 600) -> None:
    import mss
    import mss.tools

    with mss.mss() as sct:
        region = {"left": x, "top": y, "width": width, "height": height}
        shot = sct.grab(region)
        png_bytes = mss.tools.to_png(shot.rgb, shot.size)

    path = _pictures_dir() / _timestamped_name("region")
    path.write_bytes(png_bytes)
    _copy_image_to_clipboard(png_bytes)
    ctx.notify(f"Region screenshot saved: {path.name}")


def _screenshot_frame(ctx, x0: int = 0, y0: int = 0, x1: int = 800, y1: int = 600) -> None:
    left, top = min(x0, x1), min(y0, y1)
    width, height = abs(x1 - x0), abs(y1 - y0)
    _screenshot_region(ctx, x=left, y=top, width=width, height=height)


def _record_loop(ctx, path: Path, stop_event: threading.Event, fps: int = 15) -> None:
    import cv2
    import mss
    import numpy as np

    with mss.mss() as sct:
        monitor = sct.monitors[0]
        width = min(monitor["width"], 1920)
        height = min(monitor["height"], 1080)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
        interval = 1.0 / fps
        try:
            while not stop_event.is_set():
                t0 = time.monotonic()
                frame = np.array(sct.grab(monitor))[:, :, :3]
                frame = cv2.resize(frame, (width, height))
                writer.write(frame)
                elapsed = time.monotonic() - t0
                if elapsed < interval:
                    time.sleep(interval - elapsed)
        finally:
            writer.release()


def _record_toggle(ctx) -> None:
    recording = ctx.stats.get("recording_stop_event")
    if recording is not None:
        recording.set()
        ctx.stats["recording_stop_event"] = None
        ctx.notify("Recording stopped")
        return

    path = _pictures_dir() / f"recording_{dt.datetime.now():%Y%m%d_%H%M%S}.mp4"
    stop_event = threading.Event()
    thread = threading.Thread(target=_record_loop, args=(ctx, path, stop_event), daemon=True)
    ctx.stats["recording_stop_event"] = stop_event
    thread.start()
    ctx.notify(f"Recording started: {path.name}")


def _copy_to_clipboard(ctx) -> None:
    _screenshot_full(ctx)


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("capture.screenshot_full", "Screenshot", "capture", _screenshot_full))
    registry.register(
        ActionSpec(
            "capture.screenshot_region",
            "Screenshot region",
            "capture",
            _screenshot_region,
            slots=("x", "y", "width", "height"),
        )
    )
    registry.register(
        ActionSpec(
            "capture.screenshot_frame",
            "Screenshot (two-hand frame)",
            "capture",
            _screenshot_frame,
            slots=("x0", "y0", "x1", "y1"),
        )
    )
    registry.register(ActionSpec("capture.record_toggle", "Record screen toggle", "capture", _record_toggle))
    registry.register(ActionSpec("capture.copy_to_clipboard", "Copy screenshot to clipboard", "capture", _copy_to_clipboard))
