from __future__ import annotations

import json
from pathlib import Path

from actcli.commands.demo import run_demo


def test_demo_pricing_rnd_writes_all_artifacts(tmp_path: Path) -> None:
    out_dir = tmp_path / "pricing-rnd"
    run_demo(scenario="pricing-rnd", out=str(out_dir))

    expected = {
        "README.md",
        "prompt.md",
        "transcript.md",
        "workpaper.md",
        "audit.json",
        "repro.sh",
    }
    found = {p.name for p in out_dir.iterdir() if p.is_file()}
    assert expected == found

    audit = json.loads((out_dir / "audit.json").read_text(encoding="utf-8"))
    participants = audit.get("participants", [])
    assert len(participants) >= 3
    for p in participants:
        assert p["local"] is True

    for name in ("README.md", "prompt.md", "workpaper.md"):
        text = (out_dir / name).read_text(encoding="utf-8").lower()
        assert "synthetic" in text, f"{name} missing 'synthetic'"

    repro = (out_dir / "repro.sh").read_text(encoding="utf-8")
    assert "/home/alex" not in repro
    assert "/Users/alex" not in repro

    transcript = (out_dir / "transcript.md").read_text(encoding="utf-8")
    assert "ActCLI Roundtable" in transcript
    assert "Synthesis" in transcript


def test_demo_pricing_rnd_unknown_scenario(tmp_path: Path) -> None:
    try:
        run_demo(scenario="nonexistent", out=str(tmp_path / "out"))
    except SystemExit as e:
        assert e.code == 2
    else:
        raise AssertionError("Expected SystemExit for unknown scenario")
