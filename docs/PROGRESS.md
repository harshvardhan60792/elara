# PROGRESS

**How to use this file:** the lowest unchecked box is the next task. Read its spec in `docs/PLAN.md`, build it, run the acceptance check, then tick it here with a one-line note. One commit per task. If blocked, mark `[!]` and write why â€” do not silently skip.

Legend: `[ ]` todo Â· `[x]` done Â· `[!]` blocked Â· `[~]` partial

**Status:** Phases 0-2 complete and tested. Phase 3 partial (overlay, toasts, radial menu built; tray wired to real arm/disarm, profile switching still basic). 154/154 tests passing.
**Last updated:** 2026-09-09 overnight autonomous session.

---

## Phase 0 â€” Bootstrap
- [x] T001 venv on D + requirements â€” mediapipe/opencv/PySide6 install was slow (~430 kB/s network); two earlier attempts left duplicate pip processes running (one against system Python by mistake) and had to be killed and redone as a single supervised run
- [x] T002 repo skeleton, pyproject, gitignore, LICENSE, git init â€” package dirs: vision, voice, actions, platform_adapters, profiles, ui, core
- [x] T003 paths.py + config.py â€” unknown-key preservation uses a `._unknown` marker per section in `extra`, round-trip tested
- [x] T004 logging_setup.py
- [x] T005 events.py event bus â€” cross-thread signal delivery verified with qtbot.waitSignal from a worker thread
- [x] T006 app shell + tray stub (disarmed on launch) â€” SIGINT test had to be redesigned: sending a real CTRL_C_EVENT to a child process does not work in this sandboxed agent environment (no console attached to the parent), so it's tested via `signal.raise_signal` in-process instead; real Ctrl+C behavior needs HUMAN QA
- [x] T007 CLI (dry-run default)
- [x] T008 pytest harness + first test

## Phase 1 â€” Vision core
- [x] T010 camera / video / synth frame sources â€” SynthSource is a distinct interface (`read_landmarks()`), not FrameSource; it bypasses inference entirely rather than faking frames
- [x] T011 MediaPipe HandLandmarker wrapper + fetch_models.py â€” model actually downloaded and SHA-256 verified this session (`fbc2a3...62cde1`), placed at the real `models_dir()`; test only skips if that file is later missing
- [x] T012 feature extraction â€” found and fixed a real bug while writing this: `hand_span` was originally computed on normalized landmarks, which are always scale-1 by construction, making it useless as a distance-from-camera proxy; moved to raw landmarks
- [x] T013 One Euro filter
- [x] T014 static gesture classifier (12 poses) â€” writing the fixture-driven test (`tests/test_static_gestures.py`) surfaced three real classifier/fixture bugs, all fixed: (1) `point` had no guard against a pinching thumb, so a valid pinch with a straight index also matched `point`'s pattern and won on priority order; (2) the synthetic "folded" thumb was short-but-straight, which the tip-IP-MCP *angle* test reads as extended regardless of length, so `fist` classified as nothing; (3) the synthetic "straight_side" thumb's angle-to-index was 52.5Â°, under the l_shape classifier's 60Â° floor, so `l_shape` fell through to `point`
- [x] T015 synthetic landmark generator + fixtures â€” also added `held_*` fixtures (repeated-frame sequences) after discovering single-frame fixtures can never satisfy the arming gate's N-of-M vote + dwell
- [x] T016 trajectory buffer + dynamic gestures â€” real bug found via the fixture-driven test: `max_stroke_s` (meant to cap swipe completion time) was applied before branching into swipe-vs-circle, so it also rejected circles, which legitimately take longer than a quick swipe; moved the cap into the swipe branch only
- [x] T017 vision engine thread + adaptive FPS â€” pulled T027 (arming gate) forward from Phase 2 to satisfy this task's own acceptance test, which requires arming behavior; documented as ADR-022
- [x] T018 camera preview widget
- [x] T019 bench.py

## Phase 2 â€” Actions
- [x] T020 platform adapters (base + Windows real, mac/Linux stubs) â€” DND left unimplemented on Windows: Focus Assist has no supported public API (see ADR-021)
- [x] T021 action registry + executor (dry-run gate)
- [x] T022 media + volume actions
- [x] T023 mouse + keyboard actions
- [x] T024 window + desktop actions
- [x] T025 app index, launch, switch
- [x] T026 capture (screenshot, region, record) + meeting + browser + text â€” also added slides.* and elara.* (self_actions.py) to cover the full docs/GESTURES.md action catalogue
- [x] T027 arming gate (confidence, vote, dwell, cooldown, zone) â€” built ahead of numeric order (see T017 note); re-arm only happens on release+reacquire, never on cooldown alone, or a continuously held pose would refire repeatedly
- [x] T028 router
- [x] T029 end-to-end synth test â€” hit a real PySide6 gotcha: a Router with nothing holding a Python reference gets garbage-collected even though its bound-method slot is "connected," silently killing event delivery with no error; fixed by having Router anchor itself on `ctx.router`

## Phase 3 â€” UI
- [x] T030 overlay base (translucent, click-through, no focus steal)
- [x] T031 toasts
- [x] T032 radial menu
- [~] T033 full tray menu â€” arm/disarm and profile display work; profile submenu doesn't yet call elara.profile_set (needs bootstrap.py wired into tray, next step)
- [ ] T034 global hotkeys
- [ ] T035 settings window (all tabs)
- [ ] T036 onboarding + calibration wizard
- [ ] T037 stats
- [ ] T038 theme + generated icons

## Phase 4 â€” Continuous control
- [ ] T040 cursor control (active rect, acceleration, click/drag/scroll)
- [ ] T041 pinch scrub (volume/brightness/zoom)
- [ ] T042 two-hand gestures (spread, frame capture, panic)

## Phase 5 â€” Profiles
- [ ] T050 foreground app detection
- [ ] T051 profile manager + auto-switch
- [ ] T052 built-in profiles
- [ ] T053 binding schema + persistence
- [ ] T054 profile editor UI

## Phase 6 â€” Voice
- [ ] T060 mic capture
- [ ] T061 wake word (openWakeWord)
- [ ] T062 Vosk STT with constrained grammar
- [ ] T063 intent parsing + slots
- [ ] T064 TTS confirmations
- [ ] T065 command wiring (full catalogue)
- [ ] T066 dictation mode
- [ ] T067 voice settings tab
- [ ] T068 model downloader (checksums, resume, never C:)

## Phase 7 â€” Presence
- [ ] T070 face detector at 2 FPS
- [ ] T071 away/back state machine with hysteresis
- [ ] T072 presence actions (pause media, mute mic, optional lock)
- [ ] T073 presence settings + privacy copy

## Phase 8 â€” Extras
- [ ] T080 air draw / annotation
- [ ] T081 laser pointer
- [ ] T083 macro recorder
- [ ] T084 custom gesture trainer (sklearn)
- [ ] T085 plugin loader
- [ ] T086 update check (opt-in)
- [ ] T088 adaptive throttling (battery, fullscreen, typing)

## Phase 9 â€” Performance
- [ ] T090 adaptive FPS verified
- [ ] T091 idle scan mode verified
- [ ] T092 budget verification via bench.py â€” record numbers here
- [ ] T093 memory audit
- [ ] T094 perf regression test

## Phase 10 â€” Tests and CI
- [ ] T100 unit coverage â‰¥70% on vision/core/actions/intents
- [ ] T101 e2e synth suite green
- [ ] T102 ruff clean
- [ ] T103 CI workflow (windows + ubuntu, headless)
- [ ] T104 CI badge green on main

## Phase 11 â€” Packaging
- [ ] T110 PyInstaller spec + build script (TEMP on D)
- [ ] T111 Inno Setup installer (per-user, no admin)
- [ ] T112 portable zip
- [ ] T113 SHA256SUMS

## Phase 12 â€” Release
- [ ] T120 GitHub repo created and pushed
- [ ] T121 README
- [ ] T122 release workflow on tag
- [ ] T123 landing page (GitHub Pages)
- [ ] T124 demo GIFs â€” HUMAN, needs a webcam
- [ ] T125 final QA pass â€” HUMAN

---

## Measured numbers (fill in as they are obtained)

| Metric | Target | Measured | Date |
|---|---|---|---|
| Idle CPU (armed, no hand) | < 3% | â€” | â€” |
| Active CPU (30 FPS tracking) | < 12% | â€” | â€” |
| RAM active | < 400 MB | â€” | â€” |
| Gesture â†’ action latency | < 120 ms | â€” | â€” |
| Cold start to tray | < 3 s | â€” | â€” |
| Installer size | < 150 MB | â€” | â€” |

## Notes and surprises

_Append findings here as work proceeds â€” anything a future session would waste time rediscovering._

## Post-v1 backlog

_File anything discovered but out of scope here rather than expanding a task._
