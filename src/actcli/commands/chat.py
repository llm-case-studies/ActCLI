from __future__ import annotations

import asyncio
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..seminar.adapters.echo import EchoAdapter
from ..seminar.adapters.ollama import OllamaAdapter
from ..seminar.coordinator import run_round, TurnResult
from ..seminar.synthesizer import summarize


console = Console()


def _resolve_adapters(multi: str, ollama_host: str | None = None):
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
        name = {
            "claude": "claude(cloud)",
            "gpt": "gpt(cloud)",
            "gemini": "gemini(cloud)",
        }.get(i, i)
        adapters.append(EchoAdapter(name=name))
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


def run_roundtable(prompt: str, multi: str, rounds: int, timeout_s: int, ollama_host: str | None = None) -> None:
    adapters = _resolve_adapters(multi, ollama_host=ollama_host)
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

    if rounds >= 2:
        r2 = asyncio.run(run_round(adapters, prompt, seed=42, timeout_s=timeout_s, round_index=2, context_snippets=quoted))
        _render_results("Round 2 — critique & next checks", r2)
        syn, disagree = summarize(r2)
        console.print(Panel(f"{syn}\nDisagreement score: {disagree}", title="Synthesis", border_style="magenta"))


def run_chat_repl(initial_multi: str, rounds: int, timeout_s: int, ollama_host: str | None = None) -> None:
    """A minimal REPL supporting slash commands."""
    models: list[str] = [x.strip() for x in initial_multi.split(",") if x.strip()] or ["llama3", "claude", "gpt"]
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
            "/quit | /exit        Leave REPL",
        ]
        console.print(Panel("\n".join(lines), title="Commands", border_style="cyan"))

    show_help()
    while True:
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
            console.print("Unknown command. Type /help.")
            continue

        # Treat as a prompt; run with current models
        multi = ",".join(models)
        run_roundtable(prompt=line, multi=multi, rounds=rounds, timeout_s=timeout_s, ollama_host=ollama_host)
