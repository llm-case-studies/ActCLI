Request for GPT-5 Pro
Reasoned for 4m 0s
Analyzed
Always show details
# Create a unified CLI-provider adapter file that shells out to vendor CLIs
# (Gemini, Claude Code, Codex) and returns text + minimal metadata.
# The file is designed to be dropped into the user's repo and run directly.
from pathlib import Path

code = r"""#!/usr/bin/env python3
"""
code += r'''# actcli_cli_providers.py
"""
ActCLI CLI-Provider Adapters (v0.2)
===================================
Use the installed vendor CLIs (Gemini, Claude Code, OpenAI Codex) so users can
leverage their **existing subscriptions** without managing API keys in ActCLI.

- Gemini CLI:   Login with Google inside the CLI; supports non-interactive JSON.
- Claude Code:  One-time login; supports headless print (-p) with JSON output.
- Codex CLI:    "Sign in with ChatGPT" and use `codex exec` for scripting.

This script shells out safely (no shell=True), parses JSON where possible, and
returns a normalized result: {"provider","text","meta":{...}}.

Requirements (install at least what you need):
    npm i -g @anthropic-ai/claude-code     # `claude` binary
    npm i -g @openai/codex                 # `codex` binary
    # Gemini CLI is typically installed via package manager:
    #   brew install gemini-cli   (or follow repo instructions)
    # Login once in each CLI before using this script.

References:
- Gemini CLI non-interactive + JSON output:
  https://google-gemini.github.io/gemini-cli/docs/cli/   (# --output-format json, -p)
- Claude Code headless print + JSON output:
  https://docs.claude.com/en/docs/claude-code/cli-reference
- Codex CLI exec mode (non-interactive):
  https://developers.openai.com/codex/cli/

Usage
-----
$ python actcli_cli_providers.py --providers gemini,claude,codex \
    --prompt "Briefly explain the chain-ladder method."

$ python actcli_cli_providers.py --providers gemini --model gemini-2.0-flash \
    --prompt "Hi from Gemini in one sentence."
"""
import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List


@dataclass
class ProviderResult:
    provider: str
    text: str
    meta: Dict


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _parse_any_json(s: str) -> Dict:
    """
    Try to parse a variety of JSON shapes returned by CLIs.
    Gemini CLI example (per docs): {"response":"...","stats":{...},"error":null}
    Claude Code often: {"text":"..."} or {"output":"..."} with extras.
    Fallback: return {"raw": s} if not JSON.
    """
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
        return {"raw": obj}
    except Exception:
        return {"raw": s}


def _pick_text(obj: Dict) -> str:
    """
    Choose the most likely text field across CLIs.
    """
    for key in ("text", "response", "output", "content", "message"):
        if key in obj and isinstance(obj[key], str):
            return obj[key]
    # Gemini sometimes nests content under 'candidates' in SDKs; handle generically
    if "candidates" in obj and isinstance(obj["candidates"], list) and obj["candidates"]:
        cand = obj["candidates"][0]
        if isinstance(cand, dict):
            for k in ("text", "content", "output"):
                if k in cand and isinstance(cand[k], str):
                    return cand[k]
    # Fallback to stringified raw
    return obj.get("raw") if isinstance(obj.get("raw"), str) else json.dumps(obj)


def ask_gemini_cli(prompt: str, model: Optional[str] = None, timeout_s: int = 90) -> ProviderResult:
    """
    Use Gemini CLI in non-interactive mode with JSON output.
    Prefers: `gemini -p "<prompt>" --output-format json [--model <id>]`
    """
    exe = _which("gemini")
    if not exe:
        raise FileNotFoundError("Gemini CLI not found. Install and run `gemini` once to log in.")

    # Build command
    cmd: List[str] = [exe, "-p", prompt, "--output-format", "json"]
    # Many versions support --model / -m (see docs). Add if provided.
    if model:
        cmd.extend(["--model", model])

    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, check=True)
        data = _parse_any_json(cp.stdout.strip())
        text = _pick_text(data)
        return ProviderResult("gemini", text, {"raw": data, "stderr": cp.stderr})
    except subprocess.CalledProcessError as e:
        # Some Gemini versions print JSON to stderr on errors
        parsed = _parse_any_json((e.stdout or e.stderr or "").strip())
        raise RuntimeError(f"Gemini CLI failed: {e}\n{parsed}")


def ask_claude_cli(prompt: str, timeout_s: int = 90) -> ProviderResult:
    """
    Use Claude Code headless print (-p) with JSON output for scripting.
        claude -p "<prompt>" --output-format json
    """
    exe = _which("claude")
    if not exe:
        raise FileNotFoundError("Claude Code CLI not found. Install and run `claude` once to log in.")

    cmd = [exe, "-p", prompt, "--output-format", "json"]
    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, check=True)
    data = _parse_any_json(cp.stdout.strip())
    text = _pick_text(data)
    return ProviderResult("claude", text, {"raw": data, "stderr": cp.stderr})


def ask_codex_cli(prompt: str, timeout_s: int = 90) -> ProviderResult:
    """
    Use Codex CLI exec mode for non-interactive runs.
        codex exec "<prompt>" --quiet
    Returns plain text.
    """
    exe = _which("codex")
    if not exe:
        raise FileNotFoundError("Codex CLI not found. Install and run `codex` once to log in.")

    cmd = [exe, "exec", "--quiet", prompt]
    cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, check=True)
    text = (cp.stdout or "").strip()
    return ProviderResult("codex", text, {"stderr": cp.stderr})


def ask_many(prompt: str, providers: list, model: Optional[str] = None) -> Dict[str, ProviderResult]:
    results: Dict[str, ProviderResult] = {}
    for p in providers:
        p = p.strip().lower()
        try:
            if p == "gemini":
                results[p] = ask_gemini_cli(prompt, model=model)
            elif p == "claude":
                results[p] = ask_claude_cli(prompt)
            elif p == "codex":
                results[p] = ask_codex_cli(prompt)
            else:
                results[p] = ProviderResult(p, "", {"error": f"Unknown provider: {p}"})
        except Exception as e:
            results[p] = ProviderResult(p, "", {"error": str(e)})
    return results


def main():
    ap = argparse.ArgumentParser(description="ActCLI vendor CLI adapters — use your existing subscriptions.")
    ap.add_argument("--providers", default="gemini,claude,codex",
                    help="Comma-separated providers to call (default: gemini,claude,codex)")
    ap.add_argument("--prompt", required=True, help="The prompt to send.")
    ap.add_argument("--model", default=None, help="Model id (passed to Gemini CLI if provided).")
    args = ap.parse_args()

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    res = ask_many(args.prompt, providers, model=args.model)

    # Pretty print
    print("\n=== ActCLI CLI Provider Results ===")
    for name, pr in res.items():
        print(f"\n[{name}]")
        if pr.meta.get("error"):
            print(f"ERROR: {pr.meta['error']}")
        else:
            print(textwrap.shorten(pr.text.replace("\n", " "), width=400, placeholder=" …"))
            # Show minimal token stats if present
            raw = pr.meta.get("raw") or {}
            stats = raw.get("stats") or raw.get("usage") or {}
            if stats:
                print(f"(stats: {json.dumps(stats)[:200]} …)")

if __name__ == "__main__":
    main()
'''

out = Path("/mnt/data/actcli_cli_providers.py")
out.write_text(code, encoding="utf-8")
print(str(out))

STDOUT/STDERR
/mnt/data/actcli_cli_providers.py


You’re absolutely right—Gemini CLI already handles “Login with Google” for you, caches the token, and “just works.” We don’t need to re‑implement OAuth in Python to support “bring your own subscription.” The simplest path is to piggyback on vendor CLIs (Claude, Codex, Gemini) exactly the way you’re doing interactively, and call them non‑interactively from ActCLI.

Below I’ve given you a drop‑in adapter that shells out to those CLIs, parses machine‑readable output, and returns a normalized result. This lets your Multi‑AI Seminar use users’ existing logins immediately.

Why this works

Gemini CLI: supports Login with Google directly; if you have a Code Assist license, set GOOGLE_CLOUD_PROJECT and run gemini—no API key needed. 
GitHub

It also supports non‑interactive + JSON output for scripting:
gemini -p "…" --output-format json → returns a JSON object (e.g., { "response": "...", "stats": {...} }). 
Google Gemini

Claude Code: supports headless print mode -p and --output-format json (great for automation/CI). 
Claude Docs

OpenAI Codex: supports non‑interactive runs via codex exec "…". 
OpenAI Developers

Drop‑in adapter (ready to use)

I packaged a tiny, safe wrapper that calls the vendor CLIs (no shell=True), parses JSON where available, and normalizes the result:

File: actcli_cli_providers.py
Download

Examples

# Use your existing Gemini CLI login; JSON parse; optional model flag
python actcli_cli_providers.py --providers gemini \
  --prompt "ActCLI smoke test: greet me in one short sentence." \
  --model gemini-2.0-flash

# Compare multiple providers (uses your existing logins)
python actcli_cli_providers.py --providers gemini,claude,codex \
  --prompt "Briefly explain the chain-ladder method."


What it does:

Gemini: runs gemini -p "<prompt>" --output-format json [--model <id>] and extracts "response" (with stats available for tokens). 
Google Gemini
+1

Claude: runs claude -p "<prompt>" --output-format json and extracts "text" (or "output"). 
Claude Docs

Codex: runs codex exec --quiet "<prompt>" and returns plain text. 
OpenAI Developers

Tip: If your Gemini CLI is tied to a Code Assist license, set:

export GOOGLE_CLOUD_PROJECT='your-project-id'
gemini


(That’s called out in their README.) 
GitHub

Wire it into ActCLI’s “Multi‑AI Seminar”

Adapter selection in your seminar coordinator:

from actcli_cli_providers import ask_many
name_to_answer = ask_many(prompt, providers=["gemini","claude","codex"], model="gemini-2.0-flash")


Slash commands (from your Tier‑0 set) already fit:

/models add gemini → include the Gemini CLI adapter.

/compare → fan‑out to all active adapters in parallel, then summarize.

/summarize → keep synthesis local (offline) as planned.

Audit: log {"provider":"gemini","mode":"cli","command":"gemini -p --output-format json","model":"…","ts":…} alongside the response/hash.

One‑liners to sanity‑check each CLI (outside ActCLI)

Gemini (machine‑readable):
gemini -p "What is fine‑tuning?" --output-format json → inspect "response" and "stats". 
Google Gemini

Claude (machine‑readable):
claude -p "Summarize chain‑ladder." --output-format json → JSON you can pipe to jq. 
Claude Docs

Codex (non‑interactive):
codex exec "Summarize Bornhuetter‑Ferguson in 2 lines" --quiet → plain text. 
OpenAI Developers

When to use API/OAuth vs. CLI

Default (recommended): use vendor CLIs for “bring your own subscription” (zero friction; your case).

Fallback: if gemini isn’t installed, ActCLI can fall back to the Python SDK path (API key or OAuth). Keep the Gemini Doctor we generated as actcli providers doctor so users can self‑fix quickly.

Small UX nudge

Show the active engines in the REPL header each turn so you never wonder “which box am I in?”:

ActCLI • chat(seminar) • MODE: OFFLINE • participants: gemini, claude, codex • audit: ON
