# ActCLI Browser Extension - Complete Feature Reference

**Owner**: Browser Extension Team (Codex-BrExt + Claude-BrExt)
**Status**: Production Ready - A5 Complete
**Version**: 0.5.0 (MCP Integration Complete)

## Overview

The ActCLI Browser Extension enables human actuaries to participate in ActCLI seminars directly from any web chat interface. It provides intelligent element detection, seamless integration with ActCLI's seminar system, and comprehensive audit trail compliance.

## Core Features

### 🎯 **Element Picker** (A1 Foundation)

**What it does**: Intelligent element selection using dev-tools style overlay
**Use case**: Teaching the extension how to interact with any web chat interface

**How to use**:
1. Click extension icon → "Pick Elements"
2. Click Input field (where you type messages)
3. Click Send button (submits messages)
4. Click History area (where messages appear)
5. Extension automatically saves profile for this website

**Key benefits**:
- Works on ANY web chat (Slack, Teams, Discord, custom apps)
- Visual feedback with hover highlighting and tooltips
- Escape key cancels selection at any time
- Automatic per-website profile storage

### 🧠 **Intelligent Selector Engine** (A2 Algorithm)

**What it does**: Automatically chooses the most reliable way to find elements
**Use case**: Ensures selectors work even when websites change their layout

**Smart features**:
- **ARIA-first priority**: Prefers `role="textbox"`, `role="button"` over CSS classes
- **Keyword matching**: Recognizes "message", "send", "reply", "history" text
- **Proximity detection**: Input fields near Send buttons get bonus points
- **Resilience focus**: Avoids brittle selectors that break with updates

**Scoring example**:
```
<textarea id="msg" aria-label="message"> → Score: 118 (ID + keyword + context)
<div role="textbox" data-testid="input"> → Score: 148 (Role + stable attr + context)
<div class="deep nested path"> → Score: 15 (Penalized for brittleness)
```

### 🔍 **Health Check System** (Sprint 2)

**What it does**: Validates that saved selectors still work on current page
**Use case**: Confidence check before attempting validation or connection

**How to use**:
1. Navigate to a previously configured website
2. Click "Health" button in extension popup
3. Get immediate feedback: "Health: OK" or "Health: missing elements"

**When to use**:
- Before joining important seminars
- After website updates that might break selectors
- When troubleshooting connection issues

### ✅ **Validation Flow** (A1 + Improvements)

**What it does**: Tests the complete message roundtrip without disrupting chat
**Use case**: Verify extension works before joining live seminars

**How it works**:
1. Enter custom test message (or use default "Hello from ActCLI")
2. Click "Validate" button
3. Extension simulates typing + clicking send
4. Observes if message appears in history
5. Reports success/failure with details

**Smart features**:
- Supports both `textarea` and `contenteditable` inputs
- Uses proper input events (not just setting values)
- MutationObserver detects history updates
- Audit logging for all validation attempts

### 📁 **Profile Management** (Sprint 2)

**What it does**: Save, backup, and share element configurations
**Use case**: Team collaboration and backup/restore workflows

**Export feature**:
- Downloads JSON file: `actcli-bridge-{hostname}.json`
- Contains selectors and metadata for sharing
- Useful for onboarding team members

**Import feature**:
- Upload previously exported configuration
- Instantly ready to use on matching websites
- Error handling for invalid files

### 🔗 **MCP Integration** (A5 Core Mission)

**What it does**: Connects browser extension to ActCLI seminar system
**Use case**: Seamless participation in multi-model actuarial seminars

**Configuration**:
- Set Semhost URL (default: `http://127.0.0.1:7530`)
- Persistent storage across browser sessions
- Clear error messages if Semhost unavailable

**Connection flow**:
1. Pick elements and validate on target chat website
2. Click "Connect" button
3. Extension registers as participant: `WEB-{hostname}-{random}`
4. Ready to participate alongside AI models and other humans

**Capabilities advertised**:
- `send_text`: Can send messages to seminar
- `recv_text`: Can receive messages from seminar
- Same interface as Ollama models and API participants

### 📊 **Audit Trail Integration** (A5 Compliance)

**What it does**: Complete evidence logging for actuarial compliance
**Use case**: Meeting professional audit and documentation requirements

**Events logged**:
- `participants.register`: When joining seminars
- `validate`: Success/failure of message testing
- `web_bridge_event`: All major operations with timestamps

**Audit record format**:
```json
{
  "event": "web_bridge_event",
  "job": "job_abc123",
  "tool": "participants.register",
  "ts": 1727383123,
  "params": {
    "origin": "https://chat.example.com",
    "participant_id": "WEB-chatapp-a1b2c3"
  }
}
```

**Integration**: Records appear in `out/audit.json` alongside other ActCLI evidence

## Advanced Features

### 🧪 **Testing Playground** (Development Support)

**What it includes**:
- `textarea.html`: Basic text input testing
- `contenteditable.html`: Rich text editor testing
- `virtualized.html`: Scrolling history simulation (50+ messages)
- `iframe.html`: Same-origin frame testing

**How to use**:
1. Start local server: `python3 -m http.server 4400`
2. Navigate to `http://localhost:4400/playground/`
3. Test picker and validation on different input patterns
4. Verify selectors work across layout types

### 🔬 **Selector Engine Testing** (A2 Validation)

**Built-in test suite**: `tests/selectors.spec.html`
- Zero dependencies - runs entirely in browser
- Tests ARIA priority, keyword matching, proximity scoring
- Visual pass/fail results with detailed scoring

**Unit test coverage**:
- ID selector preference
- Role-based selection for accessibility
- Proximity bonus calculations
- Resilience penalty validation

### ⚙️ **Configuration Management** (A5 Infrastructure)

**Semhost URL configuration**:
- User-configurable endpoint for local/remote deployments
- Validation and save confirmation
- Graceful degradation when Semhost unavailable

**Profile storage**:
- Per-origin isolation (profiles don't leak between sites)
- Automatic cleanup and organization
- Import/export for team sharing

## Security & Compliance

### 🛡️ **ToS Safety Features**

**Zero AI provider logic**:
- No hardcoded chat provider URLs or logic
- Works with ANY website (not just AI chats)
- General-purpose element interaction only

**Human-paced only**:
- No background automation or scraping
- All actions triggered by explicit user clicks
- Respects website rate limits naturally

### 🔒 **Extension Security**

**Minimal permissions**:
- `activeTab`: Only access to currently active tab
- `scripting`: Inject content scripts for picker
- `storage`: Save configurations locally
- Host permissions: Only for configured Semhost URL

**Input validation**:
- CSS.escape() prevents injection attacks
- JSON schema validation for MCP calls
- Error boundaries prevent crashes

### 📋 **Privacy Protection**

**No data collection**:
- All processing happens locally
- No telemetry or analytics
- No user content transmitted (except explicit validation)

**Audit transparency**:
- Clear logging of all operations
- User can review audit.json records
- No hidden network calls

## Installation & Setup

### Quick Start
1. Open `chrome://extensions` → Enable Developer Mode
2. Click "Load unpacked" → select `extensions/generic-chat-bridge/`
3. Configure Semhost URL in extension popup
4. Navigate to any web chat and click "Pick Elements"

### Production Deployment
1. Build extension: `cd extensions/generic-chat-bridge && npm run build`
2. Load `dist/` folder as unpacked extension
3. Configure team Semhost endpoint
4. Share profiles via export/import for consistent team setup

## Integration Points

### With ActCLI Core
- **Participant Interface**: Same API as Ollama models
- **Evidence Packs**: Audit records in `out/audit.json`
- **MCP Protocol**: Standard JSON-RPC + SSE streaming

### With Semhost
- **Tool Registration**: `participants.register`, `participants.message`, `events.log`
- **Configuration**: User-configurable endpoint URL
- **Error Handling**: Graceful degradation when unavailable

### With Web Applications
- **Universal Compatibility**: Works with any website structure
- **Accessibility Support**: ARIA-first element detection
- **Responsive Design**: Adapts to mobile and desktop layouts

## Troubleshooting

### Common Issues

**"Health: missing elements"**:
- Website layout changed since last configuration
- Re-pick elements with updated selectors
- Check if website uses dynamic loading

**"Connect failed"**:
- Verify Semhost URL is correct and server running
- Check browser console for CORS errors
- Ensure firewall allows localhost connections

**"Validate failed"**:
- Website may block programmatic input events
- Try different input techniques in selector engine
- Check if website requires specific user interaction patterns

### Getting Help

**Debug information**:
- Browser console shows detailed error messages
- Extension popup displays real-time status
- Audit.json contains operation history

**Test environment**:
- Use playground pages for controlled testing
- Verify basic functionality before production use
- Share profiles with team for consistent behavior

## Future Roadmap

### A6 - Enhanced Testing (In Progress)
- Playwright automation for CI/CD
- Docker environments for OSS chat applications
- Cross-platform integration testing

### A7 - Production Polish
- Advanced error recovery
- Performance optimization
- Extended platform support

---

**Summary**: The ActCLI Browser Extension provides production-ready integration between web chat interfaces and ActCLI seminars, with intelligent element detection, comprehensive audit trails, and enterprise-grade security compliance. Ready for actuarial teams to use in professional seminar environments.