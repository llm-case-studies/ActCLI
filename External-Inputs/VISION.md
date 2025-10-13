# External Inputs Vision: Multi-Project Knowledge Flow

**Status:** Experimental - Testing Ground
**Date:** 2025-10-07
**Philosophy:** Big picture in mind, step on tested stones only

## The Problem

Web chats with AI (ChatGPT, Claude.ai, Gemini, etc.) generate valuable ideas during brainstorming, but:
- Ideas are scattered across platforms
- Conversations are loosely connected to project work (no file access)
- Good concepts get lost in messy chat logs
- Hard to reuse ideas across projects
- No systematic way to develop raw brainstorms into actionable work

## The Vision (Big Picture)

```
Web Chat Brainstorming
    ↓
Step 1: Extract raw ideas [Gemini] ← TESTED ✅
    ↓
ideas-list.md (conversation-specific)
    ↓
Step 2.1: Analyze & outline research needs [Claude] ← TESTING NOW 🧪
    ↓
Step 2.2: Web research + enrich details [Gemini] ← NEXT
    ↓
idea-details.md (standalone documents)
    ↓
Step 3: Merge similar ideas across chats [Claude/Codex] ← FUTURE
    ↓
Step 4: High-temp brainstorm applicability [Multi-AI Seminar] ← FUTURE
    ↓
Idea Repository (can serve multiple projects)
    ↓
Projects consume ideas as needed
```

## Current Testing: Steps 1 & 2.1

### What Works (Tested ✅)

**Step 1: Extraction (Gemini)**
- ✅ Local role override via `GEMINI.md` works reliably
- ✅ Produces clean ideas-list with line numbers + references
- ✅ Cost-effective (Gemini input/output 10x cheaper than Claude)
- ✅ Good at handling large files (2M token context)

**File:** `/intake/GEMINI.md` defines extraction role

**Output:** `[Source]/[Chat]-ideas-list.md`

**Validated:** DeepSeek/Chat-1-ideas-list.md has perfect references

### What We're Testing Now (🧪)

**Step 2.1: Analysis & Research Planning (Claude)**
- 🧪 Local role override via `CLAUDE.md` (same pattern as Gemini)
- 🧪 Read ideas-list + original chat for full context
- 🧪 Create idea-details.md with research needs outlined
- 🧪 Cost consideration: Claude does reasoning, Gemini does research

**File:** `/intake/CLAUDE.md` defines analysis role (being created)

**Output:** `[Source]/[Chat]-ideas/[idea-name].md` (one file per idea)

**Cost Strategy:**
- Claude: Deep reasoning, outline research questions (expensive but necessary)
- Gemini: Execute research queries, fetch data (cheap, parallel)

## Directory Structure (Keep It Simple During Testing)

```
External-Inputs/intake/
├── GEMINI.md           # Step 1: Extraction config ✅
├── CLAUDE.md           # Step 2.1: Analysis config 🧪
├── VISION.md           # This document
│
├── DeepSeek/
│   ├── Chat-1.md                      # Raw conversation
│   ├── Chat-1-ideas-list.md           # Step 1 output ✅
│   └── Chat-1-ideas/                  # Step 2.1 output 🧪
│       ├── api-pricing-overview.md
│       ├── byok-dilemma.md
│       └── hybrid-auth-model.md
│
├── Claude/
│   ├── Chat-1.md
│   ├── Chat-1-ideas-list.md
│   └── Chat-1-ideas/
│       └── vba-excel-integration.md
│
└── GPT/
    ├── Chat-3.md
    ├── Chat-3-ideas-list.md
    └── Chat-3-ideas/
        ├── two-sprint-poc-plan.md
        └── slash-commands-repl.md
```

**Why this structure:**
- ✅ Simple: One folder per chat's processed ideas
- ✅ Traceable: Easy to see which ideas came from which chat
- ✅ Flat: No deep nesting during testing phase
- ✅ Extensible: Can add tags/metadata later in Step 3

## Idea Document Template (Step 2.1 Output)

Each `[idea-name].md` file contains:

```markdown
# [Idea Title]

**Origin:** [Source]/Chat-N, Line XXX
**Date:** YYYY-MM-DD
**Tags:** #tag1 #tag2 #tag3  ← For Step 3 grouping

## Summary
[2-3 sentences - standalone, no chat context needed]

## Core Concept
[Detailed explanation - what, why, how]

## Technical Approach
[Implementation details mentioned in chat]

## Research Needs (for Step 2.2)
Claude identifies what Gemini should research:

- [ ] **Existing Solutions:** Are there tools that do this already?
      Query: "[specific search terms]"

- [ ] **Recent Developments:** Any 2024-2025 updates in this space?
      Query: "[specific search terms]"

- [ ] **Platform Options:** What platforms/APIs could accomplish this?
      Query: "[specific search terms]"

- [ ] **Cost/Feasibility:** Realistic pricing for implementation?
      Query: "[specific search terms]"

## Potential Applications
- [Domain 1]: [Specific use case]
- [Domain 2]: [Specific use case]

## Open Questions
- [What needs human judgment]
- [Ambiguities from original chat]

## References
- Source: [filename]
- Lines: [line numbers from ideas-list]
- Context: [why this came up in conversation]
```

## Cost Optimization Strategy

### Why Split Step 2 into 2.1 & 2.2?

**Claude (Step 2.1):**
- Cost: ~$3-15 per 1M tokens (input/output)
- Strength: Deep reasoning, context understanding, question formulation
- Task: Read chat, understand nuance, outline research needs
- Time: Minutes (does reasoning work)

**Gemini (Step 2.2):**
- Cost: ~$0.35-1.05 per 1M tokens (10x cheaper!)
- Strength: Large context, web search, parallel processing
- Task: Execute research queries, fetch data, synthesize findings
- Time: Seconds per query (does grunt work)

**Example:**
- Claude reads 10K token chat + reasons → $0.15
- Gemini runs 5 web searches + writes results → $0.05
- **Total:** $0.20 per idea vs $1.50+ if Claude did everything

**At scale (100 ideas):** $20 vs $150+ savings

## Mode Switching (Future Design - Not Tested Yet)

**Idea:** Directory-level role configs that override global instructions

**Caution:** Don't base design on untested assumptions. Current approach:
- ✅ Explicit config files (`GEMINI.md`, `CLAUDE.md`) in `/intake/`
- 🔮 Test if this reliably overrides project-level `CLAUDE.md`
- 🔮 Test if multiple AIs can work in same directory with different roles
- 🔮 If proven, extend pattern to other directories

**Later:** Could explore:
- `.ai-role` files per directory
- `actcli ai-role set <role>` commands
- Automatic role detection

## Step 3: Merge Similar Ideas (Future)

**Not testing yet, but keeping in mind:**

Ideas get tagged during Step 2.1:
```markdown
**Tags:** #vba-integration #excel #legacy-migration #actcli
```

Step 3 script:
```bash
# Find all ideas with #vba-integration
grep -r "Tags:.*#vba-integration" intake/*/ideas/

# Group for human review
# Decide: merge or keep separate?
```

Human reviews groups and decides merge strategy.

## Step 4: Applicability Brainstorming (Future)

**Vision:** Use ActCLI's existing seminar engine for creative exploration

```bash
actcli chat --multi "claude,gpt4o,deepseek" \
  --rounds 2 \
  --temperature 1.2 \
  --prompt "Given this idea: [idea-details.md],
            brainstorm unexpected applications across domains"
```

Models debate creative uses at high temperature.

## Success Metrics (What We'll Track)

### Step 1 (Extraction)
- ✅ Reference accuracy: 9/9 perfect in DeepSeek/Chat-1
- ✅ Completeness: All ideas captured?
- ✅ Processing time: ~2-5 min per chat

### Step 2.1 (Analysis)
- 🧪 Standalone quality: Can read idea-details without original chat?
- 🧪 Research questions: Are they specific enough for Gemini?
- 🧪 Cost per idea: Target <$0.20
- 🧪 Processing time: Target <5 min per idea

### Step 2.2 (Research - Next)
- 🔮 Research quality: Finds relevant info?
- 🔮 Cost: Target <$0.05 per idea
- 🔮 Time: Target <2 min per idea

### Step 3 (Merge - Future)
- 🔮 Duplicate detection: Catches similar ideas?
- 🔮 Synthesis quality: Preserves both perspectives?

## Lessons Learned

### From Step 1 Testing
1. **Local configs work!** `GEMINI.md` successfully overrides global instructions
2. **Role focus matters** - "Just extract, don't judge" works better than complex triage
3. **Line numbers + regex = gold** - Makes ideas traceable without loading huge files
4. **Gemini's 2M context is key** - Can handle 10K line conversations in one go

### From Design Mistakes
1. **Overengineering fails** - Templates, scripts, rigid workflows confused everyone
2. **Quality gates too early** - Judging "relevance" during extraction was wrong phase
3. **Software engineering mindset in wrong place** - `/intake/` is NL processing, not coding
4. **One size doesn't fit all** - Different AIs have different strengths (cost, context, reasoning)

## Next Steps

### Immediate (This Session)
1. ✅ Write VISION.md (this document)
2. 🧪 Create `/intake/CLAUDE.md` for Step 2.1 role
3. 🧪 Test on one ideas-list: DeepSeek/Chat-1-ideas-list.md
4. 🧪 Validate output quality and cost

### Soon (Next Few Sessions)
5. 🔮 If Step 2.1 works, create `/intake/GEMINI-RESEARCH.md` for Step 2.2
6. 🔮 Test full Step 2 (2.1 + 2.2) pipeline
7. 🔮 Process 3-5 chats to validate pattern at scale

### Later (When Patterns Proven)
8. 🔮 Design Step 3 merge strategy
9. 🔮 Integrate Step 4 with ActCLI seminar engine
10. 🔮 Consider multi-project idea repository structure

## Open Questions

1. **Tags vs folders?** For Step 3 grouping, should we use markdown tags or directory structure?
2. **One repo or many?** Should ideas live in ActCLI or separate `~/AI-Knowledge-Base/`?
3. **Automation level?** How much should be scripted vs manual human-in-loop?
4. **Multi-project reuse?** When to promote pattern to other projects?

## Philosophy

> "Big picture in mind, step on tested stones only."

We know where we want to go (multi-project knowledge flow), but we're building the path one validated step at a time. Each stone must hold weight before we step to the next.

---

**Current Stone:** Step 2.1 (Claude analysis & research planning)
**Next Stone:** Step 2.2 (Gemini research execution)
**Horizon:** Steps 3-4 (merge, brainstorm, multi-project)
