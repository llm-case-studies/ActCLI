from __future__ import annotations

from typing import Any, Dict, Generator
from pathlib import Path
import json
import time


def _append_audit(record: Dict[str, Any]) -> None:
    try:
        out_dir = Path("out")
        out_dir.mkdir(parents=True, exist_ok=True)
        audit_path = out_dir / "audit.json"
        try:
            existing = json.loads(audit_path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
        existing.append(record)
        audit_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    except Exception:
        # Non-fatal: do not break streaming if audit write fails
        pass


def stream(job_id: str, params: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """Stream events for web-bridge tools.

    Supported ids (routed externally):
    - participants.register
    - participants.message
    - events.log
    """
    tool = params.get("__tool_id") or params.get("tool") or "events.log"
    ts = int(time.time())
    # Normalize params (copy)
    p: Dict[str, Any] = dict(params)
    p.pop("__tool_id", None)
    p.pop("tool", None)

    # Audit record shape
    base = {
        "event": "web_bridge_event",
        "job": job_id,
        "tool": str(tool),
        "ts": ts,
    }

    # Progress
    yield {"event": "progress", "job": job_id, "pct": 5, "msg": f"{tool} received"}

    try:
        rec = {**base, "params": p}
        _append_audit(rec)
        yield {
            "event": "ok",
            "job": job_id,
            "ok": True,
            "result": {"noted": True, "ts": ts},
        }
    except Exception as e:  # pragma: no cover - non-fatal
        yield {
            "event": "fault",
            "job": job_id,
            "ok": False,
            "error": f"{type(e).__name__}",
        }

