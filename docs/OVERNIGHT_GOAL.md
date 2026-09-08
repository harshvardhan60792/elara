# Overnight goal prompt

Paste this as the goal. It is self-contained â€” the agent needs nothing from the conversation that produced the plan.

---

> Build the Elara desktop app in `D:\study\claude projects\elara`.
>
> Read `CLAUDE.md`, then `docs/HANDOFF.md`, then `docs/PLAN.md`. Work tasks in the order given in `docs/PROGRESS.md`, starting from the lowest unchecked box. For each task: implement it, run `pytest -q` plus the task's stated acceptance check, tick the box in `docs/PROGRESS.md` with a one-line note, and commit. Then move to the next task without asking.
>
> Hard constraints: everything on the D: drive, never C: (it has 4 GB free). Python 3.12 only. Never run the action layer outside dry-run â€” it can mute the machine, lock the screen, or type into whatever window has focus. No Claude/Anthropic attribution in commit messages.
>
> You have no camera and no microphone. Do not attempt to verify gesture or speech accuracy by running the app. Use the synthetic landmark fixtures. Anything that genuinely needs a human goes on the checklist in `docs/TESTING.md` â€” leave it unticked and say so.
>
> If a task is impossible as specified, mark it `[!]` in `docs/PROGRESS.md` with the reason, append an ADR to `docs/DECISIONS.md` explaining what you did instead, and carry on with the next task. Do not stop and wait.
>
> Priority if you run out of time: Phases 0â€“3 give a working, demoable app; Phase 11â€“12 make it installable and public. Phases 6â€“8 are enrichment. Never leave the repo in a state where `pytest -q` fails or the app will not start.
>
> When you stop, write a summary at the bottom of `docs/PROGRESS.md`: what got built, what is left, what surprised you, and the exact next step.

---

## Critical path

If the night runs short, this is the order that produces something worth showing:

1. **Phases 0â€“2** â€” app runs, tray icon, gestures classify, actions fire in dry-run. Without this there is nothing.
2. **Phase 3 (T030â€“T033)** â€” overlay, toasts, radial menu. This is what makes it *look* like a product and is the thing that gets screenshotted.
3. **Phase 4 (T040â€“T041)** â€” cursor and pinch-scrub. The two most visceral demos.
4. **Phase 11â€“12** â€” packaging and the public repo. An unreleased project is not a portfolio project.
5. Everything else â€” voice, presence, trainer, plugins â€” is enrichment. Genuinely good enrichment, but a polished half is worth more than a broken whole.

## What "done" looks like in the morning

- `pytest -q` green
- `python -m elara` starts, tray icon appears, app is disarmed
- `python -m elara --source synth:tests/fixtures/landmarks/swipe_left.json --dry-run` logs the expected action
- `docs/PROGRESS.md` honestly reflects state, including what was not done
- Every commit is small, conventional, and passes tests
