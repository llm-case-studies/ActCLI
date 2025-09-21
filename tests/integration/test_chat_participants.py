from __future__ import annotations

from pathlib import Path

from actcli.commands.chat import run_roundtable


def test_duplicate_participants_via_aliases(tmp_path: Path) -> None:
    md = tmp_path / "seminar.md"
    run_roundtable(
        prompt="Test",
        multi="A=echo,B=echo",
        rounds=1,
        timeout_s=2,
        save=str(md),
        audit=None,
        presenter_state=None,
        ollama_host=None,
    )
    text = md.read_text()
    assert text.count("### A ") + text.count("### B ") >= 2

