from __future__ import annotations

import json
import subprocess
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from platformdirs import user_config_dir


CACHE_DIR = Path(user_config_dir("actcli", "actcli")) / "cache" / "models"
CLOUD_PROVIDERS = {"openai", "anthropic", "google", "claude_cli", "codex_cli", "gemini_cli"}


@dataclass
class ModelDescriptor:
    provider: str
    model_id: str
    display_name: str
    capabilities: Dict[str, bool]
    cost_tier: Optional[str] = None


def _cache_path(provider: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{provider}.json"


def cache_read(provider: str) -> Optional[Dict]:
    path = _cache_path(provider)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def cache_write(provider: str, payload: Dict) -> None:
    path = _cache_path(provider)
    payload = {**payload, "fetched_at": int(time.time())}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def is_stale(cache: Optional[Dict], ttl_hours: int = 24) -> bool:
    if not cache or "fetched_at" not in cache:
        return True
    age_s = max(0, int(time.time()) - int(cache.get("fetched_at", 0)))
    return age_s > ttl_hours * 3600


def list_models_ollama(host: str) -> List[ModelDescriptor]:
    host = host.rstrip("/")
    with httpx.Client(timeout=5.0) as client:
        r = client.get(f"{host}/api/tags")
        r.raise_for_status()
        data = r.json() or {}
        out: List[ModelDescriptor] = []
        for m in data.get("models", []):
            name = m.get("name", "")
            if not name:
                continue
            out.append(ModelDescriptor(provider="ollama", model_id=name, display_name=name, capabilities={"generate": True}))
        return out


PINNED_ANTHROPIC = [
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",
]

PINNED_OPENAI_LATEST = {
    "gpt-4o": "gpt-4o-mini",
    "gpt-4.1": "gpt-4.1-mini",
}


def list_models_openai(api_key: str, refresh: bool = False) -> List[ModelDescriptor]:
    cache = cache_read("openai")
    if not refresh and not is_stale(cache):
        return [ModelDescriptor(**m) for m in cache.get("models", [])]
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=8.0) as client:
        try:
            r = client.get("https://api.openai.com/v1/models", headers=headers)
            r.raise_for_status()
            data = r.json() or {}
            items = data.get("data", [])
            models = [
                ModelDescriptor(provider="openai", model_id=it.get("id", ""), display_name=it.get("id", ""), capabilities={"generate": True})
                for it in items
                if it.get("id")
            ]
        except Exception:
            # Fallback minimal curated set
            models = [
                ModelDescriptor(provider="openai", model_id="gpt-4o-mini", display_name="gpt-4o-mini", capabilities={"generate": True}),
                ModelDescriptor(provider="openai", model_id="gpt-4o", display_name="gpt-4o", capabilities={"generate": True}),
            ]
    cache_write("openai", {"models": [vars(m) for m in models]})
    return models


def list_models_anthropic(api_key: str, refresh: bool = False) -> List[ModelDescriptor]:
    cache = cache_read("anthropic")
    if not refresh and not is_stale(cache):
        return [ModelDescriptor(**m) for m in cache.get("models", [])]
    # No public list; return pinned set
    models = [ModelDescriptor(provider="anthropic", model_id=m, display_name=m, capabilities={"generate": True}) for m in PINNED_ANTHROPIC]
    cache_write("anthropic", {"models": [vars(m) for m in models]})
    return models


def list_models_google(api_key: str, refresh: bool = False) -> List[ModelDescriptor]:
    cache = cache_read("google")
    if not refresh and not is_stale(cache):
        return [ModelDescriptor(**m) for m in cache.get("models", [])]
    with httpx.Client(timeout=8.0) as client:
        try:
            r = client.get("https://generativelanguage.googleapis.com/v1/models", params={"key": api_key})
            r.raise_for_status()
            data = r.json() or {}
            out: List[ModelDescriptor] = []
            for it in data.get("models", []):
                mid = it.get("name") or it.get("id")
                if not mid:
                    continue
                caps = it.get("supportedGenerationMethods") or []
                if "generateContent" in caps:
                    out.append(ModelDescriptor(provider="google", model_id=mid, display_name=mid, capabilities={"generate": True}))
            models = out
        except Exception:
            models = [
                ModelDescriptor(provider="google", model_id="gemini-1.5-flash-latest", display_name="gemini-1.5-flash-latest", capabilities={"generate": True}),
            ]
    cache_write("google", {"models": [vars(m) for m in models]})
    return models


def resolve_latest(provider: str, stem: str, *, openai_key: Optional[str] = None, anthropic_key: Optional[str] = None, google_key: Optional[str] = None) -> Optional[str]:
    provider = provider.lower()
    try:
        if provider == "openai":
            models = list_models_openai(openai_key or "", refresh=False)
            for m in models:
                if m.model_id.startswith(stem):
                    return m.model_id
            return PINNED_OPENAI_LATEST.get(stem)
        if provider == "anthropic":
            models = list_models_anthropic(anthropic_key or "", refresh=False)
            for m in models:
                if m.model_id.startswith(stem):
                    return m.model_id
        if provider == "google":
            models = list_models_google(google_key or "", refresh=False)
            for m in models:
                if m.model_id.startswith(stem):
                    return m.model_id
    except Exception:
        pass
    return None


def list_models_claude_cli(refresh: bool = False) -> List[ModelDescriptor]:
    """List Claude CLI available models.

    Since Claude CLI doesn't have a direct model listing command,
    we return the known available models and aliases.
    """
    cache = cache_read("claude_cli")
    if not refresh and not is_stale(cache):
        return [ModelDescriptor(**m) for m in cache.get("models", [])]

    # Check if Claude CLI is available
    if not shutil.which("claude"):
        return []

    # Known Claude CLI models (as of 2025)
    # These are based on the help text and common knowledge
    known_models = [
        # Aliases (recommended for latest versions)
        ModelDescriptor(
            provider="claude_cli",
            model_id="sonnet",
            display_name="sonnet (latest Sonnet)",
            capabilities={"generate": True},
            cost_tier="subscription"
        ),
        ModelDescriptor(
            provider="claude_cli",
            model_id="opus",
            display_name="opus (latest Opus)",
            capabilities={"generate": True},
            cost_tier="subscription"
        ),
        # Full model names (examples - these may change)
        ModelDescriptor(
            provider="claude_cli",
            model_id="claude-3-5-sonnet-20241022",
            display_name="claude-3-5-sonnet-20241022",
            capabilities={"generate": True},
            cost_tier="subscription"
        ),
        ModelDescriptor(
            provider="claude_cli",
            model_id="claude-3-opus-20240229",
            display_name="claude-3-opus-20240229",
            capabilities={"generate": True},
            cost_tier="subscription"
        ),
        ModelDescriptor(
            provider="claude_cli",
            model_id="claude-3-haiku-20240307",
            display_name="claude-3-haiku-20240307",
            capabilities={"generate": True},
            cost_tier="subscription"
        ),
    ]

    cache_write("claude_cli", {"models": [vars(m) for m in known_models]})
    return known_models


def list_models_codex_cli(refresh: bool = False) -> List[ModelDescriptor]:
    """List Codex CLI available model(s).

    Codex CLI typically uses a session-selected default model; we expose a single
    descriptor and guide users to `codex /model` to switch interactively.
    """
    cache = cache_read("codex_cli")
    if not refresh and not is_stale(cache):
        return [ModelDescriptor(**m) for m in cache.get("models", [])]

    if not shutil.which("codex"):
        return []

    models = [
        ModelDescriptor(
            provider="codex_cli",
            model_id="default",
            display_name="Codex CLI default (select via 'codex /model')",
            capabilities={"generate": True},
            cost_tier="subscription",
        )
    ]
    cache_write("codex_cli", {"models": [vars(m) for m in models]})
    return models


def list_models_gemini_cli(refresh: bool = False) -> List[ModelDescriptor]:
    """List Gemini CLI available model(s).

    The official Gemini CLI is evolving; we expose a single default profile.
    """
    cache = cache_read("gemini_cli")
    if not refresh and not is_stale(cache):
        return [ModelDescriptor(**m) for m in cache.get("models", [])]

    if not shutil.which("gemini"):
        return []

    models = [
        ModelDescriptor(
            provider="gemini_cli",
            model_id="default",
            display_name="Gemini CLI default",
            capabilities={"generate": True},
            cost_tier="subscription",
        )
    ]
    cache_write("gemini_cli", {"models": [vars(m) for m in models]})
    return models
