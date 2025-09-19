from __future__ import annotations

import json
from pathlib import Path

from actcli.seminar.adapters.base import AdapterInfo
from actcli.seminar.coordinator import TurnResult
from actcli.transcript import write_audit_json, write_presenter_state, write_transcript_md


def _result(model: str, text: str) -> TurnResult:
    info = AdapterInfo(id=model, name=model, is_local=True, model_version="0.1")
    return TurnResult(info=info, text=text, latency_ms=12)


def test_transcript_writers(tmp_path: Path) -> None:
    results = [_result("echo", "hello"), _result("echo2", "world")]
    md = tmp_path / "out.md"
    audit = tmp_path / "audit.json"
    state = tmp_path / "state.json"

    write_transcript_md(md, header="H", prompt="P", results=results, synthesis="S")
    assert md.exists()
    txt = md.read_text()
    assert "## Synthesis" in txt and "ActCLI Roundtable" in txt

    write_audit_json(audit, prompt="P", results=results, disagreement=0.25)
    data = json.loads(audit.read_text())
    assert data["prompt_len"] == 1
    assert data["disagreement_score"] == 0.25
    assert len(data["participants"]) == 2

    write_presenter_state(state, prompt="P", results=results, synthesis="S", disagreement=0.25)
    s = json.loads(state.read_text())
    assert s["prompt"] == "P"
    assert s["synthesis"] == "S"
    assert len(s["results"]) == 2

