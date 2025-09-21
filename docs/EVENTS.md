# Runtime Events & Hooks (Draft)

Updated: 2025-09-19

This document describes the runtime events ActCLI can emit, where they go, and how optional hooks work.

## Goals
- Help users and reviewers understand what is recorded (and what is not).
- Provide a stable interface for observability and optional automation.
- Keep privacy first: default is minimal, hashed, local-only.

## Where Events Go
- Stream file: `out/events.ndjson` (one JSON object per line)
- Audit-lite: when enabled, a subset of events is embedded in the audit JSON
- Presenter: independent; reads `out/presenter/state.json` (not the events stream)

## Event Types (minimum viable set)
- `session_start` { session_id }
- `session_end` { session_id }
- `mode_change` { from, to }
- `user_prompt_submit` { prompt_hash, length }
- `model_generate_start` { model_id, is_local }
- `model_generate_end` { model_id, ok, latency_ms, error? }
- `synthesis_emitted` { disagreement_score }
- `trust_change` { scope }
- `cloud_share_change` { on }
- `artifact_saved` { kind: transcript|audit|presenter, path }
- `mcp_attach` { name, url, enabled }
- `mcp_test` { name, result: healthy|unreachable|error }

Notes
- `prompt_hash` is a truncated SHA-256; no prompt text is stored by default.
- For tool calls (future), record `args_hash` and duration, never raw args.

## Hooks (disabled by default)
- Types: `session_start`, `user_prompt_submit`, `pre_tool_use`, `post_tool_use`, `notification`
- Location: `.actcli/hooks/` (project root)
- Config: `hooks.toml`, per-event lists of scripts and timeouts
- Safety & policy:
  - Hooks run only in trusted workspaces and only when explicitly enabled
  - Short timeouts (5–10s), constrained env (no secrets), working dir = project root
  - No network by default; can be enabled per hook

## Consent ("Blessing Points")
- Enabling cloud sharing (cloud_share=true)
- Enabling hooks (and which events)
- Owner-mode control over MCPs (start/reload/stop)
- Pushing to Git remotes (PR prepare/link)

See Architecture for system flows and controls: `./ARCHITECTURE.md`.

