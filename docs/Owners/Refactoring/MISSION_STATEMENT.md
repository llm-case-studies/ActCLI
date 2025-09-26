# Refactoring Owner Mission Statement

## Team Members
- **Codex-Refactoring**: Code spiking, exploration, prototyping
- **Claude-Refactoring**: Validation, testing, documentation

## Primary Mission
Transform ActCLI from prototype-quality code into production-ready, maintainable system by eliminating the 8 critical technical debt issues that block all other development.

## Ownership Scope (~60K tokens)
- **Wire Protocols**: Convert ad-hoc dictionaries to typed Pydantic v2 schemas
- **Error Handling**: Implement structured exception hierarchy with proper HTTP mapping
- **Job Persistence**: SQLite-based state management with recovery mechanisms
- **Reconnection Logic**: Exponential backoff with jitter, graceful degradation
- **Logging Infrastructure**: Structured logging with correlation IDs
- **Configuration Management**: Centralized settings with validation
- **Integration Contracts**: Golden test fixtures for API compatibility

## Working Protocol

### Codex-Refactoring (Exploration + Safety Nets)
1. **Spike**: Identify specific technical debt patterns
2. **Prototype**: Create minimal viable solutions with intention tests
3. **Document**: Capture approach, trade-offs, and edge cases
4. **Test**: Write basic unit tests showing expected behavior
5. **Handoff**: Pass code, intention tests, and findings to Claude

### Claude-Refactoring (Validation + Comprehensive Testing)
1. **Review**: Analyze Codex's prototypes for correctness
2. **Fix Tests**: Run Codex's tests, fix any broken ones
3. **Enhance Coverage**: Add missing test cases and edge conditions
4. **Integration**: Create tests that verify compatibility with other components
5. **Document**: Create migration guides and API docs
6. **Deploy**: Ensure backward compatibility with full test suite

## Success Criteria

### Phase 1: Foundation (Weeks 1-3) ✅ COMPLETED
- [x] All wire protocols use typed Pydantic v2 models
- [x] Structured error handling with proper HTTP status codes
- [x] SQLite job persistence with recovery testing
- [x] 100% backward compatibility - no breaking changes

### Phase 2: Infrastructure (Weeks 4-6) ✅ COMPLETED
- [x] Structured logging with correlation IDs
- [x] Centralized configuration with validation
- [x] Integration test suite with golden fixtures
- [x] Performance benchmarks established

### Quality Gates
- **Test Coverage**: ≥85% for all refactored code
- **Backward Compatibility**: All existing tests pass
- **Performance**: No regression in response times
- **Documentation**: Migration guides for all breaking changes

## Communication Contracts

### With Other Owners
- **Weekly Sync**: Status updates on foundation work
- **Migration Notices**: 48-hour advance notice of schema changes
- **Testing Support**: Provide compatibility layer during transitions
- **Documentation**: Clear upgrade paths and examples

### Decision Authority
- **Schema Design**: Full authority over wire format evolution
- **Error Handling**: Standardize exception patterns across all areas
- **Job Management**: Define persistence and recovery patterns
- **Testing Strategy**: Establish integration test requirements

## Risk Management
- **Breaking Changes**: Always provide compatibility shims
- **Performance**: Benchmark before/after all major refactors
- **Dependencies**: Coordinate timing with other area owners
- **Rollback**: Maintain ability to revert any change quickly

## Current Technical Debt Priority

### TIER 0 (Production Blockers) ✅ COMPLETED
1. ✅ **Untyped Wire Protocols** → Pydantic v2 models with validation
2. ✅ **Brittle Reconnection Logic** → Exponential backoff with circuit breaker
3. ✅ **No Job Persistence** → SQLite state management with WAL mode
4. ✅ **Inconsistent Error Handling** → Structured exceptions with HTTP mapping

### TIER 1 (Developer Experience) ✅ COMPLETED
5. ✅ **Missing Comprehensive Logging** → Structured logs with trace correlation
6. ✅ **Ad-hoc Configuration** → Centralized settings with environment validation
7. 🔄 **Duplicate Code Patterns** → Shared utilities and mixins (Next Sprint)
8. ✅ **Missing Integration Tests** → Contract validation with golden fixtures

## Tools and Standards
- **Type Checking**: mypy strict mode
- **Code Formatting**: ruff format
- **Testing**: pytest with coverage reporting
- **Schema Validation**: Pydantic v2 with JSON Schema export
- **Database**: SQLite with proper migrations
- **Logging**: structlog with JSON output

## Success Metrics
- **Merge Conflicts**: Reduce from 25% to <5%
- **Bug Reproduction**: 100% of issues reproducible with typed schemas
- **Developer Onboarding**: New contributors productive in 1 week
- **AI Context Efficiency**: 70%+ relevant token utilization

The foundation you build enables everyone else's success. This is unglamorous but essential work.