# Triage Checklist for External Inputs

Use this checklist when reviewing external AI conversation imports.

## Review Criteria

### 1. Quality Gates (Must Pass All)

- [ ] **Relevance**: Is this directly applicable to ActCLI's mission?
  - Actuarial workflows, multi-model seminars, terminal UI, Excel inspection, MCP integration
  - If discussing unrelated topics → REJECT

- [ ] **Novelty**: Is this something we don't already have?
  - Check existing code, docs, and backlog
  - If already implemented or documented → REJECT or MERGE with existing docs

- [ ] **Feasibility**: Can we implement this with current resources?
  - Consider time, skills, dependencies
  - If requires major architectural changes → Defer to architecture-ideas for discussion

- [ ] **Safety**: Are there security, compliance, or policy risks?
  - No credentials, API keys, or sensitive data exposed
  - Aligns with ActCLI trust/policy model
  - No ToS violations (especially for browser extension features)
  - If safety concerns → REJECT or sanitize

- [ ] **Maintainability**: Will this create technical debt?
  - Code quality standards maintained
  - Adds tests and documentation
  - Fits existing architecture patterns
  - If creates debt → REJECT or refactor proposal

### 2. Categorization

Choose ONE primary category:

- [ ] **code-suggestions**: Ready-to-implement code changes
  - Has specific file/function targets
  - Includes implementation details
  - Can be coded within 1-2 days

- [ ] **architecture-ideas**: Needs design discussion
  - Affects multiple components
  - Requires team alignment
  - May impact existing patterns

- [ ] **docs-improvements**: Documentation updates
  - Clarifications, examples, guides
  - No code changes required
  - Can be written immediately

- [ ] **rejected**: Not applicable or not worth pursuing
  - Document WHY for future reference
  - Prevents re-discussion of same topic

### 3. Priority Assignment (if accepted)

- [ ] **P0 - Critical**: Blocking issue, security fix, or major bug
  - Implement within 24-48 hours
  - Halt other work if needed

- [ ] **P1 - High**: Important feature or significant improvement
  - Implement within current sprint (1-2 weeks)
  - Schedule dedicated time

- [ ] **P2 - Medium**: Nice-to-have improvement
  - Add to backlog for next sprint
  - Implement when bandwidth available

- [ ] **P3 - Low**: Future consideration
  - Document and revisit quarterly
  - May never implement

### 4. Ownership Assignment

- [ ] **Assign to area owner**:
  - Core Platform (@alex) - backend, CLI, seminar, MCP
  - Browser Extension (@Codex-BrExt, @Claude-BrExt)
  - Refactoring (mission complete, but patterns applicable)
  - Studio (when active)

- [ ] **Cross-cutting concerns**:
  - Testing/CI
  - Documentation
  - Security/Compliance

### 5. Action Items

- [ ] **Create GitHub issue** (if code-suggestions or architecture-ideas)
  - Link to external input file
  - Include implementation checklist
  - Tag with appropriate labels

- [ ] **Update backlog** (if docs-improvements)
  - Add to relevant docs TODO section

- [ ] **Document rejection rationale** (if rejected)
  - Prevents future re-discussion
  - Explain why not applicable

- [ ] **Sanitize content** before committing to triaged/
  - Remove any API keys, credentials, personal info
  - Generalize examples if needed

## Triage Decision Template

After completing checklist, fill this in:

```markdown
## Triage Decision

**Reviewer:** @username
**Date:** YYYY-MM-DD
**Category:** [code-suggestions|architecture-ideas|docs-improvements|rejected]
**Priority:** [P0|P1|P2|P3]
**Owner:** @assigned-owner
**GitHub Issue:** #XXX (if created)

**Rationale:**
[1-2 sentences explaining the decision]

**Next Steps:**
- [ ] Specific action 1
- [ ] Specific action 2
```

## Common Rejection Reasons (for reference)

Use these as templates for rejected items:

- **Out of Scope**: "This addresses [X] but ActCLI focuses on actuarial workflows, not general [Y]."
- **Already Implemented**: "This functionality exists in [file:line]. See [link to code]."
- **Over-Engineered**: "The proposed solution adds complexity without sufficient benefit. Our current [simpler approach] is adequate."
- **Dependency Risk**: "This requires [new dependency] which conflicts with our offline-first philosophy."
- **Security Concern**: "This approach violates our trust model by [specific issue]."
- **ToS Violation**: "This would violate [provider] Terms of Service, conflicts with browser extension compliance strategy."
- **Maintenance Burden**: "This adds [X] lines of code but only serves [narrow use case]. Not worth the maintenance cost."

## Tips for Effective Triage

1. **Triage within 48 hours** of intake to maintain momentum
2. **Be generous with architecture-ideas** - better to discuss than reject prematurely
3. **Be strict with code-suggestions** - only accept if truly ready to implement
4. **Always document rejection rationale** - saves time later
5. **Look for patterns** - multiple similar suggestions may indicate real need
6. **Consult area owners** if uncertain about fit
