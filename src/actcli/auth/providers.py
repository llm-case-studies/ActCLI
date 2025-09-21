from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional
import time
import os
import httpx

from .store import CredentialStore, Credentials
from .pkce import OAuthConfig, pkce_browser_login


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
        elif method == "pkce":
            # Generic PKCE flow configured via env vars:
            #   <PROVIDER>_OAUTH_CLIENT_ID, <PROVIDER>_OAUTH_AUTH_URL, <PROVIDER>_OAUTH_TOKEN_URL, <PROVIDER>_OAUTH_SCOPE(optional)
            cid = os.getenv(f"{self.id.upper()}_OAUTH_CLIENT_ID")
            auth_url = os.getenv(f"{self.id.upper()}_OAUTH_AUTH_URL")
            token_url = os.getenv(f"{self.id.upper()}_OAUTH_TOKEN_URL")
            scope = os.getenv(f"{self.id.upper()}_OAUTH_SCOPE")
            if not (cid and auth_url and token_url):
                raise SystemExit(
                    f"Missing OAuth env vars for {self.id}. Required: {self.id.upper()}_OAUTH_CLIENT_ID, _AUTH_URL, _TOKEN_URL"
                )
            if not self.store:
                raise SystemExit("Credential store not available")
            access_token, exp = pkce_browser_login(OAuthConfig(auth_url=auth_url, token_url=token_url, client_id=cid, scope=scope))
            self.store.set(f"{self.id}_oauth", Credentials(method="pkce", token=access_token, info={"expires_at": exp}))
        else:
            # Placeholder for OAuth device
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


class GoogleOAuthDevice:
    """Minimal OAuth Device Flow for Google Gemini (user-provided client_id).

    Notes:
    - Requires a valid OAuth client_id configured by the user.
    - Tokens are stored via CredentialStore.
    - Scopes default to the Generative Language API; can be extended.
    """

    DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    SCOPE = "https://www.googleapis.com/auth/generative-language"

    def __init__(self, store: CredentialStore, client_id: str) -> None:
        self.store = store
        self.client_id = client_id

    def login(self) -> None:
        with httpx.Client(timeout=10) as client:
            # 1) Get device code
            r = client.post(self.DEVICE_CODE_URL, data={
                "client_id": self.client_id,
                "scope": self.SCOPE,
            })
            r.raise_for_status()
            data = r.json()
            device_code = data["device_code"]
            user_code = data["user_code"]
            verification_url = data["verification_url"]
            interval = int(data.get("interval", 5))
            expires_in = int(data.get("expires_in", 1800))

            print(f"To sign in: visit {verification_url} and enter code: {user_code}")

            # 2) Poll for token
            start = time.time()
            while time.time() - start < expires_in:
                time.sleep(interval)
                pr = client.post(self.TOKEN_URL, data={
                    "client_id": self.client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                })
                if pr.status_code == 200:
                    tok = pr.json()
                    access_token = tok["access_token"]
                    refresh_token = tok.get("refresh_token")
                    expires_at = int(time.time() + tok.get("expires_in", 3600))
                    self.store.set("google_oauth", Credentials(method="device", token=access_token, info={
                        "refresh_token": refresh_token,
                        "expires_at": expires_at,
                        "client_id": self.client_id,
                        "scope": self.SCOPE,
                    }))
                    print("Google OAuth device login successful.")
                    return
                else:
                    try:
                        err = pr.json().get("error", "")
                    except Exception:
                        err = pr.text[:200]
                    if err in ("authorization_pending", "slow_down"):
                        if err == "slow_down":
                            interval += 2
                        continue
                    raise RuntimeError(f"OAuth device flow failed: {err}")
            raise TimeoutError("OAuth device code expired. Try again.")

    def status(self) -> str:
        cred = self.store.get("google_oauth")
        if not cred:
            return "unauthenticated"
        exp = cred.info.get("expires_at") if cred.info else None
        if exp and exp > time.time():
            return "oauth(device): valid"
        return "oauth(device): expired"
