from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

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
from .routers import pricing as pricing_router
from .routers import conversations as conversations_router
from .routers import chat as chat_router
from .routers import history as history_router
from .routers import mcp_runtime as mcp_runtime_router
from .routers import admin as admin_router
from .routers import discovery as discovery_router
from .routers import mcp_transport as mcp_transport_router


def create_app(settings: SemhostSettings | None = None) -> FastAPI:
    st = settings or get_default_settings()
    app = FastAPI(title="ActCLI Semhost", version="1.0.0")

    # Extend PATH for vendor CLIs if configured
    if st.cli_paths:
        existing = os.environ.get("PATH", "")
        os.environ["PATH"] = os.pathsep.join(st.cli_paths + [existing])
    if getattr(st, "cli_disable_tools", True):
        os.environ["ACTCLI_DISABLE_CLI_MCP"] = "1"

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
    app.include_router(pricing_router.router)
    app.include_router(conversations_router.router)
    app.include_router(chat_router.router)
    app.include_router(history_router.router)
    app.include_router(admin_router.router)
    app.include_router(discovery_router.router)
    app.include_router(mcp_runtime_router.router)
    app.include_router(mcp_transport_router.router)

    # Serve built SPA (if present) at /ui
    try:
        ui_dir = os.path.join(os.getcwd(), "studio", "dist")
        if os.path.isdir(ui_dir):
            app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="ui")
    except Exception:
        pass

    # Ephemeral state: reset status on app creation (Sprint 1)
    _deps.reset_status()

    return app
