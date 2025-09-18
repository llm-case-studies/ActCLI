# ActCLI Tasks

Track progress with simple checkboxes. Mark [x] when done.

## WOW Prototype (Roundtable)
- [x] Concurrent fan-out coordinator (asyncio)
- [x] Echo adapter for no-network demo
- [x] Ollama adapter + project-local server (./models)
- [x] Models list/pull with progress
- [x] First-run doctor and status header
- [x] Chat REPL with /models, /rounds, /ollama

## Auth & Providers
- [x] Auth commands (status/login/logout) with API-key baseline
- [ ] Device/PKCE auth where supported (OpenAI/Anthropic/Google)
- [ ] Cloud adapters: OpenAI, Anthropic, Google

## IO & Partner Packs
- [ ] io profile (schema + DQ)
- [ ] io map (map.yaml) + preview
- [ ] io validate (JSON Schema)
- [ ] pack init scaffolder + fixtures
- [ ] db pull/push connectors
- [ ] deliver sftp/https
- [ ] REPL: /map, /schema, /db, /deliver

## Governance & Outputs
- [x] Git-MCP client + local fallback
- [x] pr prepare/link commands
- [ ] actcli.toml (persist config like ollama_host)
- [ ] Transcript writer + audit-lite toggle
- [ ] Synthesis improvements (agreements/disagreements)
- [ ] Unit tests and coverage (≥80% on new code)

