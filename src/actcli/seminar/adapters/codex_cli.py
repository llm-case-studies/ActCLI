from __future__ import annotations

import subprocess
import shutil
from typing import Optional
import os
import json


class CodexCLIAdapter:
    """OpenAI adapter using Codex CLI (subscription-backed).

    Prerequisites:
    - Codex CLI installed (Node): `npm i -g @openai/codex` or `brew install codex`
    - User signed in: run `codex` and choose "Sign in with ChatGPT"

    Notes:
    - Codex CLI model selection varies by version. We attempt, in order:
      1) `codex exec --model <model> <prompt>` (newer versions)
      2) `codex --model <model> <prompt>` (some builds)
      3) `codex /model <model>` pre-step, then `codex exec <prompt>` (fallback)
    - If none succeed, we fall back to the active CLI model.
    - System/temperature/seed are not first-class CLI flags; we fold system into the prompt.
    """

    def __init__(self, model: str = "default") -> None:
        self.model = model or "default"
        self.name = f"{self.model}(codex-cli)"
        self.is_local = False
        self.model_version = self.model

        # Ensure codex binary is available
        if not shutil.which("codex"):
            raise RuntimeError(
                "Codex CLI not found. Install with: npm i -g @openai/codex (or brew install codex), then run 'codex' to sign in."
            )

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        seed: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout_s: int = 30,
        round_index: int = 1,
        context_snippets: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> str:
        # Compose prompt with simple round/context shaping
        if round_index == 1:
            full_prompt = prompt
        else:
            ctx = context_snippets or ""
            full_prompt = (
                f"Original prompt: {prompt}\n"
                f"Peers said (snippets):\n{ctx}\n"
                f"Critique/support briefly and propose one next check."
            )
        if system:
            full_prompt = f"System: {system}\n\nUser: {full_prompt}"

        # Decide model and reasoning phrase (support ids like gpt-5-minimal)
        model = self.model
        reasoning_phrase = None
        # Allow explicit reasoning param to override model-derived level
        level_from_model = None
        if model and model.lower().startswith("gpt-5-"):
            tail = model.split("-", 2)[-1].lower()
            if tail in ("minimal", "low", "medium", "high"):
                level_from_model = tail
        if reasoning and model.startswith("gpt-5"):
            r = reasoning.strip().lower()
            if r in ("minimal", "low", "medium", "high"):
                reasoning_phrase = f"gpt-5 {r}"
        elif level_from_model:
            reasoning_phrase = f"gpt-5 {level_from_model}"
            # use base model for flag attempts; selection will be done via pre-switch
            model = "gpt-5"

        # Build environment with optional tool/MCP disable
        env = os.environ.copy()
        if env.get("ACTCLI_DISABLE_CLI_MCP") == "1":
            env["NO_MCP"] = "1"
            env["CODEX_DISABLE_MCP"] = "1"
            env["MCP_CONFIG"] = ""
            env["MCP_ENDPOINTS"] = ""

        attempts = [
            ["codex", "exec", "--model", model, full_prompt],
            ["codex", "--model", model, full_prompt],
            ["codex", "exec", full_prompt],  # default (after possible pre-step)
        ]

        pre_switched = False
        res = None
        # Try direct model flag forms first
        for i, cmd in enumerate(attempts[:2]):
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, env=env)
                if res.returncode == 0 and (res.stdout or "").strip():
                    break
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"Codex CLI timeout after {timeout_s}s")
            except Exception:
                # Try next form
                res = None
                continue

        # If both flag forms failed, try pre-switching the model (and reasoning) once
        if res is None or res.returncode != 0:
            if (model and model != "default") or reasoning_phrase:
                try:
                    target = reasoning_phrase or model
                    subprocess.run(["codex", "/model", target], capture_output=True, text=True, timeout=min(8, timeout_s), env=env)
                    pre_switched = True
                except Exception:
                    pre_switched = False
            # Final attempt with default exec
            try:
                res = subprocess.run(["codex", "exec", full_prompt], capture_output=True, text=True, timeout=timeout_s, env=env)
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"Codex CLI timeout after {timeout_s}s")
            except Exception as e:
                raise RuntimeError(f"Codex CLI error: {e}")

        if res is None or res.returncode != 0:
            err = res.stderr.strip() or res.stdout.strip() or "unknown error"
            raise RuntimeError(f"Codex CLI failed: {err}")

        raw = (res.stdout or "").strip()
        # Debug: allow returning raw stdout/stderr to diagnose parsing issues
        if os.getenv("CODEX_CLI_RAW") == "1" or os.getenv("SEMHOST_CLI_DEBUG", "").lower() in ("1", "true", "yes"): 
            dbg = raw
            if (res.stderr or "").strip():
                dbg += "\n\n[stderr]\n" + res.stderr.strip()
            return dbg.strip() or "(empty)"
        # Try JSON first if available (some builds support structured output)
        if raw.startswith("{") or raw.startswith("["):
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    for key in ("result", "text", "output", "content"):
                        if isinstance(data.get(key), str) and data.get(key).strip():
                            return data[key].strip()
            except Exception:
                pass

        # Fallback: extract the most substantial content that is not just echo
        lines = [ln.rstrip() for ln in raw.splitlines()]
        blocks: list[list[str]] = []
        cur: list[str] = []

        def is_content(ln: str) -> bool:
            s = ln.strip()
            if not s:
                return False
            if s == prompt.strip() or s.startswith("Original prompt:") or s.startswith("System:"):
                return False
            if s.lstrip().startswith("["):
                return False
            if s.startswith("workdir:") or s.startswith("model:") or s.startswith("provider:") or s.startswith("approval:"):
                return False
            if s.startswith("User instructions:") or s.startswith("--------"):
                return False
            return True

        for ln in lines:
            if is_content(ln):
                cur.append(ln)
            else:
                if cur:
                    blocks.append(cur)
                    cur = []
        if cur:
            blocks.append(cur)
        if not blocks:
            return raw
        # Choose the longest block by character count (less likely to be an echo)
        out_block = max(blocks, key=lambda b: sum(len(x) for x in b))
        out = "\n".join(out_block).strip()
        return out or raw
