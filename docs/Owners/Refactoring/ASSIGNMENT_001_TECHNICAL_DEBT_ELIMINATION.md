# Assignment 001: Critical Technical Debt Elimination

**Assignment Date**: September 25, 2025
**Team**: Codex-Refactoring (exploration) + Claude-Refactoring (validation)
**Priority**: TIER 0 - Production Blockers
**Estimated Effort**: 2-3 weeks

## Overview
This is the first concrete assignment for the Refactoring Owner team. These 8 technical debt issues are blocking all other development and must be resolved before other areas can build stable features.

## TIER 0: Production Blockers (Must Complete First)

### 1. Untyped Wire Protocols & Schema Drift
**Current Problem**: MCP messages, SSE events, job artifacts use ad-hoc dictionaries
```python
# BAD - Current state
message = {"type": "round_start", "data": {...}}  # No validation!
sse_event = {"event": "participant_response", "content": "..."}  # Anything goes!
```

**Required Fix**: Promote all wire formats to typed Pydantic v2 models with golden JSON tests
```python
# GOOD - Target state
@dataclass
class RoundStartMessage:
    type: Literal["round_start"] = "round_start"
    session_id: UUID
    prompt: str
    participants: List[ParticipantConfig]

@dataclass
class SSEParticipantResponse:
    event: Literal["participant_response"] = "participant_response"
    participant_id: str
    content: str
    timestamp: datetime
```

**Files to Examine**:
- `src/semhost/routers/sessions.py` - Session management messages
- `src/semhost/routers/ws.py` - WebSocket event formats
- `src/semhost/routers/mcp.py` - MCP JSON-RPC structures

**Deliverables**:
- [ ] `src/semhost/schemas/` directory with Pydantic v2 models
- [ ] Backward compatibility layer for existing clients
- [ ] Golden JSON test fixtures in `tests/fixtures/`
- [ ] Migration guide for other area owners

### 2. Brittle Reconnection Logic
**Current Problem**: WebSocket reconnection uses naive retry without backoff
```python
# BAD - Current reconnection in Studio
ws.onclose = () => {
    setTimeout(() => connectWS(sid), 1000) // Fixed 1s delay!
}
```

**Required Fix**: Exponential backoff with jitter and circuit breaker
```python
# GOOD - Target reconnection pattern
class ReconnectionManager:
    def __init__(self, max_delay: int = 30000):
        self.delay = 1000
        self.max_delay = max_delay
        self.attempts = 0

    def next_delay(self) -> int:
        jitter = random.uniform(0.1, 0.3)
        delay = min(self.delay * (2 ** self.attempts), self.max_delay)
        return int(delay * (1 + jitter))
```

**Files to Examine**:
- `studio/src/pages/Seminar.tsx` - WebSocket client reconnection
- `src/semhost/routers/ws.py` - Server-side connection management

**Deliverables**:
- [ ] `src/semhost/utils/reconnection.py` - Backoff logic
- [ ] Updated WebSocket client in Studio
- [ ] Connection health monitoring
- [ ] Circuit breaker for unhealthy endpoints

### 3. No Job Persistence & Recovery
**Current Problem**: MCP jobs exist only in memory, lost on restart
```python
# BAD - Current job tracking
running_jobs = {}  # Lost on server restart!
```

**Required Fix**: SQLite job state management with recovery
```python
# GOOD - Target job persistence
@dataclass
class JobRecord:
    id: UUID
    tool_name: str
    params: dict
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_msg: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
```

**Files to Examine**:
- `src/semhost/routers/mcp.py` - Job execution logic
- `src/semhost/mcp/` - MCP runtime state

**Deliverables**:
- [ ] `src/semhost/db/` directory with SQLite schema
- [ ] Job recovery logic for server restart
- [ ] Job cleanup policies (retention, archival)
- [ ] Migration from in-memory to persistent storage

### 4. Inconsistent Error Handling
**Current Problem**: Mix of generic exceptions, HTTP errors, MCP errors
```python
# BAD - Current error handling
try:
    result = tool.execute()
except Exception as e:
    return {"error": str(e)}  # Lost context!
```

**Required Fix**: Structured exception hierarchy with proper HTTP mapping
```python
# GOOD - Target error handling
class ActCLIException(Exception):
    status_code: int = 500
    error_code: str
    context: dict = field(default_factory=dict)

class MCPToolExecutionError(ActCLIException):
    status_code = 422
    error_code = "MCP_TOOL_EXECUTION_FAILED"
```

**Files to Examine**:
- All router files in `src/semhost/routers/`
- `src/semhost/mcp/` - MCP-specific errors

**Deliverables**:
- [ ] `src/semhost/exceptions.py` - Structured exception hierarchy
- [ ] Error middleware for consistent HTTP responses
- [ ] Error correlation IDs for debugging
- [ ] Client-friendly error messages

## TIER 1: Developer Experience (Complete After TIER 0)

### 5. Missing Comprehensive Logging
**Current Problem**: Print statements and inconsistent logging
**Required Fix**: Structured logging with correlation IDs

### 6. Ad-hoc Configuration Management
**Current Problem**: Environment variables scattered everywhere
**Required Fix**: Centralized settings with validation

### 7. Duplicate Code Patterns
**Current Problem**: Copy-paste utilities across modules
**Required Fix**: Shared utilities and mixins

### 8. Missing Integration Tests
**Current Problem**: No contract validation between components
**Required Fix**: API contract tests with golden fixtures

## Working Protocol

### Phase 1: Investigation + Prototyping (Week 1)
**Codex-Refactoring**:
1. Examine current codebase for each TIER 0 issue
2. Create spike solutions and prototypes
3. Write intention tests showing expected behavior
4. Document findings and edge cases in `docs/Owners/Refactoring/spikes/`
5. Create test fixtures demonstrating before/after behavior

**Claude-Refactoring**:
1. Review Codex's findings and prototypes for accuracy
2. Run Codex's intention tests, fix any that are broken
3. Identify potential breaking changes and missing test cases
4. Plan backward compatibility strategies
5. Create comprehensive test scenarios

### Phase 2: Implementation (Weeks 2-3)
**Codex-Refactoring**:
1. Implement foundation changes (schemas, job persistence)
2. Create migration utilities and scripts with basic tests
3. Update core modules to use new patterns
4. Write unit tests for all new functionality

**Claude-Refactoring**:
1. Run and fix all of Codex's tests
2. Add comprehensive test coverage for missed scenarios
3. Create integration tests with other components
4. Validate backward compatibility with full test suite
5. Create documentation and migration guides
6. Performance regression testing

## Success Criteria
- [ ] All existing tests pass without modification
- [ ] No breaking API changes for external clients
- [ ] Performance regression tests pass
- [ ] Other area owners can build on stable foundations
- [ ] Technical debt metrics show measurable improvement

## Communication
- **Daily Standup**: Brief status sync between Codex/Claude teams
- **Weekly Report**: Progress update to main project
- **Breaking Change Alerts**: 48-hour notice to other area owners
- **Documentation**: All changes documented with examples

## Dependencies
- None - this work enables all other areas
- Other areas should pause major changes until foundations are stable

## Next Assignment
After completion, Assignment 002 will focus on TIER 1 developer experience improvements and establishing patterns for other area owners to follow.