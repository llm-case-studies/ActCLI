from __future__ import annotations

from typing import List

from fastapi.testclient import TestClient

from semhost.main import create_app


def _client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_session_create_get_patch_roundtrip() -> None:
    client = _client()

    # Create with single echo participant
    req = {"participants": [{"alias": "p1", "provider": "echo", "model_id": "echo"}], "window_k": 2}
    r = client.post("/sessions", json=req)
    assert r.status_code == 200
    sid = r.json()["session_id"]

    # Read snapshot
    g = client.get(f"/sessions/{sid}")
    assert g.status_code == 200
    snap = g.json()
    assert snap["id"] == sid
    assert snap["round_idx"] == 0
    assert snap["window_k"] == 2
    assert [p["alias"] for p in snap["participants"]] == ["p1"]

    # Patch participants and window_k
    p = client.patch(
        f"/sessions/{sid}",
        json={
            "participants": [
                {"alias": "p1", "provider": "echo", "model_id": "echo"},
                {"alias": "p2", "provider": "echo", "model_id": "echo"},
            ],
            "window_k": 1,
        },
    )
    assert p.status_code == 200
    snap2 = p.json()
    assert [p["alias"] for p in snap2["participants"]] == ["p1", "p2"]
    assert snap2["window_k"] == 1

    # Start a round to ensure route returns RoundRecord
    r1 = client.post(f"/sessions/{sid}/round/start", json={"prompt": "Q"})
    assert r1.status_code == 200
    rr = r1.json()
    assert rr["index"] == 1
    assert len(rr["entries"]) == 2

