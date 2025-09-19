from __future__ import annotations

import json

import pytest
respx = pytest.importorskip("respx")
import httpx  # noqa: E402

from actcli.seminar.adapters.openai import OpenAIAdapter


@respx.mock
def test_openai_generate_and_seed(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    route = respx.post("https://api.openai.com/v1/chat/completions").respond(
        json={
            "choices": [
                {"message": {"content": "hi"}}
            ]
        }
    )
    a = OpenAIAdapter(model="gpt-4o-mini")
    out = a.generate("q", seed=7)
    assert out == "hi"
    payload = json.loads(route.calls[-1].request.content.decode())
    assert payload.get("seed") == 7


@respx.mock
def test_openai_error_propagates(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    respx.post("https://api.openai.com/v1/chat/completions").respond(status_code=400, json={"error": {"message": "bad"}})
    a = OpenAIAdapter(model="gpt-4o-mini")
    try:
        a.generate("q")
        assert False, "expected error"
    except httpx.HTTPStatusError:
        pass
