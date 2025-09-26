from __future__ import annotations

import subprocess


from actcli.seminar.adapters.codex_cli import CodexCLIAdapter


def test_codex_cli_parsing_filters_echo(monkeypatch):
    # Pretend codex is present
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")

    class _P:
        def __init__(self, stdout: str = "", stderr: str = "", code: int = 0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = code

    # Simulate output that includes metadata + echoed prompt and a real answer block
    sample = (
        "model: gpt-4o-mini\n"
        "provider: openai\n"
        "System: Use brief answers\n\n"
        "Original prompt: Q\n"
        "--------\n"
        "Here is an answer to your question.\n"
        "It is not just echoing.\n"
    )

    def _run(args, capture_output, text, timeout):
        return _P(stdout=sample, stderr="", code=0)

    monkeypatch.setattr(subprocess, "run", _run)

    adapter = CodexCLIAdapter(model="gpt-4o-mini")
    out = adapter.generate("Q", timeout_s=5)
    assert "answer" in out.lower()
    assert out.strip() != "Q"
