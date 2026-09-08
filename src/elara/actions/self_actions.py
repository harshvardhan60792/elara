"""elara.* — actions that control Elara itself rather than the OS. Named
self_actions.py (not elara.py) to avoid a submodule shadowing the top-level
package name; the action_id namespace is still elara.* per ADR-020."""

from __future__ import annotations

from elara.actions.registry import ActionRegistry, ActionSpec
from elara.events import ProfileChanged


def _arm_toggle(ctx) -> None:
    if ctx.set_armed_callback is None:
        ctx.notify("Arm toggle unavailable (no app shell attached)")
        return
    ctx.set_armed_callback(not ctx.armed)


def _panic_disarm(ctx) -> None:
    if ctx.set_armed_callback is None:
        ctx.notify("Panic disarm unavailable (no app shell attached)")
        return
    ctx.set_armed_callback(False)


_PROFILE_ORDER = ("desktop", "media", "presentation", "meeting", "browser", "reading")


def _profile_next(ctx) -> None:
    current = ctx.config.general.active_profile
    try:
        idx = _PROFILE_ORDER.index(current)
    except ValueError:
        idx = -1
    next_profile = _PROFILE_ORDER[(idx + 1) % len(_PROFILE_ORDER)]
    ctx.config.general.active_profile = next_profile
    ctx.event_bus.profile_changed.emit(ProfileChanged(name=next_profile))
    ctx.notify(f"Profile: {next_profile}")


def _profile_set(ctx, name: str = "desktop") -> None:
    ctx.config.general.active_profile = name
    ctx.event_bus.profile_changed.emit(ProfileChanged(name=name))
    ctx.notify(f"Profile: {name}")


def _open_settings(ctx) -> None:
    ctx.notify("Settings window is a Phase 3 UI feature")


def _show_help(ctx) -> None:
    ctx.notify("Hold an open palm to open the radial menu. See docs/GESTURES.md.")


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("elara.arm_toggle", "Arm / disarm", "elara", _arm_toggle))
    registry.register(
        ActionSpec("elara.panic_disarm", "Panic disarm", "elara", _panic_disarm, needs_confirm=False)
    )
    registry.register(ActionSpec("elara.profile_next", "Next profile", "elara", _profile_next))
    registry.register(ActionSpec("elara.profile_set", "Set profile", "elara", _profile_set, slots=("name",)))
    registry.register(ActionSpec("elara.open_settings", "Open settings", "elara", _open_settings))
    registry.register(ActionSpec("elara.show_help", "Show help", "elara", _show_help))
