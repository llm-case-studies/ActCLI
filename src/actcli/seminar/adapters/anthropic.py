from __future__ import annotations

import os
from typing import Optional

import httpx

from .base import ModelAdapter


class AnthropicAdapter:
    def __init__(self, model: str = "claude-3-haiku-20240307") -> None:
        self.model = model
        self.name = f"{model}(cloud)"
        self.is_local = False
        self.model_version = model
        self._api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")

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
        if round_index == 1:
            msg_content = prompt
        else:
            ctx = context_snippets or ""
            msg_content = f"Original prompt: {prompt}\nPeers said (snippets):\n{ctx}\nCritique/support briefly and propose one next check."
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                *( [ {"role": "system", "content": system} ] if system else [] ),
                {"role": "user", "content": msg_content},
            ],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            # New API returns content array
            content = data.get("content") or []
            if content and isinstance(content, list) and "text" in content[0]:
                return str(content[0]["text"]).strip()
            # Fallback older shape
            return str(data.get("completion", "")).strip()

