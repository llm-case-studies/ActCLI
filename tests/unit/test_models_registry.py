from __future__ import annotations


import pytest

respx = pytest.importorskip("respx")

from actcli.models.registry import (
    cache_read,
    list_models_openai,
    list_models_google,
    list_models_anthropic,
    is_stale,
)


@respx.mock
def test_openai_and_google_listing_and_cache(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    # OpenAI mocked list
    respx.get("https://api.openai.com/v1/models").respond(
        json={"data": [{"id": "gpt-4o-mini"}]}
    )
    rows = list_models_openai("key", refresh=True)
    assert any(m.model_id == "gpt-4o-mini" for m in rows)
    c = cache_read("openai")
    assert c and not is_stale(c)

    # Google list
    respx.get("https://generativelanguage.googleapis.com/v1/models").respond(
        json={
            "models": [
                {
                    "name": "gemini-1.5-flash-latest",
                    "supportedGenerationMethods": ["generateContent"],
                },
                {"name": "vision-only", "supportedGenerationMethods": []},
            ]
        }
    )
    rows = list_models_google("gk", refresh=True)
    assert any(m.model_id == "gemini-1.5-flash-latest" for m in rows)
    c2 = cache_read("google")
    assert c2 and not is_stale(c2)


def test_anthropic_pinned(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    rows = list_models_anthropic("key", refresh=True)
    assert len(rows) > 0
