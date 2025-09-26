from __future__ import annotations

import os
import sqlite3
from typing import List

from fastapi.testclient import TestClient

from semhost.main import create_app
from semhost.settings import SemhostSettings


def _client(db_path: str) -> TestClient:
    app = create_app(SemhostSettings(db_path=db_path))
    return TestClient(app)


def test_session_and_round_persisted(tmp_path) -> None:
    db_path = tmp_path / "semhost.db"
    client = _client(str(db_path))

    # Create a session with two echo participants
    req = {
        "participants": [
            {"alias": "e1", "provider": "echo", "model_id": "echo"},
            {"alias": "e2", "provider": "echo", "model_id": "echo"},
        ],
        "window_k": 1,
    }
    r = client.post("/sessions", json=req)
    assert r.status_code == 200
    session_id = r.json()["session_id"]

    # Start a round to trigger persistence
    r1 = client.post(f"/sessions/{session_id}/round/start", json={"prompt": "Hello"})
    assert r1.status_code == 200
    rr = r1.json()
    assert rr["index"] == 1

    # Verify DB contents
    assert os.path.exists(db_path)
    con = sqlite3.connect(db_path)
    cur = con.execute("SELECT id, window_k, max_rounds, participants_json FROM sessions WHERE id=?", (session_id,))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == session_id and row[1] == 1

    # One round persisted
    cur = con.execute("SELECT COUNT(1) FROM rounds WHERE session_id=?", (session_id,))
    assert cur.fetchone()[0] == 1
    # Two entries persisted
    cur = con.execute("SELECT COUNT(1) FROM entries WHERE session_id=? AND round_idx=1", (session_id,))
    assert cur.fetchone()[0] == 2
    con.close()

