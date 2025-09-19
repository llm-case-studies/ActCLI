from __future__ import annotations

import time
from typing import Optional


import asyncio

from actcli.seminar.coordinator import run_round


class _FakeAdapter:
    def __init__(self, name: str, delay: float = 0.0, fail: bool = False) -> None:
        self.name = name
        self.is_local = True
        self.model_version = "test"
        self._delay = delay
        self._fail = fail

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
        if self._delay:
            time.sleep(self._delay)
        if self._fail:
            raise RuntimeError("boom")
        return "ok"


def test_run_round_behaviour() -> None:
    adapters = [
        _FakeAdapter("fast"),
        _FakeAdapter("slow", delay=0.3),
        _FakeAdapter("err", fail=True),
    ]
    # Use small timeout to trigger one timeout
    results = asyncio.run(run_round(adapters, "q", seed=1, timeout_s=0.1, round_index=1))
    assert len(results) == 3
    texts = {r.info.name: (r.text, r.error) for r in results}
    assert texts["fast"][0] == "ok"
    assert texts["err"][1] == "boom"
    assert texts["slow"][1] == "timeout"
