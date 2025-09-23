from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..schemas.providers import (
    CliLoginRequest,
    CliLoginResponse,
    DoctorRow,
    CliModelSwitchRequest,
    CliModelSwitchResponse,
)
from ..services.providers_service import providers_doctor_rows, providers_login, providers_switch_model
from ..deps import get_settings
from fastapi import HTTPException


router = APIRouter()


@router.get("/providers/doctor", response_model=list[DoctorRow])
def providers_doctor_route() -> List[DoctorRow]:
    return providers_doctor_rows()


@router.post("/auth/cli/login", response_model=CliLoginResponse)
def auth_cli_login_route(req: CliLoginRequest) -> CliLoginResponse:
    return providers_login(req)


@router.post("/providers/cli/model", response_model=CliModelSwitchResponse)
def providers_cli_model_route(req: CliModelSwitchRequest) -> CliModelSwitchResponse:
    return providers_switch_model(req)


@router.get("/providers/settings")
def providers_settings_get() -> dict:
    st = get_settings()
    return {
        "cli_probe_timeout_s": getattr(st, "cli_probe_timeout_s", 12),
        "cli_debug": getattr(st, "cli_debug", False),
    }


@router.patch("/providers/settings")
def providers_settings_patch(body: dict) -> dict:
    st = get_settings()
    if "cli_probe_timeout_s" in body:
        try:
            val = int(body["cli_probe_timeout_s"])
            st.cli_probe_timeout_s = max(1, val)  # type: ignore[attr-defined]
        except Exception:
            raise HTTPException(status_code=400, detail="invalid cli_probe_timeout_s")
    if "cli_debug" in body:
        st.cli_debug = bool(body["cli_debug"])  # type: ignore[attr-defined]
    return {
        "cli_probe_timeout_s": getattr(st, "cli_probe_timeout_s", 12),
        "cli_debug": getattr(st, "cli_debug", False),
    }
