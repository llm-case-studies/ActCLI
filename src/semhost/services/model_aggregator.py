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


def _policy_allowed(source: str, status: Status) -> tuple[bool, str | None]:
    if source == "local":
        return True, None
    if status.mode != "HYBRID":
        return False, "offline"
    if not status.cloud_share:
        return False, "cloud_share_disabled"
    return True, None


def aggregate_models(settings: SemhostSettings, status: Status) -> List[ModelItem]:
    items: List[ModelItem] = []

    # We avoid invoking subprocess probes here; use binary presence only.

    # Local (ollama) — best effort; swallow network errors
    try:
        for m in list_models_ollama(settings.ollama_host):
            mech = "local"
            items.append(
                ModelItem(
                    provider="ollama",
                    id=m.model_id,
                    source="local",
                    auth=mech,
                    auth_mechanism=mech,
                    auth_state="ready",
                    policy_allowed=True,
                    policy_reason=None,
                    available=True,
                    description=None,
                    hint=None,
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
            auth_ok_env = bool(key)
            for m in func(key, refresh=False):
                mech = "env"
                policy_ok, policy_reason = _policy_allowed("cloud(api)", status)
                auth_state = "ready" if auth_ok_env else "missing"
                available = bool(policy_ok and auth_state == "ready")
                hint = None if auth_ok_env else f"Set {env_key}"
                br = _blocked_reason_for("cloud(api)", status, auth_ok_env)
                items.append(
                    ModelItem(
                        provider=provider,
                        id=m.model_id,
                        source="cloud(api)",
                        auth=mech,
                        auth_mechanism=mech,
                        auth_state=auth_state,  # type: ignore[arg-type]
                        policy_allowed=policy_ok,
                        policy_reason=policy_reason,  # type: ignore[arg-type]
                        available=available,
                        description=None,
                        hint=hint,
                        blocked_reason=br,  # back-compat
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
            cli_bin_ok = bool(shutil.which(bin_name))
            auth_state = "ready" if cli_bin_ok else "missing"
            hint = None if cli_bin_ok else (
                "Install with: npm i -g @anthropic-ai/claude-code" if provider == "claude_cli" else "Install with: npm i -g @openai/codex"
            )

            mech = "cli"
            policy_ok, policy_reason = _policy_allowed("cloud(cli)", status)
            # Back-compat mapping
            br = _blocked_reason_for("cloud(cli)", status, auth_state == "ready")

            # add rows for discovered models
            seen_provider = False
            for m in rows:
                seen_provider = True
                available = bool(policy_ok and auth_state == "ready")
                items.append(
                    ModelItem(
                        provider=provider,
                        id=m.model_id,
                        source="cloud(cli)",
                        auth=mech,
                        auth_mechanism=mech,
                        auth_state=auth_state,  # type: ignore[arg-type]
                        policy_allowed=policy_ok,
                        policy_reason=policy_reason,  # type: ignore[arg-type]
                        available=available,
                        description=m.display_name,
                        hint=hint,
                        blocked_reason=br,
                    )
                )

            # If none discovered (e.g., CLI not installed), expose a placeholder row for visibility
            if not rows:
                model_id = "sonnet" if provider == "claude_cli" else "default"
                available = bool(policy_ok and auth_state == "ready")
                items.append(
                    ModelItem(
                        provider=provider,
                        id=model_id,
                        source="cloud(cli)",
                        auth=mech,
                        auth_mechanism=mech,
                        auth_state=auth_state,  # type: ignore[arg-type]
                        policy_allowed=policy_ok,
                        policy_reason=policy_reason,  # type: ignore[arg-type]
                        available=available,
                        description=(
                            "Claude CLI latest alias (install with npm i -g @anthropic-ai/claude-code)"
                            if provider == "claude_cli"
                            else "Codex CLI default (install with npm i -g @openai/codex)"
                        ),
                        hint=hint,
                        blocked_reason=br,
                    )
                )
        except Exception:
            continue

    return items
