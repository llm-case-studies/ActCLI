from __future__ import annotations

import subprocess

import pytest

from actcli.seminar.adapters.gemini_cli import GeminiCLIAdapter


def test_gemini_cli_parses_json(monkeypatch):
    # Pretend gemini binary exists
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")

    class _P:
        def __init__(self, stdout: str = "", stderr: str = "", code: int = 0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = code

    payload = {"text": "Gemini says hi"}

    def _run(args, capture_output, text, timeout):
        return _P(stdout="{\n\"text\": \"Gemini says hi\"\n}", stderr="", code=0)

    monkeypatch.setattr(subprocess, "run", _run)
    adapter = GeminiCLIAdapter(model="default")
    out = adapter.generate("Hello", timeout_s=5)
    assert out.strip() == "Gemini says hi"

