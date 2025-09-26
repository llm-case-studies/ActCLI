from __future__ import annotations

from typing import List

from fastapi.testclient import TestClient

from semhost.main import create_app


def _c() -> TestClient:
    return TestClient(create_app())


def test_mcp_list_and_toggle() -> None:
    client = _c()
    r = client.get("/mcp")
    assert r.status_code == 200
    rows: List[dict] = r.json()
    assert len(rows) >= 2
    name = rows[0]["name"]
    enabled0 = rows[0]["enabled"]

    # Toggle
    p = client.patch(f"/mcp/{name}", json={"enabled": (not enabled0)})
    assert p.status_code == 200
    r2 = client.get("/mcp")
    rows2 = r2.json()
    changed = next(x for x in rows2 if x["name"] == name)
    assert changed["enabled"] == (not enabled0)

    # Unknown → 404
    p2 = client.patch("/mcp/unknown", json={"enabled": True})
    assert p2.status_code == 404


def test_locations_get_and_patch_roundtrip() -> None:
    client = _c()
    r = client.get("/locations")
    assert r.status_code == 200
    d = r.json()
    assert d["read"] == [] and d["write"] == []

    # Patch
    p = client.patch("/locations", json={"read": ["*.md"], "write": ["out/"]})
    assert p.status_code == 200
    d2 = p.json()
    assert d2["read"] == ["*.md"] and d2["write"] == ["out/"]

    # Reflect in GET /locations and GET /status
    r2 = client.get("/locations")
    assert r2.json() == d2
    st = client.get("/status").json()
    assert st["read"] == ["*.md"] and st["write"] == ["out/"]
