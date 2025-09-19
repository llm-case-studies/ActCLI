from __future__ import annotations

import json
from pathlib import Path

from actcli.commands.chat import run_roundtable


def test_roundtable_echo_only(tmp_path: Path, monkeypatch) -> None:
    # Use echo adapters only by passing unknown identifiers (resolved to EchoAdapter)
    md = tmp_path / "seminar.md"
    audit = tmp_path / "audit.json"
    run_roundtable(
        prompt="Compare A vs B",
        multi="echo,echo2",
        rounds=2,
        timeout_s=2,
        ollama_host=None,
        save=str(md),
        audit=str(audit),
        presenter_state=None,
    )
    assert md.exists() and audit.exists()
    data = json.loads(audit.read_text())
    assert 0.0 <= data.get("disagreement_score", 0.0) <= 1.0

