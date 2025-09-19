from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..config import Config, Defaults, write_project_config, PROJECT_FILE


console = Console()


def run_init(ollama_host: Optional[str]) -> None:
    path = Path.cwd() / PROJECT_FILE
    if path.exists():
        console.print(Panel(f"{PROJECT_FILE} already exists.", border_style="yellow"))
        return
    cfg = Config(project_name=Path.cwd().name, project_version="0.1", defaults=Defaults())
    if ollama_host:
        cfg.defaults.ollama_host = ollama_host
    write_project_config(path, cfg)
    console.print(Panel(f"Created {PROJECT_FILE}\n\nDefaults:\n- models: {cfg.defaults.models}\n- mode: {cfg.defaults.mode}\n- output_dir: {cfg.defaults.output_dir}\n- ollama_host: {cfg.defaults.ollama_host or '(none)'}", title="actcli init", border_style="green"))

