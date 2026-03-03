# Backend Architecture Separation Guide

## Problem Statement

The backend currently has poor separation of concerns between different features:
- **Game flow** (live gameplay, scoring, wolf/goat/pig mechanics)
- **Analytics/Leaderboards** (Google Sheets sync, player statistics)
- **Admin tools** (player management, course setup)
- **Scheduling** (daily signups, matchmaking)

This lack of separation causes:
1. **Unintended interactions** - Changes to game flow can break analytics
2. **Performance issues** - Sheet sync polling appears in game flow logs
3. **Hard to maintain** - Everything is mixed in `main.py` (9000+ lines)
4. **Coupling** - Shared database sessions can cause transaction conflicts

## Current Issues

### 1. Sheet Sync Frequency
**Problem**: Google Sheets sync endpoint is being called too frequently, cluttering logs

**Root Cause**: Frontend components (`Leaderboard.js`, `GoogleSheetsLiveSync.js`) manually trigger sync, but there's no rate limiting

**Current behavior**:
- Manual sync on button click
- AutoSync disabled by default (good!)
- No backend rate limiting
- No caching of results

### 2. Database Session Conflicts
**Problem**: Sheet sync and game flow share database sessions, causing potential deadlocks

**Root Cause**: Both features use `db: Session = Depends(get_db)` which can share connection pool

### 3. Logging Noise
**Problem**: Sheet sync logs appear in game flow logs, making debugging harder

**Root Cause**: Single logger, no component-based logging

## Proposed Architecture

### 1. API Module Separation

Reorganize `main.py` into separate routers:

```
backend/app/
├── routers/
│   ├── __init__.py
│   ├── game_flow.py          # Game creation, gameplay, scoring
│   ├── analytics.py           # Leaderboards, statistics
│   ├── sheet_integration.py  # Google Sheets sync
│   ├── admin.py              # Player/course management
│   ├── scheduling.py         # Daily signups, matchmaking
│   └── simulation.py         # Simulation mode
├── middleware/
│   ├── rate_limiting.py      # Rate limit sheet sync
│   └── logging.py            # Component-based logging
└── main.py                    # Just router registration
```

### 2. Rate Limiting for Sheet Sync

Add rate limiting to prevent excessive polling:

**Backend (middleware/rate_limiting.py)**:
```python
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.last_sync = {}  # {endpoint: datetime}
        self.min_interval = timedelta(hours=1)  # Default: 1 hour

    def check_rate_limit(self, endpoint: str, client_id: str = None):
        """Check if rate limit allows this request."""
        key = f"{endpoint}:{client_id or 'anonymous'}"
        now = datetime.now()

        if key in self.last_sync:
            time_since_last = now - self.last_sync[key]
            if time_since_last < self.min_interval:
                remaining = self.min_interval - time_since_last
                logger.warning(
                    f"Rate limit hit for {endpoint} (client: {client_id}). "
                    f"Wait {remaining.seconds}s"
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Too many requests",
                        "retry_after_seconds": remaining.seconds,
                        "message": f"Sheet sync limited to once per {self.min_interval.seconds // 3600} hour(s)"
                    }
                )

        self.last_sync[key] = now
        logger.info(f"Rate limit passed for {endpoint} (client: {client_id})")
        return True

# Global instance
rate_limiter = RateLimiter()
```

**Apply to sheet sync endpoint**:
```python
from fastapi import Depends
from app.middleware.rate_limiting import rate_limiter

@app.post("/sheet-integration/sync-wgp-sheet")
async def sync_wgp_sheet_data(
    request: Dict[str, str],
    db: Session = Depends(database.get_db)
):
    # Rate limit to once per hour
    rate_limiter.check_rate_limit("sheet_sync", client_id="system")

    # ... existing sync logic ...
```

### 3. Response Caching

Cache sheet sync results to avoid redundant processing:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class SyncCache:
    def __init__(self, ttl_hours: int = 1):
        self.cache = {}
        self.ttl = timedelta(hours=ttl_hours)

    def get(self, key: str):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return data
        return None

    def set(self, key: str, data):
        self.cache[key] = (data, datetime.now())

sync_cache = SyncCache(ttl_hours=1)

@app.post("/sheet-integration/sync-wgp-sheet")
async def sync_wgp_sheet_data(...):
    # Check cache first
    cached = sync_cache.get("wgp_sheet_data")
    if cached:
        logger.info("Returning cached sheet data")
        return cached

    # Perform sync...
    result = { ... }

    # Cache result
    sync_cache.set("wgp_sheet_data", result)
    return result
```

### 4. Component-Based Logging

Separate loggers for different modules:

```python
# backend/app/routers/sheet_integration.py
import logging
logger = logging.getLogger("app.sheet_integration")

# backend/app/routers/game_flow.py
import logging
logger = logging.getLogger("app.game_flow")

# backend/app/routers/analytics.py
import logging
logger = logging.getLogger("app.analytics")
```

**Configure in startup.py**:
```python
import logging

# Configure log levels per component
logging.getLogger("app.sheet_integration").setLevel(logging.WARNING)
logging.getLogger("app.game_flow").setLevel(logging.INFO)
logging.getLogger("app.analytics").setLevel(logging.DEBUG)
```

### 5. Database Session Isolation

Use isolated sessions for background tasks:

```python
from app.database import get_isolated_session

@app.post("/sheet-integration/sync-wgp-sheet")
async def sync_wgp_sheet_data(request: Dict[str, str]):
    """
    Use isolated session to avoid conflicts with game flow.
    Game flow endpoints use Depends(get_db) for request-scoped sessions.
    """
    with get_isolated_session() as db:
        # Sync logic with isolated session
        player_service = PlayerService(db)
        # ... sync work ...
        db.commit()

    return {"status": "synced"}
```

## Implementation Plan

### Phase 1: Quick Wins (Immediate)
1. ✅ Add rate limiting to sheet sync endpoint (1 hour minimum)
2. ✅ Add response caching (1 hour TTL)
3. ✅ Use component-based logging
4. ✅ Document the separation strategy

### Phase 2: Refactor (Next Sprint)
1. Extract routers from main.py
2. Move sheet integration to separate router
3. Move game flow to separate router
4. Update imports and dependencies

### Phase 3: Advanced (Future)
1. Implement proper message queue for async tasks (Celery/Redis)
2. Move scheduled jobs to separate worker process
3. Add API gateway for request routing
4. Implement distributed tracing

## Quick Fix Script

```bash
# Apply rate limiting and caching immediately
python scripts/apply_sheet_sync_limits.py
```

## Best Practices Going Forward

### 1. Feature Isolation
- Each feature gets its own router
- No shared state between features
- Clear interfaces at boundaries

### 2. Database Sessions
- **Request-scoped**: Use `Depends(get_db)` for API endpoints
- **Isolated**: Use `get_isolated_session()` for background tasks
- **Never mix**: Don't share sessions between request and background

### 3. Rate Limiting
- Apply to all expensive operations
- Document limits in API docs
- Return clear error messages with retry info

### 4. Caching
- Cache expensive read operations
- Set appropriate TTL
- Invalidate on writes

### 5. Logging
- Use component-specific loggers
- Set appropriate log levels
- Don't log PII or sensitive data

## Testing Separation

Verify separation with these tests:

```bash
# 1. Test rate limiting
curl -X POST http://localhost:8000/sheet-integration/sync-wgp-sheet
# Wait < 1 hour, should get 429

# 2. Test caching
curl -X POST http://localhost:8000/sheet-integration/sync-wgp-sheet
# Second call should be instant (cache hit)

# 3. Test game flow independence
# Start a game, verify sheet sync doesn't interfere

# 4. Test logging separation
# Check logs, sheet sync should be separate from game flow
```

## References

- [FastAPI Router Documentation](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Rate Limiting Patterns](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
- [Database Session Best Practices](docs/DATABASE_SESSION_GUIDE.md)
