from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class ExcelDepsMissing(RuntimeError):
    pass


def _ensure_deps() -> None:
    try:
        import openpyxl  # noqa: F401
    except Exception as e:
        raise ExcelDepsMissing(
            "Excel explorer requires optional dependency 'openpyxl'. Install with: pip install -e .[excel]"
        ) from e


def inspect_workbook(path: str) -> Dict[str, Any]:
    """Lightweight, no-execution workbook inspection (xlsx/xlsm).

    - Does not execute macros; uses openpyxl in read-only mode.
    - Returns a concise JSON-compatible dict suitable for export.
    """
    _ensure_deps()
    from openpyxl import load_workbook  # type: ignore

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    kind = p.suffix.lower().lstrip(".")

    keep_vba = kind == "xlsm"
    wb = load_workbook(filename=str(p), read_only=True, data_only=False, keep_vba=keep_vba)

    # Macro presence (no execution)
    has_macros = bool(getattr(wb, "vba_archive", None))

    # Sheets summary
    sheets: List[Dict[str, Any]] = []
    for ws in wb.worksheets:
        # Use calculate_dimension to avoid scanning all cells
        try:
            dim = ws.calculate_dimension()  # e.g., 'A1:C42'
        except Exception:
            dim = "A1"
        sheets.append(
            {
                "name": ws.title,
                "dimension": dim,
            }
        )

    # Defined names (workbook-level)
    names: List[str] = []
    try:
        for dn in wb.defined_names.definedName:  # type: ignore[attr-defined]
            names.append(str(getattr(dn, "name", "")))
    except Exception:
        pass

    # External links (best-effort)
    ext_links = []
    try:
        for link in getattr(wb, "_external_links", []) or []:
            tgt = getattr(link, "file_link", None)
            if tgt is not None:
                ext_links.append(str(tgt))
    except Exception:
        pass

    payload: Dict[str, Any] = {
        "workbook": {
            "path": str(p.resolve()),
            "kind": kind,
            "application": "Microsoft Excel",
            "has_macros": has_macros,
        },
        "sheets": sheets,
        "defined_names": names,
        "external_links": ext_links,
        "explorer_version": "1.0.0-poc",
    }

    try:
        wb.close()
    except Exception:
        pass
    return payload


def write_report_json(payload: Dict[str, Any], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path

