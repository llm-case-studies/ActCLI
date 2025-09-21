# Architecture & Information Flows

Updated: 2025-09-19

This diagram shows how information flows through ActCLI, what components exist, and where controls apply. Use it as a shared map for developers, compliance, and reviewers.

```mermaid
flowchart TB
  %% Top-level user loop
  U[User Terminal] --> TUI[REPL / TUI]
  TUI --> CORE[ActCLI Core]
  CORE --> POLICY[Policy / Trust Layer]

  subgraph Local Machine
    WORK[Project Workspace\n(read/write via allow-lists)]
    OLLAMA[Local Adapters (Ollama)]
    MCPCLI[MCP Client (HTTP/SSE attach-only)]
    EVENT[Event Bus]
    HOOKS[Hooks (disabled by default)]
    PRES[Presenter (local http server)]
    ART[out/: transcript.md, audit.json,\n events.ndjson, presenter state, mcp-logs/]
  end

  subgraph External Services
    OA[OpenAI API]
    AN[Anthropic API]
    GG[Google Gemini API]
    MCPS[(MCP Servers: Memory-MCP, Prior-Self-MCP, ...)]
    GIT[(Git Remote)]
  end

  %% Routing via policy
  POLICY -->|offline OR cloud_share=false| OLLAMA
  POLICY -->|cloud_share=true| OA
  POLICY -->|cloud_share=true| AN
  POLICY -->|cloud_share=true| GG

  %% MCP attach-only by default
  CORE -->|attach (enabled)| MCPCLI
  MCPCLI -->|tools.call (HTTP/SSE)| MCPS

  %% Files & presenter
  CORE <-->|read/write gated| WORK
  CORE -->|write artifacts| ART
  PRES <-->|read state.json| ART

  %% Events & hooks (opt-in)
  CORE --> EVENT
  EVENT -->|append line| ART
  EVENT -->|invoke*| HOOKS

  %% Optional Git
  CORE -->|PR prepare (optional)| GIT

  %% Guards
  classDef guard fill:#fff0,stroke:#999,stroke-dasharray:3 3
  class POLICY guard

  %% Notes
  %% * Hooks run only if explicitly enabled AND workspace trusted
```

Key Points
- Policy/Trust Layer controls model routing (offline vs cloud) and filesystem access (read/write allow-lists). Default is offline and cloud_share=false.
- MCP is attach-only by default (no start/stop). Owner mode is opt-in and gated by trust and tokens.
- Artifacts in out/: transcript, audit-lite, streaming events (NDJSON), presenter state, optional MCP logs.
- Hooks are disabled by default; enabling them requires a trusted workspace, explicit consent, and they run with strict timeouts.

Blessing Points (explicit consent required)
- Enabling cloud sharing (cloud_share=true) before any file content can leave the machine.
- Enabling hooks and choosing which events may trigger scripts.
- Owner-mode operations (start/reload/stop) for MCP servers.
- Pushing to Git remotes (PR prepare/link is user-driven).

Maintenance
- Keep this file updated when flows change (new adapters, events, artifacts).
- Cross-link from STATUS, MCP_SETUP, and other docs so reviewers always land here first.

