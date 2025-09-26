Install (MV3 Extension)

Prereqs
- Chromium/Chrome with MV3 support
- Semhost running locally (optional for MCP logging)

Steps
1) Open chrome://extensions
2) Enable Developer Mode
3) Load unpacked → select `extensions/generic-chat-bridge/`
4) Click the extension icon → set Semhost URL if needed
5) Open a Playground page and Pick → Validate

Troubleshooting
- If Validate fails on file:// pages, serve via HTTP (e.g., `python -m http.server 4400`).
- Health button checks current selectors on the page.

