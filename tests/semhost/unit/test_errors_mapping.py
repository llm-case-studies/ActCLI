from __future__ import annotations

from fastapi.testclient import TestClient

from semhost.main import create_app


def _client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_sessions_get_not_found_returns_standard_detail() -> None:
    client = _client()
    r = client.get("/sessions/__nope__")
    assert r.status_code == 404
    assert r.json() == {"detail": "session not found"}


def test_mcp_patch_not_found_returns_standard_detail() -> None:
    client = _client()
    r = client.patch("/mcp/__missing__", json={"enabled": True})
    assert r.status_code == 404
    assert r.json() == {"detail": "mcp server not found"}

