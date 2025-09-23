from __future__ import annotations

import urllib.parse as up
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ParticipantSpec:
    alias: Optional[str]
    provider: str  # ollama|openai|anthropic|google|echo
    model_id: Optional[str] = None
    host: Optional[str] = None
    params: Dict[str, object] = field(default_factory=dict)  # temperature: float, seed: int, system: str, timeout_s: int


DEFAULT_SHORTCUTS = {
    "gpt": ("openai", "gpt-4o-mini"),
    "claude": ("anthropic", "claude-3-haiku-20240307"),
    "gemini": ("google", "gemini-1.5-flash-latest"),
}


def _convert_param(key: str, val: str) -> object:
    if key in ("seed", "timeout_s"):
        try:
            return int(val)
        except Exception:
            return val
    if key in ("temperature",):
        try:
            return float(val)
        except Exception:
            return val
    if key == "reasoning":
        low = str(val).strip().lower()
        if low in ("minimal", "low", "medium", "high"):
            return low
        return val
    if key == "system":
        return up.unquote_plus(val)
    return val


def parse_participant_spec(s: str, *, default_ollama_host: Optional[str] = None) -> ParticipantSpec:
    """Parse a participant spec of the form [alias=]provider[:model][@host][?k=v&k=v].

    - If provider is omitted and token matches shortcuts (gpt/claude/gemini), map to cloud defaults.
    - If provider is omitted and token resembles an Ollama tag (contains ':' or startswith a known prefix), assume provider=ollama.
    - Special-case 'echo' tokens to a local EchoAdapter provider.
    """
    alias = None
    token = s.strip()
    if not token:
        raise ValueError("empty participant spec")

    if "=" in token:
        alias, token = token.split("=", 1)
        alias = alias.strip() or None

    # Split query params
    qpos = token.find("?")
    query = ""
    if qpos != -1:
        query = token[qpos + 1 :]
        token = token[:qpos]
    qs = {k: v[0] for k, v in up.parse_qs(query, keep_blank_values=True).items()}
    params = {k: _convert_param(k, v) for k, v in qs.items()}

    # Host part for ollama
    host = None
    if "@" in token:
        token, host = token.split("@", 1)
        if host and not host.startswith("http://") and not host.startswith("https://"):
            host = "http://" + host

    provider = None
    model_id = None

    if ":" in token:
        provider, model_id = token.split(":", 1)
        provider = provider.lower()
        # Support latest:stem pattern: model_id like 'latest:gpt-4o'
        model_id = model_id.strip()
    else:
        # Shorthand or echo
        low = token.lower()
        if low == "echo" or low.startswith("echo"):
            provider = "echo"
            model_id = low
        elif low in DEFAULT_SHORTCUTS:
            provider, model_id = DEFAULT_SHORTCUTS[low]
        else:
            provider = "ollama"
            model_id = token

    if provider == "ollama" and host is None and default_ollama_host:
        host = default_ollama_host

    return ParticipantSpec(alias=alias, provider=provider, model_id=model_id, host=host, params=params)
