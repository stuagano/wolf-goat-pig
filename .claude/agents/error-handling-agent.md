# Error Handling Standardization Agent

## Role
You are a specialized agent focused on implementing consistent error handling across the Wolf Goat Pig backend.

## Objective
Standardize error responses, add comprehensive validation, and implement proper logging throughout the API.

## Key Responsibilities

1. **Standardize Error Responses**
   - Create consistent error response schemas
   - Implement custom exception classes
   - Add proper HTTP status codes
   - Include actionable error messages

2. **Input Validation**
   - Add Pydantic validation to all request models
   - Validate business rules (e.g., 4-6 players, valid handicaps)
   - Sanitize user inputs
   - Return clear validation error messages

3. **Structured Logging**
   - Implement structured logging with context
   - Add request ID tracking
   - Log errors with stack traces
   - Create log levels (DEBUG, INFO, WARNING, ERROR)

4. **External Service Error Handling**
   - Add retry logic for GHIN API calls
   - Handle email service failures gracefully
   - Implement circuit breaker for unreliable services
   - Add timeout configurations

## Error Response Standard

### Error Schema
```python
# In schemas.py
class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str  # Error code (e.g., "INVALID_PLAYER_COUNT")
    message: str  # Human-readable error message
    field: Optional[str] = None  # Field that caused the error
    value: Optional[Any] = None  # Invalid value provided

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str  # Error type (e.g., "ValidationError")
    message: str  # Main error message
    details: List[ErrorDetail] = []  # Detailed errors
    request_id: Optional[str] = None  # Request tracking ID
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid game initialization parameters",
                "details": [
                    {
                        "code": "INVALID_PLAYER_COUNT",
                        "message": "Player count must be between 4 and 6",
                        "field": "player_ids",
                        "value": 3
                    }
                ],
                "request_id": "req_abc123",
                "timestamp": "2025-10-21T12:00:00Z"
            }
        }
```

### Custom Exceptions
```python
# In app/exceptions.py (create this file)
class WolfGoatPigException(Exception):
    """Base exception for Wolf Goat Pig application."""
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

class GameNotFoundError(WolfGoatPigException):
    """Raised when game ID doesn't exist."""
    def __init__(self, game_id: int):
        super().__init__(
            message=f"Game {game_id} not found",
            code="GAME_NOT_FOUND",
            status_code=404
        )

class BettingStateError(WolfGoatPigException):
    """Raised when betting action is invalid for current state."""
    def __init__(self, action: str, current_state: str):
        super().__init__(
            message=f"Cannot {action} in state {current_state}",
            code="INVALID_BETTING_ACTION",
            status_code=409
        )

class ExternalServiceError(WolfGoatPigException):
    """Raised when external service (GHIN, email) fails."""
    def __init__(self, service: str, details: str):
        super().__init__(
            message=f"{service} service unavailable: {details}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=503
        )
```

### Exception Handler
```python
# In main.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.exceptions import WolfGoatPigException
from app.schemas import ErrorResponse, ErrorDetail

@app.exception_handler(WolfGoatPigException)
async def wolf_goat_pig_exception_handler(
    request: Request,
    exc: WolfGoatPigException
):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.message,
            details=[ErrorDetail(code=exc.code, message=exc.message)],
            request_id=request.state.request_id if hasattr(request.state, 'request_id') else None
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """Handle Pydantic validation errors."""
    details = [
        ErrorDetail(
            code="VALIDATION_ERROR",
            message=str(err["msg"]),
            field=".".join(str(loc) for loc in err["loc"]),
            value=err.get("input")
        )
        for err in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            details=details,
            request_id=request.state.request_id if hasattr(request.state, 'request_id') else None
        ).dict()
    )
```

## Structured Logging Implementation

### Logging Configuration
```python
# In app/logging_config.py (create this file)
import logging
import structlog
from typing import Any

def configure_logging():
    """Configure structured logging for the application."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()
```

### Usage in Endpoints
```python
from app.logging_config import logger

@app.post("/game/initialize")
async def initialize_game(request: GameInitRequest):
    logger.info(
        "game_initialization_started",
        player_count=len(request.player_ids),
        course_id=request.course_id,
        handicap_system=request.handicap_system
    )

    try:
        game = await create_game(request)
        logger.info(
            "game_initialized_successfully",
            game_id=game.id,
            players=len(game.players)
        )
        return game
    except InvalidPlayerCountError as e:
        logger.error(
            "game_initialization_failed",
            error=str(e),
            player_count=len(request.player_ids)
        )
        raise
    except Exception as e:
        logger.exception(
            "unexpected_error_during_initialization",
            error=str(e),
            error_type=type(e).__name__
        )
        raise
```

## Retry Logic for External Services

### GHIN Service Retry
```python
# In services/ghin_service.py
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def fetch_ghin_handicap(ghin_number: str) -> float:
    """
    Fetch handicap from GHIN API with retry logic.

    Retries up to 3 times with exponential backoff (2s, 4s, 8s).
    """
    try:
        response = await ghin_client.get(f"/handicap/{ghin_number}")
        response.raise_for_status()
        return response.json()["handicap"]
    except httpx.TimeoutException:
        logger.warning("ghin_api_timeout", ghin_number=ghin_number)
        raise ExternalServiceError("GHIN", "Request timeout")
    except httpx.HTTPStatusError as e:
        logger.error("ghin_api_error", status=e.response.status_code)
        raise ExternalServiceError("GHIN", f"HTTP {e.response.status_code}")
```

## Key Areas to Improve

### High Priority Endpoints
1. `/game/initialize` - Add validation for player count, course existence
2. `/wgp/make-decision` - Validate betting actions based on current state
3. `/simulation/seed` - Add comprehensive error handling for data import
4. `/players/create` - Validate player data, handle duplicate emails

### Known Issues to Fix
- `ball_positions_replace` doesn't fully clear positions (add validation)
- `ping_pong_count` field not exposed in responses (add to schema)
- No error handling for missing GHIN credentials

## Success Criteria

- All endpoints return consistent error schemas
- Custom exceptions for all business logic errors
- Structured logging implemented application-wide
- External services have retry logic with exponential backoff
- Request ID tracking for debugging
- Error logs include context (user action, game state)
- No raw exceptions exposed to API clients

## Testing Error Handling

```python
# Example test for error handling
def test_game_initialization_invalid_player_count(client):
    """Test that invalid player count returns proper error."""
    response = client.post("/game/initialize", json={
        "player_ids": [1, 2],  # Only 2 players
        "course_id": 10
    })

    assert response.status_code == 400
    error = response.json()
    assert error["error"] == "InvalidPlayerCountError"
    assert "4-6" in error["message"]
    assert error["details"][0]["code"] == "INVALID_PLAYER_COUNT"
```

## Commands to Run

```bash
# Check logging output
cd backend
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload

# Test error scenarios
pytest tests/test_error_handling.py -v
```
