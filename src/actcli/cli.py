from __future__ import annotations

import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .version import __version__
from .config import load_config
from pathlib import Path

# Subcommands are loaded lazily to keep import costs low

app = typer.Typer(
    name="actcli",
    add_completion=False,
    invoke_without_command=True,
    help="ActCLI — actuarial CLI with multi-model roundtable chat",
)
console = Console()
_CONFIG, _CONFIG_PATH = load_config()


def _status_header() -> str:
    mode = (
        _CONFIG.defaults.mode if _CONFIG else os.environ.get("ACTCLI_MODE", "hybrid")
    ).upper()
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

        run_chat_repl(
            initial_multi="llama3,claude,gpt", rounds=2, timeout_s=25, ollama_host=None
        )


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
    client_id: Optional[str] = typer.Option(
        None, "--client-id", help="OAuth client_id (e.g., for Google device flow)"
    ),
) -> None:
    """Authenticate with providers (API keys or device/OAuth where supported)."""
    from .commands.auth import run_auth

    run_auth(action=action, provider=provider, method=method, client_id=client_id)


@app.command()
def chat(
    prompt: str = typer.Option(
        "", "--prompt", "-p", help="User prompt (single turn, otherwise interactive)"
    ),
    multi: str = typer.Option(
        "llama3,claude,gpt",
        "--multi",
        help="Comma-separated provider IDs: llama3, claude, gpt, gemini",
    ),
    rounds: int = typer.Option(
        2, "--rounds", min=1, max=3, help="Number of discussion rounds (1-3)"
    ),
    timeout_s: int = typer.Option(25, "--timeout-s", help="Per-call timeout seconds"),
    ollama_host: Optional[str] = typer.Option(
        None,
        "--ollama-host",
        help="Override Ollama base URL, e.g., http://127.0.0.1:11435",
    ),
    save: Optional[str] = typer.Option(
        None, "--save", help="Save transcript markdown to path (e.g., out/seminar.md)"
    ),
    audit: Optional[str] = typer.Option(
        None,
        "--audit",
        help="Save audit-lite JSON to path (e.g., out/seminar_audit.json)",
    ),
    presenter_state: Optional[str] = typer.Option(
        None,
        "--presenter-state",
        help="Write presenter state JSON (e.g., out/presenter/state.json)",
    ),
    max_rounds: Optional[int] = typer.Option(
        None,
        "--max-rounds",
        help="Cap for unlimited-mode rounds (default unlimited, soft clamp 100)",
    ),
    round_window: int = typer.Option(
        2,
        "--round-window",
        help="Number of prior rounds to include in context window (default 2)",
    ),
) -> None:
    """Multi-model chat: interactive by default, or one-shot with --prompt."""
    from .commands.chat import run_roundtable, run_chat_repl

    console.print(_status_header())

    # Simple logic: if prompt given, do one-shot; otherwise interactive
    if prompt:
        run_roundtable(
            prompt=prompt,
            multi=multi,
            rounds=rounds,
            timeout_s=timeout_s,
            ollama_host=ollama_host,
            save=save,
            audit=audit,
            presenter_state=presenter_state,
        )
    else:
        # Interactive chat (what most people want)
        run_chat_repl(
            initial_multi=multi,
            rounds=rounds,
            timeout_s=timeout_s,
            ollama_host=ollama_host,
            max_rounds=max_rounds,
            round_window=round_window,
        )


@app.command()
def models(
    action: str = typer.Argument("list", help="list|pull"),
    models: Optional[str] = typer.Option(
        None, "--models", help="Comma-separated model tags to pull"
    ),
    all: bool = typer.Option(
        False, "--all", help="Pull a default set of useful models"
    ),
    provider: str = typer.Option(
        "ollama", "--provider", help="Provider to list (ollama|openai|anthropic|google)"
    ),
    refresh: bool = typer.Option(
        False, "--refresh", help="Force refresh cached list (cloud providers)"
    ),
    ollama_host: Optional[str] = typer.Option(
        None, "--ollama-host", help="Ollama base URL (default http://127.0.0.1:11435)"
    ),
) -> None:
    """List or pull models (ollama) and show provider listings."""
    from .commands.models import list_models, pull_models, list_provider_models

    if action == "list":
        # For ollama, maintain legacy behavior when provider not specified
        if provider == "ollama":
            list_models(ollama_host)
        else:
            list_provider_models(provider, refresh=refresh, ollama_host=ollama_host)
    elif action == "pull":
        ids = [m.strip() for m in (models.split(",") if models else []) if m.strip()]
        pull_models(ollama_host, ids, use_default=all)
    else:
        raise SystemExit("Unknown action. Use: list|pull")


@app.command()
def pr(
    action: str = typer.Argument(..., help="prepare|link"),
    message: Optional[str] = typer.Option(
        None, "-m", "--message", help="Commit message (for prepare)"
    ),
    files: Optional[str] = typer.Option(
        None, "--files", help="Comma-separated globs to stage (for prepare)"
    ),
    branch: Optional[str] = typer.Option(
        None, "--branch", help="Feature branch name (for prepare)"
    ),
    target: Optional[str] = typer.Option(
        None, "--target", help="Target branch, defaults to repo default"
    ),
    remote: str = typer.Option("origin", "--remote", help="Remote name"),
    signoff: bool = typer.Option(
        False, "--signoff", help="Add Signed-off-by to commit"
    ),
) -> None:
    """Prepare a PR (commit+push+URL) or print the PR link for the current branch."""
    from .commands.pr import prepare as pr_prepare, link as pr_link

    if action == "prepare":
        if not message:
            raise SystemExit("--message is required for prepare")
        pr_prepare(
            message=message,
            files=files,
            branch=branch,
            target=target,
            remote=remote,
            signoff=signoff,
        )
    elif action == "link":
        pr_link(target=target, remote=remote)
    else:
        raise SystemExit("Unknown action. Use: prepare|link")


@app.command()
def init(
    ollama_host: Optional[str] = typer.Option(
        None, "--ollama-host", help="Write actcli.toml with this Ollama host"
    ),
) -> None:
    """Create actcli.toml with defaults in the current directory."""
    from .commands.init import run_init

    run_init(ollama_host=ollama_host)


@app.command()
def mcp(
    action: str = typer.Argument(
        "list", help="list|add|on|off|test|log|reload|restart"
    ),
    name: Optional[str] = typer.Argument(
        None, help="Server name for actions that require it"
    ),
    url: Optional[str] = typer.Option(None, "--url", help="Server URL (for add)"),
    group: Optional[str] = typer.Option(None, "--group", help="Group label (for add)"),
    desc: Optional[str] = typer.Option(None, "--desc", help="Description (for add)"),
    enable: Optional[bool] = typer.Option(
        None, "--enable", help="Enable/disable (for log)"
    ),
) -> None:
    """Manage MCP servers: list/add/on/off/test/log/reload/restart."""
    from .commands.mcp import (
        mcp_list,
        mcp_add,
        mcp_on_off,
        mcp_log,
        mcp_test,
        mcp_reload,
        mcp_restart,
    )

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
def providers(
    action: str = typer.Argument("doctor", help="doctor|login"),
    provider: Optional[str] = typer.Argument(
        None, help="codex_cli|claude_cli (for login)"
    ),
) -> None:
    """Inspect CLI-backed providers or launch their login flows."""
    from .commands.providers import providers_doctor
    from .commands.auth import run_auth

    if action == "doctor":
        providers_doctor()
        return
    if action == "login":
        if provider not in ("codex_cli", "claude_cli"):
            raise SystemExit("providers login <codex_cli|claude_cli>")
        run_auth(action="login", provider=provider, method=None)
        return
    raise SystemExit("Unknown action. Use: doctor|login")


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


@app.command()
def server(
    action: str = typer.Argument("start", help="start|status|stop|logs|restart"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(7530, "--port"),
    reload: bool = typer.Option(True, "--reload/--no-reload"),
    with_ui: bool = typer.Option(True, "--with-ui/--no-ui"),
    tail: bool = typer.Option(False, "--tail", help="Tail logs (for logs action)"),
    force: bool = typer.Option(
        False, "--force", help="On start: stop any prior pid and clean stale pid file"
    ),
) -> None:
    """Control the Semhost server (FastAPI)."""
    from .commands.server import server_start, server_status, server_stop, server_logs

    if action == "start":
        server_start(host=host, port=port, reload=reload, with_ui=with_ui, force=force)
    elif action == "status":
        server_status(host=host, port=port)
    elif action == "stop":
        server_stop()
    elif action == "logs":
        server_logs(tail=tail)
    elif action == "restart":
        server_stop()
        server_start(host=host, port=port, reload=reload, with_ui=with_ui, force=True)
    else:
        raise SystemExit("Unknown action. Use: start|status|stop|logs|restart")


@app.command()
def spa(action: str = typer.Argument("dev", help="dev|build|preview|stop")) -> None:
    """Manage the SPA (dev server/build). Single, predictable port (5173)."""
    import shutil
    import subprocess
    import os
    import signal
    import time
    from pathlib import Path as _P

    OUT = _P("out")
    OUT.mkdir(parents=True, exist_ok=True)
    PID = OUT / "spa.pid"
    LOG = OUT / "spa.log"

    def _stop() -> None:
        if not PID.exists():
            console.print("SPA: no pid file; nothing to stop.")
            return
        pid_s = PID.read_text().strip()
        try:
            pid = int(pid_s)
        except Exception:
            console.print(f"SPA: invalid pid in {PID}: {pid_s}")
            PID.unlink(missing_ok=True)
            return
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.3)
        except Exception as e:
            console.print(f"SPA: failed to stop pid={pid}: {e}")
        PID.unlink(missing_ok=True)
        console.print("SPA: stopped.")

    if action == "stop":
        _stop()
        return

    if action == "dev":
        if not shutil.which("npm"):
            raise SystemExit("npm not found; install Node.js to run SPA dev server")
        # Stop any previous dev server to avoid port guessing
        if PID.exists():
            _stop()
        with LOG.open("ab", buffering=0) as log:
            p = subprocess.Popen(
                ["npm", "run", "dev", "--prefix", "studio"], stdout=log, stderr=log
            )
        PID.write_text(str(p.pid), encoding="utf-8")
        console.print(
            "SPA dev server starting at http://127.0.0.1:5173 (logs: out/spa.log)"
        )
    elif action == "build":
        if not shutil.which("npm"):
            raise SystemExit("npm not found; install Node.js to build SPA")
        subprocess.check_call(
            ["npm", "run", "build", "--prefix", "studio"]
        )  # blocking build
        console.print("Built SPA to studio/dist. Semhost will serve it at /ui.")
    elif action == "preview":
        if not shutil.which("npm"):
            raise SystemExit("npm not found; install Node.js to preview SPA")
        # Stop any previous preview/dev server
        if PID.exists():
            _stop()
        with LOG.open("ab", buffering=0) as log:
            p = subprocess.Popen(
                ["npm", "run", "preview", "--prefix", "studio"], stdout=log, stderr=log
            )
        PID.write_text(str(p.pid), encoding="utf-8")
        console.print(
            "SPA preview server starting (defaults to 5173). Logs: out/spa.log"
        )
    else:
        raise SystemExit("Unknown action. Use: dev|build|preview|stop")


@app.command()
def excel(
    action: str = typer.Argument("explore", help="explore"),
    workbook: str = typer.Argument(..., help="Path to .xlsx/.xlsm (no execution)"),
    out: Optional[str] = typer.Option(
        None, "--out", help="Write JSON report to path (e.g., out/excel/explorer.json)"
    ),
) -> None:
    """Excel Explorer — inspect workbooks safely without executing macros."""
    if action != "explore":
        raise SystemExit("Unknown action. Use: explore")
    try:
        from .excel.explorer import (
            inspect_workbook,
            write_report_json,
            ExcelDepsMissing,
        )

        payload = inspect_workbook(workbook)
        if out:
            out_path = Path(out)
            write_report_json(payload, out_path)
            console.print(f"Wrote explorer report to: {out_path}")
        else:
            console.print_json(data=payload)
    except ExcelDepsMissing as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(2)
    except FileNotFoundError:
        console.print(f"[red]Workbook not found: {workbook}[/red]")
        raise SystemExit(2)


@app.command()
def demo(
    scenario: str = typer.Argument(..., help="Demo scenario name (e.g., pricing-rnd)"),
    out: str = typer.Option(
        "out/evaluation/pricing-rnd",
        "--out",
        help="Output directory for evaluation kit",
    ),
) -> None:
    """Run an offline, deterministic evaluation-kit demo (no cloud keys, no network)."""
    from .commands.demo import run_demo

    run_demo(scenario=scenario, out=out)


def main() -> None:
    app()
