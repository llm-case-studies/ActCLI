from __future__ import annotations

import json
import shutil
import subprocess
from typing import Optional
import os


class GeminiCLIAdapter:
    """Google Gemini adapter using the official Gemini CLI (open-source).

    Prerequisites:
    - Install: npm install -g @google/gemini-cli (or @google/gemini-cli@nightly)
    - Authenticate: run `gemini` then choose Login with Google (or use API Key/Vertex)

    Notes:
    - Command surface is evolving; this adapter tries several invocation forms.
    - We treat `model` as a label; when supported, we attempt a per-call model flag.
    - Parsing prefers JSON when available; otherwise extracts the largest content block.
    """

    def __init__(self, model: str = "default") -> None:
        self.model = model or "default"
        self.name = f"{self.model}(gemini-cli)"
        self.is_local = False
        self.model_version = self.model

        if not shutil.which("gemini"):
            raise RuntimeError(
                "Gemini CLI not found. Install with: npm i -g @google/gemini-cli (nightly) and run 'gemini' to auth."
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

        model = self.model
        # Build environment with optional tool/MCP disable
        env = os.environ.copy()
        if env.get("ACTCLI_DISABLE_CLI_MCP") == "1":
            env["NO_MCP"] = "1"
            env["GEMINI_CLI_DISABLE_TOOLS"] = "1"
            env["GEMINI_DISABLE_MCP"] = "1"
            env["MCP_CONFIG"] = ""
            env["MCP_ENDPOINTS"] = ""

        attempts = []
        if model and model != "default":
            attempts.extend(
                [
                    ["gemini", "-p", full_prompt, "--model", model],
                    ["gemini", "ask", "--model", model, full_prompt],
                ]
            )
        attempts.extend(
            [
                ["gemini", "-p", full_prompt],
                ["gemini", "ask", full_prompt],
            ]
        )

        res = None
        for cmd in attempts:
            try:
                res = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout_s, env=env
                )
                if res.returncode == 0 and (res.stdout or "").strip():
                    break
            except subprocess.TimeoutExpired:
                raise RuntimeError(f"Gemini CLI timeout after {timeout_s}s")
            except Exception:
                res = None
                continue

        if res is None or res.returncode != 0:
            err = (
                (res.stderr if res else "").strip()
                or (res.stdout if res else "").strip()
                or "unknown error"
            )
            raise RuntimeError(f"Gemini CLI failed: {err}")

        raw = (res.stdout or "").strip()
        # Try JSON
        if raw.startswith("{") or raw.startswith("["):
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    for key in ("result", "text", "output", "content"):
                        if isinstance(data.get(key), str) and data.get(key).strip():
                            return data[key].strip()
            except Exception:
                pass

        # Heuristic content extraction
        lines = [ln.rstrip() for ln in raw.splitlines()]
        blocks: list[list[str]] = []
        cur: list[str] = []

        def is_content(ln: str) -> bool:
            s = ln.strip()
            if not s:
                return False
            if (
                s == prompt.strip()
                or s.startswith("Original prompt:")
                or s.startswith("System:")
            ):
                return False
            if s.lstrip().startswith("["):
                return False
            if s.startswith("model:") or s.startswith("provider:"):
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
        out = max(blocks, key=lambda b: sum(len(x) for x in b))
        return "\n".join(out).strip() or raw
