# ActCLI — Tier‑0 & Tier‑1 Specs for Chat REPL and Multi‑AI Seminar
**Version:** 0.1 • **Date:** 2025-09-18

> Purpose: Hand this to developers as a concrete implementation spec for the first two tiers of the ActCLI chat experience, including slash commands, offline/hybrid policy, audit/trust, and reusable “seminar” module. It is aligned with the whitepaper’s CLI‑first wedge, plugin governance, and auditability goals, and designed to be “quiet by default, helpful on demand.”

---


## 0) External inspiration (OK to share)
For CLI patterns and structure, point devs to: `https://github.com/github/spec-kit/tree/main`

---

## 1) Glossary / Scope

- **Tier‑0** (ship first): core chat REPL, status header, safety & trust, file attach with permissioning, multi‑model compare + local summarize, and the assistive→approved deterministic run bridge (`/reserve` → `/approve`).
- **Tier‑1** (week‑2 add‑ons): seminar role configs, transcript save, repro shortcut, plugin verify, optional git commit.
- **Modes**: `offline` (default) and `hybrid` (cloud allowed *until* sensitive attachments appear; then auto‑lock to local for the session).

Non‑goals here: long‑running multi‑agent “debates,” cloud secrets manager, or full RBAC (later milestone).

---

## 2) UX contract

### 2.1 Status line (always visible above prompt)
```
ActCLI • chat(seminar) • MODE: OFFLINE • participants: llama3, claude • audit: ON
```
- Updates instantly when `/mode` or `/models` change.
- On first `/attach` in `hybrid`, switch to **LOCAL ONLY** for session and append a “handoff” event to the audit record.

### 2.2 First‑run hints (per project, once)
Show 3 bullets (Trust/Audit • Local/Hybrid • Seminar) and two copy‑pasteable commands; persist “seen” flag in project config.

### 2.3 Output philosophy
- Minimal by default; use `rich` for legible tables/headers; respect `--no-color` for CI.
- After successful deterministic runs, print artifacts only (paths to `report.pdf`, `audit.json`, `repro.sh`).

---

## 3) Commands and slash commands

### 3.1 CLI entry points
- `actcli chat [--multi <ids>] [--room <name>] [--mode offline|hybrid]`
- `actcli reserve chainladder -i <file> --report <pdf> --audit <json> [--seed N]` (exposed to chat via `/reserve`)

### 3.2 Slash commands (Tier‑0)
| Command | Syntax | Summary | Side Effects | Audit Event |
|---|---|---|---|---|
| **/help** | `/help [-a]` | Show top commands; `-a` shows all. | None | none |
| **/mode** | `/mode [offline|hybrid]` | Get/set mode. Auto‑lock to local when sensitive attachments exist. | Update session state | `mode_change` or `mode_lock_local` |
| **/audit** | `/audit [show|on|off-lite|save <path>]` | Audit on by default; “off‑lite” only suppresses verbose, still logs essentials. | Update audit level; save transcript | `audit_level_change`, `audit_save` |
| **/seed** | `/seed [N]` | Show/set deterministic seed for subsequent runs. | Update session seed | `seed_change` |
| **/trust** | `/trust [status|allow-once|allow-here|revoke]` | Folder trust management. | Update trust store | `trust_change` |
| **/attach** | `/attach <path>` | Permissioned file read; compute SHA‑256; add to context. If in hybrid, auto‑lock to local. | Adds attachment, maybe switches mode | `attach`, `mode_lock_local` |
| **/scan** | `/scan` | Redaction/leak scan of context (regex/allow‑list). | Adds redaction metadata | `redaction` |
| **/clear** | `/clear [files|history]` | Remove attachments or conversation history (session only). | Clears session state | `clear_files`/`clear_history` |
| **/models** | `/models [list|add <id>|remove <id>]` | Manage active backends (llama3, claude, gpt…). | Update participant set | `models_change` |
| **/focus** | `/focus <id1,id2,…>` | Send **next** turn to subset of models. | Temp routing override | `focus_set` |
| **/compare** | `/compare` | Fan‑out the **next** user prompt to all active models; render side‑by‑side + disagreement summary. | Writes transcript section | `compare_run` |
| **/summarize** | `/summarize` | Local synthesis: agreements, disagreements, next checks (offline). | Writes synthesis block | `summary` |
| **/reserve** | `/reserve chainladder -i <file> [--report <pdf>] [--audit <json>] [--seed N]` | **Draft** a deterministic run (dry‑run only). | Creates pending action | `draft_action` |
| **/approve** | `/approve` | Execute last drafted action; write artifacts. | Runs compute; writes files | `approved_run` |

### 3.3 Slash commands (Tier‑1)
- `/participants load <seminar.toml>` — load roles (Conservative/Challenger/Quant/Summarizer).
- `/save [transcript.md]` — persist transcript immediately.
- `/repro` — print path to (or generate) `out/repro.sh` for current session.
- `/plugin verify <actplugin.toml>` — lint manifest, permissions, and signature.
- `/git commit -m "<msg>"` — commit `report.pdf`, `audit.json`, and transcript; tag commit with audit ID (guard behind `config.allow_git=true`).

---

## 4) Reusable “Seminar” module

```
actcli/seminar/
  adapters/         # Model adapters: OpenAI, Anthropic, LocalOllama, etc.
  coordinator.py    # Fan‑out/fan‑in; timeouts; retries; parallelism
  synthesizer.py    # Rule-based summarize + disagreement score
  policy.py         # Offline/Hybrid enforcement; trust gates; redaction
  transcript.py     # Markdown and audit.json writers
```

### 4.1 Adapter interface
```python
class ModelAdapter(Protocol):
    name: str
    is_local: bool
    model_version: str
    def generate(self, prompt: str, *, system: str = "", seed: int | None = None, timeout_s: int = 30) -> str: ...
```

### 4.2 Coordinator contract
- Inputs: `prompt`, `adapters[]`, `seed`, `focus_ids?`, `timeout_s`.
- Behavior: parallel calls with per‑adapter timeout; collect text, latency, token counts (if available).
- Output: list of `{{name, is_local, version, text, latency_ms, token_usage?}}`.

### 4.3 Synthesis (v1 rule‑based, optional local LLM in v1.1)
- Compute per‑pair Jaccard similarity on stemmed keywords; “disagreement score” = 1 ‑ mean(similarity).
- Extract top 5 common points (agreements) and top 5 divergent statements.
- Emit “Next checks” boilerplate (templated): e.g., “Run Mack SE with `--seed` N; inspect tail factors.”

### 4.4 Policy
- `offline` → only `is_local=True` adapters allowed.
- `hybrid` → cloud allowed **until** an `/attach` occurs; then **lock** to offline for the session (`mode_lock_local` event).
- Redaction: apply allow‑list/regex to inputs before any non‑local adapter call; record masked fields in audit.

### 4.5 Transcript writer
- Markdown layout: header (participants/mode/time), per‑model sections, synthesis block, and artifact links.
- File paths default: `out/seminar.md`, `out/seminar_audit.json` (configurable via `/audit save` or `--audit`).

---

## 5) Config files

### 5.1 Project config — `actcli.toml`
```toml
[project]
name = "claims-q3"
version = "0.1"

[defaults]
mode = "offline"          # offline | hybrid
audit_level = "full"      # full | off-lite
seed = 42
banner = false
output_dir = "out"

[models]
# example IDs → adapters
llama3 = "local:ollama/llama3:8b"
claude = "anthropic:claude-3-haiku"
gpt = "openai:gpt-4o-mini"
```

### 5.2 Seminar roles — `seminar.toml` (Tier‑1)
```toml
[participants.conservative]
model = "llama3"
style = "short,cautious"
permissions = ["read:./data", "no-network"]

[participants.challenger]
model = "claude"
style = "challenging"

[participants.quant]
model = "llama3"
style = "numeric,asks-clarifying"

[summary]
method = "local_llm"      # or "rule_based"
```

### 5.3 Plugin manifest (for verify) — `actplugin.toml` (Tier‑1)
```toml
name = "ifrs17_disclosure_pack"
version = "0.1.0"
entrypoint = "plugins/ifrs17/main.py"
permissions = ["read:./data", "write:./out", "no-network"]
signature = "SIG_ED25519_BASE64..."
```

### 5.4 Trust store — `~/.config/actcli/trust.d/<fingerprint>.toml`
```toml
path = "/home/alex/projects/claims-q3"
trusted = true
granted_by = "alex"
granted_at = "2025-09-18T12:34:56Z"
scope = "persist"         # persist | once
fingerprint = "sha256:..."
```

---

## 6) Audit record (JSON schema, v0)

```jsonc
{{
  "actcli_version": "0.1.0",
  "session_id": "uuid",
  "mode": "offline",
  "audit_level": "full",
  "seed": 42,
  "participants": [
    {{"id":"llama3","local":true,"version":"8b"}},
    {{"id":"claude","local":false,"version":"3-haiku"}}
  ],
  "attachments": [
    {{"path":"data/triangles.csv","sha256":"...","size":12345}}
  ],
  "events": [
    {{"t":"2025-09-18T12:00:00Z","type":"mode_change","data":{{"to":"hybrid"}}}},
    {{"t":"2025-09-18T12:01:00Z","type":"attach","data":{{"path":"data/triangles.csv"}}}},
    {{"t":"2025-09-18T12:01:01Z","type":"mode_lock_local","data":{{"reason":"sensitive_attachment"}}}}
  ],
  "prompts": [{{"hash":"...", "redactions":["claim_id"]}}],
  "responses": [{{"model":"llama3","hash":"...","latency_ms":850}}],
  "disagreement_score": 0.32,
  "artifacts": {{
    "report_pdf": "out/report.pdf",
    "audit_json": "out/audit.json",
    "repro_script": "out/repro.sh",
    "transcript_md": "out/seminar.md"
  }}
}}
```

**Privacy note:** store only hashes for prompts/responses by default; full text goes to the transcript file (which can be excluded from VCS by default).

---

## 7) Deterministic run bridge

### 7.1 Dry‑run command rendering
- `/reserve ...` creates a “pending action”: render the exact command with resolved paths/seed, show expected outputs, and prompt to `/approve`.
- No code or data runs until `/approve`.

### 7.2 Approve execution
- On `/approve`, execute deterministic code path; capture env (Python & package versions) and write audit + `repro.sh`.
- Return exit code 0 only if artifacts exist and hashes match expectations.

---

## 8) Safety & policy

- **Network**: default deny for local adapters and plugins; allow only when explicit (`--mode hybrid`) and never after sensitive attachments.
- **Secrets**: read via standard env vars (e.g., `ANTHROPIC_API_KEY`) but never write back to disk.
- **Telemetry**: local only; counts of commands/runs/artifacts (no payload data).

---

## 9) Implementation notes

- **CLI**: Typer (or Click).  
- **Output**: `rich` for headers/tables; `--no-color` fallback.  
- **Adapters**: abstract model backends now; add real providers incrementally (Ollama first).  
- **Hashing**: SHA‑256 via streaming for large files.  
- **Concurrency**: `asyncio` or `concurrent.futures` with per‑adapter timeouts.  
- **Tests**: ship golden dataset for chainladder; byte‑stable audit JSON under fixed seed.  
- **Docs**: `docs/chat_repl_spec.md` (this file) + examples folder.

---

## 10) Acceptance criteria

**Tier‑0 DoD**
- Status header reflects mode/participants; `/mode` and `/models` work.
- `/attach` switches hybrid→local and logs `mode_lock_local`.
- `/compare` renders side‑by‑side responses; `/summarize` emits offline synthesis.
- `/reserve` shows dry‑run; `/approve` writes artifacts and audit + `repro.sh`.
- Two identical runs with `--seed 42` produce identical numeric results and stable audit fields.

**Tier‑1 DoD**
- `seminar.toml` loads; `/participants load` applies roles.
- `/plugin verify` rejects bad permissions and accepts a signed minimal manifest.
- `/save`, `/repro`, `/git commit` work; commit tagged with audit ID (when enabled).

---

## 11) Open questions (track in GitHub issues)
- What constitutes “sensitive” to trigger hybrid→local? (initial: any file attachment under project root).
- Minimum local model spec to bundle or auto‑pull (e.g., `llama3:8b`)?
- Default redaction rules (claim IDs, policy numbers, names).

---

## 12) Appendix: Example headers & help

**Header (REPL waiting):**
```
ActCLI • chat(seminar) • MODE: OFFLINE • participants: llama3, claude • audit: ON
```

**`actcli --help` (excerpt):**
```
Core commands
  reserve   Run reserving workflows (e.g., chainladder) → report + audit
  chat      Start a Multi‑AI Seminar (compare/summarize models, audited)
  plugin    Manage & verify plugins (manifests, permissions, signatures)
  config    View/set mode (offline/hybrid), defaults, telemetry
  init      Initialize project (creates actcli.toml, .gitignore entries)
  doctor    Check environment (local models, sandbox, git, PDF engine)
```
