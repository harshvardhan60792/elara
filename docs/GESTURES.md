# GESTURES & ACTIONS

Landmark indices follow MediaPipe's hand model: 0 wrist; 1–4 thumb; 5–8 index; 9–12 middle; 13–16 ring; 17–20 pinky. Tip indices are 4, 8, 12, 16, 20.

## Feature vector (computed once per frame per hand, in `vision/features.py`)

Normalisation, in order — this exact order matters for the custom classifier's stability:
1. Translate so the wrist (0) is at the origin.
2. Scale so the distance wrist→middle-MCP (0→9) equals 1. Makes features distance-invariant.
3. Rotate so the wrist→middle-MCP vector points "up". Makes features rotation-invariant in-plane.

Derived features:
- `finger_extended[5]` — bool per finger. A finger is extended when its tip is farther from the wrist than its PIP joint, in the normalised frame. The thumb uses an angle test instead (tip–IP–MCP angle > threshold) because it folds sideways, not down.
- `finger_curl[5]` — continuous 0..1, for gradient-sensitive gestures.
- `pinch_distance` — ‖tip4 − tip8‖ in normalised units. Below `pinch_on` = pinching; hysteresis band up to `pinch_off` prevents flicker.
- `palm_center` — mean of landmarks 0, 5, 9, 13, 17.
- `palm_normal` — normal of the plane through 0, 5, 17; gives facing (toward/away from camera).
- `hand_span` — bounding-box diagonal; proxy for distance from camera.
- `handedness`, `visibility_score`.
- `velocity` — palm-centre delta over the trajectory buffer, in normalised units/second.

## Static poses (rule-based, `vision/static_gestures.py`)

| id | Pose | Rule sketch |
|---|---|---|
| `open_palm` | ✋ all fingers out | all 5 extended, span above threshold |
| `fist` | ✊ closed | none extended |
| `point` | ☝️ index only | index extended, middle/ring/pinky curled |
| `peace` | ✌️ index+middle | index & middle extended, ring & pinky curled |
| `three` | index+middle+ring | those three extended, pinky curled |
| `thumbs_up` | 👍 | thumb extended and pointing up in image space, others curled |
| `thumbs_down` | 👎 | as above, pointing down |
| `pinch` | 🤏 thumb+index touching | `pinch_distance < pinch_on`, other fingers may be free |
| `ok_sign` | 👌 | pinch **and** middle/ring/pinky extended |
| `l_shape` | 🤙 thumb+index at ~90° | both extended, angle between them in range, others curled |
| `rock` | 🤟 thumb+index+pinky | those extended, middle & ring curled |
| `palm_away` | ✋ facing away | open palm with palm normal pointing away from camera |

Ambiguity is resolved by an explicit priority order (most specific first: `ok_sign` before `pinch`, `l_shape` before `point`). The classifier returns the highest-priority rule that matches, with a confidence derived from how far the measurements sit inside their thresholds — not a flat 1.0, so the arming gate has something to work with.

## Dynamic gestures (`vision/dynamic_gestures.py`)

Computed over the trajectory buffer (default 1.0 s of palm centres at frame rate).

| id | Motion | Detection |
|---|---|---|
| `swipe_left` / `swipe_right` | flat hand sweeps horizontally | net horizontal displacement > threshold, dominant axis ratio > 2:1, peak velocity above floor, completed within a time window |
| `swipe_up` / `swipe_down` | vertical sweep | same, vertical axis |
| `circle_cw` / `circle_ccw` | finger draws a circle | accumulated signed angle around the trajectory centroid exceeds 2π·0.8 with bounded radius variance |
| `push` | palm thrusts toward camera | `hand_span` grows sharply over a short window while palm centre stays put |

Swipes require the hand to *return* below the velocity floor before another swipe can register, which stops one sweep counting as several.

## Two-hand gestures

| id | Gesture | Use |
|---|---|---|
| `two_hand_spread` | both hands pinching, moving apart/together | continuous zoom |
| `frame_capture` | both hands forming L-shapes, opposite corners | screenshot of the framed rectangle |
| `two_palm_push` | both palms forward | panic stop: disarm everything |

`frame_capture` is the marquee demo gesture — you literally frame a region of the screen with your hands and it captures exactly that rectangle.

## Continuous controls

| id | Input | Output |
|---|---|---|
| `cursor` | index fingertip, One Euro filtered, mapped through an active rectangle to screen coords (multi-monitor aware) | mouse position |
| `pinch_scrub` | `pinch_distance` while pinch held | maps to volume / brightness / zoom / timeline depending on mode |
| `scroll` | two fingers (peace pose) moving vertically | scroll wheel events, velocity-scaled |
| `drag` | pinch held while cursor mode active | mouse down → move → up |

## Command mode and the radial menu

Default interaction, and the answer to both discoverability and misfires:

1. Hold `open_palm` for `attention_dwell_ms` (default 700).
2. A translucent radial menu fades in centred on the palm, showing the active profile's 6–8 primary actions with icons and labels.
3. Move the hand — the segment under the direction of travel highlights.
4. `pinch` or `fist` confirms; the action fires and the menu closes.
5. Menu auto-dismisses after `radial_timeout_ms` (default 3000) of no selection, or on `two_palm_push`.

Direct gestures (swipes, pinch-scrub) still work outside command mode, but only those bound in the active profile — which is a deliberately small set per profile.

## Action catalogue

Every action has a stable `action_id`. Bindable from gestures, voice, radial menu, and plugins.

**Media** — `media.play_pause`, `media.next`, `media.prev`, `media.stop`, `media.seek_forward`, `media.seek_back`
**Volume** — `volume.up`, `volume.down`, `volume.mute_toggle`, `volume.set` (slot: percent), `volume.scrub` (continuous), `volume.switch_output`
**Presentation** — `slides.next`, `slides.prev`, `slides.start`, `slides.end`, `slides.black_screen`, `slides.laser_toggle`, `slides.annotate_toggle`
**Cursor / input** — `cursor.toggle`, `cursor.left_click`, `cursor.right_click`, `cursor.double_click`, `cursor.drag_toggle`, `cursor.scroll_up`, `cursor.scroll_down`
**Window** — `window.switch_next`, `window.switch_prev`, `window.minimize`, `window.maximize`, `window.close`, `window.snap_left`, `window.snap_right`, `window.show_desktop`, `desktop.next`, `desktop.prev`
**Capture** — `capture.screenshot_full`, `capture.screenshot_region`, `capture.screenshot_frame` (two-hand), `capture.record_toggle`, `capture.copy_to_clipboard`
**Meeting** — `meeting.mute_toggle`, `meeting.camera_toggle`, `meeting.raise_hand`, `meeting.leave`, `meeting.share_screen` (per-app hotkey maps for Zoom, Teams, Meet)
**System** — `system.lock`, `system.sleep_display`, `system.brightness_up`, `system.brightness_down`, `system.brightness_scrub`, `system.dnd_toggle`, `system.battery_status`, `system.status_readout`
**Apps** — `apps.launch` (slot: name), `apps.switch_to` (slot: name), `apps.close_active`, `apps.radial_launcher`
**Browser** — `browser.new_tab`, `browser.close_tab`, `browser.next_tab`, `browser.prev_tab`, `browser.back`, `browser.forward`, `browser.reload`, `browser.search` (slot: query)
**Text** — `text.copy`, `text.paste`, `text.cut`, `text.undo`, `text.type` (slot), `text.dictation_toggle`, `text.read_selection_aloud`
**Beckon itself** — `beckon.arm_toggle`, `beckon.profile_next`, `beckon.profile_set` (slot), `beckon.open_settings`, `beckon.panic_disarm`, `beckon.show_help`

## Default bindings per profile

**Desktop** — palm-hold → radial menu · swipe L/R → switch window · point → cursor mode · pinch-scrub → volume · `frame_capture` → region screenshot · `two_palm_push` → panic disarm

**Media** — `open_palm` → play/pause · swipe R → next track · swipe L → previous · pinch-scrub → volume · `thumbs_up`/`thumbs_down` → volume step · `fist` → mute

**Presentation** — swipe R → next slide · swipe L → previous slide · `point` → laser pointer · `pinch` held → annotate/draw · `fist` → black screen · `peace` → start/end slideshow

**Meeting** — `fist` → mute toggle · `open_palm` → raise hand · `peace` → camera toggle · `thumbs_down` → leave (with confirmation)

**Browser** — swipe L/R → tab switch · `peace` + vertical → scroll · `point` → cursor · `circle_cw` → reload

**Reading** — swipe up/down → page down/up · `pinch_scrub` → zoom · `point` → cursor

## Voice commands

Wake phrase: **"hey jarvis"** (openWakeWord pretrained; configurable, custom models supported).

Recognised intents, each mapped to an `action_id` with slot extraction:

- *"play" / "pause" / "next track" / "previous track" / "stop"*
- *"volume up" / "volume down" / "mute" / "set volume to sixty"*
- *"brightness up" / "brightness down"*
- *"open <app>" / "switch to <app>" / "close this"*
- *"search for <query>" / "google <query>"*
- *"new tab" / "close tab" / "go back"*
- *"screenshot" / "capture region" / "start recording" / "stop recording"*
- *"lock" / "lock my screen" / "sleep the display"*
- *"mute mic" / "camera off" / "raise hand" / "leave meeting"*
- *"do not disturb on" / "do not disturb off"*
- *"set a timer for <n> minutes" / "remind me to <text> in <n> minutes"*
- *"what time is it" / "what's my battery" / "system status"*
- *"start dictation" / "stop dictation"*
- *"read this" (TTS of the current selection)*
- *"copy" / "paste"*
- *"presentation mode" / "media mode" / "desktop mode"* (profile switch)
- *"stop listening" / "go to sleep"* (disarm voice)

Unrecognised utterances produce a toast showing what was heard and the closest match, never a silent failure.

## Presence behaviours (face detection, 2 FPS)

| Trigger | Default action | Setting |
|---|---|---|
| No face for `away_delay_s` (default 45) | pause media, mute mic | on |
| No face for `lock_delay_s` (default 180) | lock workstation | off by default |
| Face returns within `resume_window_s` | resume media | on |
| Face detected while media paused by presence | resume | on |

Presence uses detection only — no recognition, no embeddings, no face data written to disk, ever. The settings page says exactly that.
