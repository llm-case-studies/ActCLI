from __future__ import annotations

from actcli.models.participant import parse_participant_spec


def test_parse_with_alias_host_and_params() -> None:
    s = "llamaA=ollama:llama3:8b@127.0.0.1:11435?temperature=0.2&seed=42&system=role%3Achallenger"
    spec = parse_participant_spec(s)
    assert spec.alias == "llamaA"
    assert spec.provider == "ollama"
    assert spec.model_id == "llama3:8b"
    assert spec.host.startswith("http://127.0.0.1:11435")
    assert spec.params["temperature"] == 0.2
    assert spec.params["seed"] == 42
    assert spec.params["system"].startswith("role:challenger")


def test_parse_shortcuts_and_echo_and_default_host() -> None:
    # Cloud shortcuts
    gpt = parse_participant_spec("gpt")
    assert gpt.provider == "openai" and gpt.model_id
    claude = parse_participant_spec("claude")
    assert claude.provider == "anthropic"
    gem = parse_participant_spec("gemini")
    assert gem.provider == "google"
    # Echo special-case
    ech = parse_participant_spec("echo2")
    assert ech.provider == "echo" and ech.alias is None
    # Default host applied for ollama
    ol = parse_participant_spec(
        "ollama:llama3", default_ollama_host="http://127.0.0.1:11435"
    )
    assert ol.host == "http://127.0.0.1:11435"
