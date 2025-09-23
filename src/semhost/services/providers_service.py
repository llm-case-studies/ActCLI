from __future__ import annotations

import shutil
import subprocess
from typing import List, Tuple

from ..schemas.providers import (
    CliLoginRequest,
    CliLoginResponse,
    DoctorRow,
    CliModelSwitchRequest,
    CliModelSwitchResponse,
)
from ..deps import get_settings


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _version(cmd: str) -> str:
    try:
        p = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
        out = (p.stdout or p.stderr or "").strip()
        return out or "-"
    except Exception:
        return "-"


def _auth_probe_codex() -> Tuple[str, str]:
    if not _which("codex"):
        return ("missing", "Install with: npm i -g @openai/codex")
    try:
        t = max(4, int(get_settings().cli_probe_timeout_s))
        _ = _version("codex")
        p = subprocess.run(["codex", "exec", "ping"], capture_output=True, text=True, timeout=t)
        if p.returncode == 0:
            return ("ok", "signed in")
        return ("no", (p.stderr or p.stdout or "not signed in").strip()[:120])
    except subprocess.TimeoutExpired:
        return ("unknown", "probe timeout")
    except Exception as e:
        return ("unknown", str(e))


def _auth_probe_claude() -> Tuple[str, str]:
    if not _which("claude"):
        return ("missing", "Install with: npm i -g @anthropic-ai/claude-code")
    try:
        t = max(4, int(get_settings().cli_probe_timeout_s))
        _ = _version("claude")
        p = subprocess.run(["claude", "-p", "test", "--output-format", "json"], capture_output=True, text=True, timeout=t)
        if p.returncode == 0:
            return ("ok", "signed in")
        return ("no", (p.stderr or p.stdout or "not signed in").strip()[:120])
    except subprocess.TimeoutExpired:
        return ("unknown", "probe timeout")
    except Exception as e:
        return ("unknown", str(e))


def _auth_probe_gemini() -> Tuple[str, str]:
    if not _which("gemini"):
        return ("missing", "Install with: npm i -g @google/gemini-cli@nightly")
    # Prefer identity call if present; otherwise tiny prompt with configurable timeout
    try:
        p = subprocess.run(["gemini", "whoami"], capture_output=True, text=True, timeout=5)
        if p.returncode == 0 and (p.stdout or "").strip():
            return ("ok", "signed in")
    except Exception:
        pass
    try:
        t = max(4, int(get_settings().cli_probe_timeout_s))
        _ = _version("gemini")
        p2 = subprocess.run(["gemini", "-p", "test"], capture_output=True, text=True, timeout=t)
        if p2.returncode == 0:
            return ("ok", "signed in")
        return ("no", (p2.stderr or p2.stdout or "not signed in").strip()[:120])
    except subprocess.TimeoutExpired:
        return ("unknown", "probe timeout")
    except Exception as e:
        return ("unknown", str(e))


def providers_doctor_rows() -> List[DoctorRow]:
    rows: List[DoctorRow] = []

    codex_bin = _which("codex") or "-"
    codex_ver = _version("codex") if codex_bin != "-" else "-"
    codex_auth, codex_hint = _auth_probe_codex()
    rows.append(
        DoctorRow(provider="codex_cli", binary=codex_bin, version=codex_ver, auth=codex_auth, hint=codex_hint)
    )

    claude_bin = _which("claude") or "-"
    claude_ver = _version("claude") if claude_bin != "-" else "-"
    claude_auth, claude_hint = _auth_probe_claude()
    rows.append(
        DoctorRow(provider="claude_cli", binary=claude_bin, version=claude_ver, auth=claude_auth, hint=claude_hint)
    )

    gem_bin = _which("gemini") or "-"
    gem_ver = _version("gemini") if gem_bin != "-" else "-"
    gem_auth, gem_hint = _auth_probe_gemini()
    rows.append(
        DoctorRow(provider="gemini_cli", binary=gem_bin, version=gem_ver, auth=gem_auth, hint=gem_hint)
    )

    return rows


def providers_login(req: CliLoginRequest) -> CliLoginResponse:
    st = get_settings()
    if req.provider == "codex_cli":
        if not _which("codex"):
            return CliLoginResponse(launched=False, hint="codex binary not found; npm i -g @openai/codex")
        try:
            # Non-blocking spawn; user completes interactively in terminal
            stderr = None if not st.cli_debug else None
            subprocess.Popen(["codex"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return CliLoginResponse(launched=True)
        except Exception as e:
            return CliLoginResponse(launched=False, hint=str(e))

    if req.provider == "claude_cli":
        if not _which("claude"):
            return CliLoginResponse(launched=False, hint="claude binary not found; npm i -g @anthropic-ai/claude-code")
        try:
            subprocess.Popen(["claude"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return CliLoginResponse(launched=True)
        except Exception as e:
            return CliLoginResponse(launched=False, hint=str(e))

    if req.provider == "gemini_cli":
        if not _which("gemini"):
            return CliLoginResponse(launched=False, hint="gemini binary not found; npm i -g @google/gemini-cli@nightly")
        try:
            subprocess.Popen(["gemini"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return CliLoginResponse(launched=True)
        except Exception as e:
            return CliLoginResponse(launched=False, hint=str(e))

    # Should not happen due to schema validation
    return CliLoginResponse(launched=False, hint="unknown provider")


def providers_switch_model(req: CliModelSwitchRequest) -> CliModelSwitchResponse:
    st = get_settings()
    prov = req.provider
    model = req.model.strip()
    try:
        if prov == "codex_cli":
            if not _which("codex"):
                return CliModelSwitchResponse(ok=False, hint="codex binary not found")
            p = subprocess.run(["codex", "/model", model], capture_output=True, text=True, timeout=8)
            if p.returncode == 0:
                return CliModelSwitchResponse(ok=True)
            hint = (p.stderr or p.stdout or "failed").strip()
            if not st.cli_debug:
                hint = hint[:160]
            return CliModelSwitchResponse(ok=False, hint=hint)
        if prov == "gemini_cli":
            if not _which("gemini"):
                return CliModelSwitchResponse(ok=False, hint="gemini binary not found")
            # Best-effort: verify model usable by making a short call with --model
            p = subprocess.run(["gemini", "-p", "test", "--model", model], capture_output=True, text=True, timeout=8)
            if p.returncode == 0:
                return CliModelSwitchResponse(ok=True)
            hint = (p.stderr or p.stdout or "failed").strip()
            if not st.cli_debug:
                hint = hint[:160]
            return CliModelSwitchResponse(ok=False, hint=hint)
        if prov == "claude_cli":
            if not _which("claude"):
                return CliModelSwitchResponse(ok=False, hint="claude binary not found")
            # Claude supports --model per call; no global switch, but verify via a quick call
            p = subprocess.run(["claude", "-p", "test", "--output-format", "json", "--model", model], capture_output=True, text=True, timeout=8)
            if p.returncode == 0:
                return CliModelSwitchResponse(ok=True)
            hint = (p.stderr or p.stdout or "failed").strip()
            if not st.cli_debug:
                hint = hint[:160]
            return CliModelSwitchResponse(ok=False, hint=hint)
    except subprocess.TimeoutExpired:
        return CliModelSwitchResponse(ok=False, hint="probe timeout")
    except Exception as e:
        return CliModelSwitchResponse(ok=False, hint=str(e))
