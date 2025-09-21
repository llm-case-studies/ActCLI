from __future__ import annotations

import subprocess

import pytest

from actcli.seminar.adapters.codex_cli import CodexCLIAdapter


def test_codex_cli_missing_binary(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(RuntimeError):
        CodexCLIAdapter()


def test_codex_cli_parse_output(monkeypatch):
    # Pretend codex exists
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")

    sample = (
        "[2025-09-20T21:22:31] OpenAI Codex v0.30.0 (research preview)\n"
        "--------\n"
        "workdir: /path\n"
        "model: gpt-5\n"
        "provider: openai\n"
        "[2025-09-20T21:22:31] User instructions:\n"
        "Say hi in one sentence.\n"
        "[2025-09-20T21:22:46] thinking\n\n"
        "Hi there—how can I help you today?\n"
        "[2025-09-20T21:22:46] codex\n\n"
        "Hi there—how can I help you today?\n"
    )

    class _CP:
        def __init__(self):
            self.returncode = 0
            self.stdout = sample
            self.stderr = ""

    def _run(cmd, capture_output, text, timeout):
        return _CP()

    monkeypatch.setattr(subprocess, "run", _run)

    a = CodexCLIAdapter(model="default")
    out = a.generate("Say hi in one sentence.")
    assert "Hi there" in out


def test_codex_cli_timeout(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/codex")

    def _run(cmd, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(subprocess, "run", _run)

    a = CodexCLIAdapter()
    with pytest.raises(RuntimeError) as ei:
        a.generate("Q", timeout_s=1)
    assert "timeout" in str(ei.value).lower()

