# Excel Explorer POC Spec

Below is a Playground POC spec for a trust‑building Excel Explorer. If the POC lands well with actuaries, we'll integrate it as a first‑class ActCLI tool.

## 1) Motivation (why this belongs in ActCLI)

Trust before transformation. Actuaries won't believe claims about modernization until they can see that we truly understand a workbook's internals—VBA modules/procedures, named ranges (and scope), formulas, external links, and data model/Power Query presence—without opening Excel or executing anything. This Explorer is the "press F11, safely, on any OS" experience.

Fits ActCLI's thesis: CLI‑first, privacy‑first, deterministic last mile, and evidence packs. The Explorer produces deterministic, audit‑ready artifacts (tree JSON + extracted code) and streams results via the same Semhost (MCP) we already define for other tools. In HYBRID mode, brainstorming is allowed; when data attaches, we log the handoff and stay LOCAL/OFFLINE.

Reusability: The Explorer's inventory powers the next steps (Preflight flags and Parity runs), keeping one set of readers and one evidence pack format.

## 2) Review of options for an Excel "Explorer"

### Option A — Read‑only, cross‑platform parse (ZIP/OLE) — Recommended for POC

**What it is:** Open the file container itself; read workbook parts (XML in .xlsx/.xlsm, binary parts in .xlsb, OLE streams in .xls) to extract structure and code—no Excel required, no macro execution.

**Pros:** Works on Win/Mac/Linux; safe; deterministic; aligns with OFFLINE/HYBRID; easy to ship as a browser UI backed by Semhost SSE/WS.

**Cons:** .xlsb formula text is limited; we disclose that explicitly.

### Option B — Automate Excel/COM to "ask Excel" for metadata

**What it is:** Launch Excel (Windows only), query the VBE and workbook objects.

**Pros:** True to Excel's internal views.

**Cons:** Windows‑only; brittle/unattended; not compatible with OFFLINE/HYBRID guarantees for everyday use. Keep as an optional enrichment later, not for POC.

### Option C — LibreOffice/UNO headless

**What it is:** Open files with LibreOffice in headless mode and query API.

**Pros:** Cross‑platform; can recalc.

**Cons:** Semantics differ from Excel; not ground‑truth for actuarial parity. Treat as a utility, not the Explorer's backbone.

**Decision for POC:** Implement Option A (read‑only ZIP/OLE parse) with a friendly Explorer UI. It maximizes trust (safe/transparent), and it's directly aligned to ActCLI's architecture (Semhost RPC/SSE/WS + evidence packs).

## 3) Explorer POC — Product spec

### 3.1 Scope & non‑goals (POC)

**In:**

- **VBA:** Project → Modules → Procedures → read‑only code (searchable), "auto‑exec" markers (Auto_Open, etc.), and "risky token" highlights (CreateObject/GetObject/Shell, URLs).
- **Named ranges:** list with scope (workbook vs sheet), definition (A1 or formula), simple "where‑used" counts.
- **Sheets:** visible/hidden/veryHidden, used‑range size, formula/error counts.
- **Formulas:** families (grouping identical structures), complexity metrics (length/nesting), volatile function usage (e.g., INDIRECT/OFFSET/NOW/RAND), dynamic array presence (e.g., FILTER/UNIQUE/XLOOKUP/LET/LAMBDA), external/3‑D references.
- **Links & external data:** ODBC/SQL connections, external workbook refs, WEBSERVICE/CUBE functions; show hashed endpoints for privacy.
- **Power Query/Data Model:** presence and counts (no execution).
- **Artifacts:** one JSON (explorer.json) + optional extracted VBA source files under /artifacts/vba/... for deep‑dive.

**Out (for POC):** No recalculation, no transformations, no risk scoring; .xlsb formula‑text limitations disclosed. (Those arrive later with excel.inspect/parity.run.)

### 3.2 Inputs & outputs

**Input (RPC):**
```json
{
  "path": "/mnt/ro/Workbook.xlsm",
  "include_vba_source": true,
  "max_formulas": 250000,
  "hash_sensitive_strings": true
}
```

**Output artifacts:**
- `explorer.json` (deterministic, byte‑stable; includes sha256, sizes, versions; excludes timestamps)
- `/artifacts/vba/<Module>/<Procedure>.bas` (optional)
- `audit.json` append: tool name, param hash, artifact hashes, timings (same audit envelope as other tools).

**explorer.json (shape excerpt):**
```json
{
  "workbook": {
    "path": "/mnt/ro/Workbook.xlsm",
    "kind": "xlsm",
    "sha256": "…",
    "size_bytes": 1234567,
    "date_system": "1900",
    "calc_mode": "auto",
    "encrypted": false
  },
  "tree": [
    {"type":"vba","label":"VBA","children":[
      {"type":"module","label":"Module1","children":[
        {"type":"procedure","label":"Auto_Open",
         "detail":{"kind":"Sub","lines":23,"autoexec":true,"risky_tokens":["CreateObject"]},
         "code_ref":"artifacts/vba/Module1/Auto_Open.bas"}
      ]}
    ]},
    {"type":"named_ranges","label":"Named Ranges","children":[
      {"type":"named_range","label":"LossRatio_Total",
       "detail":{"scope":"workbook","ref":"Summary!$E$12","formula":null,"used_by_count":3}}
    ]},
    {"type":"sheets","label":"Sheets","children":[
      {"type":"sheet","label":"Summary",
       "detail":{"visible":"visible","used_cells":1245,"formula_cells":987,"error_cells":2}}
    ]},
    {"type":"formulas","label":"Formulas","detail":{
      "count":54321,
      "families":[{"pattern":"=SUM(Table1[Paid])","count":412}],
      "volatiles":[{"func":"INDIRECT","count":19}],
      "dynamic_arrays":[{"func":"FILTER","count":7}],
      "external_refs":[{"kind":"workbook","count":3}],
      "three_d_refs":2,
      "max_length":732,
      "max_depth":22
    }},
    {"type":"connections","label":"Connections","children":[
      {"type":"connection","label":"ODBC: DSN=ClaimsDB",
       "detail":{"dsn":"ClaimsDB","command_hash":"sha256:…","kind":"odbc"}}
    ]},
    {"type":"power_query","label":"Power Query/Data Model",
     "detail":{"power_query_present":true,"query_count":7,"data_model_present":true}}
  ],
  "notes": ["xlsb: formula text may be unavailable; values/stats only"]
}
```

### 3.3 UI (Studio) — "Explorer" panel

**Layout:** Left = tree; Right = details (cards). Search box filters tree by text (e.g., LossRatio, Auto_Open, INDIRECT).

**Detail cards:**
- **Summary:** path, kind, size, sha256, calc mode, date system, "No Execution" badge.
- **VBA code viewer:** read‑only, line numbers, keyword highlighting, quick copy, "risky tokens" chips.
- **Named range panel:** scope, definition (A1/formula), where‑used count (click shows sample formulas/sheets).
- **Formula insights:** top families; volatile/dynamic‑array tabs with "where used" examples; longest/top‑N formulas; external/3‑D reference counts.
- **Connections:** list with DSN/type; SQL/URL content is hashed (privacy).
- **Limitations chip:** shows .xlsb formula‑text caveat when applicable.

**Streaming:** Progress phases (open → sheets → names → formulas → vba → links → finalize) over SSE, cancel via WS; consistent with Semhost API.

### 3.4 Implementation notes (non‑coding)

- **Readers:** OOXML ZIP parts for .xlsx/.xlsm; binary package for .xlsb (values + metadata); OLE for .xls.
- **VBA static analysis:** extract vbaProject.bin / OLE streams; list modules/procedures; tokenize for "risky tokens"; mark auto‑exec procedures. (No execution.)
- **Formulas:** read formula text where available; build families by tokenizing and normalizing; compute metrics (length, depth, function set); count volatile & dynamic array functions; detect external and 3‑D references.
- **Privacy:** hash sensitive strings (SQL/URLs) before persisting.
- **Determinism:** exclude timestamps from explorer.json; include environment versions and artifact hashes in audit.json.

### 3.5 Acceptance criteria (POC)

- Module/procedure counts match Excel VBE for known test workbooks; code view shows identical source lines.
- Named ranges show correct scope and definitions; where‑used counts are directionally correct (± small tolerance on massive sheets).
- Volatile function counts and top formula families are reproducible between runs.
- .xlsb limitation is clearly shown when encountered.
- Artifacts are byte‑identical on repeated runs in the same environment.

## 4) Backlog (future) — sandboxed execution for VBA & formulas

Not in the POC; scoped for a follow‑on sprint once Explorer earns trust.

### Windows "Excel Runner" micro‑VM

- Open workbook with macros disabled by default; force CalculateFullRebuild; snapshot target cells/ranges into baseline.json.
- Optional, explicit: reopen with macro security loosened for a whitelisted entry point and capture baseline_after_macro.json.
- Safety rails: air‑gapped VM; timeouts; read‑only inputs; hashed logs.
- Purpose: ground truth for parity.

### Cross‑platform formula evaluator

- Use a spreadsheet engine (e.g., JS or Java‑based) to evaluate most Excel functions on Linux/macOS for dev velocity; keep a coverage matrix and fall back to Excel Runner for unsupported parts.
- Purpose: fast local checks; not an audit authority.

Integration with parity.run (already sketched in ActCLI Dev Specs): use targets.yml, compare baseline.json vs migrated pipeline outputs with tolerances, and emit an audit‑ready diff report + repro.sh.

## 5) Testing approach with public‑domain workbooks (perception & fidelity)

### 5.1 Corpus design (public or synthesizable):

- **Vanilla:** small .xlsx, no macros/links (e.g., public financial sample).
- **Volatile zoo:** formulas using INDIRECT, OFFSET, RAND, TODAY, etc. (we can synthesize safely).
- **Named‑range heavy:** dozens of workbook‑ and sheet‑scoped names; nested formulas referencing names.
- **External references:** cross‑workbook links and a few WEBSERVICE/CUBE formulas (hash endpoints).
- **Power Query/Data Model:** presence only (e.g., simple query against a local CSV; no execution).
- **VBA risk sample:** macros with CreateObject/GetObject/Shell strings (demonstrate detection; do not execute).
- **.xlsb large:** many formulas to surface the "formula text limited" notice.
- **Legacy .xls:** older format with a few macros.

Where suitable public‑domain files aren't straightforward, we'll generate the workbook from open data and open‑source the generator so prospects can rebuild them. That's safer and still realistic.

### 5.2 Perception test script (30–45 min moderated):

**Tasks:**
1. "Find the Auto_Open macro and show its code."
2. "Which named ranges drive the 'Loss Ratio' on Summary?"
3. "Show me top formula families on 'Triangle' and where volatiles appear."
4. "Are there any external connections?"
5. "What are the hidden or veryHidden sheets?"

**Measures:**
- Time‑to‑answer per task (target: <60s each after a brief intro).
- Confidence rating (1–7) that "the tool sees what Excel sees."
- Perceived safety (1–7) and understanding of the "No Execution" stance.
- Clarity: tree discoverability, code readability, naming/scope comprehension.
- Exit questions: What felt missing before you'd trust parity checks? What made you trust (or doubt) the view?

### 5.3 Engineering test harness

**Golden assertions:**
- Module/procedure counts and exact procedure names match a hand‑verified baseline.
- Named ranges set equals Excel's Name Manager export for the sample.
- Volatile counts match expected per synthesized workbook.
- .xlsb sample triggers the limitation notice.

**CI:** run Explorer on the corpus; compare explorer.json to golden outputs (hash‑stable).

**Evidence:** store explorer.json + extracted VBA artifacts alongside audit.json for each sample run.

## 6) Delivery format (Playground POC)

- **Tool name (POC):** excel.explore (read‑only).
- **Semhost envelope:** POST /mcp/rpc → job; GET /mcp/sse → progress/events; GET /mcp/ws → cancel/heartbeat. Same event shapes used elsewhere.
- **Studio route:** /ui/explorer with file picker and the tree/detail view.
- **Artifacts:** explorer.json, optional /artifacts/vba/*, and audit.json append.
- **Path to integration:** When the POC is approved, promote excel.explore to excel.inspect by adding preflight flags/summary cards, then couple with parity.run for proof of equivalence—all within the existing ActCLI pillars (trust‑by‑design, hybrid/offline, evidence packs).

## Appendix — Non‑functional requirements (POC)

- **Safety:** never execute macros or queries; no egress when OFFLINE; hash sensitive strings.
- **Determinism:** identical outputs for identical inputs in same environment (exclude timestamps in primary JSON; include them only in audit).
- **Performance:** open + enumerate medium files (< 100k formulas) in < 15 s on a laptop; show progressive results via SSE.
- **Transparency:** always show file sha256, "No Execution" badge, and any format limitations (e.g., .xlsb formula text).