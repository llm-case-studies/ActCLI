from __future__ import annotations

import pytest
respx = pytest.importorskip("respx")
import httpx  # noqa: E402

from actcli.seminar.adapters.gemini import GeminiAdapter


@respx.mock
def test_gemini_generate(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "gk")
    # Exact URL with provided key
    respx.post("https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key=gk").respond(
        json={"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
    )
    a = GeminiAdapter()
    out = a.generate("q")
    assert out == "ok"


@respx.mock
def test_gemini_error(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "gk")
    respx.post("https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash-latest:generateContent?key=gk").respond(
        status_code=403, json={"error": {"message": "denied"}}
    )
    a = GeminiAdapter()
    try:
        a.generate("q")
        assert False, "expected error"
    except httpx.HTTPStatusError:
        pass
