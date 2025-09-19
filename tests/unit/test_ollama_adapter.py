from __future__ import annotations

import json

import pytest
respx = pytest.importorskip("respx")

from actcli.seminar.adapters.ollama import OllamaAdapter


@respx.mock
def test_ollama_tag_mapping() -> None:
    respx.get("http://mock/api/tags").respond(json={"models": [{"name": "llama3:8b"}]})
    a = OllamaAdapter(model="llama3", host="http://mock")
    assert a.model == "llama3:8b"
    assert a.name.startswith("llama3:8b")


@respx.mock
def test_ollama_generate_payload_and_seed() -> None:
    route = respx.post("http://mock/api/generate").respond(json={"response": "ok"})
    a = OllamaAdapter(model="llama3:8b", host="http://mock")
    text = a.generate("hello", seed=123, system="sys", timeout_s=3)
    assert text == "ok"
    # Inspect last request payload
    req = route.calls[-1].request
    payload = json.loads(req.content.decode())
    assert payload["model"] == "llama3:8b"
    assert payload.get("options", {}).get("seed") == 123
    assert payload.get("system") == "sys"


@respx.mock
def test_ollama_error_wrapped() -> None:
    respx.post("http://mock/api/generate").respond(status_code=404, json={"error": "missing"})
    a = OllamaAdapter(model="llama3", host="http://mock")
    try:
        a.generate("oops", timeout_s=1)
        assert False, "expected error"
    except RuntimeError as e:
        msg = str(e)
        assert "404" in msg and "missing" in msg
