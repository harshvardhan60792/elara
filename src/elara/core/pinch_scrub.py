"""Pinch-scrub: hold a pinch and the distance between thumb and index tips
drives a continuous value (docs/GESTURES.md: "pinch_distance while pinch
held -> volume/brightness/zoom/timeline depending on mode"). Routes through
the normal action executor (volume.scrub / system.brightness_scrub) rather
than calling the platform adapter directly, so it stays dry-run safe and
shows up in stats/notify like any other action.

Engagement uses hysteresis on the engine's precomputed closeness value
(1.0 = fully pinched, 0.0 = open past pinch_off) rather than firing on
every frame regardless of hand state — a value can drift near the
threshold from noise, and hysteresis is what keeps that from chattering
in and out of "engaged" every frame.
"""

from __future__ import annotations

ENGAGE_VALUE = 0.7
RELEASE_VALUE = 0.2


class PinchScrubController:
    def __init__(self, ctx, action_id: str = "volume.scrub") -> None:
        self.ctx = ctx
        self.action_id = action_id
        self._engaged = False

    def set_mode(self, action_id: str) -> None:
        self.action_id = action_id

    def handle_continuous(self, update) -> None:
        if update.channel != "pinch_scrub":
            return
        if not self.ctx.armed:
            self._engaged = False
            return

        if not self._engaged and update.value >= ENGAGE_VALUE:
            self._engaged = True
        elif self._engaged and update.value <= RELEASE_VALUE:
            self._engaged = False

        if self._engaged and self.ctx.executor is not None:
            self.ctx.executor.execute(self.action_id, {"value": update.value})
