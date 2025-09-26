from __future__ import annotations

from semhost.schemas.events import (
    RoundStartEvent,
    TurnResultEvent,
    RoundEndEvent,
    ArtifactsSavedEvent,
)


def test_round_start_event_dump() -> None:
    e = RoundStartEvent(session_id="s1", index=1, prompt="Hello")
    d = e.model_dump()
    assert d == {
        "type": "round_start",
        "session_id": "s1",
        "index": 1,
        "prompt": "Hello",
    }


def test_turn_result_event_dump() -> None:
    e = TurnResultEvent(
        session_id="s1", index=2, alias="p1", ok=True, latency_ms=123, text="T"
    )
    d = e.model_dump()
    assert d["type"] == "turn_result" and d["session_id"] == "s1" and d["index"] == 2
    assert (
        d["alias"] == "p1"
        and d["ok"] is True
        and d["latency_ms"] == 123
        and d["text"] == "T"
    )


def test_round_end_and_artifacts_saved_dump() -> None:
    e1 = RoundEndEvent(session_id="s2", index=3)
    e2 = ArtifactsSavedEvent(session_id="s2", index=3)
    assert e1.model_dump() == {"type": "round_end", "session_id": "s2", "index": 3}
    assert e2.model_dump() == {
        "type": "artifacts_saved",
        "session_id": "s2",
        "index": 3,
    }
