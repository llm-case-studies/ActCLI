# ActCLI Core MCP — Critical Status, Technical Debt & Strategic Roadmap

*A comprehensive consolidation of Sprint 1-3 status, extensive stakeholder feedback, critical technical debt analysis, and prioritized feature roadmap*

---

## Executive Summary

Sprint 1-3 delivered a working MCP-based Excel inspection platform, but significant technical debt and missing core features prevent production deployment. This document consolidates all feedback to identify what will break us as we scale and what critical features are missing.

**Current Reality**: We have a demo-ready Excel inspector with major architectural gaps
**Critical Gap**: No seminar orchestration, no deterministic proof tools, brittle reconnection logic
**Technical Debt**: Untyped wire protocols, ad-hoc error handling, no job persistence, provider brittleness

---

## Part I: Technical Debt Analysis - What Will Break Us

### CRITICAL Technical Debt (Will Block Production)

#### 1. Untyped Wire Protocols & Schema Drift
**Problem**: MCP messages, SSE events, job artifacts use ad-hoc dictionaries
- No Pydantic models for requests/replies
- Schema drift across tools inevitable
- No contract tests for envelope stability
- Error taxonomy is inconsistent strings

**Impact**: Tool development becomes unreliable, debugging impossible, client integrations break
**Fix Required**: Promote all wire formats to typed Pydantic v2 models with golden JSON tests

#### 2. Brittle WS/SSE Reconnection Logic
**Problem**: High-CPU reconnection loops, no exponential backoff, no connection state visibility
- Runaway loops when server down
- Hidden tab continues reconnecting
- No user feedback on connection loss
- Single point of failure for real-time updates

**Impact**: Production deployments will crash user browsers, customer complaints
**Fix Required**: Exponential backoff, "Offline • Retry" banner, pause on tab hidden

#### 3. No Job Persistence & History
**Problem**: Jobs only exist in-memory, no historical tracking, no job resumption
- Server restart = lost job status
- No "/history" endpoint for debugging/demos
- No job filtering or search capability
- No "resume from artifact" workflows

**Impact**: Production instability, inability to debug issues, poor user experience
**Fix Required**: SQLite job store with proper indexing and filtering

#### 4. Provider Brittleness & Silent Failures
**Problem**: CLI providers fail silently, no alias normalization, no capability probing
- Echo fallback invisible to users
- "claude-3-5" vs "sonnet" confusion
- No "Test models" capability
- Provider discovery cache never expires

**Impact**: Users blame ActCLI for provider issues, support burden increases
**Fix Required**: Centralized AdapterFactory with probe endpoint and visible fallback badges

#### 5. Tool Isolation & Resource Management
**Problem**: All tools run in main process, no isolation, no resource limits
- Heavy tools (parity.run, pdf processing) block everything
- No per-tool memory/CPU budgets
- No subprocess isolation option
- Cooperative cancellation only

**Impact**: Production deployments will hang/crash on large files
**Fix Required**: Worker subprocess support with isolated=true flag

### HIGH IMPACT Technical Debt

#### 6. Path Validation Scattered Across Tools
**Problem**: Each tool reimplements RO/escape/symlink validation differently
- Inconsistent security posture
- Copy-paste security bugs inevitable
- No central testing of edge cases
- Path validation logic not reusable

**Impact**: Security vulnerabilities, maintenance burden
**Fix Required**: Extract path-safety library with comprehensive test coverage

#### 7. Evidence Writer Duplication
**Problem**: Every tool manually appends audit.json, handles hashing differently
- No guaranteed audit invariants
- Inconsistent artifact schemas
- Manual audit.json corruption possible
- No centralized evidence testing

**Impact**: Evidence packs become unreliable, compliance issues
**Fix Required**: Single evidence writer service with invariant enforcement

#### 8. Configuration Management Chaos
**Problem**: Settings scattered across ENV, CLI flags, defaults with no central truth
- Effective config invisible to debugging
- Docker deployment configuration hell
- HYBRID/OFFLINE policy enforcement inconsistent
- No config validation on startup

**Impact**: Production deployment failures, inconsistent behavior
**Fix Required**: Single typed Settings class with /status endpoint

---

## Part II: Missing Core Features - The Real Roadmap

### TIER 0 - Missing Core Features Blocking Vision

#### A. Seminar Orchestration System (The Main Product!)
**What's Missing**: The entire seminar system is currently manual experiments
- **Gate-0 Triage System**: Automated decision on "should we seminar?"
  - Verification Cost, Error Consequence, Ambiguity scoring
  - Stakeholder Alignment assessment
  - Evidence Need classification
  - Auto-recusal with next pipeline recommendation
- **Protocol Execution Engine**:
  - Delphi-Lite: blind R1 → synthesis → R2 → consensus
  - CEC (Claim-Evidence-Counter): structured argument schema
  - Cross-Examination: adversarial validation
  - Annealed Round-Robin: temperature schedules for convergence
- **Consensus Claim Object**: Standardized hand-off to deterministic tools
  ```json
  {
    "sheet_range": "Results!A1:G200",
    "tolerances": {"abs": 1e-8, "rel": 1e-6, "rounding": 2},
    "method": "MackCL | BF | GLM | PQ | Python",
    "inputs": ["Triangles", "Factors"],
    "evidence": ["hash(inputs)", "model_versions", "seed"],
    "recusal": null
  }
  ```
- **SSE Event Stream**: round_start, synthesis_published, claim_logged, approved_run
- **Charter System**: Objective, Oracle, Protocol, Roles→Model tiers, Budgets, Stop criteria

**AC**: Seminar Charter saved to out/sessions/S-*/charter.json, SSE streaming works, consensus claim drives parity.run

#### B. Deterministic Proof System (parity.run)
**What's Missing**: The "prove" part of "assistive → approve → prove"
- **Baseline Comparison**: Compare workbook output vs Python/PQ pipeline
- **Tolerance Engine**: abs/rel/rounding tolerance with pass/fail determination
- **Reproducibility**: Fixed seeds/versions → identical parity_report.md
- **Evidence Integration**: SHA-256 verification, repro.sh generation
- **Approve→Run Bridge**: One-click from seminar consensus to proof execution

**AC**: Given baseline.xlsx + targets.yml + new_pipeline.py, emit parity_report.md/pdf + repro.sh that works on clean machine

#### C. Cost Policy & Escalation Framework
**What's Missing**: No cost controls, no local-first enforcement
- **Cost Budgets**: per-seminar, per-participant, per-tool limits
- **Escalation Rules**: escalate_on=[low_score, high_disagreement, consensus_failure]
- **Local-First Policy**: Try local models first, cloud only on escalation
- **Cost Tracking**: "Cloud use: N" badges, cost_summary in evidence packs
- **Failover Logic**: cloud timeout → continue with local models

**AC**: Evidence pack logs all escalations, Studio shows cost badges, local models attempted first

### TIER 1 - Major Missing Features

#### D. Excel Explorer Integration
**What's Missing**: The full Excel analysis beyond preflight
- **Explorer Tree**: VBA modules/procedures, named ranges + scope, sheet visibility
- **Formula Families**: volatile/dynamic array/3D ref classification with hotspots
- **Dependency Mapping**: formula graph with circularity detection, risk scoring
- **Connection Analysis**: XLL/COM add-ins, Excel4 macro refs, external link lineage
- **Signals & Gate-0 Tab**: "Seminar Essential/Optional/Skip" badges per finding
- **One-Click Handoff**: "Seminar on this finding" buttons

**AC**: Module/procedure counts match Excel VBE on golden samples, .xlsb limitations clearly surfaced

#### E. Core MCP Tools Bundle
**What's Missing**: Tools beyond excel.inspect to prove platform value
- **csv.audit**: Schema/delimiter checks, suspicious patterns, date validation, BOM detection
- **pdf.sanitize**: Structure safety, embedded scripts/images, metadata analysis
- **web.snapshot**: Playwright-based page capture with DOM hash, respects robots.txt
- **web.crawl**: Domain-scoped BFS with de-dupe, local LLM summarization
- **policy.extract**: Insurance policy structure parsing (headers, definitions, endorsements)

**AC**: Each tool emits minimal MD/JSON artifacts following evidence pack standards

#### F. Advanced Studio Features
**What's Missing**: Professional IDE-level capabilities
- **Command Palette**: Ctrl/Cmd+K for fuzzy actions (Start/Next/Export, open Models/Providers)
- **Model Detail Drawer**: Pricing, policy, recent usage, actions (1×1 chat, add to seminar)
- **Monaco Editors**: JSON editing with syntax highlighting for advanced configs
- **Copy/Download Buttons**: All artifacts, with toast notifications
- **Keyboard Shortcuts**: Ctrl/Cmd+Enter (Start/Next), Ctrl/Cmd+S (Export)
- **Theme Persistence**: Size/splits saved to localStorage

**AC**: Studio feels like professional IDE, keyboard-driven workflows supported

### TIER 2 - Collaboration & Growth Features

#### G. Human-AI Collaboration System
**What's Missing**: The "centaur teams" capability mentioned in experiments
- **Human Observer Links**: TTL-limited read-only seminar viewing
- **Comment-Only Mode**: Rate-limited comments (never auto-fed to models)
- **Teams/Slack Integration**: Webhook mirroring with "View Live" links
- **Moderator Controls**: Promote comments to next round prompts
- **RBAC Foundation**: Role-based access for enterprise deployment

**AC**: Multiple viewers work, comments as grey chips, all events in evidence pack

#### H. Browser Extension for Web-Only Models
**What's Missing**: Integration with web-based models lacking CLI support
- **Copy-Bridge MVP**: Manual seminar packet copy/paste workflow
- **Redaction Profiles**: Tight/Normal/Loose based on sensitivity
- **Invite Token System**: Short-lived JWT for secure model integration
- **Provider ToS Safety**: No automation, no cookie exfiltration, manual user actions only
- **Audit Integration**: All invites logged with alias/SHA-256/provenance

**AC**: User can add Grok/Claude-web responses with 2 clicks, audit trail complete

#### I. Evidence Pack v0.3 & Compliance
**What's Missing**: Enterprise-grade evidence system
- **Standard Schema**: participants[], mode_handoffs[], cost_summary, verified_assertions[]
- **Environment Detection**: GPU presence, system capabilities
- **ZIP Export**: One-click artifact packaging with signatures
- **Pack Verification**: `actcli verify pack.zip` for tamper detection
- **Retention Policies**: Configurable lifecycle management
- **Client Handoff Mode**: Redacted exports for external sharing

**AC**: Evidence packs pass compliance audit, ZIP/verify workflow works

### TIER 3 - Platform Extensions & Growth

#### J. Bulk Operations & Profiles
**What's Missing**: Enterprise-scale processing capabilities
- **Folder Queue System**: Bulk file processing with concurrency controls
- **Profile Engine**: strict/fast/custom budget configurations
- **Aggregate Reporting**: Multi-file analysis with rollup statistics
- **Resource Management**: Per-profile memory/CPU/time limits
- **Progress Tracking**: Bulk job status with pause/resume capability

#### K. Windows Excel Runner (VM-based)
**What's Missing**: Ground-truth Excel calculation capability
- **Micro-VM Architecture**: Windows VM with Office automation controls
- **Security Hardening**: msoAutomationSecurityForceDisable, air-gapped execution
- **Ground Truth Calculation**: Application.CalculateFullRebuild for baseline capture
- **Job Integration**: Same MCP envelope, status streaming to Studio
- **Macro Whitelisting**: Explicit approval workflow for macro execution

**AC**: No macros by default, CalculateFullRebuild logged, time-frozen runs for parity

#### L. Advanced Actuarial Tools
**What's Missing**: Domain-specific workflow automation
- **Loss Triangle Importer**: Common format support with anomaly detection
- **Volatile Formula Rewriter**: INDIRECT/OFFSET → INDEX/XMATCH suggestions
- **Parity Target Builder**: Visual Excel cell/range picker for parity.yml generation
- **CAS Actuarial Kata**: Deterministic exercises (Mack CL, GLM) with local model hints
- **Intelligent History Search**: Semantic search with "Rerun with diff" capability

---

## Part III: Critical Refactoring Requirements

### Package Architecture Overhaul (REQUIRED BEFORE TIER 1)

**Current Problem**: Monolithic src/ structure prevents proper separation of concerns

**Required Structure**:
```
src/
├── semhost/          # FastAPI app, MCP envelope, job manager
├── actcli/           # CLI + seminar orchestration
├── tools/            # MCP tool implementations
├── shared/           # Common types, events, validation
└── studio/           # SPA (move from root)
```

**Why Critical**: Tool isolation, clear dependencies, proper testing boundaries

### Wire Protocol Hardening (BLOCKS ALL INTEGRATIONS)

**Current Problem**: Ad-hoc JSON structures everywhere

**Required Changes**:
- Pydantic v2 models for all MCP requests/replies
- SSE event schemas with version compatibility
- Error taxonomy with deterministic codes
- Golden JSON contract tests for stability
- Idempotent job IDs by request hash

**Why Critical**: Client integrations will break without stable contracts

### Provider Normalization (BLOCKS ENTERPRISE DEPLOYMENT)

**Current Problem**: CLI provider discovery is fragile and confusing

**Required Changes**:
- Centralized AdapterFactory with capability caching
- Alias normalization (claude-3-5 → sonnet)
- "Test models" probe endpoint for Studio
- Echo-fallback badges for silent failures
- Refresh policies to prevent stale cached data

**Why Critical**: Enterprise customers need reliable provider status

---

## Part IV: New Feature Specifications (From Stakeholder Feedback)

### Engagement & Growth Features

#### 1. Challenge System ("Excel Safari")
- **VBA Safari**: Point scoring for finding Auto_Open, external links, volatiles
- **Parity Race**: First to all-green diff on target range with Python/PQ stub
- **Risk Map Hunt**: Identify highest-risk formula cluster, propose rewrite
- **Guardrails**: Sample workbooks only, OFFLINE mode enforced, evidence packs for scoring

#### 2. Share Evidence Packs System
- **Redacted Export**: ZIP with preflight.md + consensus_claim.txt, no sensitive data
- **Open-in-ActCLI**: Deeplinks for sharing challenges and results
- **Viewer Mode**: Drag-drop pack browsing, offline parity.run execution
- **Invite Tokens**: Pack sharing includes invite to try ActCLI locally

#### 3. Seminar Showdown (Protocol Comparison)
- **A/B Testing**: Same prompt through Delphi-Lite vs Annealed RR
- **Metrics Collection**: Time-to-consensus, disagreement count, cost comparison
- **Deterministic Finish**: Both protocols end with Approve→Run verification
- **Learning Loop**: Protocol selection based on historical performance

### Advanced Excel Features

#### 4. Formula Graph & Hotspot Visualization
- **Dependency Mapping**: Visual graph of cell dependencies with cluster analysis
- **Risk Scoring**: Volatile cascade detection, circular reference identification
- **Hotspot Analysis**: Most complex/risky formula clusters highlighted
- **Modernization Suggestions**: OFFSET→INDEX/XMATCH rewrites with parity stubs

#### 5. One-Click Transform Suggestions
- **Pattern Recognition**: Common volatile formula patterns
- **Safe Rewrites**: Guided transformations with before/after preview
- **Parity Harness**: Auto-generated test stubs for transformation validation
- **Evidence Integration**: All suggestions tracked in evidence pack

### Platform Integration Features

#### 6. OpenTelemetry Observability
- **Span Coverage**: POST /mcp, job execution, SSE streaming
- **Structured Logs**: Job lifecycle with queued/started/progress/fault/result
- **Path Redaction**: Secrets/sensitive paths scrubbed from logs
- **Slow Job Warnings**: Alerts for jobs approaching budget limits

#### 7. Docker Production Hardening
- **Security**: Read-only root FS, no-new-privileges, minimal base image
- **SBOM Generation**: Software bill of materials for security scanning
- **Multi-Profile Images**: core/extended/enterprise variants
- **Service Integration**: systemd/launchd/sc.exe scripts for native services

---

## Part V: Risk Analysis & Mitigation

### High-Risk Technical Decisions

#### 1. Tool Isolation Strategy
**Risk**: Worker subprocesses add complexity, debugging difficulty
**Mitigation**: Start with isolated=true flag, keep same public API, gradual migration
**Decision Point**: Accept complexity for production stability vs keep simple architecture

#### 2. Provider Extension Strategy
**Risk**: Browser extension creates ToS violations, maintenance burden
**Mitigation**: Manual copy-bridge only, no DOM automation, user-in-loop always
**Decision Point**: Collaboration value vs legal/maintenance risk

#### 3. Windows VM vs Container Strategy
**Risk**: VM orchestration complexity vs Office licensing constraints
**Mitigation**: Phase approach - containers for non-Office tools, VM only for Excel automation
**Decision Point**: Enterprise Excel accuracy vs deployment complexity

### Business Model Risks

#### 4. Feature Scope Creep
**Risk**: Actuarial convenience tools dilute core value proposition
**Mitigation**: Strict TIER system, evidence-pack alignment requirement
**Control**: All features must support "assistive → approve → prove" workflow

#### 5. Community vs Enterprise Tension
**Risk**: Open source features compete with paid enterprise features
**Mitigation**: Core bundle open, advanced orchestration/compliance paid
**Strategy**: Evidence packs + seminar orchestration = community, RBAC/SSO/audit = enterprise

---

## Part VI: Decision Framework & Next Actions

### Immediate Decisions Required (Next 2 weeks)

1. **Refactoring Priority**: Accept 2-week delay for package restructure + wire typing?
2. **Seminar Orchestrator Scope**: Full Gate-0 + protocols or minimal MVP first?
3. **parity.run Integration**: Standalone tool or built-in seminar bridge?
4. **Resource Allocation**: How many developers for next 4-week sprint?

### Technical Architecture Decisions (Next 4 weeks)

1. **Job Store**: SQLite vs PostgreSQL for production deployment?
2. **Tool Isolation**: Accept subprocess complexity or keep in-process?
3. **Provider Strategy**: Normalize all providers or focus on most reliable subset?
4. **Evidence Schema**: Lock v0.3 format or allow evolution?

### Product Strategy Decisions (Next 8 weeks)

1. **Collaboration Features**: Human invites + browser extension priority level?
2. **Excel Runner**: Windows VM development investment worth accuracy benefit?
3. **Growth Features**: Challenge system + sharing priority vs core platform?
4. **Enterprise Path**: What triggers move from open core to commercial features?

---

## Part VII: Prioritization Matrix

### MUST FIX (Will Block Production)
1. **WS/SSE Reconnection Logic** - Customer complaints inevitable
2. **Wire Protocol Typing** - Integration stability blocker
3. **Job Persistence** - Production instability
4. **Provider Brittleness** - Support burden escalation

### MUST BUILD (Core Value Missing)
1. **Seminar Orchestrator** - Main product differentiator
2. **parity.run** - Completes value proposition
3. **Cost Policy** - Enterprise requirement
4. **Evidence Pack v0.3** - Compliance requirement

### SHOULD BUILD (Competitive Advantage)
1. **Excel Explorer** - Deep differentiation
2. **Core Tools Bundle** - Platform breadth
3. **Studio Polish** - Professional perception
4. **Human Collaboration** - Unique positioning

### COULD BUILD (Growth & Engagement)
1. **Challenge System** - Viral mechanics
2. **Browser Extension** - Adoption reduction
3. **Windows VM** - Accuracy advantage
4. **Bulk Operations** - Enterprise scale

---

## Conclusion: The Real Road Ahead

We have a solid foundation with Excel inspection working, but we're missing the core seminar orchestration and proof systems that make ActCLI unique. The technical debt in reconnection, typing, and job management will cause production failures.

**Priority Order**:
1. **Fix the debt that will break us** (WS/SSE, typing, job store, providers)
2. **Build the missing core** (seminar orchestrator, parity.run, cost controls)
3. **Add competitive features** (Excel Explorer, human collaboration, tools bundle)
4. **Enable growth** (challenges, sharing, browser extension)

The castle foundation is solid, but we need to build the core rooms (seminar hall, proof laboratory) before we add the decorative towers (challenges, sharing). And we need to fix the plumbing (reconnection, typing) before residents move in.

**Next Sprint Focus**: Technical debt remediation + Seminar Orchestrator MVP + parity.run tool

---

*Document reflects consolidated analysis of all stakeholder feedback, technical gaps, and strategic requirements for ActCLI platform completion*