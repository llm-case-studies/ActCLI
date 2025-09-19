from __future__ import annotations

from pathlib import Path
from typing import Any

from typer.testing import CliRunner


class _ClientOK:
    def __init__(self, **kw: Any) -> None:
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def get(self, url: str):
        # /health
        class R:
            status_code = 200
            def json(self):
                return {"ok": True}
        return R()
    def head(self, url: str):
        class R:
            status_code = 204
        return R()


def test_mcp_commands_lifecycle(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    # Isolate config and cwd
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.chdir(tmp_path)

    # Ensure httpx calls in mcp module don't hit the network
    import actcli.commands.mcp as mcp_cmd
    monkeypatch.setattr(mcp_cmd.httpx, "Client", _ClientOK)

    # Add a server and toggle states
    cli_mod = __import__("importlib").import_module("actcli.cli")
    r = runner.invoke(cli_mod.app, ["mcp", "add", "test", "--url", "http://svc"])
    assert r.exit_code == 0
    r = runner.invoke(cli_mod.app, ["mcp", "on", "test"])
    assert r.exit_code == 0
    r = runner.invoke(cli_mod.app, ["mcp", "log", "test", "--enable"])
    assert r.exit_code == 0
    r = runner.invoke(cli_mod.app, ["mcp", "test", "test"])
    assert r.exit_code == 0

    # Config persisted under project .actcli
    proj_cfg = tmp_path / ".actcli" / "mcp.toml"
    assert proj_cfg.exists()
    text = proj_cfg.read_text()
    assert "[servers.test]" in text and "http://svc" in text
