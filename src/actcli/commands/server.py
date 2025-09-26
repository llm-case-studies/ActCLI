from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

import httpx


OUT = Path("out")
PID_FILE = OUT / "semhost.pid"
LOG_FILE = OUT / "semhost.log"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but not ours – treat as alive
        return True


def server_start(
    host: str = "127.0.0.1",
    port: int = 7530,
    reload: bool = True,
    with_ui: bool = True,
    *,
    force: bool = False,
) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if PID_FILE.exists():
        # Validate PID file; clean up stale, or stop active if --force
        try:
            pid = int(PID_FILE.read_text().strip())
        except Exception:
            pid = -1
        if pid > 0 and _pid_alive(pid):
            if force:
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.4)
                except Exception:
                    pass
                if _pid_alive(pid):
                    try:
                        os.kill(pid, signal.SIGKILL)
                        time.sleep(0.2)
                    except Exception:
                        pass
                try:
                    PID_FILE.unlink(missing_ok=True)
                except Exception:
                    pass
            else:
                print(
                    f"Server appears running (pid={pid}). Use `actcli server stop` or `actcli server start --force`.\n"
                )
                return
        else:
            # Stale pid file
            PID_FILE.unlink(missing_ok=True)

    # Refuse to start if some other process is already serving on the port
    url = f"http://{host}:{port}/health"
    try:
        with httpx.Client(timeout=1.5) as client:
            r = client.get(url)
            if r.status_code == 200:
                print(
                    f"A server is already responding at {url}. If this is an orphaned instance, stop it and retry."
                )
                return
    except Exception:
        pass
    cmd = [
        "uvicorn",
        "semhost.main:create_app",
        "--factory",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")
    env = os.environ.copy()
    if with_ui:
        # Semhost auto-serves studio/dist if present; nothing special needed here
        pass
    log = LOG_FILE.open("ab", buffering=0)
    p = subprocess.Popen(cmd, stdout=log, stderr=log, env=env)
    PID_FILE.write_text(str(p.pid), encoding="utf-8")
    print(f"Semhost started pid={p.pid} on http://{host}:{port} (logs: {LOG_FILE})")


def server_status(host: str = "127.0.0.1", port: int = 7530) -> None:
    url = f"http://{host}:{port}/health"
    try:
        with httpx.Client(timeout=2.0) as client:
            r = client.get(url)
            if r.status_code == 200:
                print(f"Semhost OK: {r.json()}")
                return
    except Exception:
        pass
    if PID_FILE.exists():
        pid = PID_FILE.read_text().strip()
        print(f"Semhost not responding at {url} but pid file exists: pid={pid}")
    else:
        print("Semhost not running (no pid file and /health failed)")


def _kill_by_port(port: int) -> bool:
    """Best-effort: find and kill processes listening on TCP port.

    Uses lsof or fuser if available. Returns True if at least one pid was signaled.
    """
    import shutil
    import subprocess

    killed = False
    try:
        if shutil.which("lsof"):
            p = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=2
            )
            pids = [int(x) for x in (p.stdout or "").split() if x.strip().isdigit()]
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.2)
                    if _pid_alive(pid):
                        os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
                killed = True
            return killed
        if shutil.which("fuser"):
            # fuser -k sends SIGKILL by default on some systems; be explicit with -TERM first
            subprocess.run(
                ["fuser", "-k", f"{port}/tcp"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return True
    except Exception:
        pass
    return killed


def server_stop(
    host: str = "127.0.0.1", port: int = 7530, *, force_port: bool = False
) -> None:
    if not PID_FILE.exists():
        print("No pid file; server may not be running.")
        # If /health responds and --force-port, attempt port kill
        if force_port:
            try:
                with httpx.Client(timeout=1.5) as client:
                    r = client.get(f"http://{host}:{port}/health")
                    if r.status_code == 200:
                        if _kill_by_port(port):
                            print(f"Killed process bound to :{port}.")
                        else:
                            print(f"Could not identify process for :{port}.")
                        return
            except Exception:
                pass
        return
    pid_s = PID_FILE.read_text().strip()
    try:
        pid = int(pid_s)
    except Exception:
        print(f"Invalid pid in {PID_FILE}: {pid_s}")
        return
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
    except Exception as e:
        print(f"Failed to stop pid={pid}: {e}")
    # Remove pid file regardless (best-effort cleanup)
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    # If something is still serving at the port, optionally kill by port
    if force_port:
        try:
            with httpx.Client(timeout=1.5) as client:
                r = client.get(f"http://{host}:{port}/health")
                if r.status_code == 200:
                    if _kill_by_port(port):
                        print(f"Killed process bound to :{port}.")
        except Exception:
            pass
    print("Semhost stopped.")


def server_logs(tail: bool = False) -> None:
    if not LOG_FILE.exists():
        print("No logs found.")
        return
    if tail:
        # Very simple tail -f loop
        try:
            with LOG_FILE.open("r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.25)
                        continue
                    print(line, end="")
        except KeyboardInterrupt:
            return
    else:
        print(LOG_FILE.read_text(encoding="utf-8", errors="ignore"))
