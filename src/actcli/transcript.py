from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .seminar.coordinator import TurnResult


@dataclass
class Participant:
    id: str
    local: bool
    version: str


def write_transcript_md(
    path: Path,
    header: str,
    prompt: str,
    results: List[TurnResult],
    synthesis: Optional[str] = None,
) -> None:
    lines = ["# ActCLI Roundtable", "", f"> {header}", "", "## Prompt", "", f"{prompt}", "", "## Responses", ""]
    for r in results:
        lines.append(f"### {r.info.name} ({'local' if r.info.is_local else 'cloud'}) — {r.latency_ms} ms")
        lines.append("")
        if r.text:
            lines.append(r.text)
        else:
            lines.append(f"_error: {r.error or 'no output'}_")
        lines.append("")
    if synthesis:
        lines.extend(["## Synthesis", "", synthesis, ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_audit_json(
    path: Path,
    prompt: str,
    results: List[TurnResult],
    disagreement: Optional[float] = None,
) -> None:
    data = {
        "actcli_version": "0.0.1",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "prompt_len": len(prompt or ""),
        "participants": [
            {"id": r.info.id, "local": r.info.is_local, "version": r.info.model_version} for r in results
        ],
        "responses": [
            {
                "id": r.info.id,
                "latency_ms": r.latency_ms,
                "ok": bool(r.text),
            }
            for r in results
        ],
    }
    if disagreement is not None:
        data["disagreement_score"] = disagreement
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_presenter_state(path: Path, *, prompt: str, results: List[TurnResult], synthesis: Optional[str], disagreement: Optional[float]) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "prompt": prompt,
        "results": [
            {
                "id": r.info.id,
                "name": r.info.name,
                "local": r.info.is_local,
                "version": r.info.model_version,
                "latency_ms": r.latency_ms,
                "text": r.text,
                "error": r.error,
            }
            for r in results
        ],
        "synthesis": synthesis,
        "disagreement": disagreement,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
