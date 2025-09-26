from __future__ import annotations

from fastapi.testclient import TestClient

from semhost.main import create_app


def _c() -> TestClient:
    return TestClient(create_app())


def test_mcp_tools_list_includes_web_bridge_tools() -> None:
    client = _c()
    r = client.get("/mcp/tools")
    assert r.status_code == 200
    items = r.json()
    names = {t["id"] for t in items}
    assert "participants.register" in names
    assert "participants.message" in names
    assert "events.log" in names


def test_mcp_events_log_streams_ok() -> None:
    client = _c()
    # Start job
    r = client.post("/mcp/rpc", json={"tool": "events.log", "params": {"event": "web_bridge_test", "data": {"x": 1}}})
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    # Consume SSE response fully (short stream)
    s = client.get(f"/mcp/sse?job={job_id}")
    assert s.status_code == 200
    body = s.text
    assert '"event": "ok"' in body or '"event":"ok"' in body

