# Assignment 001: Web Chat Bridge Implementation

**Assignment Date**: September 25, 2025
**Team**: Codex-BrExt (exploration) + Claude-BrExt (validation)
**Priority**: TIER 1 - Core Feature Development
**Estimated Effort**: 2 sprints (4 weeks)
**Token Budget**: ~100K total context (5-6K pinned working set)

## Overview
Implement a general-purpose web chat bridge that allows human participants to join ActCLI seminars from any web chat interface. The extension uses a dev-tools-style element picker and integrates via the existing Core MCP participant channel - no new backend services required.

## Strategic Positioning
**Primary Purpose**: Human collaboration bridge for ActCLI seminars
**Secondary Benefit**: Works with AI chats at user's own risk
**Integration**: Uniform participant interface (same as Ollama models, API bots)

## Technical Scope

### Core Components
- **Element Picker**: Dev-tools style overlay for user-taught selectors
- **Selector Engine**: ARIA-first with CSS fallbacks and resilience
- **MCP Integration**: Participant channel using existing `/mcp/rpc` and `/mcp/sse`
- **Evidence Logging**: Audit trail integration via `events.log` tool
- **OSS Testing**: Docker-based E2E with Rocket.Chat, Zulip, Mattermost, Element

### Architecture (Manifest V3)
```
extensions/generic-chat-bridge/
├── background/     # Service worker (MCP calls, scheduler)
├── content/        # Element picker + runtime (selectors, DOM interaction)
├── ui/             # Popup & options (Pick/Validate/Connect/Re-learn)
├── shared/         # Storage, messaging, selector scoring
├── playground/     # Local testing environment
└── tests/e2e/      # Playwright automation
```

## Participant Channel Interface

The extension speaks the same interface as other ActCLI participants:

### Registration
```json
{
  "tool": "participants.register",
  "params": {
    "channel": "web_ui",
    "origin": "https://chat.example.local",
    "display_name": "Alice @ Rocket.Chat",
    "capabilities": ["send_text", "recv_text"]
  }
}
```

### Outbound Message (Semhost → Extension)
```json
{
  "kind": "participant.send_text",
  "participant_id": "P-Alice",
  "text": "<message>"
}
```

### Inbound Message (Extension → Semhost)
```json
{
  "tool": "participants.message",
  "params": {
    "participant_id": "P-Alice",
    "text": "<visible text snippet>",
    "origin": "https://..."
  }
}
```

## UX Flow (Simple & Neutral)

1. **Pick Elements**: User selects Input, Send, History (dev-tools highlighting)
2. **Validate**: Dry-run typing, MutationObserver verification
3. **Connect**: Register as participant channel in ActCLI
4. **Run**: Relay messages bidirectionally
5. **Re-learn**: On selector breakage, prompt user to re-pick

## Selector Engine Requirements

### Priority Order:
1. **ARIA/Role**: `[role="textbox"]`, `[aria-label*="message"]`
2. **Label Proximity**: Near "Send", "Reply" text
3. **Stable Attributes**: `data-testid`, `data-qa` when present
4. **Pruned CSS**: Anchored on stable nodes, avoid `nth-child`

### Special Cases:
- **ContentEditable**: Use `beforeinput`/`input` events, not `.innerText`
- **Frames**: Same-origin only, show "cannot attach" for cross-origin
- **History**: Capture visible text from appends, ignore virtualization placeholders

## Testing Strategy (OSS Only)

### Tier 0: Local Chat Playground
- `textarea.html` - Basic text input
- `contenteditable.html` - Rich composer (Teams/Slack-like)
- `virtualized.html` - Scrolling message history
- `iframe.html` - Same-origin frame embedding

### Tier 1: OSS Servers (Docker in CI)
- **Rocket.Chat**: DM or test channel
- **Zulip**: Stream + topic
- **Mattermost**: Channel post
- **Element (Matrix)**: Room messaging

### Tier 2: Cross-Platform Triad
Two humans (Rocket.Chat + Zulip) + Llama-3-8B (Ollama) in one session. Verify bidirectional messaging through uniform participant interface.

## Area Responsibilities

| Area | Owner | Deliverables |
|------|-------|-------------|
| **A1: Picker & Overlay** | Codex-BrExt | Shadow-DOM overlay, hover highlight, 3-click capture, keyboard escape |
| **A2: Selector Engine** | Codex-BrExt | ARIA-first matching, CSS fallbacks, contenteditable typing, scoring tests |
| **A3: Runtime & Bridge** | Codex-BrExt | Connect/Disconnect, relay messages, history forwarding, re-learn on failure |
| **A4: Storage & Profiles** | Codex-BrExt | Per-origin selector profiles, import/export, health checks |
| **A5: MCP & Evidence** | Codex-BrExt | Participant registration, message handling, audit logging, retry logic |
| **A6: Playground & E2E** | Claude-BrExt | Test pages, Docker scripts, Playwright automation |
| **A7: QA & Documentation** | Claude-BrExt | User docs, evidence examples, no proprietary mentions |

## Installation & Development

### Prerequisites
- Node 20+ and pnpm
- Semhost running at `http://localhost:7530`
- Chrome/Edge/Chromium (MV3 support)

### Build Process
```bash
cd extensions/generic-chat-bridge
pnpm install
pnpm build                    # → ./dist with manifest.json
```

### Load in Browser
1. Open `chrome://extensions`
2. Toggle "Developer mode"
3. Click "Load unpacked" → select `./dist`
4. Configure Semhost URL in extension options

### CORS Configuration
Add extension origins to `SEMHOST_CORS_ORIGINS` if needed during development.

## Working Protocol

### Sprint 1 (Weeks 1-2)
**Codex-BrExt**:
1. Build element picker overlay with dev-tools highlighting
2. Implement selector engine with ARIA-first priority
3. Create runtime bridge for participant message relay
4. Write intention tests for all picker/selector scenarios

**Claude-BrExt**:
1. Set up Chat Playground with all input patterns
2. Build Docker environments for Rocket.Chat and Zulip
3. Create Playwright E2E framework
4. Run and fix Codex's tests, enhance coverage

### Sprint 2 (Weeks 3-4)
**Codex-BrExt**:
1. Integrate MCP participant registration and message handling
2. Build selector profile storage with per-origin persistence
3. Add evidence logging via `events.log` tool
4. Handle edge cases (frame detection, virtualized history)

**Claude-BrExt**:
1. Expand E2E to Mattermost and Element
2. Implement cross-platform triad test scenario
3. Create installation and usage documentation
4. Performance testing and validation

## Acceptance Criteria

### Core Functionality
- [ ] Element picker works on all Playground scenarios
- [ ] Selector engine resolves with proper fallback priority
- [ ] Participant interface matches other ActCLI channels exactly
- [ ] Evidence logging writes to `audit.json` alongside session artifacts

### Testing Coverage
- [ ] OSS E2E passes on Rocket.Chat + Zulip minimum
- [ ] Cross-platform triad: 2 humans + Llama-3-8B messaging works
- [ ] DOM mutation tests trigger re-learn (no silent failures)
- [ ] Performance: 10 sequential messages complete without drops

### Integration Quality
- [ ] Extension appears in Studio as "Connected (Web UI)" participant
- [ ] Same participant API as models - no special-case code in Semhost
- [ ] Audit records contain origin/timestamps/actions (no raw HTML)

## Risk Management
- **DOM Changes**: Multi-fallback selectors with graceful re-learning
- **Cross-Origin**: Only same-origin frames supported, clear errors otherwise
- **Scope Creep**: No protocols, no proprietary chat, stick to participant channel
- **Performance**: Human-paced only, no background automation

## Context Window Management
- **Pinned Working Set**: ~5-6K tokens (spec + snippets + E2E plan)
- **Active Development**: +2-4K per file being edited
- **Typical Session**: 12-20K tokens total
- **Max Scenario**: <100K even with multiple files + tests

## Success Metrics
- **Uniform Integration**: No special-case code paths for web participants
- **OSS Coverage**: Full green on Playground + Docker targets
- **Cross-Platform**: Human+Human+AI messaging verified
- **Resilience**: Selector failures trigger re-learn, no silent breaks
- **Audit Quality**: Complete provenance in evidence packs

## Next Assignment
After completion, Assignment 002 will focus on advanced features like multi-tab coordination and enhanced selector resilience patterns.

---

*This assignment follows the proven Codex-explore + Claude-validate pattern established by the successful Refactoring Owner team.*