from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path
from typing import Optional

import httpx


OUT = Path("out")
PID_FILE = OUT / "semhost.pid"
LOG_FILE = OUT / "semhost.log"


def server_start(host: str = "127.0.0.1", port: int = 7530, reload: bool = True, with_ui: bool = True) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if PID_FILE.exists():
        print(f"Server appears running (pid file exists at {PID_FILE}). Try `actcli server status` or `actcli server stop`.\n")
        return
    cmd = [
        "uvicorn",
        "semhost.main:create_app",
        "--factory",
        "--host", host,
        "--port", str(port),
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


def server_stop() -> None:
    if not PID_FILE.exists():
        print("No pid file; server may not be running.")
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
    try:
        PID_FILE.unlink(missing_ok=True)
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

