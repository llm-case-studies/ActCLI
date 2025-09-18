from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from platformdirs import user_config_dir


CONFIG_DIR = Path(user_config_dir("actcli", "actcli"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CREDS_PATH = CONFIG_DIR / "credentials.json"


@dataclass
class Credentials:
    method: str
    token: Optional[str] = None
    info: Optional[dict] = None


class CredentialStore:
    def __init__(self) -> None:
        self.path = CREDS_PATH
        self._cache: Dict[str, Credentials] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                for k, v in data.items():
                    self._cache[k] = Credentials(**v)
            except Exception:
                pass

    def save(self) -> None:
        tmp = {k: vars(v) for k, v in self._cache.items()}
        self.path.write_text(json.dumps(tmp, indent=2))
        os.chmod(self.path, 0o600)

    def get(self, provider: str) -> Optional[Credentials]:
        return self._cache.get(provider)

    def set(self, provider: str, creds: Credentials) -> None:
        self._cache[provider] = creds
        self.save()

    def clear(self, provider: str) -> None:
        if provider in self._cache:
            del self._cache[provider]
            self.save()

