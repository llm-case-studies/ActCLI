Usage (Picker → Validate → Connect)

- Pick Elements: Click input → send → history. Escape cancels.
- Validate: Simulates typing, clicks send, observes history append.
- Connect: Registers a participant via Semhost MCP and logs events.
- Profiles: Per-origin via chrome.storage; import/export supported.

MCP Calls
- participants.register: { origin, display_name, capabilities, participant_id }
- participants.message: { participant_id, text, origin }
- events.log: { event, origin, participant_id?, data? }

Audit
- Semhost appends `web_bridge_event` records to `out/audit.json` for provenance.

