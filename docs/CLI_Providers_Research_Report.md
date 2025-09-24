# CLI Providers — Research Report (Sprint)

This report summarizes our experiments with dynamic model discovery and one‑off chat testing across Codex CLI, Claude CLI, and Gemini CLI. The goal was to remove hardcoded model lists and rely on providers' own CLIs to determine available models, while making research fast via a batch endpoint.

## Summary of Findings

- Codex CLI
  - Reliable model: `gpt-5-codex` (works consistently).
  - "Default/current/none/empty/absent" passed literally as `--model` are rejected upstream (400 Unsupported model).
  - Reasoning labels displayed as "medium" regardless of requested level in this environment (likely build-dependent).
  - Action: Prefer explicit `gpt-5-codex`. Treat "default-ish" values by omitting `--model` entirely (use CLI session default); add one-time fallback to `gpt-5-codex` when unsupported.

- Claude CLI
  - Works: `default` (omit `--model`, uses current selection), `sonnet`, legacy full ID `claude-3-5-sonnet-20241022`.
  - Not accepted: `opus`, `claude-4-*` (CLI returns unknown error).
  - Action: Prefer `sonnet` or omit model. Add tolerant alias mapping (e.g., `claude-sonnet`, `sonne`) → `sonnet`.

- Gemini CLI
  - Works: `gemini-2.5-pro`, `gemini-2.5-flash`, also `gemini-1.5-pro-latest`, `gemini-1.5-flash-latest`.
  - 2.5‑flash is faster; 2.5‑pro higher quality. Disable tools to avoid CLI tool noise.
  - Action: Prefer 2.5 where available; keep 1.5 as fallback.

## Implementation Highlights

- Dynamic discovery module (`src/actcli/models/discovery.py`)
  - Parses interactive `/model` menus for Claude and Codex.
  - Safe by default (skips under tests or when disabled by env).

- Model listings and SPA integration
  - Registry functions call discovery and cache results (`~/.config/actcli/cache/models/*.json`).
  - We will add a strict mode and a refresh query so API/UI can show only discovered models.

- Research‑friendly batch API
  - `POST /chat/batch` runs multiple 1×1 variants in a single request with per-variant model, params, and toggles.

- Admin endpoints
  - `POST /admin/shutdown` and `/admin/restart` for quick recovery; works even when PID files are stale.

## Next Changes (planned)

1) Codex “default” semantics and fallback
   - Treat `null`, `""`, `"default"`, `"current"`, `"none"` as: omit `--model` and use CLI session selection.
   - If output indicates "Unsupported model", pre-switch to `gpt-5-codex` and retry once.

2) Claude alias normalization
   - Map common variants (e.g., `claude-sonnet`, `sonne`, `sonnet-4`) to `sonnet`.

3) Strict discovery for listings
   - API: `/models?refresh=1&strict=1` shows only dynamically discovered CLI models (no fallbacks).
   - New: `/providers/cli/discover?provider=claude_cli&raw=1` returns parsed + raw menu output.

4) CLI Help harvesting (for future auto-adaptation)
   - New endpoint: `/providers/cli/help?provider=...` captures `--help` output.
   - Future: feed help/menu outputs into the seminar to detect new flags/models and update adapters automatically.

## Practical Recommendations

- Use `codex_cli:gpt-5-codex` explicitly for Codex today.
- For Claude CLI, use `sonnet` or omit model to rely on the CLI default.
- For Gemini CLI, prefer `gemini-2.5-pro` and `gemini-2.5-flash`.
- Use `/chat/batch` for rapid prompt/model sweeps; set `raw=false` and `disable_tools=true` for clean, fast outputs.

