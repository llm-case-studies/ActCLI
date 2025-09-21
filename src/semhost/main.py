from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import SemhostSettings, get_default_settings
from . import deps as _deps
from .routers import health as health_router
from .routers import status as status_router
from .routers import models as models_router
from .routers import providers as providers_router
from .routers import sessions as sessions_router
from .routers import ws as ws_router
from .routers import mcp as mcp_router
from .routers import locations as locations_router


def create_app(settings: SemhostSettings | None = None) -> FastAPI:
    st = settings or get_default_settings()
    app = FastAPI(title="ActCLI Semhost", version="1.0.0")

    # CORS: allow specific SPA origins only; no credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=st.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["content-type"],
    )

    # Routers (Sprint 1)
    app.include_router(health_router.router)
    app.include_router(status_router.router)
    app.include_router(models_router.router)
    app.include_router(providers_router.router)
    app.include_router(sessions_router.router)
    app.include_router(ws_router.router)
    app.include_router(mcp_router.router)
    app.include_router(locations_router.router)

    # Ephemeral state: reset status on app creation (Sprint 1)
    _deps.reset_status()

    return app
