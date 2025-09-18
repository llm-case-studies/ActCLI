from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from ..mcp.git_client import GitMCPClient
from ..git.local import LocalGit


console = Console()


def prepare(message: str, files: Optional[str], branch: Optional[str], target: Optional[str], remote: str, signoff: bool) -> None:
    client = GitMCPClient()
    info = client.repo_detect()
    if not info.get("is_repo"):
        console.print("[red]Not a git repository.[/red]")
        raise SystemExit(2)

    # Make sure .gitignore includes large/local artifacts
    client.ensure_gitignore(["models/", ".venv/", "__pycache__/,", "out/"])

    # Branch
    br = branch or "feat/actcli-change"
    client.branch_ensure(br)

    # Stage files if provided
    if files:
        patterns = [p.strip() for p in files.split(",") if p.strip()]
        client.add(patterns)

    # Commit
    commit_hash = client.commit(message=message, signoff=signoff, allow_empty=False)

    # Push
    client.push(remote=remote, branch=br)

    # PR link
    # Title/body from message
    title, body = (message.split("\n", 1) + [""])[:2]
    url = client.pr_link(remote=remote, target=target, title=title, body=body)
    if url:
        console.print(Panel(url, title="Create PR", border_style="cyan"))
    else:
        console.print("[yellow]Pushed. Unable to construct PR URL; check remote configuration.[/yellow]")


def link(target: Optional[str], remote: str) -> None:
    client = GitMCPClient()
    info = client.repo_detect()
    if not info.get("is_repo"):
        console.print("[red]Not a git repository.[/red]")
        raise SystemExit(2)
    title = ""
    body = ""
    url = client.pr_link(remote=remote, target=target, title=title, body=body)
    if url:
        console.print(Panel(url, title="PR Link", border_style="cyan"))
    else:
        console.print("[yellow]Unable to construct PR URL; check remote configuration.[/yellow]")

