from __future__ import annotations

import os
from typing import Optional

import httpx

from .base import ModelAdapter


class OllamaAdapter:
    """Adapter for local Ollama models.

    Uses the Ollama HTTP API. If `OLLAMA_HOST` is set, it will be used, otherwise
    defaults to http://127.0.0.1:11434.
    """

    def __init__(self, model: str = "llama3", host: Optional[str] = None) -> None:
        self.model = model
        self.name = f"{model}(local)"
        self.is_local = True
        self.model_version = ""
        self._host = host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        seed: Optional[int] = None,
        timeout_s: int = 30,
        round_index: int = 1,
        context_snippets: Optional[str] = None,
    ) -> str:
        # Compose a minimal round-aware prompt
        if round_index == 1:
            effective_prompt = prompt
        else:
            peer_context = context_snippets or ""
            effective_prompt = (
                f"Respond to the original prompt, considering peers' points.\n"
                f"Peers said (snippets):\n{peer_context}\n"
                f"Provide a brief critique and propose one concrete next check."
            )

        payload = {
            "model": self.model,
            "prompt": effective_prompt,
            "stream": False,
        }
        options = {}
        if seed is not None:
            options["seed"] = int(seed)
        if options:
            payload["options"] = options
        if system:
            payload["system"] = system

        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(f"{self._host}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response") or data.get("message") or ""
            return text.strip()
