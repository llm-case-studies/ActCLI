# Browser Extension Implementation Guide

**Source**: Web colleague implementation specifications
**Date**: September 25, 2025
**For**: Codex-BrExt + Claude-BrExt teams
**Context Window**: 100K budget with 5-6K pinned working set

## Working Set Discipline (Context Management)

### Pin Once at Session Start (≤6K tokens):
- BrExt v0.2 Spec core (goals, participant interface, UX flow, selector rules)
- Minimal event shapes: `participants.register`, `participant.send_text`, `participants.message`, `events.log`
- OSS E2E plan (Playground + Rocket.Chat + Zulip + Mattermost/Element)
- Install/CORS checklist

### Live Editing Rule:
- **Never paste whole bundles** - one TS/JS file at a time
- Summarize other files in 3-5 bullets ("shape cards")
- Keeps per-turn context ~12-20K tokens, well under 100K ceiling

## Sprint Kickoff Board (GitHub Issues)

Create 7 issues with labels `BrExt, A1-A7`:

### **A1 - Picker & Overlay (Codex-BrExt)**
- Shadow-DOM overlay with hover highlight
- Tooltip shows role/name for elements
- 3-click capture: Input → Send → History
- Immediate Validate UI (dry-run keystrokes + MutationObserver)
- **DOD**: Works on Playground `textarea.html` and `contenteditable.html`

### **A2 - Selector Engine (Codex-BrExt)**
- ARIA-first priority, proximity to "Send/Reply"
- Pruned CSS fallback, contenteditable via `beforeinput`/`input` events
- Same-origin frames only, clear error for cross-origin
- **DOD**: Unit tests for selector scoring & fallback order

### **A3 - Runtime & Bridge (Codex-BrExt)**
- Resolve selectors, focus/type/click interactions
- Serialize visible appends from History via MutationObserver
- Pause & Re-learn on failure (no silent retries)
- **DOD**: 10 sequential messages roundtrip without misses

### **A4 - Storage & Profiles (Codex-BrExt)**
- Per-origin selector profiles in `chrome.storage`
- Health check on tab load, import/export functionality
- **DOD**: Re-open page → auto-resolve profile and pass Validate

### **A5 - MCP & Evidence (Codex-BrExt)**
- `/mcp/rpc` calls: `participants.register`, `participants.message`, `events.log`
- Listen to `participant.send_text` over SSE/WS
- Append provenance to `audit.json` (origin, selector hashes, timestamps)
- **DOD**: Events appear in `out/sessions/.../audit.json`

### **A6 - Playground & OSS E2E (Claude-BrExt)**
- `playground/`: `textarea.html`, `contenteditable.html`, `virtualized.html`, `iframe.html`
- Docker scripts for Rocket.Chat + Zulip
- Playwright E2E: Learn→Validate→Connect→Run→Mutate→Re-learn
- **DOD**: CI green on Playground, Rocket.Chat, Zulip

### **A7 - QA & Docs (Claude-BrExt)**
- `docs/install.md`, `docs/usage.md`, `docs/test-matrix.md`
- **DOD**: Cross-platform triad scenario - 2 humans + Llama-3-8B as equal participants

## Minimal Scaffolding

### Folder Layout
```
extensions/generic-chat-bridge/
├── src/
│   ├── background/        # service worker: MCP calls, SSE/WS
│   ├── content/           # picker overlay + runtime
│   ├── ui/                # popup + options
│   └── shared/            # selector engine, storage, messaging
├── playground/            # test HTML pages
├── docs/                  # install, usage, test-matrix
└── tests/e2e/             # playwright config + specs
```

### Manifest V3 (Minimal)
```json
{
  "name": "ActCLI Web Chat Bridge",
  "manifest_version": 3,
  "version": "0.1.0",
  "permissions": ["activeTab", "scripting", "storage"],
  "host_permissions": ["http://localhost:7530/*", "http://127.0.0.1:7530/*"],
  "background": { "service_worker": "background/index.js" },
  "action": { "default_popup": "ui/popup.html" },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content/index.js"],
    "all_frames": true,
    "run_at": "document_idle"
  }]
}
```

### NPM Scripts
```json
{
  "scripts": {
    "dev": "vite build --watch",
    "build": "vite build",
    "dev:playground": "ws --directory playground --port 4400",
    "e2e": "playwright test"
  }
}
```

## Installation & Setup

### Build Process
```bash
cd extensions/generic-chat-bridge
pnpm install
pnpm build
```

### Load in Browser
1. Open `chrome://extensions`
2. Toggle "Developer Mode"
3. Click "Load unpacked" → select `extensions/generic-chat-bridge/dist`
4. Configure Semhost URL in extension Options: `http://localhost:7530`
5. Add origin to `SEMHOST_CORS_ORIGINS` if CORS errors occur (dev only)

### First Run Test
```bash
pnpm dev:playground    # → http://localhost:4400/textarea.html
```
Pick → Validate → Connect → send test message from Studio/CLI

## E2E Test Plan (OSS Only)

### Playground Tests
- **Learn→Validate→Connect→Run**: 10 messages
- **DOM Mutation**: Verify Re-learn prompt triggers
- **Virtualized History**: Test observer functionality
- **Same-Origin Iframe**: Test frame handling

### Docker OSS Targets
- **Rocket.Chat + Zulip**: Login test users, connect BrExt participants
- **Roundtrip**: 10 messages each way, visible text only
- **Provenance**: Verify audit.json entries

### Triad Scenario
- Two BrExt humans (Rocket.Chat + Zulip) + Llama-3-8B (Ollama)
- Verify all three use identical participant interface
- Capture session logs showing uniform treatment

## First Edit Instructions (Codex-BrExt)

**Goal**: Land A1 + A2 in one session without context churn

### Implementation Order:
1. **`content/overlay.ts`**: Hover highlight + tooltip with role/name
2. **`shared/selectors.ts`**: Priority order (ARIA/role → proximity → stable attrs → pruned CSS)
3. **`content/learn.ts`**: Record {input,send,history} + `chrome.storage` per-origin profiles
4. **Validate Flow**: Focus input → fire `beforeinput`/`input` → preview click → MutationObserver → show ✅/retry

### Success Criteria:
- Playground pass on `textarea.html` & `contenteditable.html`
- Pin 1-page spec excerpt + event shapes
- Paste only one file at a time to stay under 100K

## First Test Instructions (Claude-BrExt)

**Goal**: Prove end-to-end on Playground, then Docker targets

### Implementation Order:
1. **Playwright**: `chat-bridge.spec.ts` with Learn→Validate→Connect→Run→Mutate→Re-learn
2. **Docker CI**: Rocket.Chat & Zulip with seeded users
3. **Evidence Validation**: Confirm `participants.message` events in `audit.json`
4. **Triad Scenario**: 2 humans + Llama-3-8B transcript capture

## Acceptance Checklist

**Must Pass**:
- [ ] Uniform participant interface (no special-casing in Semhost/Studio)
- [ ] Playground + Rocket.Chat + Zulip green in CI
- [ ] Re-learn triggers on selector breakage (no silent failures)
- [ ] `audit.json` has `web_bridge_event` records (origin, selector hashes, timestamps)

## Why This Fits Cleanly

1. **Thin Transport**: BrExt uses existing MCP envelope and audit writer - no new backend
2. **OSS Targets**: Playground + Docker keep tests deterministic and ToS-free
3. **Production Standards**: Acceptance criteria mirror current RPC/SSE/evidence bar
4. **Local-First**: Aligns with ActCLI's hybrid/offline posture

---

**Ready to Execute**: This guide provides everything needed for immediate Sprint 1 kickoff!