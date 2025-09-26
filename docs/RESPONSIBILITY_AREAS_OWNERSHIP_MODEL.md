# ActCLI Responsibility Areas: Ownership Model for Scalable Development

**Document Type**: Strategic Whitepaper
**Status**: Proposal for Implementation
**Date**: September 2025
**Target**: Hybrid Team Scaling Strategy

## Executive Summary

As ActCLI evolves from a 200K-token prototype into a production-ready actuarial toolkit, traditional monolithic development becomes untenable. This proposal introduces a **Responsibility Areas Ownership Model** that partitions the codebase into domain-specific zones, each owned by a dedicated specialist. This approach enables parallel development, reduces context switching, and maintains code quality while preparing for both human team growth and AI-assisted development at scale.

**Key Insight**: Context window limitations aren't just an AI problem—they mirror human cognitive load constraints. By designing ownership boundaries that fit within manageable complexity budgets (25K-57K tokens), we create sustainable development patterns for both human developers and AI assistants.

## The Scalability Challenge

### Current State Analysis
- **Total Codebase**: ~200K tokens across 739 relevant files
- **Architecture Complexity**: 8 critical technical debt issues blocking production
- **Development Bottleneck**: Single-owner model creates merge conflicts and knowledge silos
- **AI Integration**: Full context loading impossible, requires strategic partitioning

### Growth Trajectory Problems
Without ownership restructuring:
1. **Merge Hell**: Multiple developers touching overlapping components
2. **Knowledge Debt**: Domain expertise scattered across entire codebase
3. **AI Inefficiency**: Context thrashing when assistants switch between unrelated areas
4. **Technical Debt Accumulation**: No clear accountability for maintenance priorities

## Responsibility Areas Architecture

### Area Definitions and Token Budgets

| Area | Owner Focus | Token Budget | Key Components |
|------|-------------|--------------|----------------|
| **Refactoring Owner** | Technical debt elimination | ~60K | Wire protocols, schemas, error handling |
| **Seminar Orchestration** | Multi-model coordination | ~57K | Coordinator, synthesizer, adapters |
| **Backend & API** | Infrastructure services | ~52K | FastAPI core, auth, persistence |
| **CLI Owner** | Terminal interface | ~48K | Commands, UI layouts, auth integration |
| **Studio Owner** | Web interface | ~42K | React SPA, router APIs, real-time streaming |
| **Excel Inspection** | Static analysis tools | ~45K | oletools, security scanning, evidence |
| **MCP Runtime** | Tool orchestration | ~35K | JSON-RPC, job management, transport |
| **Evidence Pack** | Audit trail generation | ~30K | SHA-256 verification, artifact compression |
| **Browser Extension** | Web AI integration | ~25K | Extension manifest, proxy services |

**Total Distributed**: ~394K tokens across specialized domains
**Overlap Buffer**: ~20% for cross-cutting concerns and integration

### The "Refactoring Owner": First Responder

**Why This Role Gets Dirty First**: The Refactoring Owner tackles the 8 critical technical debt issues that block all other development. This isn't glamorous greenfield work—it's surgical repair of brittle foundations.

**Primary Mission**: Transform untyped, ad-hoc code into typed, testable, maintainable systems.

#### Immediate Scope (~60K tokens)
```python
# CRITICAL: Untyped Wire Protocols
# Before: Ad-hoc dictionaries everywhere
message = {"type": "round_start", "data": {...}}  # No validation!

# After: Pydantic v2 schemas with golden tests
@dataclass
class RoundStartMessage:
    type: Literal["round_start"] = "round_start"
    session_id: UUID
    prompt: str
    participants: List[ParticipantConfig]
```

**Refactoring Priority Matrix**:

1. **TIER 0 (Production Blockers)**:
   - Untyped wire protocols → Pydantic v2 models
   - Brittle reconnection logic → Exponential backoff with jitter
   - No job persistence → SQLite job state management

2. **TIER 1 (Developer Experience)**:
   - Inconsistent error handling → Structured exception hierarchy
   - Missing comprehensive logging → Structured logging with correlation IDs
   - Ad-hoc configuration → Centralized settings with validation

3. **TIER 2 (Maintenance)**:
   - Duplicate code patterns → Shared utilities and mixins
   - Missing integration tests → API contract validation
   - Undocumented APIs → OpenAPI spec generation

#### Communication Protocols

**With All Owners**: Refactoring Owner provides migration guides and compatibility layers
```python
# Migration contract example
@deprecated("Use TypedMessage instead", version="0.4.0")
def legacy_message_handler(raw_dict: dict) -> None:
    typed_msg = migrate_to_typed(raw_dict)
    new_message_handler(typed_msg)
```

**Cross-Area Impact**: Refactoring changes affect everyone, requiring:
- **Schema Evolution**: Backward-compatible versioning
- **Migration Windows**: Coordinated deployment sequences
- **Testing Contracts**: Golden JSON test fixtures for wire format validation

## Ownership Model Benefits

### 1. Parallel Development
- **No Merge Conflicts**: Clear boundaries prevent overlapping changes
- **Independent Release Cycles**: Areas can ship improvements without blocking others
- **Specialized Expertise**: Deep domain knowledge within manageable scope

### 2. AI-Assisted Development
- **Context Efficiency**: Each area fits within AI context windows
- **Domain Continuity**: AI assistants maintain context within ownership boundaries
- **Quality Consistency**: Area-specific prompts and conventions

### 3. Technical Debt Management
- **Accountability**: Clear ownership of maintenance responsibilities
- **Prioritization**: Area owners balance feature development vs debt reduction
- **Cross-Cutting Concerns**: Backend owner coordinates shared infrastructure

### 4. Knowledge Transfer
- **Documentation Scope**: Manageable area-specific docs vs overwhelming monolith
- **Onboarding**: New developers can master one area before expanding
- **Bus Factor**: Multiple people can understand any given area

## Communication Contracts

### Inter-Area Protocols

**HTTP/REST APIs**: Standard contracts for synchronous operations
```python
# Studio -> Seminar Orchestration
POST /sessions/{id}/round/start
{
  "prompt": "Evaluate IFRS 17 transition costs",
  "participants": [{"alias": "llama", "model_id": "codellama:13b"}]
}
```

**WebSocket Streaming**: Real-time event propagation
```javascript
// Studio receives orchestration progress
ws://localhost:7530/sessions/{id}/stream
{"event": "participant_response", "participant": "llama", "content": "..."}
```

**MCP JSON-RPC**: Tool coordination layer
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {"name": "excel_inspect", "arguments": {"path": "/mnt/ro/file.xlsx"}}
}
```

### Shared Infrastructure (Backend Owner)
- **Authentication**: JWT tokens, OAuth flows
- **Database**: Session persistence, audit logs
- **Configuration**: Environment variables, feature flags
- **Monitoring**: Health checks, metrics collection

## Implementation Strategy

### Phase 1: Foundation (Refactoring Owner Priority)
**Timeline**: 2-3 weeks
**Blocking Dependencies**: All other areas wait for stable foundations

1. **Wire Protocol Migration**: Pydantic v2 schemas with backward compatibility
2. **Error Handling Unification**: Structured exceptions with proper HTTP status mapping
3. **Job Persistence Layer**: SQLite-based state management with recovery
4. **Logging Infrastructure**: Structured logs with correlation IDs

**Success Criteria**: All existing tests pass, no breaking API changes

### Phase 2: Parallel Area Development
**Timeline**: 4-6 weeks concurrent
**Dependencies**: Foundation complete, communication contracts defined

**Seminar Orchestration**: Gate-0 triage, Delphi-Lite protocols
**Studio Owner**: Real-time UI improvements, command palette enhancements
**Excel Inspection**: Advanced security scanning, macro analysis
**MCP Runtime**: Tool chaining, conditional execution

### Phase 3: Integration & Polish
**Timeline**: 2-3 weeks
**Dependencies**: All areas feature-complete

**Evidence Pack Owner**: End-to-end audit trail validation
**Browser Extension**: Web AI integration pilot
**CLI Owner**: Terminal UI polish, keyboard shortcuts

## Risk Mitigation

### Technical Risks
**Schema Evolution**: Backward-compatible versioning with migration testing
**Integration Failures**: Contract testing with golden fixtures
**Performance Regression**: Area-specific benchmarking and monitoring

### Organizational Risks
**Knowledge Silos**: Cross-area code reviews and documentation requirements
**Communication Overhead**: Standardized RFC process for breaking changes
**Scope Creep**: Token budget enforcement with quarterly rebalancing

## Success Metrics

### Development Velocity
- **Merge Conflict Rate**: Target <5% (currently ~25%)
- **Time to Deploy**: Target <2 hours for area-specific changes
- **Bug Resolution**: Area-specific SLA with clear escalation paths

### Code Quality
- **Test Coverage**: 80% minimum per area with integration contract tests
- **Technical Debt**: Measured via static analysis, trending downward
- **Documentation Currency**: API specs auto-generated from typed schemas

### Developer Experience
- **Context Switching**: Developers stay within area boundaries 80% of time
- **Onboarding Time**: New contributors productive within area in 1 week
- **AI Assistant Efficiency**: Context utilization >70% (vs current ~30%)

## Conclusion

The Responsibility Areas Ownership Model transforms ActCLI from a monolithic prototype into a scalable, maintainable production system. By aligning ownership boundaries with both human cognitive limits and AI context windows, we create sustainable development patterns that will serve the project through its next phase of growth.

**The Refactoring Owner role is critical**: This person tackles unglamorous but essential foundation work that enables all other development. Without solid typed schemas, error handling, and job persistence, other areas will build on quicksand.

**Recommendation**: Implement immediately, starting with Refactoring Owner assignment and foundation migration. The technical debt will only compound with continued development on brittle foundations.

**Next Steps**:
1. Assign Refactoring Owner (volunteer or rotation basis)
2. Create area-specific GitHub labels and CODEOWNERS file
3. Begin wire protocol migration with backward compatibility
4. Establish weekly cross-area sync meetings
5. Document communication contracts in OpenAPI specs

The future of ActCLI development is distributed, specialized, and sustainable. Let's build it right.