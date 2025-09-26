from __future__ import annotations

import time

from semhost.events import EventBus
import semhost.events as events_mod
from semhost.settings import SemhostSettings


class _FailWS:
    def __init__(self, times: int) -> None:
        self.times = times
        self.calls = 0

    async def send_json(self, _payload):  # type: ignore[no-untyped-def]
        self.calls += 1
        raise RuntimeError("fail")


def test_allow_connect_rate_limited(monkeypatch) -> None:
    # Force strict limits
    st = SemhostSettings(ws_connects_per_minute_limit=2)
    monkeypatch.setattr(events_mod, "get_settings", lambda: st)
    bus = EventBus()
    ok, _ = bus.allow_connect("s1")
    assert ok is True
    ok2, _ = bus.allow_connect("s1")
    assert ok2 is True
    ok3, reason = bus.allow_connect("s1")
    assert ok3 is False and "rate" in (reason or "")


def test_emit_trips_circuit_breaker_and_cooldown(monkeypatch) -> None:
    st = SemhostSettings(ws_fail_threshold=2, ws_cooldown_s=1)
    monkeypatch.setattr(events_mod, "get_settings", lambda: st)
    bus = EventBus()
    # Inject failing websocket
    bus._subs["s2"] = events_mod._Subs(sockets={_FailWS(3)})  # type: ignore[arg-type]
    # First emit: failure count 1, not tripped
    import asyncio

    asyncio.get_event_loop().run_until_complete(bus.emit("s2", "round_start", {"index": 1}))
    assert bus._fail_counts.get("s2", 0) == 1
    # Second emit: reaches threshold and trips
    asyncio.get_event_loop().run_until_complete(bus.emit("s2", "round_start", {"index": 1}))
    assert bus._tripped_until.get("s2", 0.0) > time.time()
    # During cooldown, emits are dropped (no change to fail count)
    fc_before = bus._fail_counts.get("s2", 0)
    asyncio.get_event_loop().run_until_complete(bus.emit("s2", "round_start", {"index": 1}))
    assert bus._fail_counts.get("s2", 0) == fc_before
    # After cooldown, allow failures to be counted again
    time.sleep(1.1)
    asyncio.get_event_loop().run_until_complete(bus.emit("s2", "round_start", {"index": 1}))
