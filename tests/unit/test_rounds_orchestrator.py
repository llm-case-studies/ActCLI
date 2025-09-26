from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from actcli.seminar.rounds import RoundOrchestrator
from actcli.seminar.adapters.echo import EchoAdapter
from actcli.seminar.factory import AdapterFactory
from actcli.models.participant import ParticipantSpec


class SleepAdapter:
    def __init__(self, name: str, sleep_s: float) -> None:
        self.name = name
        self.is_local = True
        self.model_version = "test"
        self._sleep_s = sleep_s

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        seed: int | None = None,
        temperature: float | None = None,
        timeout_s: int = 30,
        round_index: int = 1,
        context_snippets: str | None = None,
    ) -> str:  # noqa: E501
        time.sleep(self._sleep_s)
        return "slow"


def chdir_tmp(tmp_path: Path) -> None:
    os.chdir(tmp_path)


def test_barrier_with_timeout_and_two_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    chdir_tmp(tmp_path)
    orch = RoundOrchestrator(window_k=2, max_rounds=5)
    A = EchoAdapter(name="A")
    B = EchoAdapter(name="B")
    C = SleepAdapter("C", sleep_s=0.2)
    orch.set_participants({"A": A, "B": B, "C": C})
    orch.start()
    rr = orch.run_current_round(prompt="Q", seed=1, timeout_s=0.05)
    assert rr.completed_at is not None
    assert len(rr.entries) == 3
    oks = [e for e in rr.entries if e.ok]
    errs = [e for e in rr.entries if not e.ok]
    assert len(oks) == 2
    assert len(errs) == 1 and (errs[0].error == "timeout")


def test_windowing_includes_only_last_k_rounds(tmp_path: Path) -> None:
    chdir_tmp(tmp_path)
    orch = RoundOrchestrator(window_k=1)
    A = EchoAdapter(name="A")
    B = EchoAdapter(name="B")
    orch.set_participants({"A": A, "B": B})
    orch.start()
    rr1 = orch.run_current_round(prompt="First", seed=1, timeout_s=1)
    assert any("Answer (simulated)" in (e.text or "") for e in rr1.entries)
    orch.next_round()
    rr2 = orch.run_current_round(prompt="First", seed=1, timeout_s=1)
    # Context builder uses last k=1 round, which should be rr2 now
    ctx = orch.build_context()
    assert "Refinement based on peers' snippets:" in ctx
    assert "Answer (simulated)" not in ctx


def test_params_snapshot_and_mood_application(tmp_path: Path) -> None:
    chdir_tmp(tmp_path)
    # Build a participant with pre-bound params
    spec = ParticipantSpec(
        alias="E1",
        provider="echo",
        model_id="echo",
        host=None,
        params={"temperature": 0.7, "system": "Hello"},
    )
    a = AdapterFactory.from_spec(spec, allow_cloud=True)
    orch = RoundOrchestrator(window_k=0)
    orch.set_participants({"E1": a})
    orch.start()
    rr = orch.run_current_round(prompt="Hi", seed=1, timeout_s=1)
    assert len(rr.entries) == 1
    e = rr.entries[0]
    assert e.params_snapshot.get("temperature") == 0.7
    assert "Hello" in (e.params_snapshot.get("system") or "")
    assert e.ok and e.text and "(temp=0.70)" in e.text


def test_persistence_creates_session_files(tmp_path: Path) -> None:
    chdir_tmp(tmp_path)
    orch = RoundOrchestrator(window_k=0)
    orch.set_participants({"A": EchoAdapter("A")})
    orch.start()
    rr = orch.run_current_round(prompt="persist", seed=None, timeout_s=1)
    assert rr.completed_at is not None
    # Files exist under out/sessions/<id>/
    root = Path("out") / "sessions" / orch.state.id
    assert (root / "session.json").exists()
    assert (root / f"round-{rr.index}.json").exists()
