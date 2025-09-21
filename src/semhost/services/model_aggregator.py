from __future__ import annotations

import os
import shutil
from typing import List

from actcli.models.registry import (
    list_models_anthropic,
    list_models_codex_cli,
    list_models_claude_cli,
    list_models_google,
    list_models_ollama,
    list_models_openai,
)

from ..schemas.models import ModelItem
from ..schemas.status import Status
from ..settings import SemhostSettings


def _auth_for(provider: str) -> str:
    if provider == "ollama":
        return "local"
    if provider == "openai":
        return "env" if os.getenv("OPENAI_API_KEY") else "none"
    if provider == "anthropic":
        return "env" if os.getenv("ANTHROPIC_API_KEY") else "none"
    if provider == "google":
        return "env" if os.getenv("GOOGLE_API_KEY") else "none"
    if provider == "claude_cli":
        return "cli" if shutil.which("claude") else "none"
    if provider == "codex_cli":
        return "cli" if shutil.which("codex") else "none"
    return "none"


def _blocked_reason_for(source: str, status: Status, auth_ok: bool) -> str | None:
    if source == "local":
        return None
    if status.mode != "HYBRID":
        return "offline"
    if not status.cloud_share:
        return "cloud_share_disabled"
    if source == "cloud(api)" and not auth_ok:
        return "missing_key"
    if source == "cloud(cli)" and not auth_ok:
        return "cli_missing"
    return None


def aggregate_models(settings: SemhostSettings, status: Status) -> List[ModelItem]:
    items: List[ModelItem] = []

    # Local (ollama) — best effort; swallow network errors
    try:
        for m in list_models_ollama(settings.ollama_host):
            items.append(
                ModelItem(
                    provider="ollama",
                    id=m.model_id,
                    source="local",
                    auth=_auth_for("ollama"),
                    available=True,
                    description=None,
                    blocked_reason=None,
                )
            )
    except Exception:
        # No local models reachable — ok
        pass

    # Cloud APIs
    for provider, func, env_key in (
        ("openai", list_models_openai, "OPENAI_API_KEY"),
        ("anthropic", list_models_anthropic, "ANTHROPIC_API_KEY"),
        ("google", list_models_google, "GOOGLE_API_KEY"),
    ):
        try:
            key = os.getenv(env_key, "")
            for m in func(key, refresh=False):
                auth_ok = bool(os.getenv(env_key))
                br = _blocked_reason_for("cloud(api)", status, auth_ok)
                items.append(
                    ModelItem(
                        provider=provider,
                        id=m.model_id,
                        source="cloud(api)",
                        auth=_auth_for(provider),
                        available=br is None,
                        description=None,
                        blocked_reason=br,
                    )
                )
        except Exception:
            continue

    # CLI-backed
    for provider, func, bin_name in (
        ("claude_cli", list_models_claude_cli, "claude"),
        ("codex_cli", list_models_codex_cli, "codex"),
    ):
        try:
            rows = func(refresh=False)
            cli_ok = bool(shutil.which(bin_name))
            br = _blocked_reason_for("cloud(cli)", status, cli_ok)
            for m in rows:
                items.append(
                    ModelItem(
                        provider=provider,
                        id=m.model_id,
                        source="cloud(cli)",
                        auth=_auth_for(provider),
                        available=br is None,
                        description=m.display_name,
                        blocked_reason=br,
                    )
                )
        except Exception:
            continue

    return items

