# DECISIONS (ADR log)

Append-only. Never edit or delete an entry. To reverse one, add a new ADR and mark the old `SUPERSEDED BY ADR-xxx`.

---

## ADR-001 — Name: Beckon
**Status:** accepted · 2026-09-09

"Beckon" means to summon someone with a gesture — literally what the product does, and it covers the voice layer too (you can beckon by calling out). Short, pronounceable, memorable, and subtle rather than sci-fi corny.

Rejected: *Jarvis* (Marvel/Meta, overused in exactly this project category), *Luna* (thousands of apps), *Mira* (collides with an existing desktop automation agent product), *Lumen* (telecom giant), *Vela* (KubeVela), *Halo* (game).

Repo: `harshvardhan60792/beckon`. Package: `beckon`. Tagline: **"Control your computer with a look, a wave, a word."**

---

## ADR-002 — Python 3.12, not 3.13/3.14
**Status:** accepted · 2026-09-09

MediaPipe publishes wheels for 3.8–3.12 only; 3.13+ requires building from source. 3.12 is installed on this machine. All tooling pins `py -3.12`.

---

## ADR-003 — Everything on D:, nothing on C:
**Status:** accepted · 2026-09-09

C: has ~4.4 GB free. MediaPipe + OpenCV + PySide6 + PyInstaller builds would exhaust it. venv, pip cache, build temp, and scratch output are all pinned to D: paths. **Why:** filling the system drive breaks the machine, not just the build.

---

## ADR-004 — MediaPipe Tasks API in LIVE_STREAM mode
**Status:** accepted · 2026-09-09

`HandLandmarker` with `RunningMode.LIVE_STREAM` tracks hands between frames instead of re-running palm detection each frame. Lower latency, materially lower CPU. The callback is async, so the vision thread pushes results onto a queue rather than returning them inline.

Rejected: legacy `mp.solutions.hands` (deprecated, absent from some builds); running `IMAGE` mode in a loop (re-detects every frame).

---

## ADR-005 — Rule-based static gesture classifier, not a trained model
**Status:** accepted · 2026-09-09

Static poses (fist, open palm, point, peace, pinch, thumbs up/down, OK, L-shape) are classified by geometric rules over the 21 landmarks — finger extension states, inter-tip distances, palm normal.

**Why:** deterministic, debuggable, zero training data, zero model download, and unit-testable against synthetic landmark arrays with no camera. A neural classifier would be a black box that an unattended agent cannot validate.

The canned `GestureRecognizer` model is *not* used for the core set — it only knows 7 gestures, gives no pinch distance, and adds a second model's inference cost. User-trained custom gestures use a small scikit-learn classifier over the same feature vector (ADR-013).

---

## ADR-006 — PySide6 for tray, overlay, and settings
**Status:** accepted · 2026-09-09

One toolkit for everything: `QSystemTrayIcon` (Windows tray, macOS menu bar), frameless translucent always-on-top windows for the HUD and radial menu, and a normal settings window. Qt's event loop is also the natural place to marshal cross-thread events via signals.

Rejected: pystray + tkinter (two toolkits, poor translucency, no click-through), Electron (hundreds of MB, absurd for a Python CV app).

Licensing note: PySide6 is LGPL, fine for an MIT app that dynamically links it.

---

## ADR-007 — Single process, three threads
**Status:** accepted · 2026-09-09

Qt main thread (UI + action dispatch), vision thread (capture + inference), audio thread (wake word + STT). MediaPipe and OpenCV release the GIL during native inference, so threads are sufficient — multiprocessing would add IPC cost and packaging pain for no gain.

Cross-thread communication is Qt signals only. No shared mutable state.

---

## ADR-008 — One Euro filter for cursor smoothing
**Status:** accepted · 2026-09-09

Raw landmark positions jitter by several pixels frame to frame. The One Euro filter adapts its cutoff to speed: heavy smoothing when the hand is nearly still (precision), light smoothing when moving fast (no lag).

**Why it matters:** this single choice is the difference between "feels like a product" and "feels like a student demo". Every comparable GitHub project uses naive linear interpolation and feels laggy or jittery.

---

## ADR-009 — Arming: dwell + N-of-M voting + per-action cooldown
**Status:** accepted · 2026-09-09

A gesture fires only when it holds for a dwell period, wins an N-of-M frame vote, clears a confidence floor, and its action is off cooldown.

**Why:** an always-watching camera that misfires is worse than no product. Accidental volume changes while gesturing on a video call would kill trust immediately.

---

## ADR-010 — Attention gesture → radial menu, as the primary interaction
**Status:** accepted · 2026-09-09

Holding an open palm for ~700 ms opens a translucent radial menu at the hand position showing the current profile's actions. Point to highlight, pinch to confirm.

**Why:** solves discoverability (nobody memorises 15 gestures), solves misfires (nothing fires outside command mode unless explicitly bound as a direct gesture), and is the single most demo-able feature in the product.

---

## ADR-011 — openWakeWord + Vosk with constrained grammar
**Status:** accepted · 2026-09-09

Wake word: openWakeWord, free and unlimited, using the pretrained `hey_jarvis` model as the shipped default (a custom "hey beckon" model can be trained later in Colab). Porcupine is disqualified by commercial licensing.

STT: Vosk small English (~50 MB), invoked only after a wake, with a **grammar constrained to the registered command phrases** — a large accuracy win over free-form recognition on a fixed vocabulary.

Dictation mode is the exception: it needs open vocabulary, so it drops the grammar and may optionally use a faster-whisper backend.

---

## ADR-012 — Voice models download on first use, vision models ship in the installer
**Status:** accepted · 2026-09-09

Hand landmarker `.task` (~8 MB) is core and bundled. Vosk (~50 MB) plus wake word models are bundled only in the "full" build; the default installer fetches them from the GitHub Release on first enable of the voice feature.

**Why:** keeps the default installer under ~100 MB and makes voice genuinely optional for users who only want gestures.

---

## ADR-013 — Custom gesture training uses scikit-learn, not MediaPipe Model Maker
**Status:** accepted · 2026-09-09

The trainer records ~30 samples of a user's new pose, extracts the same normalised feature vector used by the rule-based classifier, and fits a small classifier (e.g. `RandomForest` / `LogisticRegression`) pickled to the user's config dir.

**Why:** Model Maker pulls in TensorFlow — hundreds of MB and a packaging nightmare — to train what is, on landmark features, a trivially separable problem. scikit-learn trains in under a second on 30 samples.

---

## ADR-014 — `--dry-run` is the default for all automated execution
**Status:** accepted · 2026-09-09

The action layer is gated behind an executor that, in dry-run, logs a structured record instead of touching the OS. Tests assert against that log.

**Why:** an unattended agent building this at 3am must never actually mute the machine, lock the screen, or type into a focused window. This is also what makes the action layer testable in CI.

---

## ADR-015 — Synthetic landmark fixtures, not recorded video, for tests
**Status:** accepted · 2026-09-09

`scripts/synth_landmarks.py` generates deterministic 21-point hand landmark arrays for each pose and interpolates them into motion sequences for swipes and circles.

**Why:** an agent has no camera. Recorded video would also make the repo heavy and the tests slow and flaky. Real-camera accuracy is explicitly a human QA step in `docs/TESTING.md`, not something to be claimed as passing.

---

## ADR-016 — Adaptive frame rate as the core performance strategy
**Status:** accepted · 2026-09-09

Idle (no hand in frame): 8 FPS scan. Hand present: 30 FPS. Face presence check: 2 FPS on a separate cadence. On battery: cap at 15 FPS.

**Why:** the stated requirement is "must not hang the laptop". Running 30 FPS inference continuously for an app that is idle 95% of the time is the main thing that would make it hot, loud, and battery-hostile. This is what keeps idle CPU under the 3% budget.

---

## ADR-017 — Ship unsigned, document the SmartScreen step
**Status:** accepted · 2026-09-09

Windows will show "Windows protected your PC" for an unsigned installer. EV certificates no longer bypass this. The README documents "More info → Run anyway" and publishes SHA-256 checksums.

Revisit at Azure Trusted Signing (~$10/month) only if download volume justifies it. Cost must stay at zero for v1.

---

## ADR-018 — No telemetry, camera only while armed
**Status:** accepted · 2026-09-09

No analytics, no crash reporting, no network calls except user-initiated model download and an opt-in update check. The camera device is opened when armed and released when disarmed, so the hardware indicator light is an honest signal of state.

**Why:** the product asks for permanent webcam and microphone access. Trust is the entire premise; a single telemetry ping would undermine the pitch and the privacy claim in the README.

---

## ADR-019 — MIT licence
**Status:** accepted · 2026-09-09

Maximum adoption for a portfolio project, compatible with every dependency in the stack (MediaPipe Apache-2.0, PySide6 LGPL dynamically linked, Vosk Apache-2.0, openWakeWord Apache-2.0).
