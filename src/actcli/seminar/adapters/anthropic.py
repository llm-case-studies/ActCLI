from __future__ import annotations

import os
from typing import Optional

import httpx


class AnthropicAdapter:
    def __init__(self, model: str = "claude-3-haiku-20240307") -> None:
        self.model = model
        self.name = f"{model}(cloud)"
        self.is_local = False
        self.model_version = model
        self._api_key = os.getenv("ANTHROPIC_API_KEY")
        # Experimental: check for OAuth token if user logged in via PKCE
        try:
            from ..auth.store import CredentialStore  # type: ignore
        except Exception:
            CredentialStore = None
        self._oauth_token = None
        if CredentialStore is not None:
            try:
                store = CredentialStore()
                cred = store.get("anthropic_oauth")
                if cred and cred.token:
                    self._oauth_token = cred.token
            except Exception:
                pass
        if not self._api_key and not self._oauth_token:
            raise RuntimeError(
                "Anthropic auth missing (set ANTHROPIC_API_KEY or login with PKCE)"
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
        if round_index == 1:
            msg_content = prompt
        else:
            ctx = context_snippets or ""
            msg_content = f"Original prompt: {prompt}\nPeers said (snippets):\n{ctx}\nCritique/support briefly and propose one next check."
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                *([{"role": "system", "content": system}] if system else []),
                {"role": "user", "content": msg_content},
            ],
        }
        if temperature is not None:
            try:
                payload["temperature"] = float(temperature)
            except Exception:
                pass
        headers = {
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        if self._api_key:
            headers["x-api-key"] = self._api_key
        elif self._oauth_token:
            headers["Authorization"] = f"Bearer {self._oauth_token}"
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post(
                "https://api.anthropic.com/v1/messages", headers=headers, json=payload
            )
            r.raise_for_status()
            data = r.json()
            # New API returns content array
            content = data.get("content") or []
            if content and isinstance(content, list) and "text" in content[0]:
                return str(content[0]["text"]).strip()
            # Fallback older shape
            return str(data.get("completion", "")).strip()
