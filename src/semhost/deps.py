from __future__ import annotations

from typing import Optional

from .schemas.status import Mode, Status, StatusPatch
from .settings import SemhostSettings, get_default_settings


# Ephemeral, in-memory status for Sprint 1
_STATUS: Status = Status(
    mode=Mode.OFFLINE,
    cloud_share=False,
    window_k=2,
    max_rounds=None,
    read=[],
    write=[],
)

_SETTINGS: Optional[SemhostSettings] = None


def get_settings() -> SemhostSettings:
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = get_default_settings()
    return _SETTINGS


def get_status() -> Status:
    return _STATUS


def update_status(patch: StatusPatch) -> Status:
    global _STATUS
    data = _STATUS.model_dump()
    incoming = patch.model_dump(exclude_unset=True)
    data.update(incoming)
    _STATUS = Status(**data)
    return _STATUS


def reset_status() -> None:
    global _STATUS
    _STATUS = Status(
        mode=Mode.OFFLINE,
        cloud_share=False,
        window_k=2,
        max_rounds=None,
        read=[],
        write=[],
    )
