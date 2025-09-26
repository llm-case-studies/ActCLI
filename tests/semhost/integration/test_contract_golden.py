from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Set, List

from fastapi.testclient import TestClient

from semhost.main import create_app


GOLDEN_DIR = Path(__file__).parents[2] / "data" / "golden"


def _client() -> TestClient:
    app = create_app()
    return TestClient(app)


def _load_golden(name: str) -> Dict:
    path = GOLDEN_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def _keys(o: Dict) -> Set[str]:
    return set(o.keys())


def test_event_envelopes_match_golden_keys() -> None:
    client = _client()
    # Create a session with two echo participants
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

    k_start = _keys(_load_golden("events/round_start.json"))
    k_turn = _keys(_load_golden("events/turn_result.json"))
    k_end = _keys(_load_golden("events/round_end.json"))
    k_saved = _keys(_load_golden("events/artifacts_saved.json"))

    # Connect to WS stream
    with client.websocket_connect(f"/sessions/{session_id}/stream") as ws:
        # Start the first round
        r1 = client.post(f"/sessions/{session_id}/round/start", json={"prompt": "Hello world"})
        assert r1.status_code == 200

        evt = ws.receive_json()
        assert evt["type"] == "round_start"
        assert _keys(evt) >= k_start
        seen_turns: List[str] = []
        for _ in range(2):
            evt = ws.receive_json()
            assert evt["type"] == "turn_result"
            assert _keys(evt) >= k_turn
            seen_turns.append(evt["alias"])  # e1/e2
        assert set(seen_turns) == {"e1", "e2"}
        evt = ws.receive_json()
        assert evt["type"] == "round_end"
        assert _keys(evt) >= k_end
        evt = ws.receive_json()
        assert evt["type"] == "artifacts_saved"
        assert _keys(evt) >= k_saved


def test_round_record_matches_golden_keys() -> None:
    client = _client()
    req = {"participants": [{"alias": "p1", "provider": "echo", "model_id": "echo"}], "window_k": 1}
    r = client.post("/sessions", json=req)
    assert r.status_code == 200
    sid = r.json()["session_id"]
    r1 = client.post(f"/sessions/{sid}/round/start", json={"prompt": "Hello"})
    assert r1.status_code == 200
    rr = r1.json()

    golden_rr = _load_golden("sessions/round_record.json")
    golden_entry = _load_golden("sessions/round_entry.json")
    assert _keys(rr) >= _keys(golden_rr)
    assert len(rr["entries"]) >= 1
    assert _keys(rr["entries"][0]) >= _keys(golden_entry)

