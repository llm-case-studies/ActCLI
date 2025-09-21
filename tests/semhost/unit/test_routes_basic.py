from __future__ import annotations

import os
from typing import List

import pytest
from fastapi.testclient import TestClient

from semhost.main import create_app
from semhost.deps import update_status
from semhost.schemas.status import StatusPatch


def _new_client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_health_ok_and_version() -> None:
    client = _new_client()
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert isinstance(data.get("version"), str)


def test_cors_preflight_allowed() -> None:
    client = _new_client()
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "PATCH",
        "Access-Control-Request-Headers": "content-type",
    }
    r = client.options("/status", headers=headers)
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "PATCH" in (r.headers.get("access-control-allow-methods") or "")
    assert "content-type" in (r.headers.get("access-control-allow-headers") or "").lower()


def test_cors_preflight_denied_for_other_origin() -> None:
    client = _new_client()
    headers = {
        "Origin": "http://evil.local",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }
    r = client.options("/status", headers=headers)
    # No allow-origin header for disallowed origin
    assert r.headers.get("access-control-allow-origin") is None


def test_status_roundtrip_and_ephemeral_restart() -> None:
    client = _new_client()
    # Defaults
    r = client.get("/status")
    assert r.status_code == 200
    d = r.json()
    assert d["mode"] == "OFFLINE" and d["cloud_share"] is False
    assert d["window_k"] >= 0
    # Patch
    r2 = client.patch(
        "/status",
        json={
            "mode": "HYBRID",
            "cloud_share": True,
            "window_k": 3,
            "max_rounds": 5,
            "read": ["*.md"],
            "write": ["out/"]
        },
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["mode"] == "HYBRID" and d2["cloud_share"] is True
    assert d2["window_k"] == 3 and d2["max_rounds"] == 5
    assert d2["read"] == ["*.md"] and d2["write"] == ["out/"]

    # New app instance (ephemeral reset in Sprint 1)
    client2 = _new_client()
    r3 = client2.get("/status")
    d3 = r3.json()
    assert d3["mode"] == "OFFLINE" and d3["cloud_share"] is False


def test_models_available_and_blocked_reason(monkeypatch) -> None:
    # Prepare status: HYBRID + cloud_share true
    update_status(StatusPatch(mode="HYBRID", cloud_share=True))

    # Monkeypatch model registry functions to avoid network
    from actcli.models import registry as reg

    class _MD:
        def __init__(self, provider: str, model_id: str, display_name: str = ""):
            self.provider = provider
            self.model_id = model_id
            self.display_name = display_name or model_id
            self.capabilities = {"generate": True}

    monkeypatch.setattr(reg, "list_models_ollama", lambda host: [_MD("ollama", "llama3:8b")])
    monkeypatch.setattr(reg, "list_models_openai", lambda key, refresh=False: [_MD("openai", "gpt-4o-mini")])
    monkeypatch.setattr(reg, "list_models_anthropic", lambda key, refresh=False: [_MD("anthropic", "claude-3-haiku-20240307")])
    monkeypatch.setattr(reg, "list_models_google", lambda key, refresh=False: [_MD("google", "gemini-1.5-flash-latest")])
    monkeypatch.setattr(reg, "list_models_claude_cli", lambda refresh=False: [_MD("claude_cli", "sonnet")])
    monkeypatch.setattr(reg, "list_models_codex_cli", lambda refresh=False: [_MD("codex_cli", "default")])

    # Env/auth state
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("GOOGLE_API_KEY", "g")

    # CLI presence
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda cmd: "/usr/bin/" + cmd)

    client = _new_client()
    r = client.get("/models")
    assert r.status_code == 200
    rows: List[dict] = r.json()

    # Local always available
    ol = next(x for x in rows if x["provider"] == "ollama")
    assert ol["available"] is True and ol.get("blocked_reason") is None

    # OpenAI missing key → blocked
    op = next(x for x in rows if x["provider"] == "openai")
    assert op["available"] is False and op["blocked_reason"] == "missing_key"

    # Anthropic+Google with keys → available
    an = next(x for x in rows if x["provider"] == "anthropic")
    go = next(x for x in rows if x["provider"] == "google")
    assert an["available"] is True and an.get("blocked_reason") is None
    assert go["available"] is True and go.get("blocked_reason") is None

    # CLI-backed available when binary present
    cc = next(x for x in rows if x["provider"] == "claude_cli")
    cx = next(x for x in rows if x["provider"] == "codex_cli")
    assert cc["available"] is True and cc.get("blocked_reason") is None
    assert cx["available"] is True and cx.get("blocked_reason") is None

    # Now set OFFLINE → all cloud blocked due to offline
    update_status(StatusPatch(mode="OFFLINE", cloud_share=False))
    r2 = client.get("/models")
    rows2: List[dict] = r2.json()
    for x in rows2:
        if x["source"] == "local":
            continue
        assert x["available"] is False and x["blocked_reason"] == "offline"


def test_auth_cli_login_semantics(monkeypatch) -> None:
    client = _new_client()

    # Missing binary → launched:false
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    r = client.post("/auth/cli/login", json={"provider": "codex_cli"})
    assert r.status_code == 200
    assert r.json()["launched"] is False

    # Present binary → launched:true
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")

    class _P:
        def __init__(self):
            pass

    monkeypatch.setattr("subprocess.Popen", lambda *a, **kw: _P())
    r2 = client.post("/auth/cli/login", json={"provider": "claude_cli"})
    assert r2.status_code == 200
    assert r2.json()["launched"] is True

