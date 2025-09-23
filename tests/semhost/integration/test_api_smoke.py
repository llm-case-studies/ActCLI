from __future__ import annotations

from fastapi.testclient import TestClient

from semhost.main import create_app


def _c() -> TestClient:
    return TestClient(create_app())


def test_openapi_and_docs_smoke() -> None:
    c = _c()
    r = c.get("/openapi.json")
    assert r.status_code == 200
    r2 = c.get("/docs")
    # Swagger UI may return 200 even if assets not loaded; status is enough here
    assert r2.status_code == 200

