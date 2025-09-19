from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..config import Config, Defaults, write_project_config, PROJECT_FILE
from pathlib import Path
from ..trust import set_trust


console = Console()


def run_wizard() -> None:
    console.print(Panel("Welcome to ActCLI — quick setup", border_style="cyan"))
    # Trust
    trust_choice = typer.prompt("Trust this folder? (persist/once/deny)", default="persist")
    trust_choice = trust_choice.lower().strip()
    # Mode
    mode = typer.prompt("Default mode (offline/hybrid)", default="offline")
    # Output dir
    outdir = typer.prompt("Output directory", default="out")
    # Models
    models = typer.prompt("Default models (comma-separated)", default="llama3,claude,gpt")
    # Cloud share
    cs = typer.confirm("Allow sharing file content to cloud models by default?", default=False)

    # Write project config
    cfg = Config(project_name=None, project_version="0.1", defaults=Defaults(mode=mode, output_dir=outdir, models=models))
    write_project_config(Path.cwd() / PROJECT_FILE, cfg)

    # Trust store (except deny)
    if trust_choice in ("persist", "once"):
        set_trust(None, trust_choice, read=["./**"], write=[f"./{outdir}/**"], cloud_share=cs)
        console.print(Panel(f"Trusted this folder ({trust_choice}).", border_style="green"))
    else:
        console.print(Panel("Not trusting this folder; reads limited.", border_style="yellow"))

    console.print(Panel("Setup complete. Entering REPL…", border_style="cyan"))
