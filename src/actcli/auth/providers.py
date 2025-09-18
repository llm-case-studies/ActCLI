from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

from .store import CredentialStore, Credentials


@dataclass
class Provider:
    id: str
    env_key: Optional[str]
    method: Optional[str] = None
    store: CredentialStore | None = None

    def status(self) -> str:
        if self.env_key and os.getenv(self.env_key):
            return "env-key"
        if self.store:
            c = self.store.get(self.id)
            if c:
                return c.method
        return "unauthenticated"

    def login(self, preferred_method: Optional[str] = None) -> None:
        method = preferred_method or ("api-key" if self.env_key else "device")
        if method == "api-key":
            key = os.getenv(self.env_key or "")
            if not key:
                # For prototype: we don't prompt; instruct user to set env
                raise SystemExit(f"Set {self.env_key} or use --method device/pkce if supported")
            if self.store:
                self.store.set(self.id, Credentials(method="api-key", token=None, info={"env": self.env_key}))
        else:
            # Placeholder for OAuth device/pkce
            if self.store:
                self.store.set(self.id, Credentials(method=method, token=None, info={"note": "oauth placeholder"}))
        self.method = method

    def logout(self) -> None:
        if self.store:
            self.store.clear(self.id)
        self.method = None


class ProviderRegistry:
    def __init__(self, providers: Dict[str, Provider]) -> None:
        self.providers = providers

    def get(self, pid: str) -> Optional[Provider]:
        return self.providers.get(pid)

    @classmethod
    def default(cls) -> "ProviderRegistry":
        store = CredentialStore()
        providers = {
            "openai": Provider(id="openai", env_key="OPENAI_API_KEY", store=store),
            "anthropic": Provider(id="anthropic", env_key="ANTHROPIC_API_KEY", store=store),
            "google": Provider(id="google", env_key="GOOGLE_API_KEY", store=store),
        }
        return cls(providers)

