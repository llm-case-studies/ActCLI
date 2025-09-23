from __future__ import annotations

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class SemhostSettings(BaseSettings):
    """Runtime settings for Semhost.

    Sprint 1 focuses on app config and CORS.
    """

    bind_host: str = Field(default="127.0.0.1", alias="SEMHOST_BIND")
    bind_port: int = Field(default=7530, alias="SEMHOST_PORT")

    # Comma-separated origins (no wildcard by default)
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="SEMHOST_CORS_ORIGINS",
    )

    # Optional knobs for future sprints
    ollama_host: str = Field(default="http://127.0.0.1:11435", alias="OLLAMA_HOST")
    output_dir: str = Field(default="out", alias="OUTPUT_DIR")
    # Optional PATH extension for vendor CLIs (e.g., ~/.npm-global/bin)
    cli_paths: List[str] = Field(default_factory=list, alias="SEMHOST_CLI_PATHS")
    # Include stderr snippets in responses when CLI errors occur
    cli_debug: bool = Field(default=False, alias="SEMHOST_CLI_DEBUG")
    # Timeout for provider doctor CLI probes (seconds)
    cli_probe_timeout_s: int = Field(default=12, alias="SEMHOST_CLI_PROBE_TIMEOUT_S")
    # Disable vendor CLI MCP/tools globally (best-effort)
    cli_disable_tools: bool = Field(default=True, alias="SEMHOST_CLI_DISABLE_TOOLS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v):  # type: ignore[override]
        if v is None or isinstance(v, list):
            return v or []
        # Accept comma or whitespace separated
        parts = [p.strip() for p in str(v).replace("\n", ",").replace(" ", ",").split(",") if p.strip()]
        return parts

    @field_validator("cli_paths", mode="before")
    @classmethod
    def _parse_cli_paths(cls, v):  # type: ignore[override]
        if v is None:
            return []
        if isinstance(v, list):
            return v
        # Accept os.pathsep (:) or comma/space
        s = str(v)
        for sep in (":", ",", " "):
            s = s.replace(sep, ",")
        return [p.strip() for p in s.split(",") if p.strip()]


def get_default_settings() -> SemhostSettings:
    return SemhostSettings()
