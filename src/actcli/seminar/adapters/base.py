from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional


class ModelAdapter(Protocol):
    name: str
    is_local: bool
    model_version: str

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        seed: Optional[int] = None,
        timeout_s: int = 30,
        round_index: int = 1,
        context_snippets: Optional[str] = None,
    ) -> str: ...


@dataclass
class AdapterInfo:
    id: str
    name: str
    is_local: bool
    model_version: str

