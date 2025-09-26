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
            "path": {
                "type": "string",
                "description": "Absolute path on server (RO mount, e.g., /mnt/ro/...)",
            },
            "lint": {"type": "boolean", "default": True},
            "extract_vba": {"type": "boolean", "default": True},
            "password": {"type": "string"},
        },
        "required": ["path"],
        "additionalProperties": False,
    }
    web_bridge_events_schema = {
        "type": "object",
        "properties": {
            "event": {"type": "string", "description": "Event name (e.g., web_bridge_event)"},
            "origin": {"type": "string", "description": "Tab origin, e.g., https://chat.example"},
            "participant_id": {"type": "string"},
            "data": {"type": "object"},
            "session_id": {"type": "string"},
        },
        "required": ["event"],
        "additionalProperties": True,
    }

    participants_register_schema = {
        "type": "object",
        "properties": {
            "origin": {"type": "string"},
            "display_name": {"type": "string"},
            "capabilities": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["send_text", "recv_text"],
            },
            "participant_id": {"type": "string"},
            "session_id": {"type": "string"},
        },
        "required": ["origin", "display_name"],
        "additionalProperties": True,
    }

    participants_message_schema = {
        "type": "object",
        "properties": {
            "participant_id": {"type": "string"},
            "text": {"type": "string"},
            "origin": {"type": "string"},
            "session_id": {"type": "string"},
        },
        "required": ["participant_id", "text"],
        "additionalProperties": True,
    }

    return [
        ToolMeta(
            id="excel.inspect",
            title="Excel Inspect (static preflight)",
            profile="core",
            params_schema=excel_params,
            description="Static inspection of Excel workbooks (no macro execution). Emits JSON/MD report and artifacts.",
        ),
        ToolMeta(
            id="participants.register",
            title="Participants • Register",
            profile="custom",
            params_schema=participants_register_schema,
            description="Register a web UI participant (ActCLI experimental bridge).",
        ),
        ToolMeta(
            id="participants.message",
            title="Participants • Message",
            profile="custom",
            params_schema=participants_message_schema,
            description="Forward a message from a web UI participant.",
        ),
        ToolMeta(
            id="events.log",
            title="Events • Log",
            profile="custom",
            params_schema=web_bridge_events_schema,
            description="Append an event to audit log (web bridge provenance).",
        ),
    ]
