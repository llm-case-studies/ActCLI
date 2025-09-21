from __future__ import annotations

import pytest

from actcli.seminar.rounds import RoundOrchestrator


@pytest.mark.skip(reason="Scaffold: to be implemented by Codex-J")
def test_barrier_with_timeout_and_two_success() -> None:
    orch = RoundOrchestrator(window_k=2, max_rounds=5)
    # TODO: inject three participants, one slow/timeout
    assert orch is not None


@pytest.mark.skip(reason="Scaffold: to be implemented by Codex-J")
def test_windowing_includes_only_last_k_rounds() -> None:
    orch = RoundOrchestrator(window_k=2)
    # TODO: seed history and verify build_context slices
    assert orch.build_context() == ""


@pytest.mark.skip(reason="Scaffold: to be implemented by Codex-J")
def test_params_snapshot_and_mood_application() -> None:
    orch = RoundOrchestrator()
    # TODO: verify that per-participant temperature/system are captured per round
    assert orch.state.window_k == 2

