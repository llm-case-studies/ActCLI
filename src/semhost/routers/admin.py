from __future__ import annotations

from fastapi import APIRouter
import os
import signal
import threading
import time


router = APIRouter()


def _deferred_sigterm(delay_s: float = 0.2) -> None:
    def _go() -> None:
        time.sleep(delay_s)
        try:
            os.kill(os.getpid(), signal.SIGTERM)
        except Exception:
            # Last resort: hard exit
            os._exit(0)

    t = threading.Thread(target=_go, daemon=True)
    t.start()


@router.post("/admin/shutdown")
def admin_shutdown_route() -> dict:
    """Gracefully stop the current Semhost process.

    Notes:
    - If running under `uvicorn --reload`, the reloader parent may restart automatically.
    - Otherwise, the server will stop; restart via `actcli server start`.
    """
    _deferred_sigterm()
    return {"ok": True, "action": "shutdown"}


@router.post("/admin/restart")
def admin_restart_route() -> dict:
    """Request a restart.

    Implementation detail: sends SIGTERM to the current process.
    If supervised (reload/systemd), the supervisor will respawn; otherwise this
    behaves like shutdown and you should start the server again.
    """
    _deferred_sigterm()
    return {
        "ok": True,
        "action": "restart",
        "note": "If supervised, it will restart; else it stops.",
    }
