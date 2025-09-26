from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence, Tuple
import asyncio
import json
from pathlib import Path

from .adapters.base import ModelAdapter
from .coordinator import run_round


@dataclass
class Entry:
    alias: str
    model_id: str
    latency_ms: int
    ok: bool
    text: Optional[str] = None
    error: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    params_snapshot: Dict[str, object] = field(default_factory=dict)


@dataclass
class RoundRecord:
    index: int
    started_at: float
    completed_at: Optional[float] = None
    entries: List[Entry] = field(default_factory=list)
    synopsis: Optional[str] = None


@dataclass
class SessionState:
    id: str
    started_at: float
    round_idx: int = 0
    max_rounds: Optional[int] = None
    window_k: int = 2
    participants: Dict[str, ModelAdapter] = field(
        default_factory=dict
    )  # alias -> adapter (BoundAdapter allowed)
    history: List[RoundRecord] = field(default_factory=list)


class RoundOrchestrator:
    """Barrier‑synchronized multi‑round orchestrator (scaffold).

    Responsibilities:
    - Track session/round state
    - Build context frames (windowed prior rounds)
    - Schedule concurrent generation (one turn per alias)
    - Collect results and append to history
    - Optionally compute similarity/synopsis (future)
    """

    def __init__(self, *, window_k: int = 2, max_rounds: Optional[int] = None) -> None:
        self.state = SessionState(
            id=str(uuid.uuid4())[:8],
            started_at=time.time(),
            window_k=window_k,
            max_rounds=max_rounds,
        )
        self._focused: Optional[Sequence[str]] = None  # one‑shot focus list

    def set_participants(self, participants: Dict[str, ModelAdapter]) -> None:
        self.state.participants = dict(participants)

    def set_focus_next(self, aliases: Sequence[str]) -> None:
        self._focused = list(aliases)

    def start(self) -> None:
        if self.state.round_idx != 0:
            return
        self.state.round_idx = 1
        self.state.history.append(RoundRecord(index=1, started_at=time.time()))

    def stop(self) -> None:
        # No special behavior on scaffold
        pass

    def next_round(self) -> int:
        if self.state.round_idx == 0:
            self.start()
            return self.state.round_idx
        # Close current round if not closed (scaffold)
        cur = self._current_round()
        if cur and cur.completed_at is None:
            cur.completed_at = time.time()
        # Respect max_rounds
        if self.state.max_rounds and self.state.round_idx >= self.state.max_rounds:
            return self.state.round_idx
        self.state.round_idx += 1
        self.state.history.append(
            RoundRecord(index=self.state.round_idx, started_at=time.time())
        )
        # Clear one‑shot focus
        self._focused = None
        return self.state.round_idx

    def round_status(self) -> Tuple[int, int, int]:
        # returns (round_idx, participants_count, window_k)
        return (self.state.round_idx, len(self.state.participants), self.state.window_k)

    def build_context(self) -> str:
        """Return a windowed context summary (scaffold)."""
        k = max(0, int(self.state.window_k))
        if k <= 0 or not self.state.history:
            return ""
        last = self.state.history[-k:]
        lines: List[str] = []
        for rr in last:
            for e in rr.entries:
                if e.text:
                    lines.append(f"{e.alias}: {e.text[:200].replace('\n', ' ')}")
        return "\n".join(lines)

    # Execution entrypoint (signature only — implementation to be filled by Codex‑J)
    def run_current_round(
        self, *, prompt: str, seed: Optional[int], timeout_s: int
    ) -> RoundRecord:
        """Fan‑out to participants concurrently and collect entries into current RoundRecord.

        - Uses windowed context from build_context()
        - Respects per‑call timeouts
        - One say per alias (optionally subset via focus)
        """
        rr = self._current_round()
        if rr is None:
            self.start()
            rr = self._current_round()
        assert rr is not None

        # Build active set (focused subset for one-shot if provided)
        aliases: List[str] = []
        adapters: List[ModelAdapter] = []
        for alias, adapter in self.state.participants.items():
            if self._focused is not None and alias not in self._focused:
                continue
            aliases.append(alias)
            adapters.append(adapter)

        # Build context from last k rounds
        ctx = self.build_context()

        # Execute concurrently via existing coordinator
        results = asyncio.run(
            run_round(
                adapters,
                prompt,
                seed=seed,
                timeout_s=timeout_s,
                round_index=self.state.round_idx or 1,
                context_snippets=ctx,
            )
        )

        # Collect entries in order
        rr.entries = []
        for i, res in enumerate(results):
            alias = aliases[i] if i < len(aliases) else res.info.name
            # Snapshot params from bound adapters if available
            a = adapters[i]
            bound = getattr(a, "_bound", None)
            params_snapshot: Dict[str, object] = {}
            if bound is not None:
                params_snapshot = {
                    k: v
                    for k, v in {
                        "seed": getattr(bound, "seed", None),
                        "temperature": getattr(bound, "temperature", None),
                        "system": getattr(bound, "system", None),
                        "timeout_s": getattr(bound, "timeout_s", None),
                    }.items()
                    if v is not None and v != ""
                }
            rr.entries.append(
                Entry(
                    alias=alias,
                    model_id=res.info.name,
                    latency_ms=res.latency_ms,
                    ok=bool(res.text),
                    text=res.text or None,
                    error=res.error,
                    token_usage=None,
                    params_snapshot=params_snapshot,
                )
            )

        rr.completed_at = time.time()
        # Clear focus after a round
        self._focused = None
        # Persist lightweight JSON artifacts
        self._persist()
        return rr

    def _current_round(self) -> Optional[RoundRecord]:
        return self.state.history[-1] if self.state.history else None

    def _persist(self) -> None:
        try:
            root = Path("out") / "sessions" / self.state.id
            root.mkdir(parents=True, exist_ok=True)
            # Session snapshot
            session_payload = {
                "id": self.state.id,
                "started_at": self.state.started_at,
                "round_idx": self.state.round_idx,
                "max_rounds": self.state.max_rounds,
                "window_k": self.state.window_k,
                "participants": list(self.state.participants.keys()),
            }
            (root / "session.json").write_text(
                json.dumps(session_payload, indent=2), encoding="utf-8"
            )
            # Round payload
            cur = self._current_round()
            if cur is not None:
                payload = {
                    "index": cur.index,
                    "started_at": cur.started_at,
                    "completed_at": cur.completed_at,
                    "entries": [asdict(e) for e in cur.entries],
                    "synopsis": cur.synopsis,
                }
                (root / f"round-{cur.index}.json").write_text(
                    json.dumps(payload, indent=2), encoding="utf-8"
                )
        except Exception:
            # Persistence is best-effort
            pass
