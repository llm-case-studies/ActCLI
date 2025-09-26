# TIER 0 Refactoring Migration Notes

Status: Completed (All production blockers eliminated)

Scope:
- Typed wire protocols (schemas for events, rounds, sessions)
- Structured exceptions with standardized HTTP mapping
- Reconnection stability (rate limiting + circuit breaker)
- Job/session persistence (SQLite + WAL)
- Centralized logging with request correlation

Compatibility Summary:
- No breaking changes to API contracts or event payload shapes.
- SSE/WebSocket events maintain original envelope; now emitted via typed models.
- Error responses remain `{ "detail": "..." }` with the same status codes.
- Persistence is additive; API behavior unchanged.

Key Additions:
- Schemas: `src/semhost/schemas/events.py` and new round request models in `schemas/sessions.py`.
- Errors: `src/semhost/errors.py` with global handler registered in `main.py`.
- Stability: EventBus rate limit and circuit breaker (defaults generous).
- Persistence: `src/semhost/services/persistence.py` + DB init in app startup.
- Logging: `src/semhost/logging.py` + middleware for `request_id` propagation.

New Configuration (env vars):
- `SEMHOST_DB_PATH` (default `out/semhost.db`)
- `SEMHOST_LOG_LEVEL` (default `INFO`)
- `SEMHOST_LOG_JSON` (default `true`)
- `SEMHOST_WS_CONNS_PER_MIN` (default `120`)
- `SEMHOST_WS_FAIL_THRESHOLD` (default `50`)
- `SEMHOST_WS_COOLDOWN_S` (default `10`)

Event Contracts (unchanged shape):
```json
// round_start
{ "type": "round_start", "session_id": "...", "index": 1, "prompt": "..." }

// turn_result
{ "type": "turn_result", "session_id": "...", "index": 1, "alias": "...", "ok": true, "latency_ms": 123, "text": "...", "error": null }

// round_end
{ "type": "round_end", "session_id": "...", "index": 1 }

// artifacts_saved
{ "type": "artifacts_saved", "session_id": "...", "index": 1 }
```

Logging & Tracing:
- Pass `X-Request-Id` to propagate a custom request id into all logs.
- Logs are JSON by default. To disable: set `SEMHOST_LOG_JSON=false`.
- Session routes emit `session_created`, `session_patched`, `round_start`, `round_end` with `session_id` and `round_index`.

Persistence Notes:
- SQLite DB created at `out/semhost.db` by default (WAL mode).
- Session metadata is upserted on create/patch.
- Rounds and entries are persisted upon completion (best effort).

Golden Fixtures:
- Added under `tests/data/golden/` for event envelopes and round record/entry keys.
- Contract tests verify actual payloads are supersets of golden keys.

Operational Guidance:
- Rate limiting and breaker thresholds are generous; tune via env if needed.
- Persistence is non-blocking; failures do not break API flows.
- Error patterns should use `DomainError` classes instead of `HTTPException`.

