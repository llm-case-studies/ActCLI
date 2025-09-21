from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..schemas.providers import CliLoginRequest, CliLoginResponse, DoctorRow
from ..services.providers_service import providers_doctor_rows, providers_login


router = APIRouter()


@router.get("/providers/doctor", response_model=list[DoctorRow])
def providers_doctor_route() -> List[DoctorRow]:
    return providers_doctor_rows()


@router.post("/auth/cli/login", response_model=CliLoginResponse)
def auth_cli_login_route(req: CliLoginRequest) -> CliLoginResponse:
    return providers_login(req)

