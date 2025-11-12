# External Inputs Quick Start

**5-minute setup for capturing AI conversation insights**

## 1. First Time Setup

```bash
# Install dependencies
pip install google-generativeai rich

# Set Gemini API key (get from https://aistudio.google.com/app/apikey)
export GOOGLE_API_KEY='your-key-here'

# Add to ~/.bashrc or ~/.zshrc for persistence:
echo 'export GOOGLE_API_KEY="your-key-here"' >> ~/.bashrc
```

## 2. Capture a Conversation

When you have a valuable ChatGPT/Claude/Gemini conversation:

```bash
# Copy the template
cp External-Inputs/templates/intake-template.md \
   External-Inputs/intake/2025-10-07-anthropic-caching.md

# Fill in the template with:
# - Source (ChatGPT, Claude.ai, etc.)
# - Context (what problem you were solving)
# - Key insights (bulleted list)
# - Paste the full conversation at the bottom
```

**Tip:** Use your AI platform's "Share" feature if available, or just copy-paste the whole conversation.

## 3. Run Gemini Triage

```bash
# Triage a single file
python scripts/triage_external.py intake/2025-10-07-anthropic-caching.md

# Or triage all pending intakes
python scripts/triage_external.py --all
```

**What happens:**
1. Gemini reads the full conversation (2M token context!)
2. Applies quality gates: Relevance, Novelty, Feasibility, Safety, Maintainability
3. Suggests category: code-suggestions | architecture-ideas | docs-improvements | rejected
4. Recommends priority (P0-P3) and owner
5. Flags any risks or concerns

**You review and approve/modify the recommendation.**

## 4. Act on Triaged Items

### If Code Suggestion (Ready to Implement)

```bash
# Script offers to create GitHub issue - say yes
# Then implement:
git checkout -b feat/anthropic-caching
# ... make changes ...
git commit -m "feat(seminar): add Anthropic prompt caching (#45)"
git push

# After merge, track it:
echo "- 001-anthropic-caching → src/actcli/seminar/adapters/anthropic.py (2025-10-07) [PR #45]" \
  >> External-Inputs/incorporated/CHANGELOG.md
```

### If Architecture Idea (Needs Discussion)

- Add to next team sync agenda
- Discuss pros/cons
- Either implement, defer to backlog, or reject with rationale

### If Docs Improvement (Low Friction)

- Just do it immediately (no issue needed)
- Update the relevant `docs/*.md` file

### If Rejected

- Rationale is already documented in `triaged/rejected/`
- Serves as institutional memory
- Prevents re-discussing same topic later

## 5. Check Stats

```bash
# See what's in the pipeline
ls External-Inputs/intake/        # Pending triage
ls External-Inputs/triaged/*/     # Categorized
cat External-Inputs/incorporated/CHANGELOG.md  # Merged

# Future: python scripts/external_stats.py
```

## Common Workflows

### Workflow 1: Quick Code Fix from ChatGPT

```bash
# You ask ChatGPT: "How to implement Anthropic caching?"
# ChatGPT gives you code snippet

# Capture:
cp templates/intake-template.md intake/2025-10-07-anthropic-caching.md
# Fill in template, paste conversation

# Triage:
python scripts/triage_external.py intake/2025-10-07-anthropic-caching.md
# Gemini says: "code-suggestions, P1, @alex"
# You approve

# Implement:
# File moved to triaged/code-suggestions/001-anthropic-caching.md
# GitHub issue created: #45
# You code it, PR merged

# Track:
# Update incorporated/CHANGELOG.md
```

**Time:** 10 minutes from conversation to tracked issue

### Workflow 2: Big Architecture Discussion with Claude.ai

```bash
# Long Claude.ai session about Gate-0 design
# Multiple rounds, lots of ideas

# Capture:
# Use template, paste full conversation (Claude has 2M context)

# Triage:
python scripts/triage_external.py intake/2025-10-07-gate0-design.md
# Gemini says: "architecture-ideas, P2, needs discussion"
# You approve

# Discuss:
# File in triaged/architecture-ideas/
# Bring to team sync
# Decide: implement in Sprint 5

# Track:
# Stays in architecture-ideas until implemented
# Then move to incorporated/CHANGELOG.md
```

**Time:** 5 minutes to triage, discuss when ready

### Workflow 3: Interesting but Not Applicable

```bash
# Gemini conversation about blockchain for audit trails

# Triage:
python scripts/triage_external.py intake/2025-10-07-blockchain-idea.md
# Gemini says: "rejected, over-engineered"
# You agree

# Document:
# File moved to triaged/rejected/001-blockchain-audit-trail.md
# Rationale captured: "SHA-256 + git history sufficient"

# Benefit:
# Next time someone suggests blockchain, you point to this
# Saves re-discussion time
```

**Time:** 3 minutes, prevents future time waste

## Tips

### Capturing Conversations

✅ **Do:**
- Export immediately after valuable conversation
- Include full context, not just snippets
- Note what problem triggered the conversation

❌ **Don't:**
- Include API keys or credentials (gets redacted anyway)
- Wait days to export (you'll forget context)
- Only grab the "good parts" (Gemini needs full conversation)

### Reviewing Gemini's Analysis

✅ **Do:**
- Read Gemini's reasoning carefully
- Modify priority/category if you disagree
- Check the risks/concerns section
- Verify novelty (not already implemented)

❌ **Don't:**
- Blindly auto-approve without review
- Skip the quality gates assessment
- Forget to sanitize sensitive data

### Incorporating Ideas

✅ **Do:**
- Test code snippets before merging
- Update incorporated/CHANGELOG.md
- Reference external input in commit messages
- Add proper tests and documentation

❌ **Don't:**
- Copy-paste without understanding
- Skip backward compatibility checks
- Forget to close GitHub issue after merge

## Troubleshooting

**"GOOGLE_API_KEY not set"**
```bash
export GOOGLE_API_KEY='your-key-here'
# Get key from: https://aistudio.google.com/app/apikey
```

**"Missing dependencies"**
```bash
pip install google-generativeai rich
```

**"Gemini says rejected but I disagree"**
- You have final say!
- Modify the category/priority manually
- Move file to appropriate triaged/ subfolder
- Fill in "Triage Notes" section yourself

**"Conversation too long even for Gemini"**
- Rare (2M token context is huge)
- Split into multiple intake files by topic
- Or manually extract key insights

**"Want to re-triage a file"**
```bash
# Move back to intake/
mv triaged/*/NNN-topic.md intake/
# Re-run triage
python scripts/triage_external.py intake/NNN-topic.md
```

## Next Steps

1. **Try it once** - Capture one conversation and triage it
2. **Build the habit** - Do it weekly (Friday afternoon ritual?)
3. **Track metrics** - Monitor incorporation rate monthly
4. **Refine process** - Adjust categories/priorities as needed

---

**Questions?** See `External-Inputs/README.md` for full documentation.
