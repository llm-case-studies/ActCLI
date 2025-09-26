from __future__ import annotations

import shutil
import subprocess
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


console = Console()


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _version(cmd: str) -> str:
    try:
        p = subprocess.run(
            [cmd, "--version"], capture_output=True, text=True, timeout=5
        )
        out = (p.stdout or p.stderr or "").strip()
        return out or "-"
    except Exception:
        return "-"


def _auth_probe_codex() -> Tuple[str, str]:
    if not _which("codex"):
        return ("missing", "Install with: npm i -g @openai/codex")
    try:
        p = subprocess.run(
            ["codex", "exec", "ping"], capture_output=True, text=True, timeout=8
        )
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
        p = subprocess.run(
            ["claude", "-p", "test", "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if p.returncode == 0:
            return ("ok", "signed in")
        return ("no", (p.stderr or p.stdout or "not signed in").strip()[:120])
    except subprocess.TimeoutExpired:
        return ("unknown", "probe timeout")
    except Exception as e:
        return ("unknown", str(e))


def providers_doctor() -> None:
    """Summarize vendor CLI providers availability and auth state."""
    table = Table(title="Providers • CLI status", show_header=True, header_style="bold")
    table.add_column("Provider", style="magenta")
    table.add_column("Binary", style="cyan")
    table.add_column("Version", style="dim")
    table.add_column("Auth", style="green")
    table.add_column("Hint", style="dim")

    # Codex CLI (OpenAI)
    codex_bin = _which("codex") or "-"
    codex_ver = _version("codex") if codex_bin != "-" else "-"
    codex_auth, codex_hint = _auth_probe_codex()
    table.add_row("codex_cli", codex_bin, codex_ver, codex_auth, codex_hint)

    # Claude CLI (Anthropic)
    claude_bin = _which("claude") or "-"
    claude_ver = _version("claude") if claude_bin != "-" else "-"
    claude_auth, claude_hint = _auth_probe_claude()
    table.add_row("claude_cli", claude_bin, claude_ver, claude_auth, claude_hint)

    console.print(Panel(table, border_style="cyan"))
    console.print(
        "Launch login: 'actcli auth login codex_cli' or 'actcli auth login claude_cli'"
    )
