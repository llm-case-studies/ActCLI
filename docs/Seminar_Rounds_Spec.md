# Seminar Rounds — Unlimited, Synchronized, and Tunable

Goal: Move from 2 fixed rounds to a barrier‑synchronized, multi‑round seminar with per‑participant temperature/moods.

Outcomes
- Unlimited rounds until stopped or capped (`--max-rounds`, default unlimited; soft clamp 100).
- Synchronized rounds: each participant “speaks” exactly once per round.
- Context windowing: models see only prior rounds (`--round-window` k, default 2). Optional synopsis for older rounds.
- Per‑participant temperature and mood presets (cautious/creative/friday). Values visible via `/params show`.
- Policy respected: offline mode/cloud gating enforced.

CLI & REPL Additions
- Flags: `--max-rounds`, `--round-window`
- Slash commands:
  - `/round start|next|stop|status|max|window`
  - `/temp <alias?> <0.0-1.0>`
  - `/mood <alias?> <cautious|creative|friday>`
  - `/params show`
  - `/focus <alias1,alias2>` (next round only)

Data Structures
- SessionState: id, started_at, round_idx, max_rounds?, window_k, participants{alias->ParticipantSpec}, history[RoundRecord]
- RoundRecord: index, started_at, completed_at, entries[Entry], synopsis?
- Entry: alias, model_id, latency_ms, ok, text?, error?, token_usage?, params_snapshot

Round Orchestration
- Build context frame: global prompt + last k rounds (quotes/summaries) + per‑participant system/mood.
- Fan‑out concurrently to all participants with timeout; barrier completes when all return or timeout.
- Optional similarity detector (no‑change) to prompt stop.

Moods
- cautious → temperature=0.2, system="Prefer concise, conservative judgments."
- creative → temperature=0.8, system="Explore alternatives; propose novel ideas."
- friday → temperature=0.9, system="Relaxed tone; quick heuristics; jovial ⚡"

Persistence
- Per round: `out/sessions/<id>/round-<n>.json`
- Rolling: `out/sessions/<id>/session.json`

Scaffold
- `src/actcli/seminar/rounds.py` — RoundOrchestrator with start/next/stop and context builder (signatures only)
- `src/actcli/seminar/moods.py` — presets + apply helper (no side effects)
- Extend `cli.chat` with `--max-rounds`, `--round-window`
- Extend chat REPLs to parse `/round`, `/temp`, `/mood`, `/params show`, `/focus` (initially stubbed)

Tests (scaffold)
- Unit: orchestrator barrier, windowing, similarity, params snapshot — added as `@pytest.mark.skip` placeholders.
- Integration: echo‑only unlimited rounds and command handling — added as skipped placeholders.

Acceptance (for full implementation)
- Barrier‑synchronized rounds, windowed context, moods/temperature applied, policy honored, REPL commands operative, session files persisted.

