from __future__ import annotations

from typing import List, Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
import json


console = Console()

DEFAULT_MODELS = [
    "codellama:34b",
    "gpt-oss:20b",
    "codellama:13b",
    "llama3:8b",
    "llama3.2:3b",
]


def _resolve_host(ollama_host: Optional[str]) -> str:
    return (ollama_host or "http://127.0.0.1:11435").rstrip("/")


def list_models(ollama_host: Optional[str]) -> None:
    host = _resolve_host(ollama_host)
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{host}/api/tags")
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        console.print(Panel(str(e), title="Unable to reach Ollama host", border_style="red"))
        console.print("Tip: start the project server: scripts/ollama-local.sh serve")
        return

    models = data.get("models", [])
    table = Table(title=f"Ollama models @ {host}", show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Modified")
    table.add_column("Size")
    for m in models:
        table.add_row(m.get("name", ""), m.get("modified_at", ""), str(m.get("size", "")))
    console.print(Panel(table, border_style="cyan"))


def pull_models(ollama_host: Optional[str], ids: Optional[List[str]], use_default: bool) -> None:
    host = _resolve_host(ollama_host)
    targets = ids if ids else (DEFAULT_MODELS if use_default else [])
    if not targets:
        console.print("Provide --models or use --all to pull defaults.")
        return
    # Disable read timeout for large pulls; keep connect short
    timeout = httpx.Timeout(connect=5.0, read=None, write=None, pool=None)
    with httpx.Client(timeout=timeout) as client:
        for name in targets:
            console.print(f"Pulling [cyan]{name}[/cyan] @ {host} …")
            try:
                with client.stream("POST", f"{host}/api/pull", json={"name": name, "stream": True}) as resp:
                    resp.raise_for_status()
                    # Try to render a simple progress bar if totals are provided
                    progress = None
                    task_id = None
                    for raw in resp.iter_lines():
                        if not raw:
                            continue
                        # Some servers send multiple JSON objects per line; split if needed
                        parts = [p for p in raw.splitlines() if p.strip()]
                        for part in parts:
                            try:
                                ev = json.loads(part)
                            except Exception:
                                console.print(part)
                                continue
                            status = ev.get("status", "")
                            total = ev.get("total")
                            completed = ev.get("completed")
                            if total and completed is not None:
                                if progress is None:
                                    progress = Progress(
                                        TextColumn("[progress.description]{task.description}"),
                                        BarColumn(),
                                        TextColumn("{task.percentage:>3.0f}%"),
                                        console=console,
                                    )
                                    progress.start()
                                    task_id = progress.add_task(f"{name}", total=total)
                                progress.update(task_id, completed=completed)
                            elif status:
                                console.print(f"  {status}")
                            # Terminal condition
                            if status == "success":
                                if progress is not None:
                                    progress.update(task_id, completed=progress.tasks[0].total)
                                    progress.stop()
                                console.print("  → done")
                                break
                    else:
                        # If we exit loop without success message
                        if progress is not None:
                            progress.stop()
            except Exception as e:
                console.print(f"  → [red]failed[/red]: {e}")
