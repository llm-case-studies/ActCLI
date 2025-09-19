from __future__ import annotations

import importlib
from pathlib import Path


def test_mcp_config_merge_and_save(tmp_path: Path, monkeypatch) -> None:
    # Ensure module constants point to tmp dirs by setting XDG and CWD before import
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr("pathlib.Path.cwd", staticmethod(lambda: tmp_path))

    mod = importlib.import_module("actcli.mcp.config")
    mod = importlib.reload(mod)

    # Write a global config with server 'a'
    mod.GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
    mod.GLOBAL_FILE.write_text(
        """
[servers.a]
url = "http://global-a"
enabled = true
log = false
        """.strip()
        + "\n",
        encoding="utf-8",
    )
    # Write project config with 'a' overridden and 'b' added
    mod.get_project_dir().mkdir(parents=True, exist_ok=True)
    mod.get_project_file().write_text(
        """
[servers.a]
url = "http://project-a"
enabled = true
log = true

[servers.b]
url = "http://project-b"
enabled = false
log = false
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    cfg = mod.load_mcp_config()
    assert "a" in cfg.servers and "b" in cfg.servers
    assert cfg.servers["a"].url == "http://project-a"  # project overrides global
    assert cfg.servers["a"].log is True

    # Save round-trip project config
    cfg.servers["b"].enabled = True
    mod.save_project_mcp_config(cfg)
    text = mod.get_project_file().read_text()
    assert "[servers.a]" in text and "[servers.b]" in text
    assert "url = \"http://project-b\"" in text

