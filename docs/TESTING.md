# TESTING

## Principle

An unattended agent has no camera, no microphone, and no eyes. Everything it claims must be verifiable from synthetic input and log assertions. Anything that genuinely needs a human is listed at the bottom and is **never** reported as passing until a human ticks it.

## Running the suite

```powershell
& "D:\study\claude projects\elara\.venv\Scripts\python.exe" -m pytest -q
```

`QT_QPA_PLATFORM=offscreen` is set in `tests/conftest.py` before Qt is imported. No display required.

## Safety rule

Every automated test runs with `dry_run=True`. The action executor logs instead of executing. **No test may set `--live`.** A test that changes system volume, sends a keystroke, or locks the screen is a bug in the test, regardless of what it is trying to prove.

## Test layers

**1. Pure logic (fast, the bulk of coverage)**
`features.py`, `static_gestures.py`, `dynamic_gestures.py`, `smoothing.py`, `arming.py`, `intents.py`, `profiles/manager.py`, `throttle.py`. All take plain data, return plain data, no threads, no Qt, no I/O.

**2. Synthetic pipeline**
`SynthSource` replays generated landmark sequences through the real engine, arming gate, router, and executor. Asserts the dry-run action log. This is the regression net â€” `tests/test_e2e_synth.py` must stay green.

**3. Qt smoke tests**
Offscreen construction of every widget, one interaction each, assert no exception and no leaked timers. Coverage here is low by design.

**4. Adapter contract tests**
Introspect the platform adapter: every method in `base.py` exists with a matching signature. Never invoke them.

**5. Performance regression**
`test_perf_regression.py` asserts per-frame processing time on synth input stays under a generous ceiling. Catches a 10Ã— regression, tolerates CI noise.

## Fixtures

Regenerate with:
```powershell
& "D:\study\claude projects\elara\.venv\Scripts\python.exe" scripts\synth_landmarks.py --all --out tests\fixtures\landmarks
```
Deterministic (fixed seed) â€” `git diff` must be empty after regeneration. If it is not, the generator changed and the classifier tests need re-review.

Fixtures required: the 12 static poses, 4 motion sequences (`swipe_left`, `swipe_right`, `circle_cw`, `push`), 2 two-hand sequences, plus three **negative** fixtures â€” a slow drift, a hand entering and leaving frame, and a partially occluded hand. The negatives matter more than the positives; false fires are what would make this product unusable.

## What good coverage looks like here

Not a percentage. Ask instead:
- Does a flickering pose fire an action? (must not)
- Does one physical swipe fire two events? (must not)
- Does a 90 ms pinch click and a 900 ms pinch drag? (must)
- Does a disarmed app fire anything? (must not)
- Does a garbage voice utterance execute the closest match? (must not â€” it must ask)

---

## HUMAN QA checklist

Requires a person, a webcam, and about 30 minutes. Nothing below can be verified by an agent. Tick these only after actually doing them.

### Setup
- [ ] Fresh install on a clean Windows user profile completes without an admin prompt
- [ ] First launch opens onboarding; camera preview shows a live image
- [ ] Calibration step measures hand span and the resulting thresholds feel right
- [ ] Tray icon appears, and the app is **disarmed** with the camera LED **off**

### Core gestures
- [ ] Arming turns the camera LED on; disarming turns it off
- [ ] Open palm held ~700 ms opens the radial menu under the hand
- [ ] Pointing at a segment highlights it; pinch confirms; menu closes
- [ ] Radial menu auto-dismisses after 3 s of no selection
- [ ] Swipe left/right fires once per physical swipe, never twice
- [ ] Pinch-scrub changes volume smoothly with no stutter
- [ ] Cursor mode: pointer is steady when the hand is still, responsive when moving fast
- [ ] Pinch tap clicks; pinch hold drags; neither misfires as the other
- [ ] Two-hand frame captures exactly the framed screen region
- [ ] Two-palm push disarms immediately

### False positives (the important ones)
- [ ] Typing at the keyboard for 2 minutes fires nothing
- [ ] Talking with hands during a video call for 2 minutes fires nothing unintended
- [ ] Someone walking behind you does not trigger gestures
- [ ] Poor lighting degrades gracefully (no wild misfires)

### Profiles
- [ ] Opening PowerPoint switches to Presentation automatically
- [ ] Swipes advance slides without the overlay stealing focus from the slideshow
- [ ] Laser pointer and annotation draw over a fullscreen presentation
- [ ] Opening Spotify switches to Media
- [ ] Joining a Zoom/Meet call switches to Meeting; mute gesture actually mutes

### Voice
- [ ] "hey jarvis" wakes within ~300 ms, with a visible HUD indicator
- [ ] Ten different commands are recognised and executed correctly
- [ ] A deliberately garbled phrase produces a "did you mean" toast, not a wrong action
- [ ] Dictation types into Notepad accurately, including punctuation commands
- [ ] Disabling voice releases the microphone (indicator goes off)

### Presence
- [ ] Walking away pauses media after the configured delay
- [ ] Returning resumes it
- [ ] Turning your head or leaning out of frame briefly does **not** trigger away

### Performance and stability
- [ ] Idle armed for 30 minutes: CPU stays low, laptop stays cool, fan does not spin up
- [ ] Battery drain over an hour armed is acceptable
- [ ] Runs for 4 hours with no memory growth (check Task Manager RSS)
- [ ] No crash on: unplugging the webcam, switching users, sleep/resume, monitor hot-plug

### Packaging
- [ ] Installer runs on a machine that has never had Python
- [ ] SmartScreen warning appears; "More info â†’ Run anyway" works; README documents it
- [ ] Uninstall removes the app and offers to remove settings
- [ ] Portable zip runs from a USB stick without installation
