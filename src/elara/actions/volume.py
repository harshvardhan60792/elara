"""volume.* — mostly thin wrappers over the platform adapter. `volume.scrub`
is the continuous pinch-scrub channel (docs/GESTURES.md); it's registered
here too so voice/radial-menu can address a coarse step version of it, even
though the live continuous path (T041) drives volume_set directly from
ContinuousUpdate rather than going through the action registry."""

from __future__ import annotations

from elara.actions.registry import ActionRegistry, ActionSpec


def _up(ctx) -> None:
    ctx.platform.volume_up()


def _down(ctx) -> None:
    ctx.platform.volume_down()


def _mute_toggle(ctx) -> None:
    ctx.platform.volume_mute_toggle()


def _set(ctx, percent: int = 50) -> None:
    ctx.platform.volume_set(percent)


def _scrub(ctx, value: float = 0.5) -> None:
    ctx.platform.volume_set(int(max(0.0, min(1.0, value)) * 100))


def _switch_output(ctx) -> None:
    # No cross-platform default output switch exists without an extra
    # dependency (Windows has no public API short of the AudioDeviceCmdlets
    # PowerShell module or undocumented COM). Left unimplemented — see
    # docs/DECISIONS.md.
    raise NotImplementedError("switching the default output device is not implemented")


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("volume.up", "Volume up", "volume", _up))
    registry.register(ActionSpec("volume.down", "Volume down", "volume", _down))
    registry.register(ActionSpec("volume.mute_toggle", "Mute / unmute", "volume", _mute_toggle))
    registry.register(ActionSpec("volume.set", "Set volume", "volume", _set, slots=("percent",)))
    registry.register(ActionSpec("volume.scrub", "Volume (scrub)", "volume", _scrub, slots=("value",)))
    registry.register(ActionSpec("volume.switch_output", "Switch output device", "volume", _switch_output))
