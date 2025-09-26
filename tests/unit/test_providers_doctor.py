from __future__ import annotations

import subprocess

from actcli.commands.providers import providers_doctor


def test_providers_doctor_handles_absent_bins(monkeypatch, capsys):
    # No binaries present
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    providers_doctor()
    out = capsys.readouterr().out
    assert "codex_cli" in out and "claude_cli" in out


def test_providers_doctor_ok(monkeypatch, capsys):
    # Fake presence and versions, simulate successful probes
    monkeypatch.setattr("shutil.which", lambda cmd: f"/usr/bin/{cmd}")

    class _P:
        def __init__(self, stdout="ok", stderr="", code=0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = code

    def _run(args, capture_output, text, timeout):
        if args[:2] == ["codex", "exec"]:
            return _P(stdout="done")
        if args[:2] == ["claude", "-p"]:
            return _P(stdout='{"text": "ok"}')
        if args[-1] == "--version":
            return _P(stdout=f"{args[0]} v0")
        return _P()

    monkeypatch.setattr(subprocess, "run", _run)

    providers_doctor()
    out = capsys.readouterr().out
    assert "ok" in out
