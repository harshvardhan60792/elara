# RESEARCH — findings that shaped the design

Gathered 2026-09-09. Re-verify anything version-specific before relying on it.

## Machine facts (verified locally)

| Fact | Value |
|---|---|
| OS | Windows 11 Home Single Language 10.0.22631 |
| Python available | 3.14.3 (default), 3.12, 3.11 |
| C: free space | **4.4 GB** — effectively full |
| D: free space | 128.5 GB |
| git identity | Harshvardhan / harsh60792@gmail.com |
| GitHub account | `harshvardhan60792` (gh CLI authenticated) |

## Hand tracking

- MediaPipe **Tasks API** is the current path (`mp.tasks.vision.HandLandmarker`, `GestureRecognizer`). The legacy `mp.solutions.hands` API is deprecated and was even missing from some 0.10.x builds.
- `HandLandmarker` returns **21 landmarks per hand**, in image coordinates and world coordinates, plus handedness.
- `RunningMode.LIVE_STREAM` internally tracks between frames so palm detection does not re-run every frame — materially lower latency and CPU than re-detecting. Use it, not `IMAGE` mode in a loop.
- `GestureRecognizer` ships 7 canned gestures: 👍 👎 ✌️ ☝️ ✊ 👋 🤟.
- Custom gestures: MediaPipe Model Maker trains a classification head on landmark embeddings and exports `.task`. Requires TensorFlow — heavy.
- **PyPI**: `mediapipe` is at **1.0.1**, and `pip index versions mediapipe` under Python 3.12 resolves it, so 3.12 wheels exist. MediaPipe supports **3.8–3.12 only**; 3.13+ requires building from source.

## Wake word

- **openWakeWord** — open source, free, unlimited, ships pretrained models including `hey_jarvis`, `alexa`, `hey_mycroft`. On Windows it installs `onnxruntime` (tflite-runtime has no modern Windows support). Custom models trainable via a Colab notebook in ~1 hour.
- **Porcupine** (Picovoice) — easier custom wake words but commercial licensing, quoted around $6K/yr for full SDK. Disqualified by the "free and unlimited" requirement.
- Benchmarks in the wild report openWakeWord matching or beating Porcupine on accuracy for equivalent training data.

## Speech to text

- **Vosk** — ~50 MB small English model, ~300 MB RAM at runtime, streaming with zero-latency partials, and crucially supports a **constrained grammar** (pass a JSON list of allowed phrases) which sharply improves accuracy for a fixed command vocabulary.
- **faster-whisper** — better raw accuracy (CTranslate2, 2× faster than Whisper on CPU, int8 quantisation) but heavier and higher latency; better suited to confirmed segments than to snappy commands.
- Common production pattern is a hybrid: Vosk for low-latency partials, Whisper for confirmed segments, ~500–800 ms latency.
- Newer options exist (sherpa-onnx / Zipformer / Parakeet / Moonshine) with better accuracy per compute, worth revisiting if Vosk's accuracy disappoints.

**Choice:** Vosk small + grammar for v1 (smallest, fastest, offline, good enough for a closed command set). faster-whisper is an optional backend behind a config flag for dictation mode.

## OS control

- **Volume**: `pycaw` on Windows (Core Audio `IAudioEndpointVolume`), AppleScript via `osascript` on macOS, `pactl`/`amixer` on Linux. No single cross-platform library is trustworthy — write a thin platform adapter.
- **Media keys**: synthesise `VK_MEDIA_PLAY_PAUSE` / `NEXT_TRACK` / `PREV_TRACK`. These are honoured by Spotify, VLC, browsers, most players.
- **Cursor/keyboard**: `pynput` (also gives global hotkeys). `pyautogui` is the common choice in hobby projects but has a hard-coded failsafe and slower synthesis; `pynput` is the better base.

## Packaging

- PyInstaller does **not** pick up MediaPipe's `.task` model bundles or all its binaries automatically. Required: `--collect-all mediapipe`, explicit `--add-data` for every `.task` file, `--hidden-import mediapipe.tasks.c`, and a runtime path helper that checks `sys._MEIPASS`.
- Prefer `onedir` over `onefile`: onefile unpacks ~200 MB to temp on every launch, which is slow and, on this machine, would land on C: unless `TEMP` is redirected.
- **Code signing**: an unsigned .exe triggers SmartScreen. EV certificates no longer bypass it (that behaviour was removed in 2024) — everything now builds reputation over time. Cheapest real option is Azure Trusted Signing at roughly $10/month; Sigstore does not produce Authenticode signatures Windows trusts. **Decision: ship unsigned, publish SHA-256 checksums, document the "More info → Run anyway" step in the README.** Revisit if downloads justify $10/mo.

## Competitive landscape

Searched GitHub topics `hand-gesture`, `gesture-control`, `hand-tracking`, `mediapipe-hands`, plus AlternativeTo/ProductHunt.

- The overwhelming majority are single-file "virtual mouse" scripts: MediaPipe + PyAutoGUI, move cursor with index finger, pinch to click. No packaging, no settings, no misfire handling.
- **GestureSign** is a real Windows product but it is touchpad/tablet/mouse-stroke based, not webcam based.
- Smaller webcam tools exist (Alea-AirCursor, InScroll, Zesture) — each covers one narrow slice (cursor, or scroll, or media).
- Nothing found that combines: gestures + voice + presence, profile auto-switching, an installable packaged build, and custom gesture training.

**Differentiation to protect:** it is a *product*, not a demo. Onboarding, misfire prevention, a performance budget, and a real installer are the moat.

## Sources

- [Hand landmarks detection guide for Python](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python)
- [Gesture recognition task guide](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer)
- [Gesture recognizer model customization](https://ai.google.dev/edge/mediapipe/solutions/customization/gesture_recognizer)
- [Which Python versions does MediaPipe support (issue #6081)](https://github.com/google-ai-edge/mediapipe/issues/6081)
- [openWakeWord](https://github.com/dscripka/openWakeWord)
- [Wake word detection guide 2026 (Picovoice, for the commercial comparison)](https://picovoice.ai/blog/complete-guide-to-wake-word/)
- [Vosk API](https://github.com/alphacep/vosk-api) / [Vosk models](https://alphacephei.com/vosk/)
- [Vosk vs Whisper local, 2026](https://www.sinologic.net/en/2026-05/vosk-vs-whisper-local-the-ultimate-2026-guide-to-self-hosted-speech-recognition-stt.html)
- [PyInstaller: when things go wrong](https://pyinstaller.org/en/stable/when-things-go-wrong.html)
- [MediaPipe Python setup incl. PyInstaller notes](https://developers.google.com/edge/mediapipe/solutions/setup_python)
- [Code signing options for Windows developers](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options)
- [PySide6 QSystemTrayIcon](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSystemTrayIcon.html)
- [GitHub topic: gesture-control](https://github.com/topics/gesture-control?l=python&o=asc&s=stars)
