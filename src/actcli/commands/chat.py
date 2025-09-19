from __future__ import annotations

import asyncio
from typing import List
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

from ..seminar.adapters.echo import EchoAdapter
from ..seminar.adapters.ollama import OllamaAdapter
from ..seminar.adapters.openai import OpenAIAdapter
from ..seminar.adapters.anthropic import AnthropicAdapter
from ..seminar.adapters.gemini import GeminiAdapter
from ..seminar.coordinator import run_round, TurnResult
from ..seminar.synthesizer import summarize
from ..transcript import write_transcript_md, write_audit_json, write_presenter_state
from ..policy import Policy, merge_policy


console = Console()


def _resolve_adapters(multi: str, ollama_host: str | None = None, allow_cloud: bool = True):
    ids = [x.strip() for x in multi.split(",") if x.strip()]
    adapters = []
    for i in ids:
        # Local models via Ollama if available; otherwise echo fallback
        if i.startswith("llama") or i.startswith("mistral") or i.startswith("qwen") or ":" in i:
            try:
                adapters.append(OllamaAdapter(model=i, host=ollama_host))
                continue
            except Exception:
                # Fallback to echo if Ollama not reachable
                pass
        # Cloud placeholders for now
        if i == "gpt" and allow_cloud:
            try:
                adapters.append(OpenAIAdapter())
                continue
            except Exception:
                adapters.append(EchoAdapter(name="gpt(cloud)"))
                continue
        if i == "claude" and allow_cloud:
            try:
                adapters.append(AnthropicAdapter())
                continue
            except Exception:
                adapters.append(EchoAdapter(name="claude(cloud)"))
                continue
        if i == "gemini" and allow_cloud:
            try:
                adapters.append(GeminiAdapter())
                continue
            except Exception:
                adapters.append(EchoAdapter(name="gemini(cloud)"))
                continue
        adapters.append(EchoAdapter(name=i))
    return adapters


def _render_results(title: str, results: List[TurnResult]):
    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Latency")
    table.add_column("Text/Status", style="white")
    for r in results:
        status = r.text if r.text else f"[red]{r.error or 'no output'}[/red]"
        table.add_row(r.info.name, f"{r.latency_ms} ms", status)
    console.print(Panel(table, border_style="cyan"))


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
    adapters = _resolve_adapters(multi, ollama_host=ollama_host, allow_cloud=policy.cloud_share)
    if not policy.cloud_share and any(not getattr(a, "is_local", True) for a in adapters):
        console.print("[yellow]Cloud sharing disabled by policy; using local adapters only.[/yellow]")
        adapters = [a for a in adapters if getattr(a, "is_local", True)]
    if not prompt:
        prompt = "Compare two reserving strategies and highlight trade-offs."

    # Round 1
    r1 = asyncio.run(run_round(adapters, prompt, seed=42, timeout_s=timeout_s, round_index=1))
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
        r2 = asyncio.run(run_round(adapters, prompt, seed=42, timeout_s=timeout_s, round_index=2, context_snippets=quoted))
        _render_results("Round 2 — critique & next checks", r2)
        syn, disagree = summarize(r2)
        console.print(Panel(f"{syn}\nDisagreement score: {disagree}", title="Synthesis", border_style="magenta"))
        final_results = r2

    # Save transcript/audit if requested
    if save:
        write_transcript_md(Path(save), header="Roundtable", prompt=prompt, results=final_results, synthesis=syn)
        console.print(f"Saved transcript to {save}")
    if audit:
        write_audit_json(Path(audit), prompt=prompt, results=final_results, disagreement=disagree)
        console.print(f"Saved audit to {audit}")
    if presenter_state:
        write_presenter_state(Path(presenter_state), prompt=prompt, results=final_results, synthesis=syn, disagreement=disagree)


def run_chat_repl(initial_multi: str, rounds: int, timeout_s: int, ollama_host: str | None = None) -> None:
    """A minimal REPL supporting slash commands."""
    models: list[str] = [x.strip() for x in initial_multi.split(",") if x.strip()] or ["llama3", "claude", "gpt"]
    policy: Policy = merge_policy()
    last_prompt: str | None = None
    last_results: list[TurnResult] | None = None
    last_syn: str | None = None
    last_disagree: float | None = None
    console.print(Panel("Type a prompt to run the roundtable, or /help for commands.", title="Chat REPL", border_style="cyan"))

    def show_models():
        console.print(Panel("\n".join(models) or "(none)", title="Attending Models", border_style="cyan"))

    def show_help():
        lines = [
            "/help                Show this help",
            "/models              List attending models",
            "/attending_models    Alias for /models",
            "/models add <id>     Add a model (e.g., codellama:34b)",
            "/models remove <id>  Remove a model",
            "/rounds <n>          Set rounds (1-3)",
            "/ollama <url>        Set Ollama host (e.g., http://127.0.0.1:11435)",
            "/save <path> [audit <path>] Save transcript (and optional audit)",
            "/trust status|allow-here|allow-once|revoke",
            "/allow read|write <glob>",
            "/deny read|write <glob>",
            "/share cloud on|off",
            "/quit | /exit        Leave REPL",
        ]
        console.print(Panel("\n".join(lines), title="Commands", border_style="cyan"))

    show_help()
    while True:
        # Top divider (Claude-style cue)
        console.print(Rule(style="grey50"))
        try:
            line = input("actcli> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nExiting.")
            break
        if not line:
            continue
        if line.startswith("/"):
            parts = line.split()
            cmd = parts[0].lower()
            args = parts[1:]
            if cmd in ("/quit", "/exit"):
                break
            if cmd in ("/help",):
                show_help()
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
                    write_transcript_md(Path(out_path), header="Roundtable(REPL)", prompt=last_prompt, results=last_results, synthesis=last_syn)
                    if audit_path is not None:
                        write_audit_json(Path(audit_path), prompt=last_prompt, results=last_results, disagreement=last_disagree)
                    console.print(f"Saved transcript to {out_path}" + (f" and audit to {audit_path}" if audit_path else ""))
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
                    policy.cloud_share = (val == "on")
                    console.print(f"Cloud sharing {'enabled' if policy.cloud_share else 'disabled'}")
                else:
                    console.print("Usage: /share cloud on|off")
                continue
            console.print("Unknown command. Type /help.")
            continue

        # Treat as a prompt; run with current models
        multi = ",".join(models)
        # Run and capture minimal state for /save
        adapters = _resolve_adapters(multi, ollama_host=ollama_host, allow_cloud=policy.cloud_share)
        if not policy.cloud_share and any(not getattr(a, "is_local", True) for a in adapters):
            console.print("[yellow]Cloud sharing disabled by policy; using local adapters only.[/yellow]")
            adapters = [a for a in adapters if getattr(a, "is_local", True)]
        r1 = asyncio.run(run_round(adapters, line, seed=42, timeout_s=timeout_s, round_index=1))
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
            r2 = asyncio.run(run_round(adapters, line, seed=42, timeout_s=timeout_s, round_index=2, context_snippets=quoted))
            _render_results("Round 2 — critique & next checks", r2)
            syn, disagree = summarize(r2)
            console.print(Panel(f"{syn}\nDisagreement score: {disagree}", title="Synthesis", border_style="magenta"))
            final_results = r2
        last_prompt, last_results, last_syn, last_disagree = line, final_results, syn, disagree
        # Presenter auto-update if configured via env
        state_path = os.environ.get("ACTCLI_PRESENTER_STATE")
        if state_path:
            try:
                write_presenter_state(Path(state_path), prompt=line, results=final_results, synthesis=syn, disagreement=disagree)
                console.print(f"[dim]Presenter updated: {state_path}[/dim]")
            except Exception:
                pass
        # Bottom divider with hint
        console.print(Rule(style="grey50"))
        console.print("? for shortcuts", style="bright_black")
