ActCLI Web Chat Bridge (Experimental)

Overview
- Purpose: Human collaboration bridge to let actuaries join ActCLI seminars from any web chat UI.
- Scope: Element picker + selector profiles (per-origin), validate flow, storage. No provider-specific automation.
- Integration: Future MCP calls to Semhost for participants.register/participants.message/events.log.

Status
- MVP scaffolding only: manifest, popup, background, content overlay, and local playground pages.
- ToS safety: OSS-only testing; no references to proprietary chat providers.

Load Unpacked
1) Open chrome://extensions → Enable Developer Mode
2) Load unpacked → select `extensions/generic-chat-bridge/`
3) Open a test page (see `playground/`) and click the extension icon.

Basic Flow
- Pick Elements: Click input → send → history.
- Validate: Simulates typing and send; observes history append.
- Profiles: Stored per-origin via `chrome.storage.local`.

Playground
- Start a static server or open the files directly:
  - `playground/textarea.html`
  - `playground/contenteditable.html`
  - `playground/virtualized.html`
  - `playground/iframe.html`

Notes
- This is plain JS/HTML; no bundler required. Keep permissions minimal.
- The code intentionally avoids background automation and respects human-paced usage.
