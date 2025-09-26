from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional

from ..deps import get_settings

_LOCK = threading.Lock()
_CONN: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _CONN
    if _CONN is not None:
        return _CONN
    st = get_settings()
    db_path = getattr(st, "db_path", "out/semhost.db")
    # Ensure parent exists
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL for better concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    _CONN = conn
    return conn


def init_db() -> None:
    with _LOCK:
        conn = _get_conn()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                window_k INTEGER NOT NULL,
                max_rounds INTEGER,
                participants_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS rounds (
                session_id TEXT NOT NULL,
                idx INTEGER NOT NULL,
                started_at REAL NOT NULL,
                completed_at REAL,
                synopsis TEXT,
                PRIMARY KEY(session_id, idx)
            );
            CREATE TABLE IF NOT EXISTS entries (
                session_id TEXT NOT NULL,
                round_idx INTEGER NOT NULL,
                alias TEXT NOT NULL,
                model_id TEXT,
                ok INTEGER NOT NULL,
                latency_ms INTEGER NOT NULL,
                text TEXT,
                error TEXT,
                params_snapshot_json TEXT,
                PRIMARY KEY(session_id, round_idx, alias)
            );
            """
        )
        conn.commit()


def upsert_session(
    *,
    session_id: str,
    created_at: float,
    window_k: int,
    max_rounds: Optional[int],
    participants: List[Dict[str, Any]],
) -> None:
    payload = json.dumps(participants)
    with _LOCK:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO sessions(id, created_at, window_k, max_rounds, participants_json)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                window_k=excluded.window_k,
                max_rounds=excluded.max_rounds,
                participants_json=excluded.participants_json
            """,
            (session_id, float(created_at), int(window_k), max_rounds, payload),
        )
        conn.commit()


def persist_round(
    *, session_id: str, index: int, started_at: float, completed_at: Optional[float], synopsis: Optional[str], entries: List[Dict[str, Any]]
) -> None:
    with _LOCK:
        conn = _get_conn()
        conn.execute(
            """
            INSERT INTO rounds(session_id, idx, started_at, completed_at, synopsis)
            VALUES(?, ?, ?, ?, ?)
            ON CONFLICT(session_id, idx) DO UPDATE SET
                started_at=excluded.started_at,
                completed_at=excluded.completed_at,
                synopsis=excluded.synopsis
            """,
            (session_id, int(index), float(started_at), completed_at, synopsis),
        )
        # Upsert entries
        for e in entries:
            params_json = json.dumps(e.get("params_snapshot") or {})
            conn.execute(
                """
                INSERT INTO entries(session_id, round_idx, alias, model_id, ok, latency_ms, text, error, params_snapshot_json)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, round_idx, alias) DO UPDATE SET
                    model_id=excluded.model_id,
                    ok=excluded.ok,
                    latency_ms=excluded.latency_ms,
                    text=excluded.text,
                    error=excluded.error,
                    params_snapshot_json=excluded.params_snapshot_json
                """,
                (
                    session_id,
                    int(index),
                    str(e.get("alias", "")),
                    e.get("model_id"),
                    1 if e.get("ok") else 0,
                    int(e.get("latency_ms") or 0),
                    e.get("text"),
                    e.get("error"),
                    params_json,
                ),
            )
        conn.commit()


def list_sessions_basic() -> List[Dict[str, Any]]:
    """Return minimal info for session pickers from DB (optional helper)."""
    with _LOCK:
        conn = _get_conn()
        cur = conn.execute(
            "SELECT id, created_at, window_k, max_rounds, participants_json FROM sessions ORDER BY created_at DESC"
        )
        rows: List[Dict[str, Any]] = []
        for r in cur.fetchall():
            parts = []
            try:
                parts = [p.get("alias") for p in json.loads(r["participants_json"]) if p.get("alias")]
            except Exception:
                parts = []
            rows.append(
                {
                    "id": r["id"],
                    "created_at": r["created_at"],
                    "window_k": r["window_k"],
                    "max_rounds": r["max_rounds"],
                    "participants": parts,
                }
            )
        return rows
