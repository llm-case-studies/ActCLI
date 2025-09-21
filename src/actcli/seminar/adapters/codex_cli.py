from __future__ import annotations

import subprocess
import shutil
from typing import Optional


class CodexCLIAdapter:
    """OpenAI adapter using Codex CLI (subscription-backed).

    Prerequisites:
    - Codex CLI installed (Node): `npm i -g @openai/codex` or `brew install codex`
    - User signed in: run `codex` and choose "Sign in with ChatGPT"

    Notes:
    - Codex CLI doesn't reliably support a `--model` flag across versions; selection is interactive via `codex /model`.
    - We treat `model` value as a label; execution uses the active CLI model.
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

        cmd = ["codex", "exec", full_prompt]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Codex CLI timeout after {timeout_s}s")
        except Exception as e:
            raise RuntimeError(f"Codex CLI error: {e}")

        if res.returncode != 0:
            err = res.stderr.strip() or res.stdout.strip() or "unknown error"
            raise RuntimeError(f"Codex CLI failed: {err}")

        # Parse output: prefer the last non-empty block without leading metadata brackets
        text = res.stdout or ""
        lines = [ln.rstrip() for ln in text.splitlines()]
        # Collect contiguous blocks of "content-like" lines
        blocks: list[list[str]] = []
        cur: list[str] = []
        def is_content(ln: str) -> bool:
            if not ln.strip():
                return False
            if ln.lstrip().startswith("["):
                return False
            if ln.startswith("workdir:") or ln.startswith("model:") or ln.startswith("provider:") or ln.startswith("approval:"):
                return False
            if ln.startswith("User instructions:") or ln.startswith("--------"):
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
            return text.strip()
        # Use the last block as the answer
        out = "\n".join(blocks[-1]).strip()
        return out or text.strip()

