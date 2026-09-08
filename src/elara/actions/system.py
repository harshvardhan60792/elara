"""system.* — power, brightness, DND, and status readout actions."""

from __future__ import annotations

from elara.actions.registry import ActionRegistry, ActionSpec


def _lock(ctx) -> None:
    ctx.platform.lock()


def _sleep_display(ctx) -> None:
    ctx.platform.sleep_display()


def _brightness_up(ctx) -> None:
    ctx.platform.brightness_up()


def _brightness_down(ctx) -> None:
    ctx.platform.brightness_down()


def _brightness_scrub(ctx, value: float = 0.5) -> None:
    ctx.platform.brightness_set(int(max(0.0, min(1.0, value)) * 100))


def _dnd_toggle(ctx) -> None:
    ctx.platform.dnd_set(not ctx.platform.dnd_get())


def _battery_status(ctx) -> None:
    import psutil

    battery = psutil.sensors_battery()
    if battery is None:
        ctx.notify("No battery detected")
        return
    state = "charging" if battery.power_plugged else "on battery"
    ctx.notify(f"Battery {battery.percent:.0f}% ({state})")


def _status_readout(ctx) -> None:
    ctx.notify(f"Elara armed={ctx.armed}, profile={ctx.config.general.active_profile}")


def register(registry: ActionRegistry) -> None:
    registry.register(ActionSpec("system.lock", "Lock workstation", "system", _lock))
    registry.register(ActionSpec("system.sleep_display", "Sleep display", "system", _sleep_display))
    registry.register(ActionSpec("system.brightness_up", "Brightness up", "system", _brightness_up))
    registry.register(ActionSpec("system.brightness_down", "Brightness down", "system", _brightness_down))
    registry.register(
        ActionSpec("system.brightness_scrub", "Brightness (scrub)", "system", _brightness_scrub, slots=("value",))
    )
    registry.register(ActionSpec("system.dnd_toggle", "Do Not Disturb toggle", "system", _dnd_toggle))
    registry.register(ActionSpec("system.battery_status", "Battery status", "system", _battery_status))
    registry.register(ActionSpec("system.status_readout", "Elara status", "system", _status_readout))
