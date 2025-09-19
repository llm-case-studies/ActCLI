from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


console = Console()


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""


def _run(cmd: List[str]) -> tuple[int, str]:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return out.returncode, (out.stdout or out.stderr).strip()
    except Exception as e:
        return 1, str(e)


def run_doctor() -> None:
    checks: List[Check] = []
    # Python
    checks.append(Check("Python", "ok", platform.python_version()))
    # TTY
    checks.append(Check("TTY", "ok" if console.is_terminal else "warn", "interactive" if console.is_terminal else "non-interactive"))
    # Color
    checks.append(Check("Color", "ok" if console.color_system else "warn", str(console.color_system)))
    # Ollama
    if shutil.which("ollama"):
        code, out = _run(["ollama", "--version"])
        checks.append(Check("ollama", "ok" if code == 0 else "warn", out.splitlines()[0] if out else ""))
    else:
        checks.append(Check("ollama", "warn", "binary not found"))
    # API keys
    for key, label in [("OPENAI_API_KEY", "OpenAI"), ("ANTHROPIC_API_KEY", "Anthropic"), ("GOOGLE_API_KEY", "Google")]:
        checks.append(Check(label + " auth", "ok" if os.getenv(key) else "info", key + (" set" if os.getenv(key) else " not set")))

    # Render
    table = Table(title="Environment Checks", show_header=True, header_style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Detail", style="bright_black")
    for c in checks:
        status_text = {
            "ok": "[green]OK[/green]",
            "warn": "[yellow]WARN[/yellow]",
            "info": "[bright_black]INFO[/bright_black]",
        }.get(c.status, c.status)
        table.add_row(c.name, status_text, c.detail)

    console.print(Panel(table, border_style="cyan"))
    console.print("Tip: run 'actcli auth login <provider>' to configure cloud models.")


def build_doctor_lite_panel() -> Panel:
    """Return a compact, elegant health certificate panel."""
    items = []
    # Python / TTY / Color
    py = platform.python_version()
    tty = "yes" if console.is_terminal else "no"
    color = console.color_system or "none"
    items.append(f"Python {py} • TTY: {tty} • Color: {color}")
    # Ollama
    if shutil.which("ollama"):
        code, out = _run(["ollama", "--version"])
        stat = "ok" if code == 0 else "warn"
        ver = out.splitlines()[0] if out else "?"
        items.append(f"Ollama: {stat} ({ver})")
    else:
        items.append("Ollama: not found")
    # API keys
    keys = [k for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY") if os.getenv(k)]
    items.append(f"API keys: {len(keys)} set")

    txt = Text()
    for i, line in enumerate(items):
        style = "green" if ("ok" in line or line.startswith("Python")) else "yellow"
        txt.append("• ", style="bright_black")
        txt.append(line + ("\n" if i < len(items) - 1 else ""), style=style)
    return Panel(txt, title="Health Check", border_style="cyan")
