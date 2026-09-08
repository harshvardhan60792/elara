# ARCHITECTURE

## Threading model

One process. Three threads. Qt signals are the only cross-thread channel.

```
┌─ Qt main thread ────────────────────────────────────────────┐
│  QApplication event loop                                     │
│  · tray icon + menu        · overlay HUD / radial menu       │
│  · toasts                  · settings window                 │
│  · ActionRouter  ──────────────▶  ActionExecutor ─▶ platform │
└──────────────▲──────────────────────────▲────────────────────┘
               │ Qt signal                │ Qt signal
┌──────────────┴───────────┐  ┌───────────┴─────────────────────┐
│ Vision thread            │  │ Audio thread                     │
│ camera → landmarker →    │  │ mic → wakeword → (on wake) STT → │
│ features → classifiers → │  │ intent parse → VoiceCommand      │
│ arming → GestureEvent    │  │                                  │
└──────────────────────────┘  └──────────────────────────────────┘
```

Threads are enough because MediaPipe, OpenCV, ONNX Runtime and Vosk all release the GIL inside native inference. Actions execute on the main thread (they are microsecond-scale OS calls); anything genuinely slow — screen recording, model download, custom gesture training — goes to a `QThreadPool` worker.

**Rule:** vision and audio threads never touch Qt widgets and never call the action layer directly. They emit events. The router decides.

## Vision pipeline

```
VideoCapture (640×480, adaptive FPS)
  → BGR→RGB, mp.Image
  → HandLandmarker.detect_async(frame, timestamp_ms)      [LIVE_STREAM]
  → callback → result queue
  → FeatureExtractor      normalised landmarks, finger states, distances, palm normal, velocity
  → StaticClassifier      rule-based pose → PoseCandidate(name, confidence)
  → CustomClassifier      optional sklearn model for user-trained poses
  → TrajectoryBuffer      last ~1.0 s of palm centres, per hand
  → DynamicClassifier     swipes, circles, push
  → ArmingGate            dwell + N-of-M vote + confidence floor + active zone + cooldown
  → GestureEvent          emitted to router
```

Continuous controls (cursor position, pinch-scrub value, two-hand spread) bypass the arming gate — they are *state*, not discrete events — and are published as `ContinuousUpdate` at frame rate, smoothed by the One Euro filter, only while their owning mode is active.

### Why the arming gate exists
Any always-on camera classifier fires false positives. Four independent filters stack:
1. **Confidence floor** — reject weak poses.
2. **N-of-M vote** — pose must win e.g. 4 of the last 6 frames.
3. **Dwell** — pose must be stable for a minimum duration.
4. **Cooldown** — per action, blocks re-fire.

Plus an optional **active zone** (only respond to hands in a configured region of frame) and the **command-mode gate** (most actions only reachable via the radial menu, so nothing fires from incidental hand movement).

## Audio pipeline

```
sounddevice InputStream (16 kHz mono, 80 ms blocks)
  → ring buffer
  → openWakeWord.predict(chunk)            ~continuous, cheap
  → score > threshold → WAKE
  → Vosk KaldiRecognizer with grammar = registered command phrases
  → partial/final transcript (max ~5 s window, silence-terminated)
  → IntentParser: fuzzy match (rapidfuzz) against command registry, extract slots
  → VoiceCommand event → router
  → optional pyttsx3 confirmation
```

Dictation mode swaps the grammar out for open vocabulary and streams text to the focused window via the keyboard adapter until stopped.

## Action layer

```
GestureEvent / VoiceCommand
  → ActionRouter
       resolve binding via ProfileManager (active profile → gesture→action map)
       check cooldown, check armed state
  → ActionRegistry.get(action_id)
  → ActionExecutor
       dry_run?  → log structured record, return
       else      → platform adapter call
  → Toast feedback + stats counter
```

`ActionRegistry` is a dict of `action_id → ActionSpec(callable, label, icon, category, profiles, needs_confirm)`. Every action is addressable from gestures, voice, the radial menu, and plugins through the same id — one registry, four front-ends.

## Platform adapters

`platform/base.py` defines the interface; `windows.py`, `macos.py`, `linux.py` implement it. Windows is the v1 target; the other two must at minimum import cleanly and raise `NotImplementedError` on unsupported calls so the app still runs.

| Capability | Windows | macOS | Linux |
|---|---|---|---|
| volume | pycaw | osascript | pactl |
| media keys | VK_MEDIA_* via pynput | osascript / MediaRemote | playerctl (MPRIS2) |
| brightness | WMI | osascript | brightnessctl |
| lock / sleep | `LockWorkStation` | `pmset`/AppleScript | loginctl |
| foreground app | win32gui + psutil | NSWorkspace via pyobjc | xdotool / wmctrl |
| window mgmt | win32gui | AppleScript | wmctrl |
| DND | Focus Assist registry | `do not disturb` shortcut | dbus |

## Profiles

`ProfileManager` polls the foreground application (~2 Hz, cheap) and switches the active profile when it matches a rule. Each profile is a named map of `gesture_id → action_id` plus a radial-menu layout. Built-ins: **Desktop**, **Media**, **Presentation**, **Meeting**, **Browser**, **Reading**. Users can add profiles and rebind anything; user profiles live in the config dir and override built-ins by name.

## Configuration and state

```
%APPDATA%\Beckon\           (Windows; XDG dirs elsewhere)
  config.json               all settings, hot-reloaded on change
  profiles/*.json           user profiles and bindings
  gestures/custom.pkl       trained custom gesture classifier
  gestures/samples/*.npz    recorded training samples
  plugins/*.py              user drop-in actions
  stats.db                  local usage counters (sqlite)
  logs/beckon.log           rotating
```

Config is a nested dataclass tree with defaults in code, serialised to JSON. Unknown keys are preserved on save so a downgrade does not destroy newer settings. **Every tunable threshold lives here** — no magic numbers in logic.

## Plugin contract

A `.py` file in the plugins dir exposing:

```python
BECKON_PLUGIN = "1"

def register(api):
    api.add_action(
        id="myplugin.hello",
        label="Say hello",
        category="custom",
        run=lambda ctx: ctx.notify("hello"),
    )
```

Plugins get the same `ActionRegistry` front door as built-ins, so a plugin action is immediately bindable to a gesture, a voice phrase, and a radial-menu slot. Plugins run in-process and are trusted code — the settings UI states this plainly.

## Performance budget (enforced by `scripts/bench.py`)

| State | CPU (one core, mid-range laptop) | RAM |
|---|---|---|
| Disarmed | ~0% | < 120 MB |
| Armed, idle scan (8 FPS, no hand) | < 3% | < 250 MB |
| Armed, tracking (30 FPS, hand present) | < 12% | < 400 MB |
| Voice enabled, wake word listening | +< 2% | +~150 MB |
| Voice actively transcribing | +< 8% | +~300 MB |

Latency targets: gesture motion → action dispatch **< 120 ms**; wake word → listening state **< 300 ms**; cold start to tray icon **< 3 s**.

Techniques: adaptive FPS (ADR-016), 640×480 capture, `cv2.setNumThreads(2)` to stop OpenCV oversubscribing, `CAP_DSHOW` backend on Windows for fast open, face presence on a 2 FPS cadence rather than per frame, and releasing the camera entirely when disarmed.

## Startup sequence

1. Parse CLI (`--dry-run`, `--source`, `--headless`, `--log-level`, `--config`).
2. Resolve paths (handles PyInstaller `sys._MEIPASS`), set up rotating logs.
3. Load config; migrate if schema version is older.
4. Build `AppContext` (config, registry, platform adapter, event bus, stats).
5. Register built-in actions, load profiles, load plugins.
6. Create tray icon. **Disarmed by default** — no camera is opened.
7. If first run, launch the onboarding wizard.
8. On arm: start vision thread, and audio thread if voice is enabled.
