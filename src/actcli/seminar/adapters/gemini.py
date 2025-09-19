from __future__ import annotations

import os
from typing import Optional

import httpx

from .base import ModelAdapter


class GeminiAdapter:
    def __init__(self, model: str = "gemini-1.5-flash-latest") -> None:
        self.model = model
        self.name = f"{model}(cloud)"
        self.is_local = False
        self.model_version = model
        self._api_key = os.getenv("GOOGLE_API_KEY")
        if not self._api_key:
            raise RuntimeError("GOOGLE_API_KEY not set")

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
            content = prompt
        else:
            ctx = context_snippets or ""
            content = f"Original prompt: {prompt}\nPeers said (snippets):\n{ctx}\nCritique/support briefly and propose one next check."
        url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent?key={self._api_key}"
        payload = {
            "contents": [
                *( [ {"role": "system", "parts": [{"text": system}] } ] if system else [] ),
                {"role": "user", "parts": [{"text": content}]},
            ]
        }
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception:
                text = ""
            return text

