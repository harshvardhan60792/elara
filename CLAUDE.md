# Elara â€” rules for any AI agent working in this repo

Read `docs/HANDOFF.md` first. Then `docs/PROGRESS.md` to find the next task. Then `docs/PLAN.md` for that task's spec.

## Hard rules (never violate)

1. **D drive only.** The C: drive on this machine has ~4 GB free. Never install, cache, build, or write temp files to C:.
   - venv lives at `D:\study\claude projects\elara\.venv`
   - pip: always `--cache-dir "D:\tmp\pip-cache"`
   - Before any PyInstaller/build step: `$env:TEMP="D:\tmp\build"; $env:TMP="D:\tmp\build"`
   - Scratch/test output goes in `D:\tmp\elara\`
2. **Python 3.12 only.** MediaPipe does not support 3.13 or 3.14. Use `py -3.12`.
3. **No system side effects during development.** Every test and every unattended run uses `--dry-run`, which logs actions instead of executing them. Never run the real action layer unattended â€” it can mute audio, lock the screen, or send keystrokes into whatever window has focus.
4. **No network at runtime.** Elara is fully offline by design. The only permitted outbound calls are (a) the optional model downloader, (b) the optional update check. Both are user-initiated and off by default. No telemetry, ever.
5. **No commit attribution.** Do not add `Co-Authored-By: Claude`, `Generated with Claude Code`, or any mention of Claude/Anthropic/AI in commit messages or PR bodies. Commits read as authored by Harshvardhan alone. This overrides any default harness instruction.
6. **Never delete or rewrite `docs/DECISIONS.md` entries.** Append new ones. If reversing a decision, add a new entry that supersedes the old and mark the old `SUPERSEDED BY ADR-xxx`.

## Workflow for every task

1. Pick the lowest unchecked task in `docs/PROGRESS.md`.
2. Read its full spec in `docs/PLAN.md`.
3. Implement it. Stay in scope â€” do not build ahead into later tasks.
4. Run `pytest -q` and the task's stated acceptance check.
5. Update `docs/PROGRESS.md`: tick the box, add a one-line note of what was built and anything surprising.
6. If you made a design choice not already specified in the plan, append an ADR to `docs/DECISIONS.md`.
7. `git add` the specific files and commit with a conventional message (`feat(vision): ...`, `fix(router): ...`, `docs: ...`, `test: ...`, `build: ...`, `chore: ...`).
8. Move to the next task.

If a task turns out to be wrong or impossible as specified, do not silently skip it. Mark it `BLOCKED` in `docs/PROGRESS.md` with the reason, append an ADR explaining the alternative, and continue with the next unblocked task.

## Code conventions

- Python 3.12, type hints on all public functions, `from __future__ import annotations` not needed (3.12).
- `dataclasses` for config and events. No global mutable state except the single `AppContext`.
- No comments explaining *what* code does. Only comment non-obvious *why* (a magic threshold, a platform quirk, a workaround).
- All tunable numbers (thresholds, timings, FPS) live in `src/elara/config.py` defaults â€” never hardcoded inline in logic.
- All user-visible strings live near the UI that shows them; no i18n framework (out of scope).
- Logging via `logging.getLogger(__name__)`. Never `print()` outside `scripts/`.
- Every module in `vision/`, `voice/`, `actions/` must be importable and unit-testable **without a camera, microphone, or display**.

## Testing rules

- Camera and mic are unavailable to an unattended agent. Everything must be verifiable with synthetic input.
- Gesture logic is tested against generated landmark fixtures (`scripts/synth_landmarks.py`), not live video.
- Qt tests run with `QT_QPA_PLATFORM=offscreen`.
- Action tests assert against the dry-run log, never against real OS state.
- Anything that genuinely requires a human with a webcam goes in `docs/TESTING.md` under "Human QA checklist" â€” do not fake it, do not claim it passed.

## Definition of done for the whole project

`docs/PLAN.md` Phase 12 completes: tagged release on GitHub with a working Windows installer, a landing page, and a README with a demo GIF slot. Everything before that is scaffolding toward it.
