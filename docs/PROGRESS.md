# PROGRESS

**How to use this file:** the lowest unchecked box is the next task. Read its spec in `docs/PLAN.md`, build it, run the acceptance check, then tick it here with a one-line note. One commit per task. If blocked, mark `[!]` and write why — do not silently skip.

Legend: `[ ]` todo · `[x]` done · `[!]` blocked · `[~]` partial

**Status:** planning complete, no application code written yet.
**Last updated:** 2026-09-09 by the planning session.

---

## Phase 0 — Bootstrap
- [ ] T001 venv on D + requirements
- [ ] T002 repo skeleton, pyproject, gitignore, LICENSE, git init
- [ ] T003 paths.py + config.py
- [ ] T004 logging_setup.py
- [ ] T005 events.py event bus
- [ ] T006 app shell + tray stub (disarmed on launch)
- [ ] T007 CLI (dry-run default)
- [ ] T008 pytest harness + first test

## Phase 1 — Vision core
- [ ] T010 camera / video / synth frame sources
- [ ] T011 MediaPipe HandLandmarker wrapper + fetch_models.py
- [ ] T012 feature extraction
- [ ] T013 One Euro filter
- [ ] T014 static gesture classifier (12 poses)
- [ ] T015 synthetic landmark generator + fixtures
- [ ] T016 trajectory buffer + dynamic gestures
- [ ] T017 vision engine thread + adaptive FPS
- [ ] T018 camera preview widget
- [ ] T019 bench.py

## Phase 2 — Actions
- [ ] T020 platform adapters (base + Windows real, mac/Linux stubs)
- [ ] T021 action registry + executor (dry-run gate)
- [ ] T022 media + volume actions
- [ ] T023 mouse + keyboard actions
- [ ] T024 window + desktop actions
- [ ] T025 app index, launch, switch
- [ ] T026 capture (screenshot, region, record) + meeting + browser + text
- [ ] T027 arming gate (confidence, vote, dwell, cooldown, zone)
- [ ] T028 router
- [ ] T029 end-to-end synth test

## Phase 3 — UI
- [ ] T030 overlay base (translucent, click-through, no focus steal)
- [ ] T031 toasts
- [ ] T032 radial menu
- [ ] T033 full tray menu
- [ ] T034 global hotkeys
- [ ] T035 settings window (all tabs)
- [ ] T036 onboarding + calibration wizard
- [ ] T037 stats
- [ ] T038 theme + generated icons

## Phase 4 — Continuous control
- [ ] T040 cursor control (active rect, acceleration, click/drag/scroll)
- [ ] T041 pinch scrub (volume/brightness/zoom)
- [ ] T042 two-hand gestures (spread, frame capture, panic)

## Phase 5 — Profiles
- [ ] T050 foreground app detection
- [ ] T051 profile manager + auto-switch
- [ ] T052 built-in profiles
- [ ] T053 binding schema + persistence
- [ ] T054 profile editor UI

## Phase 6 — Voice
- [ ] T060 mic capture
- [ ] T061 wake word (openWakeWord)
- [ ] T062 Vosk STT with constrained grammar
- [ ] T063 intent parsing + slots
- [ ] T064 TTS confirmations
- [ ] T065 command wiring (full catalogue)
- [ ] T066 dictation mode
- [ ] T067 voice settings tab
- [ ] T068 model downloader (checksums, resume, never C:)

## Phase 7 — Presence
- [ ] T070 face detector at 2 FPS
- [ ] T071 away/back state machine with hysteresis
- [ ] T072 presence actions (pause media, mute mic, optional lock)
- [ ] T073 presence settings + privacy copy

## Phase 8 — Extras
- [ ] T080 air draw / annotation
- [ ] T081 laser pointer
- [ ] T083 macro recorder
- [ ] T084 custom gesture trainer (sklearn)
- [ ] T085 plugin loader
- [ ] T086 update check (opt-in)
- [ ] T088 adaptive throttling (battery, fullscreen, typing)

## Phase 9 — Performance
- [ ] T090 adaptive FPS verified
- [ ] T091 idle scan mode verified
- [ ] T092 budget verification via bench.py — record numbers here
- [ ] T093 memory audit
- [ ] T094 perf regression test

## Phase 10 — Tests and CI
- [ ] T100 unit coverage ≥70% on vision/core/actions/intents
- [ ] T101 e2e synth suite green
- [ ] T102 ruff clean
- [ ] T103 CI workflow (windows + ubuntu, headless)
- [ ] T104 CI badge green on main

## Phase 11 — Packaging
- [ ] T110 PyInstaller spec + build script (TEMP on D)
- [ ] T111 Inno Setup installer (per-user, no admin)
- [ ] T112 portable zip
- [ ] T113 SHA256SUMS

## Phase 12 — Release
- [ ] T120 GitHub repo created and pushed
- [ ] T121 README
- [ ] T122 release workflow on tag
- [ ] T123 landing page (GitHub Pages)
- [ ] T124 demo GIFs — HUMAN, needs a webcam
- [ ] T125 final QA pass — HUMAN

---

## Measured numbers (fill in as they are obtained)

| Metric | Target | Measured | Date |
|---|---|---|---|
| Idle CPU (armed, no hand) | < 3% | — | — |
| Active CPU (30 FPS tracking) | < 12% | — | — |
| RAM active | < 400 MB | — | — |
| Gesture → action latency | < 120 ms | — | — |
| Cold start to tray | < 3 s | — | — |
| Installer size | < 150 MB | — | — |

## Notes and surprises

_Append findings here as work proceeds — anything a future session would waste time rediscovering._

## Post-v1 backlog

_File anything discovered but out of scope here rather than expanding a task._
