from __future__ import annotations

import asyncio
from typing import List
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import httpx

from ..seminar.adapters.echo import EchoAdapter
from ..seminar.coordinator import run_round, TurnResult
from ..seminar.synthesizer import summarize
from ..seminar.rounds import RoundOrchestrator
from ..seminar.moods import resolve_mood, apply_mood
from ..transcript import write_transcript_md, write_audit_json, write_presenter_state
from ..policy import Policy, merge_policy
from ..ui.select import select_one
from ..mcp.config import load_mcp_config, save_project_mcp_config
from ..models.participant import parse_participant_spec
from ..seminar.factory import AdapterFactory


console = Console()


def _resolve_adapters(
    multi: str, ollama_host: str | None = None, allow_cloud: bool = True
):
    ids = [x.strip() for x in multi.split(",") if x.strip()]
    adapters = []
    for tok in ids:
        try:
            spec = parse_participant_spec(tok, default_ollama_host=ollama_host)
        except Exception:
            # Fallback to legacy echo participant
            adapters.append(EchoAdapter(name=tok))
            continue
        a = AdapterFactory.from_spec(spec, allow_cloud=allow_cloud)
        adapters.append(a)
    return adapters


def _render_results(title: str, results: List[TurnResult]):
    """Render model responses in a clean, professional format inspired by Claude CLI."""
    from ..ui.layout import CLILayout

    layout = CLILayout()

    # Use the enhanced grid rendering
    response_panel = layout.render_model_responses_grid(results)
    console.print(response_panel)

    # Add a clean separator for readability
    console.print()
    layout.render_conversation_separator()


def run_roundtable(
    prompt: str,
    multi: str,
    rounds: int,
    timeout_s: int,
    ollama_host: str | None = None,
    save: str | None = None,
    audit: str | None = None,
    presenter_state: str | None = None,
) -> None:
    policy = merge_policy()
    adapters = _resolve_adapters(
        multi, ollama_host=ollama_host, allow_cloud=policy.cloud_share
    )
    if not policy.cloud_share and any(
        not getattr(a, "is_local", True) for a in adapters
    ):
        console.print(
            "[yellow]Cloud sharing disabled by policy; using local adapters only.[/yellow]"
        )
        adapters = [a for a in adapters if getattr(a, "is_local", True)]
    if not prompt:
        prompt = "Compare two reserving strategies and highlight trade-offs."

    # Round 1
    r1 = asyncio.run(
        run_round(adapters, prompt, seed=42, timeout_s=timeout_s, round_index=1)
    )
    _render_results("Round 1 — direct answers", r1)

    # Create snippets for critique
    snippets = []
    for res in r1:
        if res.text:
            text = res.text.replace("\n", " ")
            snippets.append(f"{res.info.name}: {text[:220]}")
    quoted = "\n".join(snippets)

    final_results = r1
    syn = None
    disagree = None
    if rounds >= 2:
        r2 = asyncio.run(
            run_round(
                adapters,
                prompt,
                seed=42,
                timeout_s=timeout_s,
                round_index=2,
                context_snippets=quoted,
            )
        )
        _render_results("Round 2 — critique & next checks", r2)
        syn, disagree = summarize(r2)
        console.print(
            Panel(
                f"{syn}\nDisagreement score: {disagree}",
                title="Synthesis",
                border_style="magenta",
                padding=(0, 1),
            )
        )
        final_results = r2

    # Save transcript/audit if requested
    if save:
        write_transcript_md(
            Path(save),
            header="Roundtable",
            prompt=prompt,
            results=final_results,
            synthesis=syn,
        )
        console.print(f"Saved transcript to {save}")
    if audit:
        write_audit_json(
            Path(audit), prompt=prompt, results=final_results, disagreement=disagree
        )
        console.print(f"Saved audit to {audit}")
    if presenter_state:
        write_presenter_state(
            Path(presenter_state),
            prompt=prompt,
            results=final_results,
            synthesis=syn,
            disagreement=disagree,
        )


def run_chat_repl(
    initial_multi: str,
    rounds: int,
    timeout_s: int,
    ollama_host: str | None = None,
    *,
    max_rounds: int | None = None,
    round_window: int = 2,
) -> None:
    """Enhanced REPL with VSCode-style or Claude CLI-style layout."""
    # Check for layout preference
    import os

    layout_style = os.environ.get("ACTCLI_LAYOUT", "vscode")  # vscode, claude, or basic

    try:
        if layout_style == "vscode":
            from ..ui.vscode_layout import create_vscode_actcli

            return run_vscode_style_repl(
                initial_multi,
                rounds,
                timeout_s,
                ollama_host,
                max_rounds=max_rounds,
                round_window=round_window,
            )
        elif layout_style == "claude":
            from ..ui.claude_layout import create_claude_style_repl

            return run_claude_style_repl(
                initial_multi,
                rounds,
                timeout_s,
                ollama_host,
                max_rounds=max_rounds,
                round_window=round_window,
            )
        else:
            return run_basic_repl(initial_multi, rounds, timeout_s, ollama_host)
    except ImportError:
        console.print(
            "[yellow]Advanced layout requires prompt_toolkit. Install with: pip install '.[tui]'[/yellow]"
        )
        console.print("[yellow]Falling back to basic REPL...[/yellow]")
        return run_basic_repl(initial_multi, rounds, timeout_s, ollama_host)


def run_vscode_style_repl(
    initial_multi: str,
    rounds: int,
    timeout_s: int,
    ollama_host: str | None = None,
    max_rounds: int | None = None,
    round_window: int = 2,
) -> None:
    """VSCode-style REPL with sidebar and multi-model integration."""
    from ..ui.vscode_layout import create_vscode_actcli

    models: list[str] = [x.strip() for x in initial_multi.split(",") if x.strip()] or [
        "llama3",
        "claude",
        "gpt",
    ]
    policy: Policy = merge_policy()

    # Unlimited rounds scaffold: orchestrator prepared but not yet driving execution
    orchestrator = RoundOrchestrator(window_k=round_window, max_rounds=max_rounds)
    last_prompt: str = ""

    adapters: list = []

    def handle_input(text: str) -> str:
        """Handle user input and return response."""
        try:
            nonlocal adapters
            if not adapters:
                multi = ",".join(models)
                adapters = _resolve_adapters(
                    multi, ollama_host=ollama_host, allow_cloud=policy.cloud_share
                )
                if not policy.cloud_share and any(
                    not getattr(a, "is_local", True) for a in adapters
                ):
                    adapters = [a for a in adapters if getattr(a, "is_local", True)]
                orchestrator.set_participants(
                    {getattr(a, "name", f"p{i}"): a for i, a in enumerate(adapters)}
                )

            # Slash commands (scaffold)
            if text.startswith("/"):
                cmd = text.strip().split()
                if cmd[0] in ("/round",):
                    if len(cmd) == 1 or cmd[1] == "status":
                        r, n, k = orchestrator.round_status()
                        return f"round={r or 0} participants={n} window_k={k}"
                    if cmd[1] == "start":
                        orchestrator.start()
                        # Run current round with last_prompt if available
                        if last_prompt:
                            rr = orchestrator.run_current_round(
                                prompt=last_prompt, seed=42, timeout_s=timeout_s
                            )
                            return _format_rr(rr)
                        r, _, _ = orchestrator.round_status()
                        return f"Started round {r} (enter a prompt to run)"
                    if cmd[1] == "next":
                        # Advance and run next round with last_prompt
                        orchestrator.next_round()
                        if not last_prompt:
                            return "No prompt set. Type a prompt first."
                        rr = orchestrator.run_current_round(
                            prompt=last_prompt, seed=42, timeout_s=timeout_s
                        )
                        return _format_rr(rr)
                    if cmd[1] == "stop":
                        orchestrator.stop()
                        return "Stopped (will not advance further)"
                    if cmd[1] == "max" and len(cmd) >= 3:
                        try:
                            m = max(1, min(100, int(cmd[2])))
                            orchestrator.state.max_rounds = m
                            return f"max_rounds={m}"
                        except Exception:
                            return "Invalid max value"
                    if cmd[1] == "window" and len(cmd) >= 3:
                        try:
                            k = max(0, int(cmd[2]))
                            orchestrator.state.window_k = k
                            return f"window_k={k}"
                        except Exception:
                            return "Invalid window value"
                    return "Unknown /round subcommand"
                if cmd[0] in ("/focus",):
                    if len(cmd) >= 2:
                        aliases = [
                            t.strip()
                            for t in " ".join(cmd[1:]).replace(",", " ").split()
                            if t.strip()
                        ]
                        orchestrator.set_focus_next(aliases)
                        return f"focus next: {', '.join(aliases)}"
                    return "Usage: /focus <alias1,alias2>"
                if cmd[0] in ("/temp",):
                    try:
                        # /temp [alias] <value>
                        if len(cmd) == 2:
                            val = float(cmd[1])
                        for a in adapters:
                            if hasattr(a, "_bound"):
                                a._bound.temperature = val  # type: ignore[attr-defined]
                            return f"temperature={val} (all)"
                        if len(cmd) == 3:
                            alias, val_s = cmd[1], cmd[2]
                            val = float(val_s)
                            for a in adapters:
                                if getattr(a, "name", "").startswith(alias) and hasattr(
                                    a, "_bound"
                                ):
                                    a._bound.temperature = val  # type: ignore[attr-defined]
                            return f"temperature[{alias}]={val}"
                        return "Usage: /temp [alias] <0.0-1.0>"
                    except Exception:
                        return "Invalid temperature"
                if cmd[0] in ("/mood",):
                    if len(cmd) < 2:
                        return "Usage: /mood <preset> | /mood <alias> <preset>"
                    if len(cmd) == 2:
                        mood = resolve_mood(cmd[1])
                        if not mood:
                            return "Unknown mood"
                        for a in adapters:
                            if hasattr(a, "_bound"):
                                a._bound.system = apply_mood(
                                    {"system": getattr(a._bound, "system", "")}, mood
                                )["system"]  # type: ignore[attr-defined]
                                a._bound.temperature = mood.temperature  # type: ignore[attr-defined]
                        return f"mood={mood.name} (all)"
                    if len(cmd) == 3:
                        alias, mname = cmd[1], cmd[2]
                        mood = resolve_mood(mname)
                        if not mood:
                            return "Unknown mood"
                        for a in adapters:
                            if getattr(a, "name", "").startswith(alias) and hasattr(
                                a, "_bound"
                            ):
                                a._bound.system = apply_mood(
                                    {"system": getattr(a._bound, "system", "")}, mood
                                )["system"]  # type: ignore[attr-defined]
                                a._bound.temperature = mood.temperature  # type: ignore[attr-defined]
                        return f"mood[{alias}]={mood.name}"
                if cmd[0] in ("/params",) and len(cmd) >= 2 and cmd[1] == "show":
                    parts = []
                    for a in adapters:
                        seed = getattr(getattr(a, "_bound", None), "seed", None)
                        temp = getattr(getattr(a, "_bound", None), "temperature", None)
                        system = getattr(getattr(a, "_bound", None), "system", "")
                        tmo = getattr(getattr(a, "_bound", None), "timeout_s", None)
                        parts.append(
                            f"{getattr(a, 'name', '?')}: seed={seed} temp={temp} timeout={tmo} system={'yes' if system else 'no'}"
                        )
                    return "\n".join(parts)

            # Non-command input: set prompt and run current round (start if needed)
            last_prompt = text
            # Ensure participants are set (in case prompt arrives first)
            if not adapters:
                multi = ",".join(models)
                adapters = _resolve_adapters(
                    multi, ollama_host=ollama_host, allow_cloud=policy.cloud_share
                )
                if not policy.cloud_share and any(
                    not getattr(a, "is_local", True) for a in adapters
                ):
                    adapters = [a for a in adapters if getattr(a, "is_local", True)]
                orchestrator.set_participants(
                    {getattr(a, "name", f"p{i}"): a for i, a in enumerate(adapters)}
                )
            if orchestrator.state.round_idx == 0:
                orchestrator.start()
            rr = orchestrator.run_current_round(
                prompt=last_prompt, seed=42, timeout_s=timeout_s
            )
            return _format_rr(rr)

        except Exception as e:
            return f"<error>Error: {str(e)}</error>"

    def _format_rr(rr):
        # Format RoundRecord to VSCode-style compact lines
        out = []
        for e in rr.entries:
            preview = (e.text or e.error or "").strip()
            if len(preview) > 150:
                preview = preview[:150] + "..."
            if e.ok and e.text:
                out.append(
                    f"<model-response><model-name>{e.alias}</model-name>: {preview}</model-response>"
                )
            else:
                out.append(
                    f"<error>{e.alias}: Error - {preview or 'no output'}</error>"
                )
        return "\n".join(out)

    # Create and run the VSCode-style CLI
    cli = create_vscode_actcli(on_input=handle_input)
    cli.run()


def run_claude_style_repl(
    initial_multi: str,
    rounds: int,
    timeout_s: int,
    ollama_host: str | None = None,
    *,
    max_rounds: int | None = None,
    round_window: int = 2,
) -> None:
    """Claude CLI-style REPL with proper terminal layout."""
    from ..ui.claude_layout import create_claude_style_repl

    models: list[str] = [x.strip() for x in initial_multi.split(",") if x.strip()] or [
        "llama3",
        "claude",
        "gpt",
    ]
    policy: Policy = merge_policy()
    last_results: list[TurnResult] | None = None

    orchestrator = RoundOrchestrator(window_k=round_window, max_rounds=max_rounds)
    last_prompt: str = ""

    def handle_input(text: str) -> str:
        nonlocal last_results, policy

        if text.startswith("/"):
            # Handle slash commands
            if text in ("/quit", "/exit"):
                import sys

                sys.exit(0)
            elif text in ("/help", "/?"):
                return "Commands: /models, /rounds, /save, /trust, /share, /mcp, /quit"
            elif text == "/models":
                return f"Current models: {', '.join(models)}"
            elif text.startswith("/round"):
                cmd = text.split()
                if len(cmd) == 1 or cmd[1] == "status":
                    r, n, k = orchestrator.round_status()
                    return f"round={r or 0} participants={n} window_k={k}"
                if cmd[1] == "start":
                    orchestrator.start()
                    if last_prompt:
                        rr = orchestrator.run_current_round(
                            prompt=last_prompt, seed=42, timeout_s=timeout_s
                        )
                        return _format_rr_plain(rr)
                    r, _, _ = orchestrator.round_status()
                    return f"Started round {r} (enter a prompt to run)"
                if cmd[1] == "next":
                    orchestrator.next_round()
                    if not last_prompt:
                        return "No prompt set. Type a prompt first."
                    rr = orchestrator.run_current_round(
                        prompt=last_prompt, seed=42, timeout_s=timeout_s
                    )
                    return _format_rr_plain(rr)
                if cmd[1] == "stop":
                    orchestrator.stop()
                    return "Stopped"
                return "Unknown /round subcommand"
            elif (
                text.startswith("/temp")
                or text.startswith("/mood")
                or text.startswith("/params")
            ):
                return "Use /params show, /temp [alias] <val>, /mood [alias] <preset> (vscode layout provides detailed echo)"
            else:
                return f"Command '{text}' not yet implemented in layout mode"

        # Handle regular prompts
        try:
            multi = ",".join(models)
            adapters = _resolve_adapters(
                multi, ollama_host=ollama_host, allow_cloud=policy.cloud_share
            )
            if not policy.cloud_share and any(
                not getattr(a, "is_local", True) for a in adapters
            ):
                adapters = [a for a in adapters if getattr(a, "is_local", True)]

            # Non-command input: set prompt and orchestrate rounds
            last_prompt = text
            orchestrator.set_participants(
                {getattr(a, "name", f"p{i}"): a for i, a in enumerate(adapters)}
            )
            if orchestrator.state.round_idx == 0:
                orchestrator.start()
            rr = orchestrator.run_current_round(
                prompt=last_prompt, seed=42, timeout_s=timeout_s
            )
            last_results = None
            return _format_rr_plain(rr)

        except Exception as e:
            return f"Error: {str(e)}"

    def get_status() -> str:
        mode = "HYBRID" if policy.cloud_share else "OFFLINE"
        return f"ActCLI • chat(seminar) • MODE: {mode} • participants: {', '.join(models)} • audit: ON"

    def _format_rr_plain(rr):
        lines = []
        for e in rr.entries:
            if e.ok and e.text:
                t = e.text
                if len(t) > 200:
                    t = t[:200] + "..."
                lines.append(f"{e.alias}: {t}")
            else:
                msg = e.error or "no output"
                lines.append(f"{e.alias}: [Error: {msg}]")
        return "\n".join(lines)

    # Create and run the CLI
    cli = create_claude_style_repl(on_input=handle_input, get_status=get_status)
    cli.run()


def run_basic_repl(
    initial_multi: str, rounds: int, timeout_s: int, ollama_host: str | None = None
) -> None:
    """Fallback basic REPL for when prompt_toolkit is not available."""
    models: list[str] = [x.strip() for x in initial_multi.split(",") if x.strip()] or [
        "llama3",
        "claude",
        "gpt",
    ]
    policy: Policy = merge_policy()
    last_prompt: str | None = None
    last_results: list[TurnResult] | None = None
    last_syn: str | None = None
    last_disagree: float | None = None
    console.print(
        "[bright_black]Type /help (or /?) for commands; enter a prompt to run.[/bright_black]"
    )
    console.print("")

    def show_models():
        console.print(
            Panel(
                "\n".join(models) or "(none)",
                title="Attending Models",
                border_style="cyan",
                padding=(0, 1),
            )
        )

    def _commands_catalog() -> list[tuple[str, str]]:
        return [
            ("/help", "Show this help"),
            ("/models list", "List attending models"),
            ("/models add", "Add a model (pick from local tags)"),
            ("/models remove", "Remove a model (pick from current)"),
            ("/rounds", "Set rounds (1-3)"),
            ("/ollama", "Set Ollama host (enter URL)"),
            ("/save", "Save transcript (and optional audit)"),
            ("/trust status", "Show trust info"),
            ("/trust allow-here", "Trust this folder (persist)"),
            ("/trust allow-once", "Trust this folder (session)"),
            ("/trust revoke", "Revoke trust for this folder"),
            ("/share cloud on", "Enable cloud sharing"),
            ("/share cloud off", "Disable cloud sharing"),
            ("/mcp ui", "Manage MCP servers"),
            ("/quit", "Leave REPL"),
        ]

    def show_suggestions(prefix: str):
        items = [
            (cmd, desc) for cmd, desc in _commands_catalog() if cmd.startswith(prefix)
        ]
        if not items:
            return console.print("[bright_black]No suggestions.[/bright_black]")
        grid = Table.grid(padding=(0, 2))
        for cmd, desc in items:
            grid.add_row(cmd, desc)
        console.print(grid)

    def pick_and_execute(prefix: str) -> None:
        nonlocal rounds, ollama_host, policy
        items = [
            (cmd, desc) for cmd, desc in _commands_catalog() if cmd.startswith(prefix)
        ]
        if not items:
            show_suggestions(prefix)
            return
        choice = select_one(items, title="Commands")
        if not choice:
            return
        toks = choice.split()
        base = toks[0]
        sub = toks[1:] if len(toks) > 1 else []
        if base == "/help":
            show_help()
            return
        if base == "/quit":
            running = False
            return
        if base == "/models":
            if sub and sub[0] == "list":
                show_models()
                return
            if sub and sub[0] == "add":
                tags = list_local_model_tags(ollama_host)
                tag = select_one(tags, title="Add model") if tags else None
                if tag and tag not in models:
                    models.append(tag)
                    show_models()
                elif not tags:
                    console.print(
                        "[bright_black]No local models detected or host unreachable.[/bright_black]"
                    )
                return
            if sub and sub[0] == "remove":
                if not models:
                    console.print("[bright_black]No models to remove.")
                    return
                tag = select_one(models, title="Remove model")
                if tag:
                    models[:] = [m for m in models if m != tag]
                    show_models()
                return
        if base == "/rounds":
            r = select_one(["1", "2", "3"], title="Rounds")
            if r and r.isdigit():
                val = int(r)
                if 1 <= val <= 3:
                    rounds = val
                    console.print(f"Rounds set to {rounds}")
            return
        if base == "/ollama":
            url = input("Ollama URL: ").strip()
            if url:
                ollama_host = url
                console.print(f"Ollama host set to {ollama_host}")
            return
        if base == "/save":
            out_path = input("Transcript path (e.g., out/seminar.md): ").strip()
            audit_path = input("Audit path (optional): ").strip()
            if last_results and last_prompt and out_path:
                write_transcript_md(
                    Path(out_path),
                    header="Roundtable(REPL)",
                    prompt=last_prompt,
                    results=last_results,
                    synthesis=last_syn,
                )
                if audit_path:
                    write_audit_json(
                        Path(audit_path),
                        prompt=last_prompt,
                        results=last_results,
                        disagreement=last_disagree,
                    )
                console.print(
                    f"Saved transcript to {out_path}"
                    + (f" and audit to {audit_path}" if audit_path else "")
                )
            else:
                console.print("Nothing to save yet; run a prompt first.")
            return
        if base == "/trust":
            from .trust import run_trust as trust_cli

            subcmd = sub[0] if sub else "status"
            trust_cli(action=subcmd, scope=None, cloud_share=None)
            nonlocal policy
            policy = merge_policy()
            return
        if base == "/share":
            if sub and sub[0] == "cloud" and len(sub) > 1 and sub[1] in ("on", "off"):
                policy.cloud_share = sub[1] == "on"
                console.print(
                    f"Cloud sharing {'enabled' if policy.cloud_share else 'disabled'}"
                )
            else:
                console.print("Usage: /share cloud on|off")
            return
        if base == "/mcp" and sub and sub[0] == "ui":
            cfg = load_mcp_config()
            items2 = []
            for name, s in cfg.servers.items():
                status = "on" if s.enabled else "off"
                items2.append((name, f"{status}  •  {s.url}"))
            sel = select_one(items2, title="MCP Servers (Enter toggles on/off)")
            if sel and sel in cfg.servers:
                srv = cfg.servers[sel]
                srv.enabled = not srv.enabled
                save_project_mcp_config(cfg)
                console.print(f"{sel}: {'enabled' if srv.enabled else 'disabled'}")
            return

    def list_local_model_tags(host: str | None) -> list[str]:
        if not host:
            return []
        try:
            with httpx.Client(timeout=3.0) as client:
                r = client.get(f"{host.rstrip('/')}/api/tags")
                r.raise_for_status()
                data = r.json() or {}
                return [
                    m.get("name", "") for m in data.get("models", []) if m.get("name")
                ]
        except Exception:
            return []

    def show_help():
        grid = Table.grid(padding=(0, 3))
        for cmd, desc in _commands_catalog():
            grid.add_row(cmd, desc)
        console.print(
            Panel(grid, title="Commands", border_style="cyan", padding=(0, 1))
        )

    from ..ui.layout import (
        print_persistent_header,
        print_input_prompt_area,
        enhanced_input_with_status,
    )

    show_help()
    while True:
        # Claude CLI-style persistent header
        print_persistent_header(
            mode=policy.cloud_share and "HYBRID" or "OFFLINE", models=models, audit=True
        )

        # Clean input area with proper spacing
        print_input_prompt_area()

        try:
            # Enhanced input with status awareness (no visible prompt like Claude CLI)
            status_info = (
                f"Models: {', '.join(models)} • Rounds: {rounds} • /? for help"
            )
            line = enhanced_input_with_status("", status_info)
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Exiting...[/dim]")
            break
        if not line:
            continue
        if line.startswith("/"):
            parts = line.split()
            cmd = parts[0].lower()
            args = parts[1:]
            if cmd in ("/quit", "/exit"):
                break
            if cmd in ("/help", "/?"):
                # Arrow-key command palette
                choice = select_one(_commands_catalog(), title="Commands")
                if choice:
                    # Map selection to quick actions
                    if choice == "/models":
                        show_models()
                    elif choice.startswith("/models add"):
                        tags = list_local_model_tags(ollama_host)
                        tag = select_one(tags, title="Add model") if tags else None
                        if tag:
                            if tag not in models:
                                models.append(tag)
                            show_models()
                    elif choice == "/rounds <n>":
                        console.print("Usage: /rounds <1-3>")
                    elif choice == "/ollama <url>":
                        console.print("Usage: /ollama http://127.0.0.1:11435")
                    elif choice.startswith("/save"):
                        console.print(
                            "Usage: /save out/seminar.md audit out/audit.json"
                        )
                    else:
                        console.print(f"Selected: {choice}")
                continue
            if cmd in ("/models", "/attending_models"):
                show_models()
                continue
            if cmd == "/models" and args:
                sub = args[0].lower()
                if sub == "add" and len(args) >= 2:
                    mid = args[1]
                    if mid not in models:
                        models.append(mid)
                    show_models()
                elif sub == "remove" and len(args) >= 2:
                    mid = args[1]
                    models[:] = [m for m in models if m != mid]
                    show_models()
                elif sub == "add" and len(args) == 1:
                    tags = list_local_model_tags(ollama_host)
                    tag = select_one(tags, title="Add model") if tags else None
                    if tag:
                        if tag not in models:
                            models.append(tag)
                        show_models()
                    elif not tags:
                        console.print(
                            "[bright_black]No local models detected or host unreachable.[/bright_black]"
                        )
                else:
                    console.print("Usage: /models add <id> | /models remove <id>")
                continue
            if cmd == "/rounds" and args:
                try:
                    r = int(args[0])
                    if 1 <= r <= 3:
                        rounds = r
                        console.print(f"Rounds set to {rounds}")
                    else:
                        console.print("Rounds must be 1-3")
                except ValueError:
                    console.print("Usage: /rounds <n>")
                continue
            if cmd == "/ollama" and args:
                ollama_host = args[0]
                console.print(f"Ollama host set to {ollama_host}")
                continue
            if cmd == "/save" and args:
                out_path = args[0]
                audit_path = None
                if len(args) >= 3 and args[1].lower() == "audit":
                    audit_path = args[2]
                if last_results and last_prompt:
                    write_transcript_md(
                        Path(out_path),
                        header="Roundtable(REPL)",
                        prompt=last_prompt,
                        results=last_results,
                        synthesis=last_syn,
                    )
                    if audit_path is not None:
                        write_audit_json(
                            Path(audit_path),
                            prompt=last_prompt,
                            results=last_results,
                            disagreement=last_disagree,
                        )
                    console.print(
                        f"Saved transcript to {out_path}"
                        + (f" and audit to {audit_path}" if audit_path else "")
                    )
                else:
                    console.print("Nothing to save yet; run a prompt first.")
                continue
            if cmd == "/trust":
                from .trust import run_trust as trust_cli

                sub = args[0] if args else "status"
                trust_cli(action=sub, scope=None, cloud_share=None)
                policy = merge_policy()
                continue
            if cmd == "/allow" and len(args) >= 2:
                kind = args[0].lower()
                glob = args[1]
                if kind == "read":
                    policy.allow_read(glob)
                elif kind == "write":
                    policy.allow_write(glob)
                else:
                    console.print("Usage: /allow read|write <glob>")
                continue
            if cmd == "/deny" and len(args) >= 2:
                kind = args[0].lower()
                glob = args[1]
                if kind in ("read", "write"):
                    policy.deny(kind, glob)
                else:
                    console.print("Usage: /deny read|write <glob>")
                continue
            if cmd == "/share" and len(args) >= 2 and args[0].lower() == "cloud":
                val = args[1].lower()
                if val in ("on", "off"):
                    policy.cloud_share = val == "on"
                    console.print(
                        f"Cloud sharing {'enabled' if policy.cloud_share else 'disabled'}"
                    )
                else:
                    console.print("Usage: /share cloud on|off")
                continue
            if cmd == "/mcp" and len(args) >= 1 and args[0].lower() == "ui":
                cfg = load_mcp_config()
                items = []
                for name, s in cfg.servers.items():
                    status = "on" if s.enabled else "off"
                    items.append((name, f"{status}  •  {s.url}"))
                choice = select_one(items, title="MCP Servers (Enter toggles on/off)")
                if choice and choice in cfg.servers:
                    srv = cfg.servers[choice]
                    srv.enabled = not srv.enabled
                    save_project_mcp_config(cfg)
                    console.print(
                        f"{choice}: {'enabled' if srv.enabled else 'disabled'}"
                    )
                continue
            # Intellisense-style picker: select command (and subcommand) with arrows
            pick_and_execute(cmd)
            continue

        # Treat as a prompt; run with current models
        multi = ",".join(models)
        # Run and capture minimal state for /save
        adapters = _resolve_adapters(
            multi, ollama_host=ollama_host, allow_cloud=policy.cloud_share
        )
        if not policy.cloud_share and any(
            not getattr(a, "is_local", True) for a in adapters
        ):
            console.print(
                "[yellow]Cloud sharing disabled by policy; using local adapters only.[/yellow]"
            )
            adapters = [a for a in adapters if getattr(a, "is_local", True)]
        r1 = asyncio.run(
            run_round(adapters, line, seed=42, timeout_s=timeout_s, round_index=1)
        )
        _render_results("Round 1 — direct answers", r1)
        snippets = []
        for res in r1:
            if res.text:
                text = res.text.replace("\n", " ")
                snippets.append(f"{res.info.name}: {text[:220]}")
        quoted = "\n".join(snippets)
        final_results = r1
        syn = None
        disagree = None
        if rounds >= 2:
            r2 = asyncio.run(
                run_round(
                    adapters,
                    line,
                    seed=42,
                    timeout_s=timeout_s,
                    round_index=2,
                    context_snippets=quoted,
                )
            )
            _render_results("Round 2 — critique & next checks", r2)
            syn, disagree = summarize(r2)
            console.print(
                Panel(
                    f"{syn}\nDisagreement score: {disagree}",
                    title="Synthesis",
                    border_style="magenta",
                )
            )
            final_results = r2
        last_prompt, last_results, last_syn, last_disagree = (
            line,
            final_results,
            syn,
            disagree,
        )
        # Presenter auto-update if configured via env
        state_path = os.environ.get("ACTCLI_PRESENTER_STATE")
        if state_path:
            try:
                write_presenter_state(
                    Path(state_path),
                    prompt=line,
                    results=final_results,
                    synthesis=syn,
                    disagreement=disagree,
                )
                console.print(f"[dim]Presenter updated: {state_path}[/dim]")
            except Exception:
                pass
        # Keep output area clean; no bottom divider to avoid visual confusion
