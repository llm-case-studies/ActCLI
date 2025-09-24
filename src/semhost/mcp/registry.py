from __future__ import annotations

from typing import List
from ..schemas.mcp_runtime import ToolMeta


def list_tools() -> List[ToolMeta]:
    """Return MCP tool metadata available in this runtime.

    MVP: advertise excel.inspect only, with a JSON schema for params.
    """
    excel_params = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path on server (RO mount, e.g., /mnt/ro/...)"},
            "lint": {"type": "boolean", "default": True},
            "extract_vba": {"type": "boolean", "default": True},
            "password": {"type": "string"},
        },
        "required": ["path"],
        "additionalProperties": False,
    }
    return [
        ToolMeta(
            id="excel.inspect",
            title="Excel Inspect (static preflight)",
            profile="core",
            params_schema=excel_params,
            description="Static inspection of Excel workbooks (no macro execution). Emits JSON/MD report and artifacts.",
        )
    ]

