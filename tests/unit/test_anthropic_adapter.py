from __future__ import annotations

import pytest
respx = pytest.importorskip("respx")
import httpx  # noqa: E402

from actcli.seminar.adapters.anthropic import AnthropicAdapter


@respx.mock
def test_anthropic_generate(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ak-test")
    respx.post("https://api.anthropic.com/v1/messages").respond(
        json={"content": [{"text": "hello"}]}
    )
    a = AnthropicAdapter()
    out = a.generate("q")
    assert out == "hello"


@respx.mock
def test_anthropic_error(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ak-test")
    respx.post("https://api.anthropic.com/v1/messages").respond(status_code=500, json={"error": "x"})
    a = AnthropicAdapter()
    try:
        a.generate("q")
        assert False, "expected error"
    except httpx.HTTPStatusError:
        pass
