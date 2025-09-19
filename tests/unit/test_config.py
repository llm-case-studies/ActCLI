from __future__ import annotations

from pathlib import Path

from actcli.config import Config, Defaults, PROJECT_FILE, load_config, write_project_config


def test_write_and_load_project_config(tmp_path: Path) -> None:
    cfg = Config(project_name="demo", project_version="0.1", defaults=Defaults())
    path = tmp_path / PROJECT_FILE
    write_project_config(path, cfg)
    loaded, loaded_path = load_config(cwd=tmp_path)
    assert loaded_path == path
    assert loaded.project_name == "demo"
    assert loaded.defaults.mode == cfg.defaults.mode
    assert loaded.defaults.models == cfg.defaults.models


def test_load_user_config_fallback(tmp_path: Path, monkeypatch) -> None:
    # Point user_config_dir used by module to a tmp path
    user_dir = tmp_path / "usercfg"
    monkeypatch.setattr("actcli.config.user_config_dir", lambda *a, **k: str(user_dir))
    # Write only the user config; no project file in cwd
    ufile = user_dir / PROJECT_FILE
    user_dir.mkdir(parents=True)
    ufile.write_text(
        """
[project]
name = "user-proj"
version = "9.9"

[defaults]
mode = "offline"
audit_level = "off-lite"
seed = 7
output_dir = "out"
models = "llama3"
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    loaded, loaded_path = load_config(cwd=tmp_path)
    assert loaded_path == ufile
    assert loaded.project_name == "user-proj"
    assert loaded.defaults.mode == "offline"
    assert loaded.defaults.seed == 7

