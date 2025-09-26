from __future__ import annotations

from fastapi.testclient import TestClient
import logging

from semhost.main import create_app


def _client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_request_id_propagates_to_logs(caplog) -> None:
    client = _client()
    with caplog.at_level(logging.INFO, logger="semhost"):
        r = client.get("/health", headers={"x-request-id": "req-123"})
        assert r.status_code == 200
    assert any(getattr(rec, "request_id", None) == "req-123" and rec.getMessage() == "request" for rec in caplog.records)


def test_round_logs_include_session_and_round(caplog) -> None:
    client = _client()
    # Create session
    req = {"participants": [{"alias": "p1", "provider": "echo", "model_id": "echo"}], "window_k": 1}
    r = client.post("/sessions", json=req)
    assert r.status_code == 200
    sid = r.json()["session_id"]
    with caplog.at_level(logging.INFO, logger="semhost"):
        r1 = client.post(f"/sessions/{sid}/round/start", json={"prompt": "Hello"})
        assert r1.status_code == 200
    # At least one log record has session_id and round_index
    assert any(
        getattr(rec, "session_id", None) == sid and hasattr(rec, "round_index") for rec in caplog.records
    )

