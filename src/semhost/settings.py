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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_origins(cls, v):  # type: ignore[override]
        if v is None or isinstance(v, list):
            return v or []
        # Accept comma or whitespace separated
        parts = [p.strip() for p in str(v).replace("\n", ",").replace(" ", ",").split(",") if p.strip()]
        return parts


def get_default_settings() -> SemhostSettings:
    return SemhostSettings()

