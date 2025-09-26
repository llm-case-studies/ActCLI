from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from typing import Literal
import shutil

from actcli.models.discovery import (
    discover_claude_cli_models_sync,
    discover_codex_cli_models_sync,
    discover_claude_cli_raw_menu,
    discover_codex_cli_raw_menu,
)


router = APIRouter()


@router.get("/providers/cli/discover")
def providers_cli_discover(
    provider: Literal["claude_cli", "codex_cli"] = Query(
        ..., description="CLI provider"
    ),
    raw: bool = Query(False, description="Include raw menu output when available"),
) -> dict:
    if provider == "claude_cli":
        if not shutil.which("claude"):
            raise HTTPException(status_code=400, detail="claude binary not found")
        models = [m.__dict__ for m in discover_claude_cli_models_sync()]
        payload = {"provider": provider, "models": models}
        if raw:
            payload["raw"] = discover_claude_cli_raw_menu()
        return payload
    if provider == "codex_cli":
        if not shutil.which("codex"):
            raise HTTPException(status_code=400, detail="codex binary not found")
        models = [m.__dict__ for m in discover_codex_cli_models_sync()]
        payload = {"provider": provider, "models": models}
        if raw:
            payload["raw"] = discover_codex_cli_raw_menu()
        return payload
    raise HTTPException(status_code=400, detail="unsupported provider")


@router.get("/providers/cli/help")
def providers_cli_help(
    provider: Literal["claude_cli", "codex_cli", "gemini_cli"] = Query(
        ..., description="CLI provider"
    ),
) -> dict:
    import subprocess

    bin_map = {"claude_cli": "claude", "codex_cli": "codex", "gemini_cli": "gemini"}
    cmd = bin_map.get(provider)
    if not cmd or not shutil.which(cmd):
        raise HTTPException(status_code=400, detail=f"binary not found for {provider}")
    try:
        p = subprocess.run([cmd, "--help"], capture_output=True, text=True, timeout=6)
        out = p.stdout or ""
        err = p.stderr or ""
        return {
            "provider": provider,
            "ok": p.returncode == 0,
            "stdout": out,
            "stderr": err,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
