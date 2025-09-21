from __future__ import annotations

import os
from typing import Optional

import httpx



class OllamaAdapter:
    """Adapter for local Ollama models.

    Uses the Ollama HTTP API. If `OLLAMA_HOST` is set, it will be used, otherwise
    defaults to http://127.0.0.1:11434.
    """

    def __init__(self, model: str = "llama3", host: Optional[str] = None) -> None:
        self.model = model
        self.is_local = True
        self.model_version = ""
        self._host = host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        # Try to map short names (e.g., 'llama3') to available tags (e.g., 'llama3:8b')
        mapped = self._map_model_tag(self.model)
        if mapped and mapped != self.model:
            self.model = mapped
        self.name = f"{self.model}(local)"

    def _map_model_tag(self, name: str) -> Optional[str]:
        if ":" in name:
            return name
        try:
            with httpx.Client(timeout=3.0) as client:
                r = client.get(f"{self._host.rstrip('/')}/api/tags")
                r.raise_for_status()
                data = r.json() or {}
                models = [m.get("name", "") for m in data.get("models", [])]
                for m in models:
                    if m.startswith(f"{name}:"):
                        return m
        except Exception:
            return name
        return name

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
        if temperature is not None:
            try:
                options["temperature"] = float(temperature)
            except Exception:
                pass
        if options:
            payload["options"] = options
        if system:
            payload["system"] = system

        with httpx.Client(timeout=timeout_s) as client:
            url = f"{self._host.rstrip('/')}/api/generate"
            resp = client.post(url, json=payload)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Include server message if available for better diagnostics
                detail = ""
                try:
                    js = resp.json()
                    detail = js.get("error") or js.get("message") or resp.text[:200]
                except Exception:
                    detail = resp.text[:200]
                raise RuntimeError(f"Ollama error {resp.status_code}: {detail}") from e
            data = resp.json()
            text = data.get("response") or data.get("message") or ""
            return text.strip()
