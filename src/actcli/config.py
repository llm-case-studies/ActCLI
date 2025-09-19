from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from platformdirs import user_config_dir

try:
    import tomllib as toml  # py311+
except Exception:  # pragma: no cover
    import tomli as toml  # type: ignore


PROJECT_FILE = "actcli.toml"


@dataclass
class Defaults:
    mode: str = "hybrid"  # offline|hybrid
    audit_level: str = "off-lite"  # full|off-lite
    seed: int = 42
    output_dir: str = "out"
    models: str = "llama3,claude,gpt"
    ollama_host: Optional[str] = None


@dataclass
class Config:
    project_name: Optional[str] = None
    project_version: Optional[str] = None
    defaults: Defaults = field(default_factory=Defaults)


def _parse_config(path: Path) -> Config:
    data = toml.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    proj = data.get("project", {})
    defaults = data.get("defaults", {})
    cfg = Config(
        project_name=proj.get("name"),
        project_version=proj.get("version"),
        defaults=Defaults(
            mode=defaults.get("mode", Defaults.mode),
            audit_level=defaults.get("audit_level", Defaults.audit_level),
            seed=int(defaults.get("seed", Defaults.seed)),
            output_dir=defaults.get("output_dir", Defaults.output_dir),
            models=defaults.get("models", Defaults.models),
            ollama_host=defaults.get("ollama_host"),
        ),
    )
    return cfg


def load_config(cwd: Optional[Path] = None) -> tuple[Config, Optional[Path]]:
    """Load config from project file or user config dir. Returns (config, path)."""
    cwd = cwd or Path.cwd()
    proj_path = cwd / PROJECT_FILE
    if proj_path.exists():
        return _parse_config(proj_path), proj_path
    # Fallback to user config
    udir = Path(user_config_dir("actcli", "actcli"))
    udir.mkdir(parents=True, exist_ok=True)
    user_path = udir / PROJECT_FILE
    return _parse_config(user_path), (user_path if user_path.exists() else None)


def write_project_config(path: Path, cfg: Config) -> None:
    lines = [
        "[project]",
        f"name = \"{cfg.project_name or Path.cwd().name}\"",
        f"version = \"{cfg.project_version or '0.1'}\"",
        "",
        "[defaults]",
        f"mode = \"{cfg.defaults.mode}\"",
        f"audit_level = \"{cfg.defaults.audit_level}\"",
        f"seed = {cfg.defaults.seed}",
        f"output_dir = \"{cfg.defaults.output_dir}\"",
        f"models = \"{cfg.defaults.models}\"",
    ]
    if cfg.defaults.ollama_host:
        lines.append(f"ollama_host = \"{cfg.defaults.ollama_host}\"")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

