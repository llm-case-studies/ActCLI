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

        # Decide model and reasoning phrase
        model = self.model
        reasoning_phrase = None
        if reasoning and model.startswith("gpt-5"):
            r = reasoning.strip().lower()
            if r in ("minimal", "low", "medium", "high"):
                reasoning_phrase = f"gpt-5 {r}"

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
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
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
                    subprocess.run(["codex", "/model", target], capture_output=True, text=True, timeout=min(8, timeout_s))
                    pre_switched = True
                except Exception:
                    pre_switched = False
            # Final attempt with default exec
            try:
                res = subprocess.run(["codex", "exec", full_prompt], capture_output=True, text=True, timeout=timeout_s)
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"Codex CLI timeout after {timeout_s}s")
            except Exception as e:
                raise RuntimeError(f"Codex CLI error: {e}")
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Codex CLI timeout after {timeout_s}s")
        except Exception as e:
            raise RuntimeError(f"Codex CLI error: {e}")

        if res is None or res.returncode != 0:
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
