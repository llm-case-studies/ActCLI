from __future__ import annotations

import os
from typing import Optional

import google.generativeai as genai
from google.oauth2.credentials import Credentials

class GeminiAdapter:
    def __init__(self, model: str = "gemini-pro") -> None:
        self.model = model
        self.name = f"{model}(cloud)"
        self.is_local = False
        self.model_version = model
        self._api_key = os.getenv("GOOGLE_API_KEY")
        self._creds = None

        try:
            from ..auth.store import CredentialStore
            store = CredentialStore()
            cred = store.get("google_oauth")
            if cred:
                self._creds = Credentials(
                    token=cred.token,
                    refresh_token=cred.refresh_token,
                    client_id=cred.client_id,
                    client_secret=cred.client_secret,
                    token_uri="https://oauth2.googleapis.com/token",
                )
        except Exception:
            pass

        if self._api_key:
            genai.configure(api_key=self._api_key)
        elif self._creds:
            genai.configure(credentials=self._creds)
        else:
            # Try Application Default Credentials (from gcloud auth or actcli auth login google)
            try:
                genai.configure()  # Uses ADC automatically
            except Exception as e:
                raise RuntimeError(f"Gemini auth missing. Please run: actcli auth login google")

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
        model = genai.GenerativeModel(self.model)
        generation_config = {}
        if temperature is not None:
            generation_config["temperature"] = temperature

        if round_index == 1:
            contents = [prompt]
        else:
            ctx = context_snippets or ""
            contents = [f"Original prompt: {prompt}\nPeers said (snippets):\n{ctx}\nCritique/support briefly and propose one next check."]

        if system:
            model.system_instruction = system

        response = model.generate_content(contents, generation_config=generation_config)

        return response.text
