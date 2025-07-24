# 🛡️ Defensive Coding Checklist for Wolf Goat Pig Backend

## 1. Class and State Initialization
- [ ] Initialize all attributes in `__init__` and after deserialization, even if to `None` or an empty value.
- [ ] Use `getattr(self, "field", default)` in serialization and DB save methods to avoid `AttributeError`.

## 2. Safe Dictionary Access
- [ ] Never use `dict['key']` unless you are certain the key exists.
- [ ] Use a helper like `_require_key(obj, key, context)` for required keys, and `_safe_get(obj, key, default)` for optional keys.
- [ ] Log and raise a clear error if a required key is missing.

## 3. API Endpoint Validation
- [ ] Use Pydantic models for all request bodies and responses.
- [ ] Validate all incoming data for required fields, types, and value ranges.
- [ ] Return clear, descriptive error messages for all 400s (bad requests).
- [ ] Log all errors with context and stack traces.

## 4. Database Operations
- [ ] Wrap all DB reads/writes in `try/except` blocks.
- [ ] Log all DB errors with context.
- [ ] On DB failure, return a safe fallback or error message—never crash.

## 5. Simulation/Business Logic
- [ ] Check all preconditions before state transitions (e.g., “is the game active?”, “are all required fields set?”).
- [ ] Validate all input ranges and types for random/AI logic.
- [ ] Log and return a clear error if a precondition fails.

## 6. Global Exception Handling
- [ ] Use a FastAPI global exception handler to catch all unhandled exceptions.
- [ ] Return a JSON error with a unique error code and log the stack trace.

## 7. Logging
- [ ] Use the `logging` module for all warnings, errors, and info.
- [ ] Include context (user, endpoint, payload, state) in every log.
- [ ] For critical errors, log the full stack trace (`traceback.format_exc()`).

## 8. Testing Defensive Patterns
- [ ] Write tests that intentionally send bad/missing data to every endpoint and method.
- [ ] Assert that the response is a clear, descriptive error, not a crash or generic 500.

## 9. Frontend Defensive Patterns
- [ ] Always check backend response status and error messages.
- [ ] Never assume a request will succeed; handle and display errors gracefully.
- [ ] Disable UI actions that would trigger invalid backend calls.

## 10. Documentation and Error Codes
- [ ] Document all possible error codes and messages for each endpoint.
- [ ] Use unique error codes for common failure modes (e.g., `ERR_MISSING_FIELD`, `ERR_INVALID_STATE`).

---

## Sample Helper Functions

```python
def _require_key(obj, key, context):
    if key not in obj:
        logging.error(f"Missing '{key}' key in {context}: {obj}")
        raise ValueError(f"Simulation error: missing '{key}' key in {context}")
    return obj[key]

def _safe_get(obj, key, default=None):
    return obj[key] if key in obj else default
```

---

## Sample FastAPI Global Exception Handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logging.error(f"Unhandled exception at {request.url}: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc), "code": "ERR_INTERNAL"}
    )
```

---

**Adopt this checklist for all new code and code reviews to ensure your backend is robust, maintainable, and user-friendly!** 