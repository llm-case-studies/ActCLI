from __future__ import annotations

import os
from typing import Optional

import httpx

from .base import ModelAdapter


class OpenAIAdapter:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self.name = f"{model}(cloud)"
        self.is_local = False
        self.model_version = model
        self._api_key = os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

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
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if round_index == 1:
            messages.append({"role": "user", "content": prompt})
        else:
            ctx = context_snippets or ""
            messages.append({
                "role": "user",
                "content": f"Original prompt: {prompt}\nPeers said (snippets):\n{ctx}\nCritique/support briefly and propose one next check."
            })
        payload = {
            "model": self.model,
            "messages": messages,
        }
        # OpenAI may support seed for determinism in some models; include if provided
        if seed is not None:
            payload["seed"] = int(seed)

        headers = {"Authorization": f"Bearer {self._api_key}"}
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"].strip()
            return text

