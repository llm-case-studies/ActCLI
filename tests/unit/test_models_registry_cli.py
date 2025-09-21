from __future__ import annotations

import pytest

from actcli.models.registry import list_models_codex_cli, list_models_claude_cli


def test_list_models_codex_cli(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")
    rows = list_models_codex_cli(refresh=True)
    assert any(m.model_id == "default" for m in rows)


def test_list_models_claude_cli(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/claude")
    rows = list_models_claude_cli(refresh=True)
    assert len(rows) > 0

