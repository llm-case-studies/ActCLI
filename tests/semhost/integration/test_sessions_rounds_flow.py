from __future__ import annotations

from typing import List

from fastapi.testclient import TestClient

from semhost.main import create_app


def _client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_sessions_create_start_next_with_echo_and_ws_events(tmp_path) -> None:
    client = _client()

    # Create a session with two local echo participants
    req = {
        "participants": [
            {"alias": "e1", "provider": "echo", "model_id": "echo"},
            {"alias": "e2", "provider": "echo", "model_id": "echo"},
        ],
        "window_k": 1,
        "max_rounds": 3,
    }
    r = client.post("/sessions", json=req)
    assert r.status_code == 200
    session_id = r.json()["session_id"]

    # Connect to WS stream
    with client.websocket_connect(f"/sessions/{session_id}/stream") as ws:
        # Start the first round
        r1 = client.post(
            f"/sessions/{session_id}/round/start", json={"prompt": "Hello world"}
        )
        assert r1.status_code == 200
        first = r1.json()
        assert first["index"] == 1
        assert len(first["entries"]) == 2

        # Expect events in order: round_start, 2×turn_result (any order), round_end, artifacts_saved
        evt = ws.receive_json()
        assert evt["type"] == "round_start" and evt["session_id"] == session_id
        seen_turns: List[str] = []
        for _ in range(2):
            evt = ws.receive_json()
            assert evt["type"] == "turn_result" and evt["index"] == 1
            seen_turns.append(evt["alias"])  # e1/e2
        assert set(seen_turns) == {"e1", "e2"}
        evt = ws.receive_json()
        assert evt["type"] == "round_end" and evt["index"] == 1
        evt = ws.receive_json()
        assert evt["type"] == "artifacts_saved" and evt["index"] == 1

        # Start next round
        r2 = client.post(
            f"/sessions/{session_id}/round/next", json={"prompt": "Continue"}
        )
        assert r2.status_code == 200
        second = r2.json()
        assert second["index"] == 2
        assert len(second["entries"]) == 2

        evt = ws.receive_json()
        assert evt["type"] == "round_start" and evt["index"] == 2
        turns2: List[str] = []
        for _ in range(2):
            evt = ws.receive_json()
            assert evt["type"] == "turn_result" and evt["index"] == 2
            turns2.append(evt["alias"])
        assert set(turns2) == {"e1", "e2"}
        evt = ws.receive_json()
        assert evt["type"] == "round_end" and evt["index"] == 2
        evt = ws.receive_json()
        assert evt["type"] == "artifacts_saved" and evt["index"] == 2
