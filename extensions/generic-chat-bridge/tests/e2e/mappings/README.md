Mappings for Real Sites (Optional)

Place site-specific selector mappings here to reuse across runs.

Example: rocketchat.json
{
  "origin": "http://127.0.0.1:3000",
  "input": "[contenteditable=\"true\"][role=\"textbox\"]",
  "send": "__ENTER__",
  "history": "[role=\"list\"]"
}

Notes
- `send` may be `__ENTER__` for Enter-to-submit flows.
- These files are not auto-generated; export from the popup (Export Profile) and copy here, or edit manually.
- Tests look for `mappings/rocketchat.json` and inject mapping if present; otherwise fall back to overlay picking.

