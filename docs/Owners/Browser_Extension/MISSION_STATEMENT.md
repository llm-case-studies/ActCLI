# Browser Extension Owner Mission Statement

## Team Members
- **Codex-BrExt**: Exploration, prototyping, element picker UX design
- **Claude-BrExt**: Validation, testing, policy compliance verification

## Primary Mission
Create a defensible, general-purpose web chat bridge that primarily enables human collaboration in ActCLI seminars while maintaining strict policy compliance and user safety.

## Strategic Positioning
**NOT**: AI chat automation tool (high ToS risk)
**IS**: General-purpose human collaboration bridge with accidental AI compatibility

## Ownership Scope (~25K tokens)
- **Element Picker Engine**: Dev-tools style UI for user-taught selectors
- **Chat Playground**: Local testing environment with multiple input patterns
- **Policy Compliance Framework**: ToS analysis, denylist management, user acknowledgment flows
- **Audit Integration**: Evidence pack logging for extension usage
- **E2E Testing**: Playwright-based automated testing with Docker targets

## Working Protocol

### Codex-BrExt (Exploration + Safety Prototyping)
1. **Research**: Analyze web chat patterns and ToS compliance requirements
2. **Spike**: Create element picker UX prototypes and Chat Playground
3. **Policy Design**: Draft denylist strategies and user acknowledgment flows
4. **Test Foundation**: Write intention tests showing expected behavior patterns
5. **Handoff**: Pass prototypes, findings, and policy framework to Claude

### Claude-BrExt (Validation + Production Readiness)
1. **Review**: Validate Codex's prototypes for technical correctness and policy compliance
2. **Fix Tests**: Run Codex's tests, fix any broken implementations
3. **Enhance Coverage**: Add comprehensive E2E testing with Playwright
4. **Integration**: Ensure compatibility with ActCLI audit/evidence pack system
5. **Document**: Create deployment guides and policy compliance documentation
6. **Deploy**: Validate experimental mode integration with Studio UI

## Success Criteria

### Phase 1: Foundation & Compliance (Weeks 1-2)
- [ ] ToS compliance analysis for major chat providers completed
- [ ] Element picker UX prototype with dev-tools style selection
- [ ] Chat Playground with textarea, contenteditable, and virtualized history
- [ ] Denylist framework with user acknowledgment flows

### Phase 2: Testing & Integration (Weeks 3-4)
- [ ] Playwright E2E tests covering all input patterns
- [ ] Docker-based testing with Rocket.Chat/Zulip
- [ ] Audit trail integration with ActCLI evidence packs
- [ ] Studio UI "Experimental Mode" toggle implementation

### Quality Gates
- **Policy Compliance**: Clear ToS analysis with risk mitigation strategies
- **Test Coverage**: ≥90% coverage on element picker and bridge logic
- **User Safety**: Default denylist with explicit user acknowledgment required
- **Audit Integration**: All extension usage logged to evidence packs

## Communication Contracts

### With Other Owners
- **Backend Owner**: Audit logging APIs and MCP integration points
- **Studio Owner**: Experimental mode UI and risk warning displays
- **Seminar Owner**: Gate-0 integration for participant channel selection
- **Refactoring Owner**: Learn from successful wire protocol and testing patterns

### Decision Authority
- **Element Selection Strategy**: Full authority over picker UX and selector resilience
- **Policy Framework**: Determine denylist criteria and user acknowledgment flows
- **Testing Strategy**: Establish E2E testing patterns for web chat interfaces
- **Risk Management**: Balance functionality vs compliance requirements

## Risk Management
- **ToS Compliance**: Default to deny for known problematic providers
- **User Education**: Clear warnings about third-party ToS responsibility
- **Technical Safeguards**: Human-paced throttling, visible-DOM only, no rate limit bypass
- **Graceful Degradation**: Fallback to manual copy-paste when selectors fail

## Key Principles (Following Refactoring Team Success Pattern)
1. **User-Taught Approach**: Let users select elements rather than hardcoding selectors
2. **General-Purpose Design**: Support any web chat, not just AI providers
3. **Policy-First Development**: Compliance analysis before technical implementation
4. **Experimental Positioning**: Ship as optional/off-by-default feature
5. **Audit Integration**: Full traceability via evidence pack system

## Current Priority Focus

### Immediate Tasks (Week 1)
1. **ToS Research**: Comprehensive analysis per GPT-5 architect recommendations
2. **Element Picker Spike**: Dev-tools style selection prototype
3. **Chat Playground**: Local testing environment for CI/CD
4. **Policy Framework**: Denylist and user acknowledgment system design

### Success Metrics
- **ToS Compliance**: Clear risk assessment for all major providers
- **Technical Robustness**: Selector resilience across layout changes
- **User Safety**: Zero accidental ToS violations via default settings
- **Integration Quality**: Seamless audit trail and evidence pack logging

## Tools and Standards
- **Browser Extension**: Manifest V3 with proper permissions
- **Testing**: Playwright with Docker-based targets
- **Policy Management**: JSON-based denylist with version control
- **Audit Logging**: MCP integration for evidence pack compatibility
- **User Interface**: Shadow DOM for picker overlay, proper ARIA support

The Browser Extension bridges human collaboration while respecting platform policies and maintaining ActCLI's trust-by-design principles.