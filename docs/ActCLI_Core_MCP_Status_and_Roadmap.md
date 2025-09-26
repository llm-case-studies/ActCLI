# ActCLI Core MCP — Status, Compass, and Roadmap (Sprint 3)

This document summarizes what we shipped across Sprints 1–3, why it matters, and proposes a pragmatic path to production. It is written for founders, product/marketing, business analysts, and engineering.

## Executive Summary

- We delivered a secure, local‑first platform for Excel workbook preflight using a modern MCP (Model Context Protocol) runtime with JSON‑RPC over HTTP and SSE streaming.
- The Studio SPA now includes a full Excel Inspect experience: select files from RO mounts, run the job, see real‑time progress, and review the evidence pack without context switching.
- The foundation is auditable, extensible, and production‑hardened: strict path validation, budgets/timeouts, cooperative cancel, encryption handling, and artifact hashing.
- We are ready to plan production deployment and expand the Core‑MCP tool bundle.

## What We Shipped (S1 → S3)

- Semhost backend (FastAPI) with app status, model/provider listings, sessions, WS support, and VSCode‑style SPA (S1)
- CLI providers (Claude, Codex, Gemini) with dynamic discovery, improved adapters, and a research‑first batch API for rapid prompting (S2)
- Core MCP runtime with JSON‑RPC POST /mcp and SSE GET /mcp/sse — tool execution with job IDs, progress, results, and heartbeats (S2)
- Excel Inspect (excel.inspect) tool delivering:
  - Static parsing (no macro execution) for .xlsx/.xlsm/.xlsb/.xls
  - Formula scan with volatile function detection and 3D ref heuristics (openpyxl)
  - VBA extraction and safe code analysis (oletools) — modules/procedures/risky calls
  - External links & connections via OpenXML parts (connections.xml, externalLinks, rels)
  - SHA‑256 hashing for input and all artifacts; preflight.json + preflight.md; job.json and audit.json append
  - Encryption support for OOXML via msoffcrypto‑tool (PASSWORD_REQUIRED, PASSWORD_INVALID)
  - Budgets (default 120s), warnings (80%), and cooperative cancel
- Policy & Audit:
  - HYBRID→OFFLINE lock on first RO path with audit event (mode_lock_local)
  - No network access used by tools; reads strictly from RO, writes to out/tools and audit
- Discovery/Debug:
  - /providers/cli/discover (raw menu), /providers/cli/help, /models?refresh=1&strict=1
- SPA Excel Inspect Page (S3):
  - RO file picker (GET /fs/ro/list), configurable options (lint, extract VBA, password, budget)
  - Real‑time progress viewer and result summary (severity with reasons)
  - ArtifactsTree and in‑app ReportViewer (GET /fs/out/get)

## Architecture Overview

- One front door: POST /mcp (JSON‑RPC 2.0) for initialize, tools/list, tools/call; GET /mcp/sse?job=… for progress/result with heartbeats
- Session & headers: Mcp-Session-Id returned on initialize; MCP-Protocol-Version echoed; X‑ActCLI‑Mode reflects OFFLINE/HYBRID
- Job runtime: in‑process JobManager (bounded next); idempotency by request hash; cooperative cancel; budgets & warnings
- Evidence pack: out/tools/J‑…/ with preflight.json/.md, vba/*, parts/*, job.json; audit.json is append‑only

## Security & Compliance Posture

- Never executes Excel or macros; strictly parses containers and text
- Strict path validation under /mnt/ro; symlink/escape rejection; RO read; out/ writes only
- Time budget and cancel to mitigate pathological files
- Encryption: denies scan without password; decrypts to job‑local temp copy when provided (requires msoffcrypto)
- Auditability: job.json and audit.json with hashes, flags, and timestamps; mode_lock_local recorded

## Product Value (User/Buyer)

- Safely preflight legacy Excel workbooks on any OS without opening Excel
- Catch volatile formulas, macros, risky calls, and network/external links
- Produce deterministic, evidence‑ready packs for audit, compliance, or client hand‑off
- Local‑first by default; hybrid where explicitly allowed

## Demo Script (5–7 minutes)

1) Open Studio → Tools → Excel Inspect
2) Browse RO to select examples/excel‑legacy/…
3) Run with defaults (lint, extract VBA; password if needed)
4) Watch progress; show HYBRID→OFFLINE indicator switching in status (and audit event)
5) Inspect preflight.md and preflight.json inline; click artifacts in the tree; copy SHA‑256
6) Highlight audit.json entry and out/tools/J‑…/ structure

## Deployment (Docker Plan)

### Goals
- Single published port; Semhost serves APIs and (optionally) SPA under /ui
- Volumes: ro/rw/audit explicitly mounted with correct ownership
- No network access by tools; cloud access only via explicit policy (and not used by excel.inspect)

### Compose (proposal)
```yaml
version: '3.9'
services:
  semhost:
    image: actcli/semhost:latest
    build: .
    ports: ["7530:7530"]
    environment:
      SEMHOST_BIND: 0.0.0.0
      SEMHOST_PORT: 7530
      SEMHOST_CORS_ORIGINS: http://127.0.0.1:5173,http://localhost:5173
      SEMHOST_CLI_DISABLE_TOOLS: "1"
      ACTCLI_REQUIRE_AUTH: "0"
    volumes:
      - ./ro:/mnt/ro:ro
      - ./out:/out
      - ./work:/mnt/rw
    restart: unless-stopped
```

### Dockerfile (proposal)
```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .[dev] && useradd -m app && chown -R app:app /app
USER app
ENV SEMHOST_BIND=0.0.0.0 SEMHOST_PORT=7530
CMD ["uvicorn", "semhost.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "7530"]
```

### Notes
- Mount `./ro` as RO; `./out` for artifacts; `./work` for temp (optional)
- If serving SPA from Semhost, copy studio/dist into container and `app.mount("/ui", ...)` will serve it
- For Linux devs needing localhost model bridges, include `extra_hosts: ["host.docker.internal:host-gateway"]`

## Roadmap (Next 4–6 Weeks)

**M4 — Productionization & UX polish**
- Packaging & Docker images; compose starter; optional SPA prebuilt
- Observability: request logs, slow‑job warnings, audit events in structured logs
- SPA polish: mode pill, severity tooltips with top reasons; copy/download buttons for artifacts

**M5 — Advanced Excel Analysis**
- Formula dependency mapping; circularity/path heuristics
- Rich external connection parsing; XLL/COM add‑in detection; Excel4 macro references
- Value sampling for formula hotspots (no execution)

**M6 — Bulk Operations & Profiles**
- Bulk scan flows (folder queue) with concurrency and budgets
- Profiles (strict vs. fast) with different budgets/flags

**M7 — Core MCP Tools Expansion**
- pdf.sanitize (structural safety, embedded scripts/images)
- csv.audit (schema checks, suspicious patterns, delimiter consistency)
- parity.run (deterministic compare of two evidence packs)

**M8 — Model/Chat Enhancements (Backlog)**
- Adapters: default semantics + alias normalization; effective_model in responses
- Auto‑adaptation: analyze /providers/cli/help and /discover raw menus to evolve adapters without code pushes

## Risks & Mitigations

- Large/encrypted workbooks → mitigate with budgets and PASSWORD_REQUIRED/INVALID categories
- Optional libs missing → surface notes; continue safely
- Tool sprawl → adopt MCP registry with profiles (core/extended); per‑tool permissions and budgets
- Security posture drift → keep RO/RW/audit mounts explicit; never execute Excel; ensure audit invariants

## Acceptance Criteria (Production)

- /mcp JSON‑RPC + SSE heartbeats + cancel; idempotent job IDs for identical calls
- excel.inspect: no macro execution, supports all four major formats, artifacts + hashes, severity badge + breakdown, password flow
- SPA: end‑to‑end Excel Inspect with RO picker, progress, severity badges, artifact preview, and history
- Docker: single port, three volumes, runs on Win/mac/Linux; SPA accessible; artifacts written to mounted out/

## Ask / Decision Points

- Confirm dockerization scope for M4 (SPA served by Semhost vs. separate edge)
- Approve initial Core‑MCP tool bundle beyond excel.inspect (pdf.sanitize, csv.audit, parity.run)
- Confirm compliance posture for audit.json retention and logging destinations

---

We've built a secure, local‑first foundation with a professional UX and robust audit trail. From here, we can confidently productize, expand tool coverage, and roll into enterprise‑grade deployments.

## Reviews & Comments

### What’s Working Well
- Local‑first posture with strict RO/RW mounts and no macro execution establishes a credible security baseline for Excel preflight.
- MCP envelope (JSON‑RPC + SSE) plus job IDs and artifact hashing is the right contract for audit and deterministic packs.
- VSCode‑style Studio flow (Excel Inspect page, artifacts panel, inline report viewer) shortens the “question → evidence” cycle.
- Docker plan with a single public port, optional SPA at `/ui`, and mounted volumes matches real installs on Win/mac/Linux.

### Gaps / Polish Opportunities
- WS/SSE reconnection: add exponential backoff, stop on page hidden, and visible “Offline • Retry” banner to prevent runaway loops.
- CLI providers: add a “Test models” probe and normalize aliases (e.g., `claude-3-5` → `sonnet`, default Codex → `gpt-5-codex`). Surface Echo‑fallback as a badge so users notice misconfigs.
- Model Detail View: provide a single “detail pane” with pricing, policy, recent usage, and actions (1×1 chat, add to seminar, switch model) for faster triage.
- Tool permissions: show per‑tool RO/RW/network policy in the UI; disable actions when OFFLINE/HYBRID forbids them.
- Observability: add structured logs for job lifecycle (queued/started/progress/fault/result), slow‑job warnings, and job metrics.

### Future Iterations (Functional Ideas)

1) Seminar & Model Operations
- Detail View for models: pricing, recent usage (`/history`), policy badges, and “Use fast profile” presets.
- One‑click 1×1 chat from Detail View with `raw`/`disable_tools` toggles; add “Add to Seminar” (pick session or create).
- CLI model probe endpoint + SPA “Test models” button to auto‑discover supported models per machine/plan.

2) Core MCP Runtime
- Tool isolation: `isolated=true` tools run in worker subprocesses with timeouts and cancel; later allow loopback HTTP workers without changing the public API.
- Budgets/quotas: per‑tool time/CPU/memory budgets; profile‑based defaults (strict vs. fast).
- Job store: simple SQLite index of jobs for history, filtering, and “resume from artifact”.
- Approval hooks: optional “assistive → approve → execute” step with sign‑off user/role and snapshot in audit.

3) Excel Inspect Enhancements
- Formula dependency mapping and circularity heuristics; show hotspots and volatile cascades.
- Rich connection parsing (XLL/COM add‑ins, Excel4 macro references); clearer `/notes` when xlsb formula text is limited.
- Bulk scan: folder queue, concurrency with budgets, and aggregate RAG report by file.

4) Additional Tools (Core Bundle)
- parity.run: deterministic compare of two preflight packs; emit markdown+PDF and a repro shell script.
- csv.audit: delimiter/schema checks, suspicious patterns, out‑of‑range dates, BOMs.
- pdf.sanitize: structure, embedded scripts, images; redaction helper.

5) SPA UX / Studio “IDE”
- Command Palette (Ctrl/Cmd+K): fuzzy actions (Start/Next/Export; open Models/Providers/Status; run Tool).
- Monaco in “Advanced” JSON editors; copy/download buttons; toast notifications with deep links.
- Keyboard shortcuts: Ctrl/Cmd+Enter (Start/Next), Ctrl/Cmd+S (Export), Ctrl/Cmd+P (Palette).
- Theme tokens mapped to a small VSCode palette; persist sizes/splits and theme in localStorage.

6) Ops, Packaging & Governance
- Profiles & re‑packaging: `core`, `road_nerd`, `pronunco` via manifest/ENV; publish targeted Docker images or meta‑packages.
- Container hardening: read‑only root FS, `no-new-privileges`, minimal base; SBOM and pinned wheels for tool deps.
- Windows/mac services: scripts for systemd/launchd/sc.exe; log rotation guidance.
- Evidence lifecycle: configurable retention, export to ZIP, and artifact signing.

7) Integrations (Backlog)
- Simple RO file browser API for `/mnt/ro` to make picking inputs easier on Windows/mac.
- Presenter/Reports: compile markdown reports to PDF (wkhtmltopdf/headless Chrome) for client hand‑offs.
- OpenTelemetry spans for job lifecycle; redaction of paths/secrets in logs.

### Suggested Near‑Term Adds
- Implement `/history` for recent usage (model/tool) by aggregating `out/sessions/*/round-*.json` and job index; power the Detail View.
- Add SPA “Test models” and “Use fast profile” CTAs; normalize CLI aliases in AdapterFactory.
- Ship the WS/SSE backoff + banner to eliminate high‑CPU reconnect loops when servers are down.

###### Feedback 2
Fantastic progress—congrats on the new bundle! I reviewed the repo and your Sprint-3 status/roadmap docs, the Vision, Dev Specs, and the seminar experiments. Below is a concise “review + next features” package you can paste into the Reviews & Comments section (with a prioritized backlog afterward), plus notes on refactors, Windows runners, and a Playwright crawler.

Quick read of where you are (so we scope “what’s next” correctly)

Core MCP & job plumbing are solid: JSON‑RPC POST /mcp + SSE progress, job IDs, cancel, budgets, strict RO/RW/audit mounts, artifact hashing; Excel Inspect is shipping with Studio page + evidence pack.

Vision & positioning are crisp: CLI‑first, deterministic last mile, evidence packs, hybrid mode (lock local on attach), Excel modernization + seminars as the two “aha!” paths.

Seminars validated by experiments: value from disagreement, Gate‑0 triage, local models resilient when cloud CLIs time out; evidence packs already part of the story.

Repo scaffolding shows CLI, semhost, studio, examples/tests/doc bundles (models/providers, adapters, VSCode‑style UI). 
GitHub

Add these to Reviews & Comments → “What should go next”
A) Seminar protocol & orchestration (make it a first‑class tool)

Protocols: Round‑Robin (R1/R2), Delphi‑Lite (2–3 rounds with consensus pass), and CEC (Collaborative Expert Consultation) presets with role libraries (Reviewer, Skeptic, Explainer). Wire to the same MCP job envelope with cost/time budgets and audit.

Gate‑0 triage: built‑in pre‑check (Verification Cost, Error Consequence, Ambiguity, Stakeholder Alignment, Evidence Need, Data Sensitivity). Surface Seminar Essential / Optional / Skip badges. (Directly reflects your experiments.)

Annealing & synthesis: temperature schedule, prompt‑grid exploration, Kemeny/Borda-style rank aggregation, and disagreement map in the evidence pack.

Studio UX: “Start Seminar” wizard, Model Detail drawer (pricing, policy, recent usage, actions), 1×1 quick‑chat that can be “added to seminar,” and a /history view to browse past sessions.

B) Excel Explorer → Inspect integration (trust first, then flags)

Ship the Explorer tree (VBA modules/procedures, named ranges + scope, sheets visibility, formula families/volatiles/dynamic arrays, links, PQ/Model presence). Add a Signals & Gate‑0 tab; one‑click “Seminar on this finding.” (Audit continuity with Inspect.)

C) parity.run (deterministic compare) — “proof after trust”

Deterministic comparison of baseline cells/ranges vs. migrated pipeline output with tolerances, parity_report.md + repro.sh. It closes your “see → assess → prove” arc.

D) Core runtime polish

WS/SSE reconnection policies and an “Offline • Retry” banner; structured job lifecycle logs (queued/started/progress/fault/result). Add /history (SQLite index of jobs & sessions).

E) Packaging & deploy

One‑port Docker with SPA served by semhost, three volumes (RO/RW/audit), optional profiles (strict vs fast) that set budgets/timeouts.

Refactors I’d do before adding more tools

Type the wire: Promote MCP messages, progress events, and artifact manifests to typed models (Pydantic v2) to prevent schema drift across tools.

Registry split: Separate tool contracts (schemas) from implementations; keep a thin adapter layer so tools can move to worker subprocesses later without API change.

Providers normalization: Centralize aliasing (claude-3-5→sonnet; openai family; ollama tags) and add a “Test models” probe endpoint the Studio can call.

Job store: Lightweight SQLite for /history, filters (“Excel jobs last 7 days”), and “open artifact.” This also enables Studio’s Model Detail usage stats.

UI consolidation: Command Palette, detail drawers, consistent copy/download actions; show per‑tool RO/RW/network policy in the UI to reinforce the security posture.

Windows: container vs. runner (what’s realistic)

Microsoft does not support server‑side/unattended Office automation, and Office isn’t supported in Windows containers (technical & licensing). That means “Excel in a container” is a non‑starter for production. Use a Windows micro‑VM runner instead. 
Microsoft Learn
+3
Microsoft Support
+3
Microsoft Learn
+3

Recommended design

Windows “Excel Runner” VM (not container):

Open workbook with Application.AutomationSecurity = msoAutomationSecurityForceDisable; Application.CalculateFullRebuild for ground‑truth recalculation; snapshot targets to baseline.json. Only run a whitelisted macro if explicitly approved. 
Microsoft Knowledge Base Archive
+1

Air‑gapped, read‑only input mounts, timeout/kill guard; job launched from semhost with status streamed back to Studio (same MCP job envelope).

Windows container with native goodies (allowed): for things that don’t require Office—PowerShell 7, .NET, ODBC drivers, registry queries, OLE tools, msoffcrypto-tool, etc. Use this for static inspection or file wrangling, not Excel automation. (Office/Excel themselves remain in VM land.) 
Microsoft Learn

Playwright crawler (ActCLI‑native “firecrawl‑style,” local LLM + seminar)

Why: Capture public evidence (docs/pages) with a license you control, render dynamic sites, and summarize with local models; orchestrate Seminars for cross‑site synthesis and disagreement surfacing—with the same evidence‑pack guarantees.

Tool pair

web.snapshot: Given a URL list, render with Playwright, save HTML, Markdown, text, screenshots, PDFs, and a DOM hash. Respect robots.txt, rate‑limit, rotate user‑agents; configurable denylist.

web.crawl: Domain‑scoped BFS with depth/TTL, de‑dup by content hash, store to /out/crawl/J‑…/.

Optional pipeline: local LLM extractors (key facts, table normalization) → Seminar synth across pages → crawl_report.md with citations and per‑page hashes.

Request/Result (shape)

// call
{ "start": ["https://example.gov/"], "allow_domains": ["example.gov"], "max_pages": 150, "depth": 3, "render": "desktop", "rate": "1/s" }

// artifacts
{
  "summary": "out/tools/J-.../crawl_report.md",
  "pages": [
    { "url": "...", "sha256": "...", "html": "pages/0001.html", "md": "pages/0001.md", "screenshot": "shots/0001.png" }
  ],
  "audit": "out/tools/J-.../audit.json"
}


Seminar hook

After crawl, run seminar.run with roles: Extractor, Skeptic, Validator. Output seminar.md + cost/time. (Local models first; cloud is optional by policy.) This aligns with your experiment‑proven value of disagreement and Gate‑0.

Licensing

Everything is self‑hosted, no SaaS license risk; evidence pack includes page hashes and snapshots to defend provenance.

Prioritized backlog (4–6 weeks)

Seminar orchestration (MVP) — presets, Gate‑0, annealing, synthesis, evidence writer; Model Detail view; /history for sessions.

Explorer → Inspect — deliver the Explorer tree + Signals tab; keep it read‑only & deterministic; optional “Seminar on this finding.”

parity.run — deterministic compare and repro.sh with tolerances; plug outputs into the same artifact tree.

Runtime polish — WS/SSE reconnection, structured logs, /history index; Studio banner + copy/download affordances.

Crawl POC — web.snapshot + web.crawl with Playwright; local LLM summarizer; optional Seminar synth.

Windows Excel Runner (design + stub) — VM control plane & job contract; macros disabled by default; time‑frozen runs for parity. (Containers only for non‑Office “goodies.”) 
Microsoft Support
+1

Acceptance checkpoints to keep quality high

Seminars: deterministic evidence (seminar.md + transcripts + model roster + costs); Gate‑0 is visible, not implicit.

Explorer: module/procedure counts match Excel VBE on golden samples; named scopes/defs are correct; .xlsb formula‑text limitation clearly surfaced.

parity.run: fixed seeds/versions ⇒ identical parity_report.md; repro.sh works on a clean machine.

Crawler: page snapshots are reproducible; all pages carry hashes; robots.txt & rate limits obeyed; Seminar results cite specific pages.

Windows Runner: no macros by default (ForceDisable), documented whitelisting, and logs show CalculateFullRebuild and a frozen clock when needed. 
Microsoft Knowledge Base Archive
+1

Small repo nits (worth fixing while you’re here)

Add adapter alias normalization and a “Test models” button in Studio; show an Echo‑fallback badge if a provider silently degrades.

Promote /history early; your Studio UX will instantly feel “productized.”

In excel.inspect, always echo mode lock events (HYBRID→OFFLINE) prominently in the UI to reinforce the posture.


###### Feedback 3

Fantastic—congrats on the Sprint‑3 bundle. I reviewed the new core (Semhost + MCP + Excel Inspect + SPA), your experiments, the Vision/Architecture briefs, and the repo layout. Below is (1) what’s solid, (2) what to add next to the “Reviews & Comments → Suggested Near‑Term Adds / Future Iterations” sections (PR‑ready text), and (3) refactors that will keep the pace without accruing drag.

What’s solid: single front door (/mcp JSON‑RPC + /mcp/sse streaming), strict RO/RW mounts and evidence packs, HYBRID→OFFLINE mode lock, and a polished Studio flow for Excel Inspect with preflight artifacts and audit trails. This is exactly the trust‑by‑design foundation we want.

Repo layout matches the story (CLI + Semhost + Studio + docs), with a clear README and provider adapters scaffolded for local and cloud models. 
GitHub

Your experiments meanwhile validate when seminars create value (diversity, disagreement, anti‑anchoring), and when Gate 0 rightly says “skip seminar.” We should productize that.

Add these to Reviews & Comments → Suggested Near‑Term Adds (PR‑ready)

Note: These plug directly into the Sprint‑3 doc sections you already have (“Suggested Near‑Term Adds”, “Gaps/Polish”), and align with the Vision/Architecture briefs. I’ve kept acceptance criteria crisp so devs can pick them up.

A) Seminar Protocols & Orchestration (top priority)

Gate 0 (5‑min huddle) UI & automation.
Why: Prevent token burn; encode “do we even need a seminar?” and set the oracle.
Ship: A small modal/page that captures: Objective, Oracle, Data policy (HYBRID/OFFLINE; handoff rule), Protocol, Roles→Model tiers, Budgets/Caps, Stop criteria, Evidence checklist.
AC: Gate 0 saved as a Seminar Charter JSON/MD in out/sessions/S‑*/charter.*; surfaced in the final report. Organizer override of “no seminar” is logged.

Protocol runner (Delphi‑Lite, CEC, Annealed, Approve→Run).
Why: Move beyond round‑robin to predictable outcomes.
Ship: Add “Protocol” select + params (rounds, ε, rubric). Implement minimal orchestration for:

Delphi‑Lite (blind R1 → local synthesis → R2),

CEC (Claim–Evidence–Counter schema per turn),

Annealed RR (diverge high‑T/BoN → cluster/judge → low‑T converge),

Propose→Approve→Run (deterministic finish).
AC: SSE events include round_start, synthesis_published, claim_logged, mode_lock_local, approved_run. Reports include a CEC table and a shortlist with rationale/risks/next steps.

Approve→Run bridge (deterministic last mile).
Why: Turn assistive output into proof.
Ship: /approve triggers a deterministic job (tests/sim or parity.run).
AC: Writes parity_report.md/pdf, repro.sh, hashes/seeds, and an approval record into audit.json. Promote parity.run from M7 to near‑term.

B) Cost, Reliability, and Model Operations

Cost policy & escalation controls.
Why: Keep bills low; leverage local SLMs first.
Ship: Config (policy.cost) with max_cloud_calls, escalate_on=[low_score, high_disagreement], top‑K escalation.
AC: Evidence pack logs all escalations; Studio displays a small “Cloud use: N” badge.

Model Detail View + “Test models” probe.
Why: Faster troubleshooting; fewer silent misconfigs.
Ship: Single pane with pricing/policy, recent usage, actions (1×1 chat, add to seminar, switch). “Test models” button probes adapters and renders supported params.
AC: /providers/cli/discover + /models?refresh=1&strict=1 shown inline; alias normalization visible (e.g., claude-3-5 → sonnet).

WS/SSE reconnection/backoff + “Offline • Retry” banner.
Why: Avoid runaway loops and mystery states.
AC: Exponential backoff; pause when tab is hidden; banner toggles on connection loss; single reconnect loop per tab. (Promote from Gaps/Polish to immediate.)

C) Evidence & Reports

Seminar Report generator (MD→PDF).
Why: Client hand‑offs and demos.
Ship: Compile seminar MD (with Charter, rounds, CEC table) to PDF.
AC: One‑click Export; artifacts zipped with audit.json and hashes. (Backed by wkhtmltopdf/headless Chrome.)

Evidence pack lifecycle.
Why: Compliance + portability.
Ship: ZIP export, retention policy, optional pack signing.
AC: Export includes audit.json, job.json, SHA‑256 manifest, and artifacts.

D) Core MCP tools (pull‑forward from M7)

parity.run (deterministic compare of two packs).
Why: Unlock the Excel modernization demo end‑to‑end now.
AC: Given baseline.workbook, targets.yml, and new pipeline (Python or M), emits parity_report.md/pdf + repro.sh; diffs within tolerances pass.

csv.audit & pdf.sanitize (starter profiles).
Why: Broaden the story beyond Excel with quick wins.
AC: csv.audit flags schema/delimiter oddities, out‑of‑range dates, BOMs; pdf.sanitize checks structure and embedded scripts. Both write minimal MD/JSON artifacts.

E) Observability & History

Job history + structured logs.
Why: Support triage, metrics, demos.
Ship: /history endpoint; structured lifecycle logs (queued/started/progress/fault/result), slow‑job warnings.
AC: Studio “Recent” shows jobs and sessions; filters by tool/model/outcome. (You already scoped this—mark as near‑term.)

OpenTelemetry (minimal).
Why: Production readiness.
AC: Spans for POST /mcp, job execution, and SSE streaming; redaction of paths/secrets in logs.

Add these to Reviews & Comments → Gaps / Polish Opportunities

Tool permissions surfaced in‑UI. Show RO/RW/network policy per tool; disable actions when policy forbids them (especially after mode_lock_local).

Timeouts & budgets UX. Inline controls for time/memory budgets by profile (strict vs fast), with per‑tool defaults.

Model alias normalization and echo‑fallback badge. Make silent adapter failures visible.

Add these to Reviews & Comments → Future Iterations

Protocol A/B harness. Run the same prompt with Delphi‑Lite vs Annealed RR; record novelty (cluster count), judge scores, decision latency, and cost to learn when each wins. (Anchored in your experiments.)

Prompt‑variation grid. First‑class support for paraphrase/role/morphological grids with dedupe and rubric scoring; great for ideation without over‑spending.

Seminar separation (later). Keep Semhost as policy/audit governor; factor “seminar‑engine” into a worker if/when concurrency and tenancy drive it. Trigger: many parallel seminars or tenant isolation.

Refactors I’d suggest after Sprint‑3 (to reduce future drag)

These are repo‑level adjustments; they don’t change user‑visible behavior but make the next sprints safer and faster. They match the brief’s stable envelope and deployment patterns.

Package boundaries & naming.
Split src/ into semhost/ (FastAPI app, MCP envelope, job manager, evidence) and actcli/ (CLI + seminar orchestration). Add tools/ (MCP tools) and shared/ (types/events). This mirrors the one‑front‑door design and clarifies dependencies. 
GitHub

Typed envelope & event models.
Define Pydantic models for RPC requests/replies and SSE/WS events (progress, synthesis_published, claim_logged, approved_run, error taxonomy). Add contract tests (golden JSON) for the envelope.

Job state machine & error taxonomy.
Flatten ad‑hoc error strings into a small set of codes (PASSWORD_REQUIRED, BUDGET_EXCEEDED, INVALID_PATH, …); guarantee idempotent job IDs by request hash (already noted). Helps SPA/CLI handle retries deterministically.

Tool isolation option.
Support isolated=true tools in a worker subprocess with timeouts & cancel; keep public API unchanged. Useful for heavier tools (parity.run, pdf.sanitize).

Provider AdapterFactory.
Centralize adapter capability discovery and alias normalization; cache discover/help to avoid repeated CLI scans; expose a “Test models” probe. (You called this out—just consolidate it.)

Policy/Config unification.
Single typed config (Settings) for mounts, budgets, cost policy, and HYBRID/OFFLINE rules; load from env + TOML; surface effective config via /status. Keeps deployments predictable.

Filesystem & path‑safety helpers.
Extract path validation/rewriting into a tiny library with tests (RO escape, symlinks, normpath, deny‑list). Reuse across all tools. (You’ve already got strict validation—factor it out for consistency.)

Evidence writer as a service.
Single module that appends audit.json, writes hashes, versions, seeds, and mode events. Tools call it; tests assert invariants (“audit append‑only”, “all outputs hashed”).

Docs structure.
Create docs/adr/ (Semhost runtime, streaming, mode policy, evidence schema), docs/playbooks/ (Gate 0, protocols), and keep docs/seminar-reports/ for outcomes. Tie to your Vision/Architecture briefs so new contributors ramp fast.

What to promote on the Roadmap right now

Move Seminar Orchestration (Gate 0 + Protocol runner + Approve→Run) into M4–M5, ahead of some polish items; it’s the biggest product unlock and showcases the deterministic last mile.

Pull parity.run into the same window so the Excel modernization demo becomes end‑to‑end “wow” (Preflight → Parity → Audit).

Why these choices fit ActCLI

They double down on your four pillars—trust‑by‑design, local‑first/hybrid, CLI + Studio, open core—and convert the seminar experiments into first‑class, auditable product features. The result is a repeatable “assistive → approve → deterministic run → evidence pack” loop for workbook migration and beyond.

###### Feedback 4

Awesome—congrats on the new bundle! I reviewed the Sprint‑3 status/roadmap plus the live seminar write‑ups and artifacts. Below is copy‑ready text you can paste into the “Reviews & Comments” section of your Sprint doc, split into the same subheads you already use. I’ve prioritized Seminar protocol/orchestration (as you asked), and added in‑product engagement (“share” + “challenge a friend”) that fits your local‑first/audit posture.

Reviews & Comments — Additions
What’s Working Well (add)

Seminar value proven in the wild. Two live runs demonstrated real convergence (AV pricing) and a critical flaw caught (“Smart Cities” discount), with cost/latency/model IDs captured in the evidence pack—perfect proof points for demos and enterprise trust.

Hybrid reliability advantage. When cloud CLIs time out, local Ollama still delivers; the logs and artifacts make that reliability visible. This is a differentiator we should surface in UI and marketing.

Gaps / Polish Opportunities (add)

WS/SSE resiliency (UI polish). Ship exponential backoff + a visible “Offline • Retry” banner on the Studio header during /mcp/sse disconnects to prevent runaway loops while keeping user confidence high. (Mentioned earlier; promote to “next.”)

Evidence Pack v0.3 fields (standardize). Add verified_assertions[], recusal, mode_handoffs[], and environment.gpu_detected so every pack ends with numbers + checks + provenance; your live seminars already collect most of this.

Model alias normalization + quick probe. One “Test models” button that calls /models?refresh=1&strict=1 and probes each CLI/Ollama target, showing a green check or an “Echo fallback” badge if misconfigured. This shortens first‑run friction and explains failures.

Approvals everywhere. Expose an optional “Assist → Approve → Execute” gate for any tool (e.g., excel.inspect → parity.run) to align the Studio UX with your trust‑by‑design story.

Future Iterations (Functional Ideas) — promote these to “Next”

Seminar Protocol & Orchestrator (core)

Protocols: Round‑Robin, Cross‑Examination, Delphi‑Lite consensus, and Annealed Round‑Robin (temperature/budget schedules). Store a consensus_claim object with sheet/range + tolerances for hand‑off to deterministic jobs.

Gate‑0 automation: Make the “When NOT to Seminar” decision automatic (low ambiguity/mandated method/zero stakeholder alignment ⇒ recuse with next pipeline). Persist {reason, gate0_scores, next_pipeline} in audit.json.

Budgets & failover: Per‑participant time/cost budgets, parallelism, provider failover (cloud timeout ⇒ continue with local), and a Replay Cassette (recorded responses) for deterministic webinars.

Approve→Run bridge: One click from consensus_claim → parity.run or calculator with the claim’s tolerances prefilled. (This glues seminars to deterministic proof.)

Deterministic Proof Tools (ship as a bundle)

parity.run (MVP): Compare two evidence packs (e.g., legacy vs. Python/PQ) and emit diff table + PDF + repro.sh. It’s already in your core‑bundle plan—move up in priority.

csv.audit: Schema, delimiter, date sanity, “text‑as‑number” detection; great companion to excel.inspect.

pdf.sanitize: Basic structure scan + embedded scripts/images flags for safe client hand‑offs.

Excel Modernization (demo‑visible upgrades)

Formula graph & hotspots: Visualize dependency clusters and volatile cascades (OFFSET/INDIRECT) with a “risk map.”

Connection & add‑ins scan: XLL/COM/Excel4 macro references and external link lineage surfaced in a single “Connections” pane.

One‑click “safer transform” suggestions: Guided rewrites (OFFSET→INDEX/XMATCH) with parity harness stubs pre‑generated.

History & Observability

/history index + Model Detail pane (pricing, usage, recent runs, “add to seminar”). Powers better triage and cost governance.

Structured job metrics: Queue/started/progress/fault/complete in logs; slow‑job warnings. (You already proposed this—affirm as near‑term.)

Suggested Near‑Term Adds (expand)

Studio: “Test Models” & “Use Fast Profile” CTAs on the Models page; surface effective_model and a common alias (e.g., sonnet, gemini-flash) to reduce confusion.

Seminar preset gallery: “AV Pricing (Delphi‑Lite)”, “Validation Audit (CEC)”, “Spreadsheet Migration (Cross‑Exam)”. Each ships with constraints (HYBRID→OFFLINE at data attach) and replay cassettes.

Evidence Pack v0.3 writer (schema above) and ZIP exporter with signature + actcli verify pack.zip for tamper detection—great for client hand‑offs.

New: Engagement & Growth Features (in‑product)

Keep it local‑first and evidence‑centric, but make it fun to invite peers.

Share a Pack (safe by default)

“Share → Export (Redacted)”: ZIP with preflight.md, preflight.json, consensus_claim.txt, verified_assertions[], artifacts, hashes, and no raw sensitive data. Generates a signed manifest and an Open‑in‑ActCLI deeplink.

Viewer mode in Studio (read‑only): drag‑drop a pack to browse artifacts, see cost/latency meters, and rerun parity.run offline.

Challenge a Friend — Excel/VBA/Formulas

Goal: Turn your Excel modernizer into a shareable game that still teaches “trust before transformation.”

Flows:

VBA Safari: “Find the smells.” Points for catching Auto_Open, external links, volatile functions, hidden sheets. (All via excel.inspect; no macro execution.)

Parity Race: First to get all‑green diff on a target range using a provided Python/PQ stub.

Risk Map Hunt: Identify the highest‑risk formula cluster from the graph and propose the safest rewrite.

Artifacts: Each challenge compiles an evidence pack with findings and a score; packs are shareable via the “Share → Export (Redacted)” flow above.

Guardrails: Default to sample workbooks we host locally; enforcement of OFFLINE mode at data attach; “no personal data” banner.

Seminar Showdown (lighthearted but useful)

Two presets enter, one claim leaves. Run Round‑Robin vs. Delphi‑Lite on the same prompt and show: time‑to‑consensus, #disagreements resolved, and cost. Tie it to the Approve→Run deterministic output so the “game” still ends with a verified number.

Referral hooks (zero‑spam)

Invite by Pack. Every shared ZIP includes an invite token that opens Studio in Viewer mode with the challenge pre‑loaded. After viewing, they can “Run locally” to try the tool—no signup wall.

Weekly “Actuarial Kata” (library‑friendly)

Preload a small, open set (e.g., LEV/LER calculator, GLM with offset, triangle parity) as deterministic mini‑exercises with unit tests and tolerance checks. It’s an easy on‑ramp that actuaries recognize. (Matches vision: AI assists; code proves.)

Seminar Protocol & Orchestration — spec sketch for the doc

Consensus Claim (hand‑off object)

{
  "sheet_range": "Results!A1:G200",
  "tolerances": {"abs": 1e-8, "rel": 1e-6, "rounding": 2},
  "method": "MackCL | BF | GLM | PQ | Python",
  "inputs": ["Triangles", "Factors"],
  "evidence": ["hash(inputs)", "model_versions", "seed"],
  "recusal": null
}


This object lands in the evidence pack and drives Approve→Run. It keeps the seminar honest: discussion yields a testable claim; code delivers proof.

Replay Cassette
Store raw participant texts + timing + model IDs so booths and webinars can run deterministically offline; you already have the per‑participant telemetry in your live sessions.

Why these “next” items fit now

They connect your proven seminar value (convergence + flaw catching) to deterministic outcomes with standardized evidence, which is the core promise in your Vision/Brief.

They reduce friction (probe models, history, approvals) and increase reach (share packs, challenges) without compromising the OFFLINE/HYBRID posture or audit trail.

If you drop this straight into the doc under Reviews & Comments, the roadmap naturally points to (1) Seminar Orchestrator + Approve→Run bridge, (2) parity.run bundle, and (3) Share/Challenge as the first engagement wedge—each already supported by your current architecture and live evidence.


###### Founder's summary:

Short answer: yes—you’re moving in the right direction, fast. The Sprint‑3 bundle nails the trust‑by‑design core (one MCP entrypoint, JSON‑RPC + SSE with heartbeats/cancel, strict RO/RW mounts, artifact hashing, HYBRID→OFFLINE mode‑lock), and the Studio flow for Excel Inspect already feels “productized.” That foundation cleanly matches the vision in the whitepaper (local/hybrid + MCP), the strategic addendum (governance/audit), and the earlier concept critique (“productize trust”).

Below is a pragmatic what’s next—prioritized to maximize user impact and stick to the ActCLI thesis—plus a set of actuary convenience tools (command history, doc summarizer, CAS prep, policy analyzer) with concrete specs.

What’s great (keep doing this)

Single front door + stable job envelope. POST /mcp (initialize/tools.list/tools.call) and SSE /mcp/sse with job IDs and heartbeats + cancel is exactly the right contract; you’re already appending audit entries and hashing every artifact.

Excel Inspect hits the cross‑platform, no‑execution preflight you promised: formulas (volatile flags), VBA extraction and risky calls, external links, SHA‑256 artifacts, PASSWORD_REQUIRED/INVALID taxonomy.

Mode policy is visible and enforced: HYBRID→OFFLINE lock on first RO path with mode_lock_local in the audit—clean alignment with the docs.

Your experiments also validate the “seminar” wedge (independent convergence, productive disagreement, Gate‑0 triage, local reliability when clouds time out), so it’s smart to productize that now.

Priority roadmap (next 4–6 weeks)

Think in three tracks—Proof → Orchestration → Reliability/History. Each item has a crisp acceptance criterion.

TIER 0 (Now): turn evidence into proof

parity.run (deterministic compare).
AC: Given a baseline workbook + targets.yml + new pipeline (Python or M), emit parity_report.md/pdf + repro.sh; append seeds/versions/hashes to audit.json; pass/fail within tolerances. This completes the “see → assess → prove” arc you sell.

Seminar Orchestrator (Gate‑0 + Delphi‑Lite/CEC + Approve→Run).
AC: Charter saved (objective, protocol, roles, budgets), rounds streamed as SSE (round_start, synthesis_published, claim_logged), and Approve triggers parity.run. Evidence pack contains the charter, transcripts, model roster, costs, and the consensus claim with tolerances. This turns your experiments into a first‑class, auditable product surface.

TIER 1 (Reliability & Ops)

WS/SSE resiliency + “Offline • Retry” banner.
AC: Exponential backoff; pause when tab hidden; one reconnect loop per tab; visible banner; events continue when re‑connected. (Called out in your own “Gaps/Polish.”)

/history + structured lifecycle logs.
AC: A lightweight job index (SQLite) drives a Studio “Recent” view (filter by tool/outcome) and structured logs record queued/started/progress/fault/result with durations—handy for demos and triage.

Model operations: “Test models” probe + alias normalization.
AC: One click probes adapters (Claude/Codex/Gemini/Ollama), normalizes aliases (e.g., claude-3-5 → sonnet) and shows an Echo‑fallback badge if misconfigured. Reduces first‑run friction.

TIER 2 (Breadth & polish)

csv.audit and pdf.sanitize (starter profiles).
AC: Minimal MD/JSON reports with flags (delimiter/schema/date/BOM for CSV; embedded scripts/objects for PDF). Adds “beyond Excel” credibility with small effort.

Evidence pack v0.3.
AC: Standard fields added: participants[], mode_handoffs[], cost_summary, verified_assertions[], and environment info; one‑click ZIP export. Matches the compliance deep‑dive.

This ordering keeps you laser‑aligned with the whitepaper’s enhanced AI+MCP section (local/hybrid, deterministic last mile), while converting the experiment learnings into a shippable differentiator.

Actuary convenience tools (scoped, ROI‑positive)

Here are four add‑ons that make daily use delightful without diluting the core. Each follows the assistive → approve → deterministic principle.

1) Intelligent command history (terminal & Studio)

What: Semantic search over prior runs + “one‑click rerun” with diff‑view of params; suggestions surfaced as wizards (“Re‑run last Inspect on *.xlsm with STRICT profile?”).

Data: Store normalized commands + params hash + artifacts in a small /history table (ties into TIER‑1).

Safety: Strip secrets/paths on export; keep packs local by default.

AC: From Studio or CLI, actcli history search "xlsb volatile" returns past jobs; “Rerun” regenerates identical artifacts (same seed/versions).

Why now: tiny build on top of /history; directly improves repetition-heavy actuarial workflows.

2) Doc summarizer & binder (local‑first)

What: Summarize preflight/parity reports and supporting docs into a client‑ready binder.md → PDF, strictly from local artifacts; optional redaction.

AC: “Export Binder” produces a single PDF with cover, findings (with SHA‑256s), and the audit excerpt. No external calls in OFFLINE.

Why: packaging win for consultants/validators; leverages what you already generate.

3) CAS Exam companion (“Actuarial Kata”)

What: A library of deterministic exercises (triangles, GLM with offsets, Mack CL) with unit tests & tolerances; local model provides hints/explanations.

AC: kata.run mack_cl runs tests with tolerances and renders a step‑by‑step explanation panel; all reproducible.

Why: low‑risk growth loop that recruits power users and new grads into ActCLI’s way of working. (Nice community/brand play; not required for enterprise pilots.)

4) Insurance policy analyzer (phase‑1: safe & structural)

What: Pair pdf.sanitize with a structural policy.extract (sections, definitions, endorsements; no legal advice).

AC: Given a specimen PDF, emit policy.json (TOC, section spans, defined terms, references) and MD with cross‑links; include source page hashes for provenance.

Why: frequent actuarial ask that maps to your “evidence pack” ethos; start with structure before NLP interpretation.

How to prioritize (quick rubric you can paste in your doc)

Score each proposal on Impact (I), Alignment (A) with trust‑by‑design, Risk (R) (lower is better), and Effort (E) (lower is better). Weight: I 40% • A 25% • (1−R) 20% • (1−E) 15%. Result: focus TIER 0 → TIER 2 above.

Top cluster (do now): parity.run, Seminar Orchestrator, WS/SSE resiliency, /history + logs.

Next cluster (near‑term): “Test models” probe + alias normalization, csv.audit, pdf.sanitize, Evidence v0.3, Intelligent history.

Nice‑to‑ship (growth/engagement): Doc binder, Kata, Policy analyzer (phase‑1).

This ordering aligns with the Sprint‑3 roadmap you drafted (M4–M7) but pulls parity.run and seminar orchestration up to convert today’s demo into a decision‑grade workflow.

A few surgical refinements to the shipped bundle

SSE heartbeats: keep : ping\n\n every ~10 s and surface a visible banner on disconnect; stop reconnects on hidden tab. (You already flagged this—ship it.)

Idempotent tools.call: cache by request hash for safe retries; return the same job_id if body matches.

Evidence invariants: every job → {preflight.json, preflight.md, hashes for input+artifacts, job.json} + audit append; expose a ZIP export. (Matches your compliance deep dive.)

Model detail drawer: pricing/policy, recent usage, “Test models”, Echo‑fallback badge. (Already in your “Gaps/Polish,” worth promoting.)

Why this stays true to the vision

The whitepaper argues for local models + MCP to enable secure, creative workflows—Seminar Orchestrator + parity.run is that in action. (See Enhanced AI Integration… on pp.3–4.)

The strategic addendum stresses governance, RBAC, audit, and an enterprise compliance posture—evidence pack v0.3, ZIP/export, and /history head there.

The concept critique insists on explainability and deterministic last mile—exactly what parity.run and the Approve→Run bridge deliver.

Your experiments prove the seminar value (convergence/disagreement/Gate‑0) and local reliability: making that first‑class will resonate in demos and production.

TL;DR

You have the right core and a polished Inspect experience. Ship parity.run + Seminar Orchestrator (Gate‑0 → Approve→Run) first; harden SSE + add /history; then broaden with csv.audit, pdf.sanitize, and intelligent history. Add the convenience tools (doc binder, CAS kata, policy analyzer‑phase‑1) as on‑ramps. This keeps ActCLI unmistakably different: AI assists, humans approve, code proves—locally, with an evidence pack.


###### Feedback on Summary and discussion

Expanding Collaboration: Browser Extension for AI Invites
To further enhance the collaborative potential of ActCLI's seminars, a browser extension can serve as a complementary tool for inviting AI models that lack native CLI support or for quickly adding model variants. This extension does not replace the robust CLI integration—which remains the core for seamless, scripted workflows—but instead acts as a bridge for web-based AIs like Grok or Claude variants that users may access through their subscriptions. Users can log into their web chat interfaces, select a model from the provider's dropdown, and "invite" it to an ActCLI seminar with a custom alias or avatar (e.g., "Senior Actuary" for Claude-Opus). The extension proxies the invite securely to ActCLI's backend, streaming responses into the seminar thread while maintaining privacy through redaction and MCP filters.
This method reduces setup friction for newcomers, allowing them to incorporate familiar web-based models without CLI configuration. For instance, an actuary could invite "Grok as Trend Spotter" to debate reserving parameters, with the extension handling context sharing and response integration. By focusing on models without CLI equivalents or rapid variant testing, the extension complements ActCLI's existing CLI providers, enabling hybrid sessions that blend local LLMs with web-accessible experts.
Incorporating Human Participants: Optional Invites for Observation and Input
ActCLI's seminar framework can also accommodate human participants as optional invitees, fostering true hybrid human-AI collaboration without imposing any pressure. This feature allows users to share a seminar link with colleagues (e.g., via Teams or Slack channels), inviting them to observe the AI-driven discussion or contribute insights if they choose. For example, an actuary in Princeton could invite a peer from the San Francisco branch to join a reserving debate— the human receives a secure link to a shared thread or meeting, where they can view real-time AI exchanges and add "2 cents" (e.g., "That tail risk adjustment overlooks our Q2 data") at their discretion.
Human invites emphasize voluntariness: No obligation to participate actively; observers can simply lurk and absorb, while willing contributors enhance the session with real-world judgment. Integration through familiar tools like Teams (for sync video discussions) or Slack (for async threading) keeps it low-effort, with ActCLI's MCP runtime proxying human inputs into the seminar stream (redacted for privacy). Evidence packs log human contributions (e.g., with timestamps and roles) for auditability, aligning with actuarial practices of collaborative validation. This optional layer turns seminars into distributed "centaur" teams, amplifying AI outputs with human expertise when desired.
ChatGPT said:
Request for GPT-5 Pro
Reasoned for 11m 22s

Love these two ideas. They’re both feasible without blowing up scope if you stage them and keep the same guardrails you’ve already shipped (OFFLINE/HYBRID policy, evidence packs, single front door). Below is a pragmatic take: what they are, how hard they are, how to build them incrementally, risks/guardrails, and where they should sit in the roadmap. I’ve also added a short list of actuary‑convenience tools that give quick daily wins.

Quick take

Browser “AI Invite” extension: Medium complexity, high adoption upside. Start with a “copy‑bridge” MVP (no DOM automation), then add live streaming where the provider’s UI allows it.

Human invites (observer/commenter): Low→Medium complexity, high collaboration value. Start with observer‑only links; add comment‑only next; full participation later (SSO/RBAC when you go enterprise).

Both fit your architecture: semhost/Core‑MCP stays the only network surface; Studio/SPA is the control plane; all invites are opt‑in, redacted, and audited.

1) Browser Extension — “AI Invite”
What it does

Let a user who is already logged into a web chat (e.g., Grok, a Claude web variant, etc.) manually send the current “seminar packet” and paste back the model’s reply into the ActCLI seminar under a chosen alias (e.g., “Senior Actuary”). This is a bridge for web‑only models; it does not replace CLI providers.

Complexity snapshot

MVP (copy‑bridge): Low — no automation beyond copying text; user clicks send in the chat UI.

v1 live stream (content script reads message as it appears): Medium — per‑site selectors + fallbacks.

v2 (multiple providers, variant profiles, redaction presets): Medium→High depending on coverage.

MVP flow (Manifest V3; no scraping)

In Studio: Invite AI → choose “Browser extension” → pick an alias/avatar → Generate “seminar packet” (facts, question, constraints, EV# links).

Click “Copy to extension” → signs payload with a short‑lived token from semhost; places a redacted text block on the clipboard.

User focuses the chat tab (any provider), pastes, and hits Send.

When the reply appears, user selects it → “Send back to ActCLI” button in the extension popup reads selection (document.getSelection().toString()), posts it to semhost /invite/ingest, which logs provenance and emits it into the seminar as a message from the alias.

Audit entry: provider URL (origin only), alias, token id, time, payload SHA‑256 (not cookies), and redaction profile used.

Why this first: no DOM dependencies, no auto‑actions, very ToS‑safe, minimal engineering, still removes a ton of friction.

v1 live stream (opt‑in, per‑site)

Add a content script for selected domains that observes the response container (MutationObserver) and streams chunks via WebSocket/SSE to semhost.

Keep manual send—no automatic typing/clicking.

Maintain a provider profile file (CSS selectors, rate‑limit hints). If the page layout changes, the extension silently falls back to MVP copy‑bridge.

Security & policy guardrails (non‑negotiable)

Mode gate: In OFFLINE, the Invite button is disabled. In HYBRID, only redacted packets (facts, EV# references, no raw files) may be exported.

Redaction profiles: Tight (facts only), Normal (facts + short quotes), Loose (for non‑sensitive test sessions).

No background scraping: The extension never auto‑reads the page unless the user clicks “Send back to ActCLI.”

No cookies/tokens exfiltration: Never transmit provider cookies; include only location.origin + a coarse provider label in audit.

Short‑lived invite tokens: Semhost mints a JWT with role=invitee, alias, ttl, origin=* or specific, and scopes it to a single seminar id.

Minimal API additions (semhost)
POST /invite/issue      # returns {invite_token, seminar_id, alias}
POST /invite/ingest     # {invite_token, alias, text, provider_hint, provenance}
WS/SSE /seminar/{id}/stream  # already have this; treat invitee as a participant


Acceptance (MVP):

User can add one web‑only model reply into a seminar with two clicks (copy packet, send back).

Audit shows the invite event and the ingested reply with alias and SHA‑256 of the packet.

OFFLINE mode disables the feature; HYBRID logs the export.

Risks: ToS differences across providers; DOM churn. Mitigations: default to manual copy/paste; per‑site profiles optional; keep user‑in‑the‑loop.

2) Human Invites — Observer and Commenter
What it does

Allow colleagues to watch a seminar in real time and (optionally) add comments (not full agent messages) via a secure link. This is for “centaur” sessions—AI + humans.

Complexity snapshot

Observer‑only: Low — read‑only WebSocket stream; no auth beyond a signed one‑time link.

Comment‑only: Low→Medium — same stream + a comment box that posts to semhost; comments appear as grey chips in the transcript.

Full participant: Medium→High — RBAC, throttling, attribution, and SSO.

MVP flows

Studio: Invite human → choose Observer or Commenter, set TTL, Generate link.

Link opens a minimalist page (or an embedded panel in Teams/Slack) that subscribes to WS/SSE read‑only.

For Commenter: a single input box posts to /seminar/{id}/comment (rate‑limited, profanity‑filter, never forwarded to external models by default). Moderator can promote a comment into the next round’s prompt.

Audit: invited emails (hashed display), role (observer/commenter), timestamps, and any comments (with author & SHA‑256).

Teams/Slack (optional first cut)

Use a standard incoming webhook to mirror seminar updates into a channel with a “View Live” link.

For comments, accept reply with hashtag (e.g., #actcli) and relay as a comment into the seminar. Keep it strictly opt‑in; nothing leaves without intentional action.

Policy

OFFLINE: observer/commenter allowed (it’s local); no export to external bots.

HYBRID: if a file is attached and mode locks to local, human invites remain ok (they don’t leak data); extension invites are disabled unless redaction profile allows.

Acceptance (Observer/Commenter):

Read‑only stream works for multiple viewers; comments show as separate chips, never auto‑fed to LLMs; all events in the evidence pack.

3) Where they fit in the roadmap

Now (after parity.run + Seminar Orchestrator MVP land smoothly):

Human Observer‑only, then Comment‑only. Cheap, high perceived value, no ToS risk.

Next: Browser Invite (MVP copy‑bridge) — unlocks web‑only models without tying you to brittle DOM glue or ToS risk.

Later: Live streaming per provider (profiled) if teams love it.

This keeps you focused on your core thesis (proof/audit) while giving a fun “wow” that doesn’t endanger privacy or stability.

4) Extra actuary‑convenience tools (scoped, high ROI)

Intelligent history (Studio & CLI)

Semantic search across job.json + audit.json, “Rerun” with param diff; save as template.

Why: instant reuse; tiny on top of the /history index.

Binder export

One click packages preflight.md, parity_report.md, and selected artifacts + SHA‑256 manifest into binder.pdf and pack.zip.

Why: turns outputs into client‑ready deliverables.

Parity target builder (Excel picker)

Studio helper to open baseline workbook, click cells/ranges, and auto‑generate parity.yml.

Why: removes the most error‑prone step when setting up parity.

Volatile‑to‑stable formula rewriter

Suggests INDIRECT/OFFSET rewrites to structured refs or INDEX/XMATCH, with before/after preview.

Why: common modernization pain; fast win.

Loss triangle importer & sanity checks

Quick importer for common triangle formats; flags monotonicity and obvious anomalies; emits tidy CSV.

Why: frequent daily chore; aligns with your actuarial focus.

CAS “Actuarial Kata” (deterministic exercises)

A few curated problems (Mack CL, GLM with exposure/offsets) with unit tests; local model provides hints only.

Why: community + recruiting; keeps everything deterministic.

Policy structure extractor (phase‑1)

Headers/definitions/endorsements + cross‑refs; no legal advice.

Why: adds breadth for P&C without scope creep.

5) Risks & mitigations (so we don’t step on landmines)

Provider ToS / automation flags: keep the extension manual first; no automatic clicks; no cookie exfiltration; fall back to “copy‑bridge” if a site changes.

Data leakage: enforce redaction profiles; extension is disabled in OFFLINE; HYBRID export is logged with packet hash.

Attribution: every invite (AI or human) must stamp alias/avatar + provenance and land in the evidence pack.

Noise: default human role is observer; comments are opt‑in and never auto‑fed to models—moderator must promote.

6) Acceptance checklist you can paste into the repo

Browser Invite (MVP)

 Studio renders “Invite AI via browser” → alias/avatar → Copy Packet.

 Extension pastes packet to clipboard and can ingest selection back to semhost.

 OFFLINE disables; HYBRID export logged (packet SHA‑256, alias, provider origin).

 Evidence pack updated.

Human Invites (Observer/Commenter)

 Generate signed link with TTL/role.

 Observer shows live transcript; Commenter posts grey chips; rate‑limited.

 Comments never auto‑feed to LLMs; moderator promotion only.

 Evidence pack logs participants and messages.

Convenience

 /history search + “Rerun”

 Binder export (PDF + ZIP)

 Parity target builder (cell/range picker)

Bottom line

Both features are doable without heavy lift if you start small: human observer/commenter links and a manual copy‑bridge extension. They preserve your trust posture (local‑first, audited hand‑offs) and meaningfully reduce friction. Once parity.run + the Seminar Orchestrator are in place, these become delight features that make seminars feel collaborative and inclusive—without compromising privacy or maintainability.

If you’d like, I can draft a Manifest V3 skeleton for the extension and the semhost endpoints (/invite/issue, /invite/ingest) so your devs can wire the MVP quickly.