from __future__ import annotations

import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .version import __version__
from .config import load_config
from .trust import get_trust

# Subcommands are loaded lazily to keep import costs low

app = typer.Typer(name="actcli", add_completion=False, invoke_without_command=True, help="ActCLI — actuarial CLI with multi-model roundtable chat")
console = Console()
_CONFIG, _CONFIG_PATH = load_config()


def _status_header() -> str:
    mode = (_CONFIG.defaults.mode if _CONFIG else os.environ.get("ACTCLI_MODE", "hybrid")).upper()
    return f"ActCLI • chat(roundtable) • MODE: {mode} • v{__version__}"


def _first_run_banner_if_needed() -> None:
    # Lightweight, elegant banner + health certificate (doctor-lite)
    title = Text()
    title.append("ActCLI", style="bold cyan")
    subtitle = Text("  •  concurrent roundtable • offline-first", style="bright_black")
    console.print(Panel(Text.assemble(title, subtitle), border_style="cyan"))
    console.print(_status_header())
    try:
        from .commands.doctor import build_doctor_lite_panel
        console.print(build_doctor_lite_panel())
    except Exception:
        pass


@app.callback()
def _root(ctx: typer.Context):
    global _CONFIG, _CONFIG_PATH
    if ctx.invoked_subcommand is None:
        # Just go straight to chat - keep it simple!
        console.print(_status_header())
        from .commands.chat import run_chat_repl
        run_chat_repl(initial_multi="llama3,claude,gpt", rounds=2, timeout_s=25, ollama_host=None)


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
    prompt: str = typer.Option("", "--prompt", "-p", help="User prompt (single turn, otherwise interactive)"),
    multi: str = typer.Option("llama3,claude,gpt", "--multi", help="Comma-separated provider IDs: llama3, claude, gpt, gemini"),
    rounds: int = typer.Option(2, "--rounds", min=1, max=3, help="Number of discussion rounds (1-3)"),
    timeout_s: int = typer.Option(25, "--timeout-s", help="Per-call timeout seconds"),
    ollama_host: Optional[str] = typer.Option(None, "--ollama-host", help="Override Ollama base URL, e.g., http://127.0.0.1:11435"),
    save: Optional[str] = typer.Option(None, "--save", help="Save transcript markdown to path (e.g., out/seminar.md)"),
    audit: Optional[str] = typer.Option(None, "--audit", help="Save audit-lite JSON to path (e.g., out/seminar_audit.json)"),
    presenter_state: Optional[str] = typer.Option(None, "--presenter-state", help="Write presenter state JSON (e.g., out/presenter/state.json)"),
) -> None:
    """Multi-model chat: interactive by default, or one-shot with --prompt."""
    from .commands.chat import run_roundtable, run_chat_repl

    console.print(_status_header())

    # Simple logic: if prompt given, do one-shot; otherwise interactive
    if prompt:
        run_roundtable(prompt=prompt, multi=multi, rounds=rounds, timeout_s=timeout_s,
                      ollama_host=ollama_host, save=save, audit=audit, presenter_state=presenter_state)
    else:
        # Interactive chat (what most people want)
        run_chat_repl(initial_multi=multi, rounds=rounds, timeout_s=timeout_s, ollama_host=ollama_host)


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


@app.command()
def init(ollama_host: Optional[str] = typer.Option(None, "--ollama-host", help="Write actcli.toml with this Ollama host")) -> None:
    """Create actcli.toml with defaults in the current directory."""
    from .commands.init import run_init

    run_init(ollama_host=ollama_host)


@app.command()
def mcp(
    action: str = typer.Argument("list", help="list|add|on|off|test|log|reload|restart"),
    name: Optional[str] = typer.Argument(None, help="Server name for actions that require it"),
    url: Optional[str] = typer.Option(None, "--url", help="Server URL (for add)"),
    group: Optional[str] = typer.Option(None, "--group", help="Group label (for add)"),
    desc: Optional[str] = typer.Option(None, "--desc", help="Description (for add)"),
    enable: Optional[bool] = typer.Option(None, "--enable", help="Enable/disable (for log)"),
) -> None:
    """Manage MCP servers: list/add/on/off/test/log/reload/restart."""
    from .commands.mcp import mcp_list, mcp_add, mcp_on_off, mcp_log, mcp_test, mcp_reload, mcp_restart

    if action == "list":
        mcp_list()
    elif action == "add":
        if not name or not url:
            raise SystemExit("mcp add <name> --url <url> [--group g] [--desc '...']")
        mcp_add(name, url, group, desc)
    elif action == "on":
        if not name:
            raise SystemExit("mcp on <name>")
        mcp_on_off(name, True)
    elif action == "off":
        if not name:
            raise SystemExit("mcp off <name>")
        mcp_on_off(name, False)
    elif action == "test":
        if not name:
            raise SystemExit("mcp test <name>")
        mcp_test(name)
    elif action == "log":
        if not name or enable is None:
            raise SystemExit("mcp log <name> --enable {true|false}")
        mcp_log(name, bool(enable))
    elif action == "reload":
        if not name:
            raise SystemExit("mcp reload <name>")
        mcp_reload(name)
    elif action == "restart":
        if not name:
            raise SystemExit("mcp restart <name>")
        mcp_restart(name)
    else:
        raise SystemExit("Unknown action. Use: list|add|on|off|test|log|reload|restart")


@app.command()
def presenter(
    action: str = typer.Argument("start", help="start|prepare"),
    port: int = typer.Option(8765, "--port", help="Presenter HTTP port"),
    open: bool = typer.Option(True, "--open/--no-open", help="Open browser on start"),
) -> None:
    """Serve a lightweight presenter UI that reads state.json and renders the session."""
    from .commands.presenter import start_presenter, prepare_presenter
    from pathlib import Path

    if action == "start":
        start_presenter(port=port, open_browser=open)
    elif action == "prepare":
        root = prepare_presenter(Path("out"))
        console.print(f"Prepared presenter files at: {root}")
    else:
        raise SystemExit("Unknown action. Use: start|prepare")

def main() -> None:
    app()
