from __future__ import annotations

import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .version import __version__

# Subcommands are loaded lazily to keep import costs low

app = typer.Typer(name="actcli", add_completion=False, no_args_is_help=True, help="ActCLI — actuarial CLI with multi-model roundtable chat")
console = Console()


def _status_header() -> str:
    mode = os.environ.get("ACTCLI_MODE", "hybrid").upper()
    return f"ActCLI • chat(roundtable) • MODE: {mode} • v{__version__}"


def _first_run_banner_if_needed() -> None:
    # Very lightweight first-run indicator; we avoid writing state until commands run.
    banner = Text()
    banner.append("\nActCLI\n", style="bold cyan")
    banner.append("Concurrent multi-model roundtable chat — prototype\n", style="bright_black")
    console.print(Panel(banner, border_style="cyan"))
    console.print(_status_header())


@app.callback()
def _root(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        _first_run_banner_if_needed()


@app.command()
def version() -> None:
    """Show version."""
    console.print(f"ActCLI {__version__}")


@app.command()
def doctor() -> None:
    """Run environment self-checks (Python, TTY, ollama, API keys)."""
    from .commands.doctor import run_doctor

    console.print(_status_header())
    run_doctor()


@app.command()
def auth(
    action: str = typer.Argument(..., help="login|status|logout"),
    provider: Optional[str] = typer.Argument(None, help="openai|anthropic|google"),
    method: Optional[str] = typer.Option(None, help="api-key|device|pkce"),
) -> None:
    """Authenticate with providers (API keys or device/OAuth where supported)."""
    from .commands.auth import run_auth

    run_auth(action=action, provider=provider, method=method)


@app.command()
def chat(
    prompt: str = typer.Option("", "--prompt", "-p", help="User prompt (single turn)"),
    multi: str = typer.Option("llama3,claude,gpt", "--multi", help="Comma-separated provider IDs: llama3, claude, gpt, gemini"),
    rounds: int = typer.Option(2, "--rounds", min=1, max=3, help="Number of discussion rounds (1-3)"),
    timeout_s: int = typer.Option(25, "--timeout-s", help="Per-call timeout seconds"),
    ollama_host: Optional[str] = typer.Option(None, "--ollama-host", help="Override Ollama base URL, e.g., http://127.0.0.1:11435"),
    repl: bool = typer.Option(False, "--repl", help="Start an interactive REPL that supports slash commands"),
) -> None:
    """Run a brief multi-model roundtable (prototype)."""
    from .commands.chat import run_roundtable, run_chat_repl

    console.print(_status_header())
    if repl:
        run_chat_repl(initial_multi=multi, rounds=rounds, timeout_s=timeout_s, ollama_host=ollama_host)
    else:
        run_roundtable(prompt=prompt, multi=multi, rounds=rounds, timeout_s=timeout_s, ollama_host=ollama_host)


@app.command()
def models(
    action: str = typer.Argument("list", help="list|pull"),
    models: Optional[str] = typer.Option(None, "--models", help="Comma-separated model tags to pull"),
    all: bool = typer.Option(False, "--all", help="Pull a default set of useful models"),
    ollama_host: Optional[str] = typer.Option(None, "--ollama-host", help="Ollama base URL (default http://127.0.0.1:11435)"),
) -> None:
    """List or pull models from the configured Ollama host."""
    from .commands.models import list_models, pull_models

    if action == "list":
        list_models(ollama_host)
    elif action == "pull":
        ids = [m.strip() for m in (models.split(",") if models else []) if m.strip()]
        pull_models(ollama_host, ids, use_default=all)
    else:
        raise SystemExit("Unknown action. Use: list|pull")


@app.command()
def pr(
    action: str = typer.Argument(..., help="prepare|link"),
    message: Optional[str] = typer.Option(None, "-m", "--message", help="Commit message (for prepare)"),
    files: Optional[str] = typer.Option(None, "--files", help="Comma-separated globs to stage (for prepare)"),
    branch: Optional[str] = typer.Option(None, "--branch", help="Feature branch name (for prepare)"),
    target: Optional[str] = typer.Option(None, "--target", help="Target branch, defaults to repo default"),
    remote: str = typer.Option("origin", "--remote", help="Remote name"),
    signoff: bool = typer.Option(False, "--signoff", help="Add Signed-off-by to commit"),
) -> None:
    """Prepare a PR (commit+push+URL) or print the PR link for the current branch."""
    from .commands.pr import prepare as pr_prepare, link as pr_link

    if action == "prepare":
        if not message:
            raise SystemExit("--message is required for prepare")
        pr_prepare(message=message, files=files, branch=branch, target=target, remote=remote, signoff=signoff)
    elif action == "link":
        pr_link(target=target, remote=remote)
    else:
        raise SystemExit("Unknown action. Use: prepare|link")


def main() -> None:
    app()
