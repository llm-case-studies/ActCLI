from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from ..events import get_event_bus


def _safe_read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def export_conversation(
    session_id: str,
    *,
    out_root: Path,
    format: Literal["md", "json", "zip"] = "md",
    compact: Literal["none", "window", "summarize"] = "none",
    window_k: int = 2,
    include_events: bool = False,
) -> Path:
    # Read persisted artifacts from out/sessions/<id>
    src_root = Path("out") / "sessions" / session_id
    if not src_root.exists():
        raise FileNotFoundError(f"session artifacts not found: {src_root}")

    conv_root = out_root / "conversations" / session_id
    conv_root.mkdir(parents=True, exist_ok=True)

    # Load session
    session = _safe_read_json(src_root / "session.json")
    # Collect round files
    rounds = sorted(src_root.glob("round-*.json"), key=lambda p: p)
    if compact in ("window", "summarize") and window_k > 0:
        rounds = rounds[-window_k:]

    # Build markdown report (simple concise form)
    md_lines = [
        f"# Seminar Report — {session_id}",
        "",
        f"Rounds: {len(rounds)}",
        f"Participants: {', '.join(session.get('participants', []))}",
        "",
    ]
    for rp in rounds:
        rj = _safe_read_json(rp)
        idx = rj.get("index")
        md_lines.append(f"## Round {idx}")
        for e in rj.get("entries", []):
            alias = e.get("alias")
            ok = e.get("ok")
            text = (e.get("text") or "").strip()
            if compact == "summarize" and len(text) > 240:
                text = text[:240] + "…"
            if not text and e.get("error"):
                text = f"(error: {e.get('error')})"
            md_lines.append(f"- {alias}: {text}")
        md_lines.append("")

    out_md = conv_root / "seminar.md"
    out_md.write_text("\n".join(md_lines), encoding="utf-8")

    # Emit event
    try:
        bus = get_event_bus()
        import asyncio

        asyncio.get_event_loop().create_task(
            bus.emit(session_id, "export_saved", {"path": str(out_md)})
        )
    except Exception:
        pass

    return out_md
