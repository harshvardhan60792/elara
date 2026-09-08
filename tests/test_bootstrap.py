from __future__ import annotations

from elara.bootstrap import DEFAULT_BINDINGS, build_full_context


def test_build_full_context_wires_registry_platform_executor_router():
    ctx, router = build_full_context(dry_run=True)

    assert ctx.registry is not None
    assert ctx.executor is not None
    assert router.registry is ctx.registry
    assert router.bindings == DEFAULT_BINDINGS

    for action_id in DEFAULT_BINDINGS.values():
        assert action_id in ctx.registry, f"default binding references unknown action {action_id}"


def test_default_bindings_fire_through_router_in_dry_run():
    from elara.events import GestureEvent

    ctx, router = build_full_context(dry_run=True)
    ctx.armed = True

    event = GestureEvent(id="fist", hand="right", confidence=0.9, position=(0.5, 0.5), timestamp=0.0)
    router.handle_gesture(event)

    assert len(ctx.executor.dry_run_log) == 1
    assert ctx.executor.dry_run_log[0].action_id == "volume.mute_toggle"
