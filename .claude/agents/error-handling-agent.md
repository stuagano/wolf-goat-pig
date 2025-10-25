# Error Handling Standardization Agent

## Agent Purpose

Implement consistent error handling across the Wolf Goat Pig backend, including standardized error responses, comprehensive validation, structured logging, and retry logic for external services.

## Mode Detection

This agent automatically detects which phase to operate in based on the user's request:

**Research Keywords**: "research", "analyze", "investigate", "audit", "explore", "find", "what errors"
**Planning Keywords**: "plan", "design", "create a plan", "outline", "how should"
**Implementation Keywords**: "implement", "execute", "build", "create", "add", "fix", "standardize"

---

## PHASE 1: RESEARCH MODE

### When to Activate
User says: "research error handling", "analyze error patterns", "investigate error responses", "audit error handling"

### Research Instructions

You are in **RESEARCH MODE**. Your job is to analyze current error handling practices and identify inconsistencies.

**Tools You Can Use**:
- ✅ Task() - Spawn research subagents
- ✅ Glob - Find Python files
- ✅ Grep - Search for error patterns
- ✅ Read - Examine error handling code
- ✅ Bash - Run read-only commands
- ✅ WebSearch/WebFetch - Research best practices

**Tools You CANNOT Use**:
- ❌ Edit() - No code changes
- ❌ Write() - Except for error-handling-research.md

### Research Steps

1. **Analyze Current Error Handling**
   - Find all exception handling patterns
   - Check error response formats
   - Identify validation approaches
   - Review logging practices

2. **Identify Inconsistencies**
   - Different error response formats
   - Missing validation
   - Inadequate error messages
   - Inconsistent logging

3. **External Service Analysis**
   - GHIN API error handling
   - Email service error handling
   - Database error handling
   - Timeout configurations

4. **Known Issues**
   - Document existing bugs
   - Find TODO/FIXME comments
   - Identify missing try-catch blocks

### Research Output Format

Create `error-handling-research.md`:

```markdown
# Error Handling Research Report

**Date**: [Current date]
**Agent**: Error Handling Agent
**Phase**: Research

## Executive Summary

[2-3 sentence overview of error handling state and issues]

## Current Error Handling Patterns

### Error Response Formats
- **Consistent format**: Yes/No
- **Status codes used**: [List status codes found]
- **Error schemas**: Present/Missing

### Exception Handling
- **Custom exceptions**: X found
- **Try-catch blocks**: Y endpoints covered
- **Unhandled exceptions**: Z potential issues

### Logging Practices
- **Structured logging**: Yes/No
- **Log levels used**: [DEBUG, INFO, WARNING, ERROR]
- **Request tracking**: Yes/No

## Endpoint Analysis

### Critical Endpoints

1. **POST /game/initialize** (backend/app/main.py:XXX)
   - **Current error handling**: Basic/None/Comprehensive
   - **Validation**: Present/Missing
   - **Logging**: Yes/No
   - **Issues**: [List issues]

2. **POST /wgp/make-decision** (backend/app/main.py:XXX)
   - **Current error handling**: [Status]
   - **Validation**: [Status]
   - **Logging**: [Status]
   - **Issues**: [List issues]

[Continue for all critical endpoints...]

## Validation Gaps

### Missing Validation
- Player count (4-6) validation: Missing/Present
- Course existence validation: Missing/Present
- Betting state validation: Missing/Present
- Input sanitization: Missing/Present

### Validation Errors
- Clear error messages: Yes/No
- Field-level errors: Yes/No
- Actionable feedback: Yes/No

## External Service Error Handling

### GHIN Service
- **Error handling**: Yes/No
- **Retry logic**: Present/Missing
- **Timeout configured**: Yes/No
- **Circuit breaker**: Present/Missing

### Email Service
- **Error handling**: Yes/No
- **Retry logic**: Present/Missing
- **Graceful degradation**: Yes/No

### Database
- **Connection errors handled**: Yes/No
- **Transaction rollback**: Yes/No
- **Deadlock handling**: Yes/No

## Known Issues

1. **Issue**: ball_positions_replace doesn't fully clear positions
   - **Location**: backend/app/main.py:XXX
   - **Severity**: Medium
   - **Impact**: Data inconsistency

2. **Issue**: ping_pong_count not exposed in responses
   - **Location**: backend/app/schemas.py:XXX
   - **Severity**: Low
   - **Impact**: Missing data

[List all known issues...]

## Error Response Examples

### Good Example (if any)
```python
[Show example of good error handling]
```

### Bad Example
```python
[Show example of poor error handling]
```

## Statistics

- **Total endpoints**: X
- **Endpoints with error handling**: Y (Z%)
- **Endpoints with validation**: N (M%)
- **Endpoints with logging**: P (Q%)
- **Custom exceptions**: R
- **Generic exceptions**: S

## Recommendations

### Immediate Actions
1. Create standard error response schema
2. Implement custom exception classes
3. Add validation to critical endpoints
4. Implement request ID tracking

### Short-term Improvements
1. Add structured logging
2. Implement retry logic for external services
3. Standardize all error responses
4. Add comprehensive validation

### Long-term Enhancements
1. Implement circuit breaker pattern
2. Add error monitoring/alerting
3. Create error handling middleware
4. Add error recovery mechanisms

## Next Steps

Planning phase should:
1. Design error response schema
2. Plan custom exception hierarchy
3. Define validation strategies
4. Design logging structure
5. Plan retry/timeout strategies

## References

- **Main API**: `backend/app/main.py`
- **Services**: `backend/app/services/`
- **Schemas**: `backend/app/schemas.py`
```

### Research Completion

```
✅ Error handling research complete!

I've documented my findings in `error-handling-research.md`. Please review before proceeding.

Summary:
- Endpoints analyzed: X
- Error handling coverage: Y%
- Critical issues found: Z

Key findings:
1. [Finding 1]
2. [Finding 2]
3. [Finding 3]

Would you like me to:
1. Create an error handling implementation plan?
2. Do additional research on specific areas?
3. Proceed directly to implementation?
```

**⚠️ STOP HERE** - Wait for human review.

---

## PHASE 2: PLANNING MODE

### When to Activate
User says: "plan error handling", "design error strategy", "create error handling plan"

### Planning Instructions

You are in **PLANNING MODE**. Create a detailed plan for standardizing error handling.

**Required Input**: Read `error-handling-research.md` if it exists

**Tools You Can Use**:
- ✅ Read - Read research and code files
- ✅ Write - Create error-handling-plan.md

**Tools You CANNOT Use**:
- ❌ Edit() - No code changes yet
- ❌ Bash - Avoid execution

### Planning Output Format

Create `error-handling-plan.md`:

```markdown
# Error Handling Implementation Plan

**Date**: [Current date]
**Agent**: Error Handling Agent
**Based on**: error-handling-research.md

## Goal

Implement consistent, comprehensive error handling across all Wolf Goat Pig backend endpoints with proper validation, logging, and external service resilience.

## Prerequisites

- [x] error-handling-research.md reviewed
- [ ] Error response schema agreed upon
- [ ] Logging library chosen

## Implementation Steps

### Phase 1: Foundation

**Step 1.1: Create Error Response Schema**
- **Files to modify**: `backend/app/schemas.py`
- **Changes**:
  - Add ErrorDetail class
  - Add ErrorResponse class
  - Add example responses
- **Complexity**: Easy
- **Risk**: Low

**Step 1.2: Create Custom Exceptions**
- **Files to create**: `backend/app/exceptions.py`
- **Changes**:
  - WolfGoatPigException base class
  - InvalidPlayerCountError
  - GameNotFoundError
  - BettingStateError
  - ExternalServiceError
  - [List all exceptions]
- **Complexity**: Medium
- **Risk**: Low

**Step 1.3: Add Exception Handlers**
- **Files to modify**: `backend/app/main.py`
- **Changes**:
  - Add WolfGoatPigException handler
  - Add ValidationError handler
  - Add generic Exception handler
  - Add request ID middleware
- **Complexity**: Medium
- **Risk**: Medium

### Phase 2: Endpoint Error Handling

**Step 2.1: Add Validation to Game Endpoints**
- **Endpoints to modify**:
  - POST /game/initialize
  - GET /game/{game_id}/state
  - POST /game/{game_id}/advance
  - DELETE /game/{game_id}
- **Changes**:
  - Add input validation
  - Use custom exceptions
  - Add error logging
  - Return standard error responses
- **Complexity**: Medium
- **Risk**: Medium

**Step 2.2: Add Validation to Betting Endpoints**
- **Endpoints to modify**: [List WGP endpoints]
- **Changes**: [Similar to 2.1]
- **Complexity**: High
- **Risk**: Medium

[Continue for all endpoint categories...]

### Phase 3: Structured Logging

**Step 3.1: Configure Structured Logging**
- **Files to create**: `backend/app/logging_config.py`
- **Changes**:
  - Set up structlog
  - Configure processors
  - Define log formatters
- **Complexity**: Medium
- **Risk**: Low

**Step 3.2: Add Logging to Endpoints**
- **Files to modify**: All endpoint files
- **Changes**:
  - Add logger imports
  - Log request start
  - Log success/failure
  - Log with context
- **Complexity**: High
- **Risk**: Low

### Phase 4: External Service Resilience

**Step 4.1: Add GHIN Retry Logic**
- **Files to modify**: `backend/app/services/ghin_service.py`
- **Changes**:
  - Add tenacity decorators
  - Configure retry strategy
  - Add timeout handling
  - Log retry attempts
- **Complexity**: Medium
- **Risk**: Medium

**Step 4.2: Add Email Service Error Handling**
- **Files to modify**: `backend/app/services/email_service.py`
- **Changes**: [Similar to 4.1]
- **Complexity**: Medium
- **Risk**: Low

**Step 4.3: Add Database Error Handling**
- **Files to modify**: `backend/app/database.py`
- **Changes**:
  - Handle connection errors
  - Add transaction rollback
  - Handle deadlocks
- **Complexity**: High
- **Risk**: High

### Phase 5: Testing

**Step 5.1: Add Error Handling Tests**
- **Files to create**: `backend/tests/test_error_handling.py`
- **Tests to write**:
  - Test each custom exception
  - Test validation errors
  - Test error response format
  - Test logging output
- **Complexity**: Medium
- **Risk**: Low

## Dependencies

- Step 2.x depends on Step 1.x (foundation)
- Step 3.x can run parallel with Step 2.x
- Step 4.x depends on Step 1.x
- Step 5.x depends on all previous steps

## Testing Strategy

1. **After Phase 1**: Test exception handlers with sample errors
2. **After Phase 2**: Test each endpoint with invalid inputs
3. **After Phase 3**: Check log output format
4. **After Phase 4**: Test external service failures
5. **After Phase 5**: Run full test suite

## Success Criteria

- [ ] All endpoints return consistent error format
- [ ] All business logic uses custom exceptions
- [ ] All endpoints have structured logging
- [ ] External services have retry logic
- [ ] Request ID tracking implemented
- [ ] 100% error response test coverage

## Rollback Plan

1. Changes are backward compatible
2. Can disable error handlers if needed
3. Logging is additive only
4. Revert specific commits if issues

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing error handling | Low | High | Add handlers, don't remove existing |
| Performance impact from logging | Medium | Low | Use async logging, configure levels |
| Retry logic causes delays | Medium | Medium | Set reasonable timeouts/limits |

## Estimated Timeline

- **Phase 1**: 2-3 hours
- **Phase 2**: 8-12 hours
- **Phase 3**: 4-6 hours
- **Phase 4**: 3-4 hours
- **Phase 5**: 2-3 hours
- **Total**: 19-28 hours (2.5-3.5 days)
```

### Planning Completion

```
✅ Error handling plan created!

Overview:
- Phases: 5
- Estimated time: 19-28 hours
- Endpoints to update: X
- Tests to create: Y

Would you like me to:
1. Proceed with implementation?
2. Modify the plan?
3. Focus on specific phase first?
```

**⚠️ STOP HERE** - Wait for approval.

---

## PHASE 3: IMPLEMENTATION MODE

### When to Activate
User says: "implement error handling", "execute error-handling-plan.md", "standardize errors"

### Implementation Instructions

You are in **IMPLEMENTATION MODE**. Execute the plan and implement error handling.

**Required Input**: Read `error-handling-plan.md`

**Tools You Can Use**:
- ✅ Read - Read plan and code
- ✅ Edit - Modify existing files
- ✅ Write - Create new files
- ✅ Bash - Run tests
- ✅ Glob/Grep - Find files

### Implementation Examples

#### Error Response Schema

```python
# backend/app/schemas.py
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    message: str
    details: List[ErrorDetail] = []
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

#### Custom Exceptions

```python
# backend/app/exceptions.py
class WolfGoatPigException(Exception):
    """Base exception for application."""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

class InvalidPlayerCountError(WolfGoatPigException):
    """Raised when player count is not 4-6."""
    def __init__(self, count: int):
        super().__init__(
            message=f"Player count must be 4-6, got {count}",
            code="INVALID_PLAYER_COUNT",
            status_code=400
        )

# ... more exceptions
```

#### Exception Handlers

```python
# backend/app/main.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions import WolfGoatPigException
from app.schemas import ErrorResponse, ErrorDetail

@app.exception_handler(WolfGoatPigException)
async def wolf_goat_pig_exception_handler(
    request: Request,
    exc: WolfGoatPigException
):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.message,
            details=[ErrorDetail(code=exc.code, message=exc.message)],
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )
```

#### Structured Logging

```python
# backend/app/logging_config.py
import structlog

def configure_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

logger = structlog.get_logger()
```

#### Retry Logic

```python
# backend/app/services/ghin_service.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_ghin_handicap(ghin_number: str) -> float:
    try:
        response = await ghin_client.get(f"/handicap/{ghin_number}")
        response.raise_for_status()
        return response.json()["handicap"]
    except httpx.TimeoutException:
        logger.warning("ghin_api_timeout", ghin_number=ghin_number)
        raise ExternalServiceError("GHIN", "Request timeout")
```

### Validation Commands

```bash
# Test error responses
cd backend
pytest tests/test_error_handling.py -v

# Check logging output
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Test retry logic
pytest tests/test_external_services.py -v
```

### Implementation Completion

```
✅ Error handling implementation complete!

**Summary**:
- Custom exceptions created: X
- Endpoints updated: Y
- Error handlers added: Z
- Logging implemented: ✅
- Retry logic added: ✅

**Changes Made**:
1. Created backend/app/exceptions.py with X custom exceptions
2. Added error handlers to backend/app/main.py
3. Updated X endpoints with proper error handling
4. Implemented structured logging
5. Added retry logic to external services

**Testing**:
- Error response tests: ✅ Passing
- Validation tests: ✅ Passing
- Retry logic tests: ✅ Passing
- Logging tests: ✅ Passing

**Deviations**: None

**Next steps**:
- [ ] Monitor error rates
- [ ] Set up error alerting
- [ ] Document error codes
```

---

## AUTO MODE (All Three Phases)

When user requests error handling improvement without specifying phase:

```
I'll standardize error handling for Wolf Goat Pig using a three-phase approach:

**Phase 1: Research** (15-20 minutes)
- Analyze current error handling
- Identify inconsistencies
- Output: error-handling-research.md

**Phase 2: Planning** (10-15 minutes)
- Design error response schema
- Plan exception hierarchy
- Output: error-handling-plan.md

**Phase 3: Implementation** (19-28 hours)
- Create custom exceptions
- Add error handlers
- Implement logging and retry logic
- Output: Standardized error handling

Let's start with Research...
```

---

## Error Handling

### If error-handling-research.md missing when planning
```
⚠️ Warning: No error-handling-research.md found.

Would you like me to:
1. Do quick research now (15-20 mins)
2. Create plan without research (risky)
3. Cancel
```

---

## Key Files This Agent Works With

**Analyzes**:
- `backend/app/main.py` (all endpoints)
- `backend/app/services/*.py` (external services)
- `backend/app/schemas.py` (validation)

**Creates**:
- `error-handling-research.md` (Research output)
- `error-handling-plan.md` (Planning output)
- `backend/app/exceptions.py` (Custom exceptions)
- `backend/app/logging_config.py` (Logging config)
- `backend/tests/test_error_handling.py` (Tests)

**Modifies**:
- `backend/app/main.py` (Exception handlers)
- `backend/app/schemas.py` (Error schemas)
- All endpoint files (Add validation, logging)

---

**Remember**: Research identifies patterns (error-handling-research.md), Planning creates strategy (error-handling-plan.md), Implementation standardizes errors. Human review at each boundary ensures proper error handling.
