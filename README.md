# Elara

**Control your computer with a look, a wave, a word.**

Elara is a desktop app that turns your webcam into a hands-free controller. Raise a palm and a menu appears under your hand. Swipe to change slides. Pinch and lift to turn the volume up. Say "hey jarvis, open Spotify". Walk away and your music pauses by itself.

Everything runs **on your machine**. No account, no cloud, no subscription, no data leaves your computer. The camera is only on while Elara is armed.

> Status: in development. See [`docs/PROGRESS.md`](docs/PROGRESS.md).

<!-- DEMO GIF SLOT: docs/demo.gif -->

## What it does

**Gestures** â€” a radial menu you summon with an open palm, swipes for slides and tracks, pinch-and-drag for volume and brightness, fingertip cursor control with click and drag, and a two-handed "frame" gesture that screenshots exactly the region you outline with your hands.

**Voice** â€” an offline wake word and a local speech recogniser. Open apps, search, control media, set timers, dictate text, read the selection aloud. Nothing is transcribed off-device.

**Presence** â€” Elara notices when you leave. It pauses your media, mutes your mic, and optionally locks the screen. It resumes when you come back.

**Profiles** â€” bindings switch automatically with the app you are using. Swipes advance slides in PowerPoint, skip tracks in Spotify, and change tabs in your browser, without you configuring anything.

**Yours to change** â€” rebind any gesture, train your own gestures from ~30 samples, record macros, or drop a Python file in the plugins folder to add your own actions.

## Why it exists

Accessibility, presentations, and the kitchen-hands problem: the times you need your computer but cannot touch it. It is also a demonstration that a genuinely useful hands-free interface can run entirely offline on an ordinary laptop without melting the battery.

## Install

Downloads will be on the [Releases](https://github.com/harshvardhan60792/elara/releases) page once v0.1.0 ships.

Windows will show *"Windows protected your PC"* because the installer is not code-signed (certificates cost money; this project is free). Click **More info â†’ Run anyway**. Verify the download against `SHA256SUMS.txt` if you would rather check than trust.

## Build from source

Requires **Python 3.12** â€” MediaPipe does not support 3.13+.

```powershell
git clone https://github.com/harshvardhan60792/elara
cd elara
.\scripts\setup_dev.ps1
.\.venv\Scripts\python.exe -m elara
```

Elara starts disarmed and in dry-run mode by default. Pass `--live` to let it actually control your machine.

## Privacy

- The webcam opens when you arm Elara and is released when you disarm it. The hardware indicator light is an honest signal.
- The microphone is only opened if you enable voice.
- No telemetry, no analytics, no crash reporting. The only network requests the app can ever make are the optional model download and an opt-in update check.
- Face detection is used for presence only â€” it detects *that* a face is there, never *whose*. Nothing about your face is stored or computed beyond a bounding box.
- Voice transcripts stay in memory and are logged only at DEBUG level, which is off by default.

## How it works

```
webcam â†’ MediaPipe hand landmarks â†’ geometric features â†’ pose + motion classifiers
       â†’ arming gate (confidence, voting, dwell, cooldown) â†’ profile bindings â†’ OS action

 mic   â†’ openWakeWord â†’ Vosk (grammar-constrained) â†’ intent match â†’ same OS actions
```

Design notes and the reasoning behind every choice are in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Documentation

| Doc | What is in it |
|---|---|
| [HANDOFF.md](docs/HANDOFF.md) | Start here |
| [PLAN.md](docs/PLAN.md) | Full implementation plan, task by task |
| [PROGRESS.md](docs/PROGRESS.md) | What is built so far |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Threading model, pipelines, performance budget |
| [DECISIONS.md](docs/DECISIONS.md) | Every design decision and why |
| [GESTURES.md](docs/GESTURES.md) | Gesture vocabulary and action catalogue |
| [TESTING.md](docs/TESTING.md) | Test strategy and the human QA checklist |
| [OVERNIGHT_GOAL.md](docs/OVERNIGHT_GOAL.md) | The build prompt and triage order |
| [RESEARCH.md](docs/RESEARCH.md) | Library evaluation and prior art |

## Licence

MIT.
