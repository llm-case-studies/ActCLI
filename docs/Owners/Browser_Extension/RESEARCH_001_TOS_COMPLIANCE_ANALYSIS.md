# Research Assignment 001: AI Provider ToS Compliance Analysis

**Assignment Date**: September 25, 2025
**Research Team**: Grok, Gemini, DeepSeek
**Priority**: BLOCKING - Must resolve before Browser Extension development
**Timeline**: 1-2 weeks

## Research Objective

Analyze major web-chat AI provider Terms of Service to determine if ActCLI's proposed browser extension integration pattern violates any usage restrictions, and identify compliant implementation approaches.

## Use Case Specification

**ActCLI Browser Extension Pattern**:
1. **Personal Browser Usage**: User installs extension on their own machine, own browser
2. **Own Subscription**: User leveraging their personal paid subscription (Plus/Pro/Premium)
3. **Rate Limit Respect**: If provider rate limits, user simply waits (like in CLI with API timeouts)
4. **Manual Alternative**: Extension replaces tedious copy-paste workflow, not server automation
5. **Single User, Single Session**: One person using one ActCLI seminar at a time

**Key Distinction - Personal vs Server Usage**:
- ❌ **NOT**: Automated server making thousands of requests
- ❌ **NOT**: Bypassing quotas or rate limits
- ❌ **NOT**: Commercial service reselling AI responses
- ✅ **IS**: Personal productivity tool on user's own browser
- ✅ **IS**: User waits for rate limits like any other personal usage
- ✅ **IS**: Replacing manual copy-paste with seamless integration

**Technical Reality**:
- Extension runs in user's browser (client-side, not server automation)
- Uses existing authenticated session (no credential sharing)
- Respects all rate limits (user waits, just like CLI API timeouts)
- One query at a time, human-paced usage patterns

## Research Targets

### Primary Providers (Must Analyze)
1. **OpenAI ChatGPT** (ChatGPT Plus, Team, Enterprise)
2. **Anthropic Claude** (Claude Pro, Team, Enterprise)
3. **Google Gemini** (Gemini Advanced, Business)
4. **X.AI Grok** (Premium, Premium+ subscriptions)
5. **Meta AI** (WhatsApp, Instagram, web interface)

### Secondary Providers (If Available)
6. **DeepSeek Chat** (Pro subscriptions)
7. **Perplexity AI** (Pro, Enterprise)
8. **Character.AI** (Plus subscriptions)

## Research Framework

### A. Terms of Service Analysis
**Refined Research Questions**:
1. **Personal Browser Tools**: Do ToS distinguish between server automation vs personal browser extensions?
2. **Own Subscription Usage**: Does using your own paid subscription in your own browser violate terms?
3. **Rate Limit Philosophy**: If providers impose rate limits, is waiting for them (like CLI APIs) compliant?
4. **Copy-Paste Alternative**: Is programmatic extraction worse than manual copy-paste of the same content?
5. **Professional Personal Use**: Can actuaries use personal subscriptions for professional analysis?
6. **Browser Extension Precedent**: Are there existing browser extensions that integrate with these providers?

### B. Compliance Risk Assessment
**Risk Categories**:
- 🟥 **HIGH RISK**: Clear ToS violation, account termination likely
- 🟨 **MEDIUM RISK**: Gray area, might trigger review or warnings
- 🟩 **LOW RISK**: Likely compliant, within intended personal use

### C. Mitigation Strategies
**For each provider, identify**:
- **Compliant Patterns**: How to structure usage to avoid violations
- **Official Alternatives**: API access, partnership programs, business accounts
- **Technical Safeguards**: Rate limiting, usage tracking, compliance monitoring

## Research Assignments

### Grok (Lead: OpenAI & Anthropic Analysis)
**Focus**: ChatGPT and Claude ToS deep-dive
1. Analyze ChatGPT Plus/Team ToS sections on automation and commercial use
2. Review Anthropic Claude Pro/Team policies on browser integration
3. Research precedents of browser extension integration for both providers
4. **Deliverable**: `TOS_Analysis_OpenAI_Anthropic.md` with risk assessment

### Gemini (Lead: Google & X.AI Analysis)
**Focus**: Google Gemini and X.AI Grok ToS analysis
1. Examine Google AI/Gemini Advanced terms regarding automation
2. Analyze X.AI Grok Premium ToS for integration restrictions
3. Review Google's broader API policies that might apply
4. **Deliverable**: `TOS_Analysis_Google_XAI.md` with compliance recommendations

### DeepSeek (Lead: Secondary Providers & Synthesis)
**Focus**: Remaining providers and pattern synthesis
1. Research Meta AI, DeepSeek, Perplexity, Character.AI policies
2. Identify common patterns across provider ToS
3. Create compliance framework applicable to all providers
4. **Deliverable**: `TOS_Compliance_Framework.md` with unified recommendations

## Expected Findings & Decision Tree

### Scenario 1: Broadly Compliant
**If most providers allow personal subscription automation**:
- ✅ Proceed with browser extension development
- Implement usage tracking and rate limiting safeguards
- Create provider-specific compliance modes

### Scenario 2: Mixed Compliance
**If some providers prohibit, others allow**:
- 🟨 Implement selective provider support
- Focus on compliant providers first
- Negotiate business partnerships for restricted providers

### Scenario 3: Broadly Prohibited
**If most providers prohibit web interface automation**:
- 🟥 Pivot to official API integrations only
- Explore business account alternatives
- Consider partnership/whitelisting requests

## Compliance Architecture Recommendations

### Technical Safeguards (Regardless of Findings)
```javascript
// Example compliance patterns
const ComplianceManager = {
  rateLimiting: {
    maxQueriesPerHour: 50,      // Well below typical quotas
    cooldownBetweenQueries: 5000, // 5 second minimum delay
  },
  usageTracking: {
    dailyUsageReports: true,
    quotaWarnings: true,
    automaticCutoffs: true,
  },
  userConsent: {
    explicitOptIn: true,
    tosAcceptance: true,
    riskDisclosures: true,
  }
}
```

### Legal Safeguards
- **Clear User Disclaimers**: Users acknowledge ToS compliance responsibility
- **Usage Guidelines**: Best practices for staying within provider limits
- **Account Protection**: Features to avoid triggering automated detection

## Success Criteria

1. **Complete Analysis**: All primary providers researched thoroughly
2. **Clear Risk Assessment**: Each provider categorized (High/Medium/Low risk)
3. **Actionable Recommendations**: Specific implementation guidance for compliant integration
4. **Decision Framework**: Go/No-Go recommendations with supporting evidence
5. **Fallback Plans**: Alternative approaches if direct integration is prohibited

## Timeline & Deliverables

**Week 1: Research Phase**
- Grok: OpenAI & Anthropic ToS analysis
- Gemini: Google & X.AI ToS analysis
- DeepSeek: Secondary providers research

**Week 2: Synthesis Phase**
- DeepSeek: Compliance framework creation
- All: Cross-validation of findings
- Final recommendation report

## Risk Mitigation

**If ToS Violations Identified**:
1. **Official API Pivot**: Transition to sanctioned integration methods
2. **Business Account Upgrade**: Move to enterprise tiers with broader permissions
3. **Partnership Outreach**: Formal collaboration discussions with providers
4. **Feature Scoping**: Reduce integration scope to compliant use cases only

This research will determine the viability and implementation approach for the Browser Extension responsibility area. **No development should proceed until compliance is established.**