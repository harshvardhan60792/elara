# HANDOFF â€” read this first

You are picking up **Elara**, a desktop app that lets someone control their computer with hand gestures, voice, and webcam presence â€” fully offline, free, no account, no cloud.

Owner: Harshvardhan (GitHub `harshvardhan60792`). Machine: Windows 11, Python 3.12 available, C: drive nearly full so **everything lives on D:**.

## What Elara is, in one paragraph

A tray app. You arm it with a click or a hotkey. It watches a webcam, tracks your hands with MediaPipe, and turns poses and motions into real OS actions â€” volume, media, slides, cursor, window management, screenshots. Raise an open palm and a radial menu appears under your hand so you never have to memorise gestures. Say "hey jarvis" and it listens for a spoken command, parsed entirely on-device. It notices when you walk away and pauses your music and locks your screen. It switches gesture profiles automatically depending on whether you're in PowerPoint, Spotify, or a Zoom call. Everything runs locally; the camera is only on while armed.

## Why this exists

Portfolio project that a non-technical person can watch for five seconds and immediately understand, while still being technically deep enough to defend in an interview: real-time CV pipeline, signal filtering, temporal state machines, on-device ASR, cross-platform OS integration, threading under a GUI event loop, packaging and CI.

Every comparable project on GitHub is a 200-line "virtual mouse" script. The gap Elara fills: it is an actual installable product â€” profiles, misfire prevention, a settings UI, an onboarding wizard, custom gesture training, plugins, and a signed-off performance budget.

## Where to start

1. `docs/PROGRESS.md` â€” the live checklist. The lowest unchecked box is your task.
2. `docs/PLAN.md` â€” every task's full spec: files to touch, what to implement, acceptance criteria.
3. `CLAUDE.md` â€” the hard rules (D-drive only, Python 3.12, dry-run, no attribution).
4. `docs/ARCHITECTURE.md` â€” how the pieces fit and why the threading model is what it is.
5. `docs/DECISIONS.md` â€” every choice already made and the reason. Do not re-litigate these; if you must reverse one, append a superseding ADR.
6. `docs/GESTURES.md` â€” the gesture vocabulary and the action catalogue.
7. `docs/TESTING.md` â€” how to verify without a camera, and what only a human can check.

## The three things most likely to trip you up

1. **You cannot see the webcam.** Do not try to validate gesture accuracy by running the app. Use `scripts/synth_landmarks.py` to generate deterministic landmark sequences and test the classifier against those. Real-camera accuracy is a human QA step.
2. **Actions have real side effects.** Running the router for real will mute the machine, send keystrokes to the focused window, or lock the screen. `--dry-run` is the default in every test and every unattended run. Only a human flips it off.
3. **The C: drive will fill up.** MediaPipe, OpenCV, PySide6, and PyInstaller pull hundreds of megabytes. Every pip and build command in this repo pins its cache and temp dir to D:. Do not run a bare `pip install`.

## Current state

See `docs/PROGRESS.md`. At the time this file was written: planning complete, no application code written yet.
