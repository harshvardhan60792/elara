# IMPLEMENTATION PLAN

Read `CLAUDE.md` and `docs/HANDOFF.md` first. Work tasks in order. Tick them off in `docs/PROGRESS.md` as you go, one commit per task.

Task IDs are stable. Never renumber. If you add work, append a new id at the end of the phase (e.g. `T029b`).

Every task below states **Files**, **Do**, and **Accept**. "Accept" is a check you can actually run without a camera, a microphone, or a human — unless it explicitly says `HUMAN`, in which case it goes to the checklist in `docs/TESTING.md` and is *not* claimed as passing.

**If time runs short**, the triage order is in `docs/OVERNIGHT_GOAL.md`: Phases 0–2 make it work, Phase 3 makes it look like a product, Phase 4 makes it feel like one, Phases 11–12 make it public. Voice, presence and the extras are enrichment — a polished half beats a broken whole. Never end a session with a failing `pytest -q` or an app that will not start.

---

# Phase 0 — Bootstrap

## T001 — Environment
**Files:** `scripts/setup_dev.ps1`, `requirements.txt`, `requirements-dev.txt`

**Do:** Create the venv with Python 3.12 at `D:\study\claude projects\beckon\.venv`. Every pip call passes `--cache-dir "D:\tmp\pip-cache"`.

```powershell
py -3.12 -m venv "D:\study\claude projects\beckon\.venv"
& "D:\study\claude projects\beckon\.venv\Scripts\python.exe" -m pip install --upgrade pip --cache-dir "D:\tmp\pip-cache"
& "D:\study\claude projects\beckon\.venv\Scripts\python.exe" -m pip install -r requirements.txt --cache-dir "D:\tmp\pip-cache"
```

`requirements.txt` (pin majors, let patches float):
```
mediapipe>=1.0,<2
opencv-python>=4.10
numpy>=1.26,<3
PySide6>=6.7
pynput>=1.7
psutil>=6.0
pycaw>=20240210 ; sys_platform == "win32"
comtypes>=1.4 ; sys_platform == "win32"
pywin32>=306 ; sys_platform == "win32"
scikit-learn>=1.5
platformdirs>=4.2
rapidfuzz>=3.9
mss>=9.0
Pillow>=10.3
```
Voice deps go in a separate `requirements-voice.txt` (installed only when the user enables voice, and bundled in the "full" build): `openwakeword>=0.6`, `onnxruntime>=1.18`, `vosk>=0.3.45`, `sounddevice>=0.4.7`, `pyttsx3>=2.90`.

`requirements-dev.txt`: `pytest`, `pytest-qt`, `pytest-cov`, `ruff`, `pyinstaller>=6.6`.

**Accept:** `.venv\Scripts\python.exe -c "import mediapipe, cv2, PySide6, numpy; print('ok')"` prints `ok`. `Get-PSDrive C` shows free space did not drop by more than ~200 MB.

## T002 — Repo skeleton
**Files:** `pyproject.toml`, `.gitignore`, `LICENSE` (MIT, "Harshvardhan", 2026), `src/beckon/__init__.py` (with `__version__ = "0.1.0"`), empty package dirs with `__init__.py`: `vision`, `voice`, `actions`, `platform_adapters`, `profiles`, `ui`, `core`.

Note: the package dir is `platform_adapters`, **not** `platform` — `platform` shadows a stdlib module and will cause obscure import failures.

`.gitignore` must include `.venv/`, `__pycache__/`, `models/`, `dist/`, `build/`, `*.spec` (except the checked-in one), `.pytest_cache/`, `D:/tmp` artifacts, `*.log`.

**Do:** `git init`, first commit. Do **not** create the GitHub remote yet (that is T120).

**Accept:** `python -c "import beckon; print(beckon.__version__)"` works with `src` on the path (`pip install -e .`).

## T003 — Paths and config
**Files:** `src/beckon/paths.py`, `src/beckon/config.py`

**Do:** `paths.py` resolves, in a PyInstaller-safe way:
```python
def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
```
plus `config_dir()`, `models_dir()`, `logs_dir()`, `plugins_dir()`, `data_dir()` via `platformdirs` (`Beckon`, no author dir), each creating on first access.

`config.py`: nested `@dataclass` tree with defaults, `load()`/`save()` to `config.json`, a `schema_version` int, and a migration hook. Preserve unknown keys on save. Sections: `general`, `camera`, `vision`, `arming`, `cursor`, `ui`, `voice`, `presence`, `privacy`, `performance`.

Every threshold named in `docs/GESTURES.md` and every number in the performance budget must appear here as a default. Examples: `arming.dwell_ms=250`, `arming.vote_n=4`, `arming.vote_m=6`, `arming.confidence_floor=0.72`, `arming.cooldown_ms=800`, `vision.pinch_on=0.055`, `vision.pinch_off=0.085`, `ui.attention_dwell_ms=700`, `ui.radial_timeout_ms=3000`, `performance.fps_active=30`, `performance.fps_idle=8`, `performance.fps_battery_cap=15`, `presence.away_delay_s=45`.

**Accept:** unit test round-trips a config through save/load with an injected unknown key and asserts the key survives and defaults fill in missing sections.

## T004 — Logging
**Files:** `src/beckon/logging_setup.py`

**Do:** Rotating file handler in `logs_dir()` (5 MB × 3), console handler at the CLI-selected level. A `dry_run` filter that tags records. Never log frame data or transcripts at INFO — transcripts are DEBUG only, and the privacy section of the README says so.

**Accept:** calling setup twice does not duplicate handlers; log file appears under the app data dir, not on C: unless that is where the OS app-data dir genuinely is (that is fine — it is kilobytes).

## T005 — Event bus
**Files:** `src/beckon/events.py`

**Do:** Frozen dataclasses `GestureEvent(id, hand, confidence, position, timestamp)`, `ContinuousUpdate(channel, value, position)`, `VoiceCommand(intent, slots, raw_text, confidence)`, `PresenceEvent(state)`, `ProfileChanged(name)`, `StateChanged(armed)`. A `QObject` `EventBus` exposing one Qt `Signal` per type.

**Accept:** a pytest emits each signal from a worker thread and asserts the main thread receives it (`pytest-qt`, offscreen platform).

## T006 — App shell and tray
**Files:** `src/beckon/app.py`, `src/beckon/__main__.py`, `src/beckon/ui/tray.py`, `assets/icon_armed.png`, `assets/icon_idle.png`

**Do:** `AppContext` dataclass holding config, event bus, registry, platform adapter, stats. `QApplication` with `setQuitOnLastWindowClosed(False)`. Tray icon with a menu: Arm/Disarm (checkable), Profile submenu (stub), Settings (stub), Quit. Icon swaps on armed state. **Disarmed on launch, camera never opened at startup.**

Generate the two icons programmatically in `scripts/make_icons.py` (a filled circle and a hollow circle, brand colour) so the repo has no binary-blob dependency you cannot regenerate.

**Accept:** `python -m beckon --headless --dry-run` starts and exits cleanly on SIGINT. With `QT_QPA_PLATFORM=offscreen`, a pytest constructs the app, toggles arm state twice, and asserts `StateChanged` fired twice.

## T007 — CLI
**Files:** `src/beckon/cli.py`

**Do:** `argparse` with `--dry-run` (**default True**; `--live` is the explicit opt-out), `--source {camera:N|video:PATH|synth:PATH}`, `--headless`, `--log-level`, `--config PATH`, `--profile NAME`, `--version`.

**Accept:** `python -m beckon --version` prints the version. `--live` is required to disable dry-run; assert in a test that default parse yields `dry_run is True`.

## T008 — Test harness
**Files:** `tests/conftest.py`, `pytest.ini` (or `[tool.pytest]` in pyproject), `tests/test_config.py`

**Do:** Fixtures: `app_context` (dry-run config in a tmp dir), `qapp` (offscreen), `caplog_actions` (captures the dry-run action log). Set `QT_QPA_PLATFORM=offscreen` in conftest before Qt import.

**Accept:** `pytest -q` green with at least the config round-trip test.

---

# Phase 1 — Vision core

## T010 — Camera source abstraction
**Files:** `src/beckon/vision/camera.py`

**Do:** `FrameSource` protocol with `read() -> np.ndarray | None`, `close()`, `set_fps(int)`. Implementations: `CameraSource` (OpenCV, `CAP_DSHOW` on Windows, 640×480, MJPG fourcc for lower USB bandwidth), `VideoFileSource` (loops a file, honours real-time pacing), `SynthSource` (replays a landmark JSON — used by tests; it bypasses inference and injects landmarks directly downstream).

Camera enumeration: probe indices 0–5, return names where the platform allows. Open lazily, release on `close()` so the hardware LED reflects real state.

**Accept:** `VideoFileSource` test using a 10-frame video generated by numpy+`cv2.VideoWriter` in a tmp dir returns 10 frames then loops. No camera required.

## T011 — Landmarker wrapper
**Files:** `src/beckon/vision/landmarker.py`, `scripts/fetch_models.py`

**Do:** Wrap `mp.tasks.vision.HandLandmarker` in LIVE_STREAM mode. Async result callback pushes `(timestamp_ms, result)` onto a bounded `queue.Queue(maxsize=2)`; drop oldest on overflow (never block the callback).

```python
base = mp.tasks.BaseOptions(model_asset_path=str(models_dir() / "hand_landmarker.task"))
opts = mp.tasks.vision.HandLandmarkerOptions(
    base_options=base,
    running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5,
    result_callback=self._on_result,
)
```
Timestamps must be **monotonically increasing integers in milliseconds** or MediaPipe raises. Derive from a frame counter, not wall clock.

`fetch_models.py` downloads `hand_landmarker.task` (and later the face detector) into `models_dir()`, verifying SHA-256, skipping if present. Never into C:.

**Accept:** with the model present, feeding a synthetic solid-colour frame produces a result (zero hands) without raising. Test is skipped with a clear reason if the model file is absent.

## T012 — Feature extraction
**Files:** `src/beckon/vision/features.py`

**Do:** Implement exactly the normalisation and derived features specified in `docs/GESTURES.md` (translate → scale → rotate, then finger states, curls, pinch distance, palm centre/normal, span, velocity). Pure functions over `np.ndarray` of shape `(21, 3)`. No MediaPipe import in this module — it takes plain arrays, which is what makes it testable.

**Accept:** unit tests assert scale invariance (features identical when landmarks are scaled 2×) and translation invariance, using synthetic arrays.

## T013 — One Euro filter
**Files:** `src/beckon/vision/smoothing.py`

**Do:**
```python
class OneEuroFilter:
    def __init__(self, freq, mincutoff=1.0, beta=0.007, dcutoff=1.0): ...
    def __call__(self, x: float, timestamp: float) -> float: ...
```
Standard formulation: low-pass the derivative with `dcutoff`, derive an adaptive cutoff `mincutoff + beta*|dx|`, low-pass the signal with it. Provide `Vec2Filter` wrapping two instances.

**Accept:** test that a step input converges, that a noisy stationary signal has lower variance out than in, and that a fast ramp lags by less than a fixed budget (this is the property that matters — smoothing must not cost responsiveness).

## T014 — Static gesture classifier
**Files:** `src/beckon/vision/static_gestures.py`

**Do:** All 12 poses from `docs/GESTURES.md`, in the stated priority order, each returning a graded confidence (distance from threshold, squashed to 0..1) rather than a boolean. Thresholds read from config, never inline.

**Accept:** T015's fixtures classify to the expected pose for every one of the 12, and the "no hand"/ambiguous cases return `None`. This is the single most important test file in the project.

## T015 — Synthetic landmark generator
**Files:** `scripts/synth_landmarks.py`, `tests/fixtures/landmarks/*.json`

**Do:** Build a canonical hand skeleton in normalised coordinates, then pose it: per-finger curl parameters (0 = straight, 1 = fully curled) produce the tip/PIP/MCP positions for each pose. Emit one JSON per pose. Also emit motion sequences: `swipe_left.json`, `swipe_right.json`, `circle_cw.json`, `push.json` as arrays of frames with timestamps, by translating/scaling the base pose along a path with a realistic velocity profile (ease in/out, ~350 ms for a swipe).

Add jitter injection (`--noise 0.01`) so tests can assert the classifier is robust to landmark noise.

**Accept:** running the script regenerates every fixture deterministically (fixed seed); `git diff` is empty after regeneration.

## T016 — Trajectory buffer + dynamic gestures
**Files:** `src/beckon/vision/dynamic_gestures.py`

**Do:** Ring buffer of `(timestamp, palm_center, hand_span)` per hand, default 1.0 s. Swipe detection: net displacement, axis dominance ratio ≥ 2, peak velocity floor, completion window, plus the "velocity must return below floor before re-arming" rule. Circle: accumulated signed angle about the trajectory centroid > 0.8·2π with bounded radius variance. Push: `hand_span` growth rate over a short window with a stationary palm centre.

**Accept:** the four motion fixtures from T015 classify correctly; the *reversed* swipe fixture classifies as the opposite direction; a slow drift across the frame classifies as **nothing** (the critical false-positive test).

## T017 — Vision engine
**Files:** `src/beckon/vision/engine.py`

**Do:** The thread that owns the frame source and the landmarker, runs the pipeline, and emits events. Adaptive FPS per ADR-016: 8 FPS when no hand seen for `idle_after_ms`, 30 FPS when a hand is present, capped at 15 on battery (`psutil.sensors_battery()`). Publishes `ContinuousUpdate` at frame rate and hands discrete candidates to the arming gate (T027).

Must accept a `SynthSource` and skip inference entirely — that is how the full pipeline is testable end-to-end without a camera.

**Accept:** driving the engine with a synth swipe sequence emits exactly one `swipe_left` event. Driving it with 200 frames of a stationary open palm emits at most one event (dwell + cooldown working).

## T018 — Camera preview widget
**Files:** `src/beckon/ui/preview.py`

**Do:** A `QWidget` showing the frame with the hand skeleton drawn over it, the detected pose name, confidence, current FPS, and CPU%. Used inside settings and the onboarding wizard. Draw with `QPainter` on a `QImage` wrapping the numpy buffer — do not convert per-frame through PIL.

**Accept:** offscreen test feeds one frame and asserts the widget renders without exception. `HUMAN`: visual check that the skeleton lines up with the hand.

## T019 — Benchmark harness
**Files:** `scripts/bench.py`

**Do:** Runs the engine against a video or synth source for N seconds and reports mean/p95 frame latency, achieved FPS, CPU% (via `psutil.Process`), and peak RSS. Writes `bench_results.json` to `D:\tmp\beckon\`.

**Accept:** produces a report on a synth source. The numbers become the baseline that Phase 9 must meet.

---

# Phase 2 — Actions

## T020 — Platform adapter interface + Windows implementation
**Files:** `src/beckon/platform_adapters/base.py`, `windows.py`, `macos.py`, `linux.py`, `__init__.py` (factory picking by `sys.platform`)

**Do:** `base.py` declares the capability methods from the table in `docs/ARCHITECTURE.md`, each raising `NotImplementedError` by default and each declaring `supported: bool`. Windows: pycaw for volume, `pynput` key synthesis for media keys, `ctypes.windll.user32.LockWorkStation()` for lock, WMI for brightness, `win32gui`/`psutil` for foreground app and window operations. macOS/Linux: stubs that import cleanly and report `supported=False`, with the real implementation noted as future work.

Guard every COM call — pycaw needs `CoInitialize` on the calling thread. Since actions run on the Qt main thread this is once at startup, but assert it rather than discovering it at 3am.

**Accept:** `get_adapter()` returns the Windows adapter; every method exists with the right signature (introspection test); nothing is executed.

## T021 — Action registry and executor
**Files:** `src/beckon/actions/registry.py`, `src/beckon/actions/executor.py`

**Do:** `ActionSpec(id, label, category, run, icon, profiles, needs_confirm, slots)`. `ActionRegistry` with `register()`, `get()`, `search()`, `by_category()`. `ActionExecutor.execute(action_id, slots, ctx)`:
- if `ctx.dry_run`: append `{action_id, slots, ts}` to an in-memory log **and** log at INFO with prefix `DRYRUN`; return success without touching the OS
- else call the spec's `run`
- catch and log every exception; a failing action must never kill the app
- record to stats; emit a toast

**Accept:** a test registers a fake action, executes it in dry-run, and asserts the OS was untouched and the log has exactly one entry. This test is the safety net for every later phase.

## T022–T026 — Action implementations
**Files:** `src/beckon/actions/media.py`, `volume.py`, `system.py`, `window.py`, `mouse.py`, `keyboard.py`, `apps.py`, `capture.py`, `meeting.py`, `browser.py`, `text.py`

**Do:** Implement every `action_id` listed in `docs/GESTURES.md`, each a thin function calling the platform adapter. Notes:
- `apps.launch` needs an app index: scan Start Menu `.lnk` files (Windows) once at startup into a name→path map, fuzzy-matched with rapidfuzz so "vs code" finds "Visual Studio Code". Cache it in the data dir with a refresh action.
- `capture.screenshot_region` and `capture.screenshot_frame` use `mss` for the grab and write to the user's Pictures dir plus the clipboard.
- `capture.record_toggle` writes frames via `cv2.VideoWriter` on a worker thread. Cap at 15 FPS and 1080p to keep it cheap; it is a convenience, not OBS.
- `meeting.*` maps to per-app hotkeys chosen by the detected foreground app (Zoom `Alt+A`, Teams `Ctrl+Shift+M`, Meet `Ctrl+D`) — table lives in `meeting.py`, extensible via config.
- `text.read_selection_aloud` copies the selection (`Ctrl+C`), reads the clipboard, and speaks it via the TTS module; degrade gracefully when voice deps are absent.

**Accept:** each module has a test asserting that invoking every action in dry-run produces exactly one log record with the right id and slots. No test executes anything for real.

## T027 — Arming gate
**Files:** `src/beckon/core/arming.py`

**Do:** The four-filter stack from `docs/ARCHITECTURE.md`: confidence floor → N-of-M vote → dwell → per-action cooldown, plus optional active zone. Pure logic over `(pose, confidence, timestamp)`; no Qt, no threads.

**Accept:** table-driven tests: a pose flickering below the vote threshold never fires; a stable pose fires once and not again until cooldown elapses; a pose entering and leaving the active zone fires only inside it.

## T028 — Router
**Files:** `src/beckon/core/router.py`

**Do:** Subscribes to `GestureEvent` / `VoiceCommand` / `ContinuousUpdate`, resolves the binding through the active profile, and calls the executor. Handles `needs_confirm` actions by routing them through a confirmation toast instead of firing directly. Honours global armed state and the panic disarm.

**Accept:** with a stub profile mapping `swipe_left → media.prev`, feeding a `swipe_left` event produces exactly one dry-run record for `media.prev`. Feeding the same event while disarmed produces none.

## T029 — End-to-end dry run
**Files:** `tests/test_e2e_synth.py`

**Do:** Wire `SynthSource → engine → arming → router → executor` and assert the dry-run log for a scripted sequence of poses and motions.

**Accept:** a 20-step scripted sequence produces exactly the expected action list. This test must stay green for the rest of the project — it is the regression net.

---

# Phase 3 — UI

## T030 — Overlay base
**Files:** `src/beckon/ui/overlay.py`

**Do:** Frameless, translucent, always-on-top, click-through window:
```python
self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.WindowTransparentForInput)
self.setAttribute(Qt.WA_TranslucentBackground)
self.setAttribute(Qt.WA_ShowWithoutActivating)
```
`Qt.Tool` keeps it out of the taskbar and alt-tab. Multi-monitor aware: track which screen the cursor/hand maps to and reposition. Must never steal focus — that would break the whole product (you cannot swipe to change a slide if the overlay stole focus from PowerPoint).

**Accept:** offscreen test constructs it, shows, moves between two simulated screens, and asserts geometry. `HUMAN`: confirm it does not steal focus from a fullscreen presentation.

## T031 — Toasts
**Files:** `src/beckon/ui/toast.py`

**Do:** Small overlay card near a screen corner: icon, action label, fade in/out (200 ms), stacked queue, auto-dismiss after ~1.4 s. Used for every executed action, gesture rejections when in "learning" mode, and voice transcripts.

**Accept:** offscreen test queues three toasts and asserts they dismiss in order without leaking widgets.

## T032 — Radial menu
**Files:** `src/beckon/ui/radial_menu.py`

**Do:** The interaction from `docs/GESTURES.md`. Geometry: N segments over 360°, inner dead zone radius, labels on the outer ring, hover determined by the angle from centre to the smoothed hand position and a minimum radius so a stationary hand selects nothing. Confirm on `pinch`/`fist`; auto-dismiss on timeout. Animate open/close with `QPropertyAnimation` (scale + opacity, ~180 ms) — this is the piece people will screenshot, so it has to look right.

**Accept:** unit test on the geometry function alone: given a centre, a radius, and a point at a known angle, the correct segment index is returned, and points inside the dead zone return `None`. `HUMAN`: visual polish check.

## T033 — Tray, full
**Files:** `src/beckon/ui/tray.py`

**Do:** Arm/disarm with live state icon, profile switcher (radio group, plus "Auto"), voice on/off, "Open settings", "Onboarding", "Show stats", "Pause for 15 minutes", Quit. Tooltip shows current profile and FPS.

**Accept:** offscreen test asserts menu actions exist and toggling each fires the right signal.

## T034 — Global hotkeys
**Files:** `src/beckon/core/hotkeys.py`

**Do:** `pynput.keyboard.GlobalHotKeys` on a daemon thread. Defaults: `Ctrl+Shift+G` arm/disarm, `Ctrl+Shift+V` push-to-talk voice, `Ctrl+Shift+Esc`… (no — that is Task Manager) use `Ctrl+Alt+Shift+P` panic disarm. Rebindable in settings. Hotkey capture must not block; deliver via the event bus.

**Accept:** test injects the callback directly and asserts the arm signal fires. Real key capture is `HUMAN`.

## T035 — Settings window
**Files:** `src/beckon/ui/settings_window.py` (+ one module per tab under `ui/settings/`)

**Do:** Tabs: **General** (start with OS, arm on start, theme, hotkeys) · **Camera** (device, resolution, mirror, active zone editor, live preview) · **Gestures** (per-profile binding table, sensitivity sliders bound to the arming config, "test mode" that shows what would fire without firing it) · **Voice** (enable, wake word, mic device, model download button with progress, command list) · **Presence** (away/lock delays, per-behaviour toggles) · **Profiles** (create/edit/delete, app-match rules) · **Privacy** (plain-language statement, "camera is only on while armed", "no data leaves this device", buttons to clear stats and delete trained gestures) · **About** (version, update check, links, licence).

"Test mode" on the Gestures tab is important: it lets a user tune sensitivity safely, and it is also how a human QA session verifies gestures without side effects.

**Accept:** offscreen test opens every tab, changes one value on each, saves, reloads, and asserts persistence.

## T036 — Onboarding wizard
**Files:** `src/beckon/ui/onboarding.py`

**Do:** First-run flow: welcome → camera permission and selection with live preview → "hold up your open palm" calibration (measures the user's hand span and lighting, writes derived thresholds to config) → teaches three gestures with live feedback and a success tick → optional voice setup and model download → done. Skippable, re-runnable from the tray.

The calibration step matters: hand size and camera FOV vary enormously, and a fixed pinch threshold is exactly why hobby projects feel broken for half their users.

**Accept:** offscreen test drives the wizard programmatically through every page with a synth source and asserts the config gains calibration values. `HUMAN`: run it once for real.

## T037 — Stats view
**Files:** `src/beckon/core/stats.py`, `src/beckon/ui/stats_view.py`

**Do:** SQLite counters: actions fired by id, gestures recognised, rejections, session durations, uptime armed. A simple view with totals and a 7-day sparkline. Local only; a visible "delete all statistics" button.

**Accept:** test inserts events, asserts aggregates; delete clears them.

## T038 — Theme and assets
**Files:** `src/beckon/ui/theme.py`, `scripts/make_icons.py`, `assets/*`

**Do:** One palette + type scale, dark and light, following the OS theme. Generate every icon programmatically. Keep the visual language restrained: translucent charcoal surfaces, one accent colour, no gradients-on-gradients. The HUD sits on top of other people's screens; it must feel like system UI, not a toy.

**Accept:** icons regenerate deterministically; a theme test asserts both palettes define every token.

---

# Phase 4 — Continuous control

## T040 — Cursor control
**Files:** `src/beckon/core/cursor.py`

**Do:** Map the index fingertip through an **active rectangle** (a sub-region of the camera frame, configurable) onto the virtual desktop, so a small hand movement crosses the whole screen without the hand leaving frame. One Euro filtered. Multi-monitor: map to the union rect of all screens, with an option to restrict to the primary. Include an acceleration curve (slow hand → 1:1 precision, fast hand → amplified) — this is what makes it usable rather than a novelty.

Click = pinch tap (pinch on and off within `click_max_ms`). Drag = pinch held. Right-click = two-finger pinch (thumb+middle). Scroll = peace pose moving vertically, velocity-scaled.

**Accept:** feed a synth path and assert the emitted cursor positions follow the expected screen path within tolerance, in dry-run. Assert a 90 ms pinch produces a click and a 900 ms pinch produces a drag, not two clicks.

## T041 — Pinch scrub
**Files:** `src/beckon/core/scrub.py`

**Do:** While a scrub-bound pinch is held, map `pinch_distance` (or vertical hand travel — configurable, vertical is more ergonomic for volume) to a 0–100 value, emit `ContinuousUpdate`, show a HUD bar. Apply on release, or live-apply with rate limiting for volume. Rate-limit OS calls to ~20 Hz regardless of frame rate.

**Accept:** synth sequence produces a monotonic value ramp and exactly one final applied value in dry-run.

## T042 — Two-hand gestures
**Files:** `src/beckon/vision/two_hand.py`

**Do:** `two_hand_spread` (zoom), `frame_capture` (screenshot of the framed rect — map the two L-corners from camera space to screen space through the active rectangle), `two_palm_push` (panic disarm).

**Accept:** synth two-hand fixtures classify correctly; the frame→screen rect mapping has a unit test with known inputs.

---

# Phase 5 — Profiles

## T050 — Foreground app detection
**Files:** `src/beckon/profiles/foreground.py`

**Do:** 2 Hz poll returning `(process_name, window_title)`. Windows via `win32gui.GetForegroundWindow` → `GetWindowThreadProcessId` → `psutil.Process().name()`. Cache and only emit on change.

**Accept:** test with a stubbed adapter asserts change-only emission.

## T051–T053 — Profile manager, built-ins, bindings
**Files:** `src/beckon/profiles/manager.py`, `builtin.py`, `schema.py`

**Do:** Profile = name, match rules (process names, window-title regex), bindings map, radial layout, enabled flag. Built-ins exactly as specified in `docs/GESTURES.md`. Auto-switch when a rule matches; manual override pins the profile until cleared. User profiles in the config dir override built-ins by name.

**Accept:** table-driven test: given a foreground app, the expected profile activates; a manual pin survives foreground changes; an unknown app falls back to Desktop.

## T054 — Profile editor UI
**Files:** `src/beckon/ui/settings/profiles_tab.py`

**Do:** CRUD for profiles, a binding table (gesture → action dropdown from the registry), match-rule editor, and a "duplicate built-in" button so users start from something working.

**Accept:** offscreen test creates a profile, binds a gesture, saves, reloads, asserts persistence.

---

# Phase 6 — Voice

## T060 — Mic capture
**Files:** `src/beckon/voice/mic.py`

**Do:** `sounddevice.InputStream` at 16 kHz mono, 80 ms blocks, into a ring buffer. Device enumeration and selection. Start/stop cleanly; release the device when voice is disabled so the mic indicator is honest.

**Accept:** test with a synthetic generator source (no real mic) fills and wraps the ring buffer correctly.

## T061 — Wake word
**Files:** `src/beckon/voice/wakeword.py`

**Do:** openWakeWord with the pretrained `hey_jarvis` ONNX model, score threshold from config, refractory period after a trigger so one utterance does not wake twice. Emit `WakeEvent`.

**Accept:** feeding silence for 10 s of synthetic audio yields zero wakes (false-positive floor). Real detection is `HUMAN`.

## T062 — STT with grammar
**Files:** `src/beckon/voice/stt.py`

**Do:** Vosk `KaldiRecognizer` constructed with a grammar JSON built from the registered command phrases plus `"[unk]"`. Listen window ≤ 5 s, terminated early on silence. Dictation mode constructs a second recogniser without the grammar.

```python
grammar = json.dumps(sorted(phrases) + ["[unk]"])
rec = KaldiRecognizer(model, 16000, grammar)
```

**Accept:** unit test builds the grammar from a stub registry and asserts every registered phrase appears. Transcription accuracy is `HUMAN`.

## T063 — Intent parsing
**Files:** `src/beckon/voice/intents.py`

**Do:** Phrase templates with slots (`"set volume to {n}"`, `"open {app}"`, `"remind me to {text} in {n} minutes"`). Match with rapidfuzz against templates, extract slots, normalise number words ("sixty" → 60) with a small word-to-number table. Below a confidence floor, emit a "did you mean" toast rather than acting.

**Accept:** a table of ~40 utterances (including near-misses and noise) maps to the expected intent and slots; three deliberate garbage inputs map to `None`.

## T064–T066 — TTS, command wiring, dictation
**Files:** `src/beckon/voice/tts.py`, `src/beckon/voice/commands.py`, `src/beckon/core/dictation.py`

**Do:** pyttsx3 confirmations (short, off by default except for actions with no visible effect). Wire every intent from `docs/GESTURES.md` to its `action_id`. Dictation streams recognised text to the focused window via the keyboard adapter, with punctuation commands ("comma", "new line", "period") and a visible HUD indicator while active.

**Accept:** dry-run test drives 20 intents through the router and asserts the action list. Dictation test asserts the keystroke sequence sent to a stub adapter.

## T067–T068 — Voice settings and model downloader
**Files:** `src/beckon/ui/settings/voice_tab.py`, `src/beckon/voice/models.py`

**Do:** Download Vosk + wake word models from the GitHub Release assets into `models_dir()`, with progress, SHA-256 verification, resume on failure, and a clear size warning before starting. Voice stays disabled until models are present. **Never download to C:.**

**Accept:** test against a local HTTP stub asserts checksum failure is rejected and a partial file is retried.

---

# Phase 7 — Presence

## T070–T073 — Face presence
**Files:** `src/beckon/vision/presence.py`, settings integration

**Do:** MediaPipe FaceDetector at 2 FPS on the same frames the vision thread already grabs (no second camera handle). State machine: `PRESENT → (no face for away_delay_s) → AWAY → (face for 2 s) → PRESENT`. Actions per `docs/GESTURES.md`, each individually toggleable, lock defaulting to **off**.

Hysteresis is essential — a person turning their head must not trigger away. Require the absence to be continuous across the whole delay, and require two consecutive detections to return.

**Accept:** state machine tested with a synthetic timeline of detection booleans; assert no transition on a 3 s gap, transition on a 50 s gap.

---

# Phase 8 — Extras

## T080 — Air draw / annotation
**Files:** `src/beckon/ui/annotate.py`

**Do:** A full-screen transparent canvas (not click-through while active) that draws a stroke following the pinch position. Colour and width picker via the radial menu, undo (`fist` shake or a bound action), clear on exit. Persist nothing; it is an ephemeral presentation tool.

**Accept:** offscreen test feeds a synth path and asserts the resulting stroke polyline. `HUMAN`: draw over a slide.

## T081 — Laser pointer
**Files:** part of `ui/annotate.py`

**Do:** A soft glowing dot following the fingertip, with a short fading trail. Click-through. Toggled by `slides.laser_toggle`.

**Accept:** offscreen render test. `HUMAN`: visual.

## T083 — Macro recorder
**Files:** `src/beckon/actions/macros.py`, `src/beckon/ui/settings/macros_tab.py`

**Do:** Record a keystroke sequence (with `pynput` listener) or accept a shell command, save it as a user action registered under `macro.<name>`, bindable like any built-in. Warn plainly that shell macros execute arbitrary commands.

**Accept:** a recorded macro appears in the registry and dry-runs to the expected keystroke list.

## T084 — Custom gesture trainer
**Files:** `src/beckon/vision/custom_model.py`, `src/beckon/ui/trainer.py`

**Do:** Wizard: name the gesture → record ~30 samples with a live countdown and a sample counter → extract the T012 feature vector for each → fit a scikit-learn classifier (start with `LogisticRegression`; fall back to `RandomForest` if accuracy on a held-out split is poor) → report cross-validated accuracy → save to the config dir → the new gesture appears in binding dropdowns immediately.

At inference, the custom classifier runs only if a model exists, and its output competes with the rule-based poses on confidence.

**Accept:** train on synthetic feature vectors from two distinct synthetic poses; assert ≥95% held-out accuracy and that the model round-trips through save/load.

## T085 — Plugin loader
**Files:** `src/beckon/actions/plugins.py`

**Do:** Load `plugins_dir()/*.py` that declare `BECKON_PLUGIN` and expose `register(api)`. Sandbox nothing — but isolate failures: a plugin that raises on import is logged, disabled, and surfaced in settings without stopping startup.

**Accept:** a fixture plugin registers an action that becomes bindable; a deliberately broken plugin is reported and does not crash the app.

## T086 — Update check
**Files:** `src/beckon/core/updater.py`

**Do:** Opt-in, off by default. Fetch the GitHub Releases API `latest`, compare semver, and show a tray notification with a link. Never auto-download, never auto-install.

**Accept:** test against a stubbed response asserts correct comparison for older/equal/newer, and that it is a no-op when disabled.

## T088 — Adaptive throttling
**Files:** `src/beckon/core/throttle.py`

**Do:** Drop to `fps_battery_cap` on battery; pause the vision thread entirely while a fullscreen exclusive app is foreground (games) unless the user opts in; pause while the user is actively typing (`pynput` keystroke rate above a threshold) to avoid gestures firing mid-typing.

**Accept:** unit tests on the policy function for each input combination.

---

# Phase 9 — Performance

## T090–T094
**Do:** Verify every number in the performance budget table in `docs/ARCHITECTURE.md` using `scripts/bench.py`. Fix what misses. Likely levers, in order of expected payoff: frame downscale before inference, `cv2.setNumThreads(2)`, skipping feature extraction when landmarks are unchanged, reusing numpy buffers instead of allocating per frame, and moving the face detector to every Nth frame.

Add `tests/test_perf_regression.py` that asserts per-frame processing stays under a wall-clock budget on synth input (generous enough not to be flaky in CI, tight enough to catch a 10× regression).

**Accept:** `bench.py` output meets every budget row on this machine, recorded in `docs/PROGRESS.md`. Any row that cannot be met gets an ADR explaining the revised number and why.

---

# Phase 10 — Tests and CI

## T100–T104
**Files:** `.github/workflows/ci.yml`, `tests/*`

**Do:** CI on `windows-latest` and `ubuntu-latest`: install deps (cached), `ruff check`, `pytest -q --cov=beckon`, upload coverage summary. Everything must pass headless with no camera, no mic, no display (`QT_QPA_PLATFORM=offscreen`, and `xvfb` is *not* needed if offscreen is used correctly).

Target ≥70% line coverage on `vision/`, `core/`, `actions/`, `voice/intents.py`. UI coverage will be lower; that is fine and expected.

**Accept:** a green CI badge on the default branch.

---

# Phase 11 — Packaging

## T110 — PyInstaller spec
**Files:** `beckon.spec`, `scripts/build_windows.ps1`

**Do:** `onedir` build. Critical bits:
```
--collect-all mediapipe
--hidden-import mediapipe.tasks.c
--add-data "models/hand_landmarker.task;models"
--add-data "assets;assets"
--noconsole
--icon assets/beckon.ico
```
The build script sets `$env:TEMP` and `$env:TMP` to `D:\tmp\build` **before** invoking PyInstaller, and outputs to `D:\study\claude projects\beckon\dist`.

Exclude what is not needed: `matplotlib`, `tkinter`, `PySide6.QtWebEngine*`, test packages. Expect ~250–350 MB unpacked; report the actual size in `PROGRESS.md`.

**Accept:** `dist\Beckon\Beckon.exe --version` prints the version. `dist\Beckon\Beckon.exe --headless --dry-run` starts and exits cleanly. Verify the `.task` model resolves via `sys._MEIPASS`.

## T111 — Installer
**Files:** `installer/beckon.iss`

**Do:** Inno Setup script: install per-user (no admin prompt) to `%LOCALAPPDATA%\Programs\Beckon`, Start Menu shortcut, optional "start with Windows" checkbox, clean uninstall that offers to remove the config dir. Output `Beckon-Setup-{version}.exe`.

**Accept:** the installer builds. Actual install/uninstall on a clean machine is `HUMAN`.

## T112 — Portable build
**Do:** Zip the `onedir` output as `Beckon-{version}-portable-win64.zip` with a `PORTABLE` marker file that makes the app keep its config next to the exe instead of in APPDATA.

**Accept:** running from the extracted zip writes config beside the exe.

## T113 — Checksums
**Do:** Emit `SHA256SUMS.txt` for every release artifact from the build script.

**Accept:** file present, hashes verify.

---

# Phase 12 — Release and distribution

## T120 — GitHub repository
**Do:** `gh repo create harshvardhan60792/beckon --public --source . --description "..."`. Push `main`. Topics: `computer-vision`, `mediapipe`, `gesture-control`, `voice-assistant`, `accessibility`, `python`, `offline-first`, `desktop-app`.

**Accept:** repo exists, CI runs green on the first push.

## T121 — README
**Files:** `README.md`

**Do:** Above the fold: one-sentence pitch, a demo GIF placeholder (`docs/demo.gif`, marked `HUMAN` to record), a feature list, and the install link. Then: how it works (with the pipeline diagram), the full gesture and voice reference, privacy statement, performance numbers measured on this machine, build-from-source instructions, the SmartScreen note, roadmap, and licence.

Write it for two readers at once: a recruiter skimming for 20 seconds, and a developer deciding whether to clone it.

**Accept:** renders correctly on GitHub; every link resolves; no placeholder text remains except the GIF slot.

## T122 — Release workflow
**Files:** `.github/workflows/release.yml`

**Do:** On a `v*` tag: build on `windows-latest`, run the installer build, attach the installer, the portable zip, and `SHA256SUMS.txt` to a GitHub Release with generated notes.

**Accept:** a `v0.1.0-rc1` tag produces a draft release with all three artifacts attached.

## T123 — Landing page
**Files:** `docs/site/index.html` (GitHub Pages from `/docs`)

**Do:** One page, no framework: hero with the demo GIF, three feature panels, a "how it works" diagram, a download button pointing at the latest release, and the privacy statement. Dark by default, respects `prefers-color-scheme`. Must load with zero external requests except a font, and work with JavaScript disabled.

**Accept:** Pages builds and serves; Lighthouse performance and accessibility both ≥95.

## T124 — Demo assets
**Do:** `HUMAN` — record three short clips (radial menu, presentation swipe, two-hand frame screenshot), convert to GIFs under 5 MB each, drop into `docs/`. Leave clear filename slots so the README works the moment they land.

## T125 — Final QA pass
**Do:** Walk the entire human checklist in `docs/TESTING.md` on a clean Windows user profile. File anything broken as a task in `PROGRESS.md` under "Post-v1".

---

# Out of scope for v1 (write these down, do not build them)

macOS and Linux beyond stub adapters · eye/gaze tracking · full ASL translation · cloud sync · mobile companion · multi-user profiles · a plugin marketplace · custom wake word training inside the app (Colab notebook link only).
