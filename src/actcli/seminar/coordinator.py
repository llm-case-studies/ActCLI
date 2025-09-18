from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional

from .adapters.base import ModelAdapter, AdapterInfo


@dataclass
class TurnResult:
    info: AdapterInfo
    text: str
    latency_ms: int
    error: Optional[str] = None


async def _call_adapter(
    adapter: ModelAdapter,
    prompt: str,
    *,
    seed: Optional[int],
    timeout_s: int,
    round_index: int,
    context_snippets: Optional[str],
) -> TurnResult:
    start = time.perf_counter()
    try:
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(
            None,
            lambda: adapter.generate(
                prompt, seed=seed, timeout_s=timeout_s, round_index=round_index, context_snippets=context_snippets
            ),
        )
        latency = int((time.perf_counter() - start) * 1000)
        info = AdapterInfo(id=getattr(adapter, "name", "unknown"), name=getattr(adapter, "name", "unknown"), is_local=getattr(adapter, "is_local", False), model_version=getattr(adapter, "model_version", ""))
        return TurnResult(info=info, text=text, latency_ms=latency)
    except Exception as e:
        latency = int((time.perf_counter() - start) * 1000)
        info = AdapterInfo(id=getattr(adapter, "name", "unknown"), name=getattr(adapter, "name", "unknown"), is_local=getattr(adapter, "is_local", False), model_version=getattr(adapter, "model_version", ""))
        return TurnResult(info=info, text="", latency_ms=latency, error=str(e))


async def run_round(
    adapters: List[ModelAdapter],
    prompt: str,
    *,
    seed: Optional[int] = None,
    timeout_s: int = 25,
    round_index: int = 1,
    context_snippets: Optional[str] = None,
) -> List[TurnResult]:
    tasks = [
        asyncio.create_task(
            asyncio.wait_for(
                _call_adapter(a, prompt, seed=seed, timeout_s=timeout_s, round_index=round_index, context_snippets=context_snippets),
                timeout=timeout_s,
            )
        )
        for a in adapters
    ]
    results: List[TurnResult] = []
    for t in tasks:
        try:
            res = await t
            results.append(res)
        except asyncio.TimeoutError:
            # Build a minimal timeout result
            adapter = adapters[tasks.index(t)]
            info = AdapterInfo(id=getattr(adapter, "name", "unknown"), name=getattr(adapter, "name", "unknown"), is_local=getattr(adapter, "is_local", False), model_version=getattr(adapter, "model_version", ""))
            results.append(TurnResult(info=info, text="", latency_ms=timeout_s * 1000, error="timeout"))
    return results

