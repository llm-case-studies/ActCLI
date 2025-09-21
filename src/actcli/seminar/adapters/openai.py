from __future__ import annotations

import os
from typing import Optional

import httpx



class OpenAIAdapter:
    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self.name = f"{model}(cloud)"
        self.is_local = False
        self.model_version = model
        self._api_key = os.getenv("OPENAI_API_KEY")
        # OAuth token (if user logged in via PKCE)
        try:
            from ..auth.store import CredentialStore  # type: ignore
        except Exception:
            CredentialStore = None
        self._oauth_token = None
        if CredentialStore is not None:
            try:
                store = CredentialStore()
                cred = store.get("openai_oauth")
                if cred and cred.token:
                    self._oauth_token = cred.token
            except Exception:
                pass
        if not self._api_key and not self._oauth_token:
            raise RuntimeError("OpenAI auth missing (set OPENAI_API_KEY or login with PKCE)")

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
        if temperature is not None:
            try:
                payload["temperature"] = float(temperature)
            except Exception:
                pass

        token = self._oauth_token or self._api_key
        headers = {"Authorization": f"Bearer {token}"}
        with httpx.Client(timeout=timeout_s) as client:
            r = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"].strip()
            return text
