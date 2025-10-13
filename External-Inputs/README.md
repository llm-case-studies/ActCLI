# External Inputs: AI Conversation Triage Process

**Purpose:** Capture valuable insights from external AI conversations (ChatGPT, Claude.ai, Gemini, etc.) and systematically evaluate them for incorporation into ActCLI.

**Status:** Internal process for building ActCLI (not a product feature - see backlog for future feature development)

## Quick Start

### 1. Capture a Conversation

When you have a valuable AI conversation:

1. Export/copy the conversation (use platform's share feature if available)
2. Copy `templates/intake-template.md` to `intake/YYYY-MM-DD-brief-topic.md`
3. Fill in the template with conversation details
4. Commit to your branch (intake/ is git-ignored, so only you see it until triaged)

**Example filename:** `intake/2025-09-30-anthropic-caching-implementation.md`

### 2. Triage with Gemini

Run the automated triage helper:

```bash
# Triage a single file
python scripts/triage_external.py intake/2025-09-30-anthropic-caching-implementation.md

# Triage all pending intakes
python scripts/triage_external.py --all
```

Gemini will:
- Read the full conversation (2M token context!)
- Apply quality gates from `templates/triage-checklist.md`
- Suggest category, priority, and owner
- Generate a triage summary

Review Gemini's recommendation and approve/modify.

### 3. Manual Triage (Alternative)

If you prefer manual review:

1. Read `templates/triage-checklist.md`
2. Review the intake file
3. Decide: code-suggestions | architecture-ideas | docs-improvements | rejected
4. Move file to appropriate `triaged/` subfolder
5. Fill in "Triage Notes" section at bottom of file

### 4. Act on Triaged Items

**For code-suggestions:**
```bash
# Create GitHub issue
gh issue create --title "Implement Anthropic prompt caching" \
  --body "See External-Inputs/triaged/code-suggestions/001-anthropic-caching.md" \
  --label enhancement --assignee @alex

# Implement and reference
git commit -m "feat(seminar): add prompt caching (#45)"

# Mark as incorporated
echo "- 001-anthropic-caching → src/actcli/seminar/adapters/anthropic.py ($(date +%Y-%m-%d))" \
  >> incorporated/CHANGELOG.md
```

**For architecture-ideas:**
- Add to next team sync agenda
- Document in relevant `docs/` file with "Future Consideration" section

**For docs-improvements:**
- Implement immediately (low friction)
- No issue needed unless substantial

**For rejected:**
- Ensure rationale is documented
- Serves as institutional memory

## Directory Structure

```
External-Inputs/
├── README.md                    # This file
├── .gitignore                   # Protects intake/ from accidental commits
├── intake/                      # Your raw conversation dumps (git-ignored)
│   ├── .gitkeep
│   └── 2025-09-30-*.md         # Manual imports, only visible to you
├── triaged/                     # Reviewed & categorized (committed to repo)
│   ├── code-suggestions/       # Ready to implement
│   │   ├── 001-anthropic-caching.md
│   │   └── 002-gate0-extended-thinking.md
│   ├── architecture-ideas/     # Needs design discussion
│   │   └── 001-seminar-orchestration-improvements.md
│   ├── docs-improvements/      # Documentation updates
│   │   └── 001-ownership-model-refinement.md
│   └── rejected/               # Not applicable (with rationale)
│       └── 001-blockchain-audit-trail.md
├── incorporated/               # Successfully merged
│   └── CHANGELOG.md            # Track what got incorporated where
└── templates/                  # Standardized formats
    ├── intake-template.md      # Use this for manual imports
    └── triage-checklist.md     # Review criteria
```

## Workflow Diagram

```
External AI Chat (ChatGPT, Claude.ai, etc.)
    ↓
[Manual Export] → intake/YYYY-MM-DD-topic.md
    ↓
[Gemini Triage] → Analysis + Recommendation
    ↓
[Human Review] → Accept/Modify/Reject
    ↓
Move to triaged/{category}/NNN-topic.md
    ↓
┌────────────────┬──────────────────┬─────────────────┬──────────────┐
│ code-suggests  │ architecture     │ docs-improve    │ rejected     │
│ → GitHub issue │ → team sync      │ → implement now │ → document   │
│ → implement    │ → design doc     │                 │   rationale  │
│ → PR + merge   │ → future backlog │                 │              │
└────────────────┴──────────────────┴─────────────────┴──────────────┘
    ↓
incorporated/CHANGELOG.md (track success)
```

## Why Gemini for Triage?

**Strengths:**
- **2M token context window** - can read entire long conversations without truncation
- **No code modification risk** - only analyzing/recommending, not editing files
- **Pattern recognition** - good at identifying themes across multiple conversations
- **Cost effective** - cheaper than Claude/GPT-4 for bulk analysis

**Role:**
- Read conversation
- Apply quality gates (relevance, novelty, feasibility, safety, maintainability)
- Suggest category + priority
- Flag risks or concerns
- **Human has final say** - Gemini recommends, you decide

## Quality Gates (Applied During Triage)

All inputs must pass:
1. **Relevance**: Directly applicable to ActCLI mission
2. **Novelty**: Not already implemented or documented
3. **Feasibility**: Can implement with current resources
4. **Safety**: No security/compliance risks
5. **Maintainability**: Won't create technical debt

See `templates/triage-checklist.md` for detailed criteria.

## Success Metrics

Track monthly:
- **Intake volume**: How many conversations captured
- **Triage rate**: % reviewed within 48 hours
- **Incorporation rate**: % triaged → merged to codebase
- **Rejection rate**: % rejected (with rationale)
- **Cycle time**: Days from intake to incorporation

Goal: **>50% incorporation rate** (high-quality filtering)

## Tips for Effective Use

### For Capturing Conversations

✅ **Do:**
- Export immediately when conversation concludes
- Include full context (don't just grab the "good parts")
- Note what problem you were trying to solve
- Capture URLs if platform provides shareable links

❌ **Don't:**
- Copy conversations with API keys or credentials (sanitize first)
- Wait days to export (you'll forget the context)
- Cherry-pick snippets (Gemini needs full conversation for analysis)

### For Triage

✅ **Do:**
- Triage within 48 hours while memory is fresh
- Be honest about rejection (saves time later)
- Document why you reject (institutional memory)
- Consult area owners if unsure about fit

❌ **Don't:**
- Auto-accept Gemini's recommendation without review
- Skip the "Risk Assessment" section
- Assume code snippets from AI are production-ready (test first!)
- Create GitHub issues for rejected items

### For Incorporation

✅ **Do:**
- Reference the external input file in commit messages
- Add tests for any code from external suggestions
- Update `incorporated/CHANGELOG.md` when merged
- Give credit if conversation had novel insight

❌ **Don't:**
- Blindly copy-paste code without understanding it
- Skip backward compatibility checks
- Forget to sanitize any sensitive data
- Lose track of what got incorporated (update changelog!)

## Integration with ActCLI Workflow

### Ownership Areas
External inputs get assigned to area owners:
- **Core Platform** (@alex): Backend, CLI, seminar, MCP
- **Browser Extension** (@Codex-BrExt, @Claude-BrExt)
- **Studio** (future): SPA/web interface
- **Testing/Docs** (cross-cutting)

### Audit Trail
Incorporated external inputs are tracked in:
- `incorporated/CHANGELOG.md` - what got merged
- Git commit messages - reference external input file
- GitHub issues - link to triaged file

### Team Sync
- Weekly agenda item: "Review pending architecture-ideas"
- Monthly metric review: incorporation rate, common themes

## Future Enhancements

When this becomes a product feature (see backlog):
- Browser extension "Export to ActCLI" button
- Semhost API endpoint: `POST /external-inputs/intake`
- CLI command: `actcli external triage <file>`
- Automatic similarity detection (avoid duplicates)
- Integration with ActCLI seminar for collaborative triage

For now: **keep it simple, manual, and disciplined.**

## Examples

### Example 1: Code Suggestion → Merged

**File:** `intake/2025-09-30-anthropic-caching.md`
**Gemini Analysis:** "High relevance, ready to implement, P1 priority"
**Human Decision:** Agree, assign to Core Platform owner
**Outcome:**
- Moved to `triaged/code-suggestions/001-anthropic-caching.md`
- Issue #45 created
- PR merged within 3 days
- Added to `incorporated/CHANGELOG.md`

### Example 2: Architecture Idea → Deferred

**File:** `intake/2025-09-29-gate0-extended-thinking.md`
**Gemini Analysis:** "Interesting but needs design discussion, P2 priority"
**Human Decision:** Agree, defer to architecture-ideas
**Outcome:**
- Moved to `triaged/architecture-ideas/001-gate0-extended-thinking.md`
- Added to team sync agenda
- No immediate action, revisit in Sprint 5

### Example 3: Rejected

**File:** `intake/2025-09-28-blockchain-audit-trail.md`
**Gemini Analysis:** "Over-engineered, conflicts with current SHA-256 approach"
**Human Decision:** Agree, reject with rationale
**Outcome:**
- Moved to `triaged/rejected/001-blockchain-audit-trail.md`
- Rationale documented: "SHA-256 + git history sufficient for compliance"
- Prevents future re-discussion of same topic

## Getting Help

- **Template unclear?** See existing triaged examples in `triaged/*/`
- **Triage uncertain?** Review `templates/triage-checklist.md` criteria
- **Gemini script issues?** Check `scripts/README.md` (when available)
- **Process feedback?** Open issue or discuss in team sync

---

**Remember:** This process exists to **capture value, not create bureaucracy.** If it feels heavy, simplify. The goal is to avoid losing good ideas from external AI chats, not to slow down development.
