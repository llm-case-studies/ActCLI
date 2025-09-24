from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import List


router = APIRouter()


@router.get("/fs/ro/list")
def fs_ro_list(
    path: str = Query(default="/mnt/ro", description="Absolute path under /mnt/ro"),
    limit: int = Query(default=500, ge=1, le=5000),
) -> List[dict]:
    try:
        base = Path("/mnt/ro").resolve()
        p = Path(path).resolve()
        if not str(p).startswith(str(base)):
            raise HTTPException(status_code=400, detail="path must be under /mnt/ro")
        if not p.exists():
            raise HTTPException(status_code=404, detail="path not found")
        entries: List[dict] = []
        if p.is_dir():
            # List entries (limited), sorted by name
            for child in sorted(p.iterdir(), key=lambda x: x.name)[: limit]:
                try:
                    entries.append({
                        "name": child.name,
                        "path": str(child),
                        "type": ("dir" if child.is_dir() else "file"),
                        "size": (child.stat().st_size if child.is_file() else None),
                    })
                except Exception:
                    continue
            return entries
        else:
            # Return single file info
            return [{
                "name": p.name,
                "path": str(p),
                "type": "file",
                "size": p.stat().st_size,
            }]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

