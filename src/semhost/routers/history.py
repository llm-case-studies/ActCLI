from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..settings import get_default_settings
from ..schemas.history import HistoryRow


router = APIRouter()


@router.get("/history", response_model=List[HistoryRow])
def history_route(provider: str = Query(...), id: str = Query(...), limit: int = Query(50, ge=1, le=500)) -> List[HistoryRow]:
    """Best-effort usage history for a given provider:id by scanning out/sessions/*.

    Matches entries whose model_id contains the given id token. For providers that
    label adapter names with suffixes (e.g., "(codex-cli)", "(gemini-cli)", "(local)", "(cloud)"),
    we match by prefix before the suffix.
    """
    st = get_default_settings()
    sessions_root = Path(st.output_dir) / "sessions"
    if not sessions_root.exists():
        return []
    rows: List[HistoryRow] = []
    # Normalize tokens
    id_tok = str(id).strip()
    prov = (provider or "").strip().lower()
    try:
        for sess_dir in sorted(sessions_root.iterdir()):
            if not sess_dir.is_dir():
                continue
            session_id = sess_dir.name
            session_created_at: float = 0.0
            sess_file = sess_dir / "session.json"
            if sess_file.exists():
                try:
                    sj = json.loads(sess_file.read_text())
                    session_created_at = float(sj.get("started_at") or 0.0)
                except Exception:
                    session_created_at = 0.0
            for round_file in sorted(sess_dir.glob("round-*.json")):
                try:
                    rj = json.loads(round_file.read_text())
                except Exception:
                    continue
                round_index = int(rj.get("index") or 0)
                started_at = float(rj.get("started_at") or 0.0)
                entries = rj.get("entries") or []
                for e in entries:
                    model_id = str(e.get("model_id") or "")
                    # Extract base id before suffix "(xxx)"
                    base = model_id.split("(", 1)[0]
                    if not base:
                        continue
                    if id_tok and id_tok not in base:
                        continue
                    # Optional provider hint: skip if suffix implies a different provider
                    if prov:
                        if prov == "ollama" and not model_id.endswith("(local)"):
                            continue
                        if prov == "codex_cli" and "(codex-cli)" not in model_id:
                            continue
                        if prov == "gemini_cli" and "(gemini-cli)" not in model_id:
                            continue
                        if prov in ("openai", "anthropic", "google") and not model_id.endswith("(cloud)"):
                            continue
                    ok = bool(e.get("ok"))
                    latency_ms = int(e.get("latency_ms") or 0)
                    text = str(e.get("text") or "")
                    excerpt = text.strip().replace("\n", " ")[:160]
                    rows.append(
                        HistoryRow(
                            session_id=session_id,
                            session_created_at=session_created_at,
                            round_index=round_index,
                            alias=str(e.get("alias") or ""),
                            ok=ok,
                            latency_ms=latency_ms,
                            text_excerpt=excerpt,
                            started_at=started_at,
                        )
                    )
    except Exception as e:
        # Best-effort; surface error as 500 only if directory exists but unreadable entirely
        raise HTTPException(status_code=500, detail=f"history scan error: {e}")
    # Newest-first by started_at then limit
    rows.sort(key=lambda r: (r.started_at, r.round_index), reverse=True)
    return rows[: limit]

