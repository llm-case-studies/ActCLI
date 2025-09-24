# ActCLI Seminar Playbook

**Gate 0 → Protocol → Evidence Pack** - A practical guide for running multi-AI seminars with ActCLI.

## Gate 0: The 5-Minute Huddle (Before Any Round 1)

**Purpose:** Decide if a seminar is warranted; if yes, define verification, data policy, protocol, and stop criteria.

### Quick Decision Matrix

Score each dimension (0-2). **Sum < 4 = Skip seminar**, **4-7 = Lite seminar**, **8+ = Structured seminar**.

| Dimension | 0 (Skip) | 1 (Maybe) | 2 (Seminar) |
|-----------|----------|-----------|--------------|
| **Verification Cost** | Tests run in minutes | Slow simulation/validation | Expensive human review |
| **Error Consequence** | Low, reversible | Medium business impact | High stakes, regulated |
| **Ambiguity** | Well-known pattern | Some uncertainty | Many plausible paths |
| **Stakeholder Alignment** | Solo decision | Team coordination | Cross-functional buy-in |
| **Evidence Need** | Informal rationale | Documented decision | Audit-ready evidence pack |
| **Data Sensitivity** | Public/synthetic | Internal data | Regulated/sensitive files |

### Gate 0 Questions (Record Answers)

1. **Objective:** What decision do we need by when?
2. **Oracle:** What will verify success? (tests/parity.run/rubric → deterministic artifact)
3. **Data Policy:** HYBRID or OFFLINE? (Rule: first sensitive file attach → lock LOCAL)
4. **Protocol:** Which format fits the complexity? (see Protocol Cards below)
5. **Participants:** Which models, what roles? (local-first, escalate premium selectively)
6. **Budget:** Token cap, round cap, time limit?
7. **Stop Criteria:** Novelty plateau, score threshold, or human /stop?

## Protocol Cards (Choose the Lightest That Works)

### 🎯 **Delphi-Lite** (Anti-anchoring, 2-3 rounds)
**When:** Assumptions, requirements clarification, quick consensus
**Format:**
- R1: Blind responses (no peer visibility)
- Synthesis: Neutral summary of consensus + gaps
- R2: Revisions based on synthesis only
**Stop:** Change < epsilon or consensus reached

### 📊 **CEC (Claim-Evidence-Counter)** (Evidence-backed recommendations)
**When:** Audit-ready decisions, regulated outcomes
**Format:** Each response must include:
- **Claim:** Specific recommendation
- **Evidence:** Citation/calc/data with ID
- **Counter:** What could disprove this
**Output:** Ranked claims by evidence strength

### 🔄 **Annealed Round-Robin** (Breadth → Convergence)
**When:** Need creative options, stuck in local optimum
**Format:**
- **Diverge:** High-temperature diverse ideas (local models)
- **Prune:** Cluster/dedupe, score novelty (cheap judge)
- **Converge:** Low-temperature synthesis (local summarizer)

### ✅ **Propose → Approve → Run** (Deterministic finish)
**When:** Ground truth exists but evaluation is expensive
**Format:**
- Models propose solution
- Humans red-team proposal
- Organizer `/approve`
- System runs deterministic verification (tests/parity.run)

## Seminar Charter Template

```markdown
# [Topic] — Seminar Charter

**Organizer:** [Name] | **Facilitator:** Claude
**Decision Deadline:** [Date]

**Objective:** [1-2 sentences: what decision, why now]

**Oracle:** [How we'll verify: tests|parity.run|rubric → artifact]

**Data Policy:** HYBRID|OFFLINE
*Rule: First sensitive file attach → mode_lock_local, continue offline*

**Protocol:** [Delphi-Lite|CEC|Annealed RR|Propose→Approve→Run]

**Participants:**
- Router/Ideators: [local models]
- Judge/Quant: [local or premium]
- Summarizer: [local]
- Finalists: [premium, max N calls]

**Budget:** [token cap] | [round cap] | [time limit]

**Stop Criteria:** [novelty plateau|score threshold|timebox]

**Evidence Pack:** input hashes, seeds, versions, citations, approvals, mode events
```

## Ready-to-Run Topics

### 1. **Workbook Migration Strategy** (Perfect for CEC → Propose→Approve→Run)

**Gate 0 Setup:**
- **Objective:** Migrate Legacy_Claims.xlsm to Python/Power Query while preserving calculations
- **Oracle:** parity.run with targets.yml (95%+ match within tolerance)
- **Data Policy:** HYBRID until workbook attach → LOCAL
- **Protocol:** CEC (evidence-backed migration plan) → Propose→Approve→Run (parity check)

**Starter Prompt:**
```
We need to migrate a legacy actuarial workbook with VBA macros and complex formulas.
Using CEC format, recommend migration approach with evidence from:
- VBA complexity analysis from excel.inspect
- Formula volatility patterns
- External dependency audit
Each claim must cite specific evidence and propose counter-tests.
```

### 2. **Autonomous Vehicle Coverage Pricing** (Annealed RR → CEC)

**Gate 0 Setup:**
- **Objective:** Design pricing framework for AV fleet coverage (new product line)
- **Oracle:** Rubric scoring + pilot KPI dashboard (deterministic monitoring)
- **Data Policy:** HYBRID (public data/literature) → LOCAL if client data
- **Protocol:** Annealed RR (explore approaches) → CEC (evidence-backed recommendation)

**Starter Prompt:**
```
New business: autonomous vehicle fleet insurance. High uncertainty in:
- Frequency vs severity shifts
- Liability allocation (manufacturer/operator/owner)
- Technology risk evolution

Round 1: Generate diverse pricing framework options (high temperature)
Round 2: Converge to top 3 with implementation feasibility
```

### 3. **Workers Comp AI Impact** (Delphi-Lite → CEC)

**Gate 0 Setup:**
- **Objective:** Assess emerging workers comp risks from AI adoption
- **Oracle:** Risk monitoring framework + trigger thresholds
- **Data Policy:** HYBRID (industry reports) → LOCAL (client exposure data)
- **Protocol:** Delphi-Lite (assumptions) → CEC (risk framework)

### 4. **Integration Test Debug** (No Seminar - Single Agent)

**Decision:** Skip seminar ✋
- **Why:** Verification is cheap (compile → test → pass)
- **Action:** Single-agent debug loop with Claude
- **Evidence:** Git commit with passing tests

## Facilitator Script for Claude

### Kickoff
```
I'm facilitating this seminar. Before Round 1, confirming Gate 0:

Organizer, please confirm:
1. Objective & deadline?
2. Verification oracle?
3. Data policy (HYBRID/OFFLINE)?
4. Chosen protocol?
5. Participant roles?
6. Budget & stop criteria?

Once confirmed, I'll enforce the protocol and policy rules.
```

### Policy Enforcement
```
🔒 POLICY: If any file is attached, I will record "mode_lock_local"
and restrict to local models only. This will be logged in the evidence pack.
```

### Protocol Execution

**For CEC:**
```
Using CEC format. Each response must include:
- Claim: [specific recommendation]
- Evidence: [citation/data with ID]
- Counter: [what would disprove this]

I will reject responses without proper evidence citations.
```

**For Delphi-Lite:**
```
Round 1: Blind responses only. 150-word limit. No peer visibility.
[After synthesis]
Round 2: Revise based on synthesis only. No raw peer responses.
```

### Closeout
```
Seminar complete. Final report includes:
- Decision & rationale
- Risk log with owners
- Next actions (who/when)
- Evidence pack: mode events, approvals, seeds, hashes, citations

Ready to file report or need amendments?
```

## Report Template

```markdown
# [Topic] — Seminar Report

## Charter
[Paste charter block from above]

## Protocol & Participants
**Protocol:** [Name + key parameters]
**Models:** [Local SLMs] → [Premium finalists]
**Rounds:** [Number completed]

## Key Findings
| Claim | Evidence | Strength | Counter-Risk |
|-------|----------|----------|--------------|
| [Rec 1] | [Source/ID] | High | [What could break] |
| [Rec 2] | [Source/ID] | Medium | [Uncertainty] |

## Decision
**What we will do:** [Clear action]
**Why:** [Top 2-3 reasons with evidence]
**By when:** [Timeline]

## Risks & Mitigations
- **Risk 1:** [Description] → **Owner:** [Name] → **Due:** [Date]
- **Risk 2:** [Description] → **Owner:** [Name] → **Due:** [Date]

## Next Actions
- [ ] **[Action 1]** → [Owner] → [Due date]
- [ ] **[Action 2]** → [Owner] → [Due date]
- [ ] **Deterministic verification** → [/approve → run]

## Evidence Pack
- **Mode events:** [HYBRID→LOCAL transitions logged]
- **Approvals:** [Human gates + timestamps]
- **Artifacts:** [Hashes of inputs/outputs]
- **Citations:** [Evidence IDs → sources]
- **Seeds/Versions:** [Model versions + random seeds]
```

## Success Metrics

**Gate 0 Effectiveness:**
- 80%+ unnecessary seminars avoided
- Clear oracle defined before Round 1

**Protocol Performance:**
- Decision reached within budget
- Evidence quality sufficient for verification
- Deterministic artifacts generated

**Business Value:**
- Decisions stick (low reversal rate)
- Evidence packs pass audit
- Time-to-decision improved vs traditional meetings

---

*This playbook transforms "should we have a seminar?" into a 5-minute habit that preserves ActCLI's trust-by-design, local-first controls, and evidence-based decisions.* 🚀