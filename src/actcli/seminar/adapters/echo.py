from __future__ import annotations

import random
import textwrap
from typing import Optional

from .base import ModelAdapter


class EchoAdapter:
    """A local, dependency-free adapter for demos/tests.

    It simulates latency and returns a short, deterministic response.
    """

    def __init__(self, name: str = "echo", version: str = "0.1") -> None:
        self.name = name
        self.is_local = True
        self.model_version = version

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
        if seed is not None:
            random.seed(seed + round_index)
        # Simulate answering + optional critique of snippets
        parts = []
        if round_index == 1:
            parts.append(f"Answer (simulated) to: {prompt[:120]}")
        else:
            parts.append("Refinement based on peers' snippets:")
            if context_snippets:
                # Keep it short to simulate quoting
                quoted = textwrap.shorten(context_snippets.replace("\n", " "), width=160, placeholder="…")
                parts.append(f"Considering: \"{quoted}\"")
            parts.append("One next check: validate assumptions with a small sample.")
        return "\n".join(parts)

