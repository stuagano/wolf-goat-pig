# Router Extraction Plan

## Current State

- **main.py**: 9,576 lines, 141 endpoints
- **Problem**: Everything in one file, hard to maintain, poor separation of concerns
- **Goal**: Break into 10-12 focused router modules

## Completed ✅

### 1. Health Router
- **File**: `app/routers/health.py` (262 lines)
- **Endpoints**: 2 endpoints
  - GET `/health` - Comprehensive health check with 7 system component diagnostics
  - GET `/healthz` - Simplified health endpoint for Render monitoring
- **Features**:
  - Component-based logging: `logger = logging.getLogger("app.routers.health")`
  - Tagged for API docs: `tags=["health"]`
  - System checks: database, courses, rules, AI players, simulation, game state, data seeding

### 2. Sheet Integration Router
- **File**: `app/routers/sheet_integration.py` (690 lines)
- **Endpoints**: 7 endpoints
  - POST `/sheet-integration/analyze-structure`
  - POST `/sheet-integration/create-leaderboard`
  - POST `/sheet-integration/sync-data`
  - GET  `/sheet-integration/export-current-data`
  - POST `/sheet-integration/sync-wgp-sheet` (with rate limiting & caching)
  - POST `/sheet-integration/fetch-google-sheet`
  - POST `/sheet-integration/compare-data`
- **Features**:
  - Component-based logging: `logger = logging.getLogger("app.routers.sheet_integration")`
  - Rate limiting and caching already applied
  - Clean imports and dependencies
  - Tagged for API docs: `tags=["sheet_integration"]`

### 3. Players Router
- **File**: `app/routers/players.py`
- **Endpoints**: 23 endpoints
- **Status**: Completed via PR #139 (Nov 11, 2025)

### 4. Courses Router
- **File**: `app/routers/courses.py` (258 lines)
- **Endpoints**: 9 endpoints
  - GET `/courses` - List all courses with fallback handling
  - GET `/courses/{course_id}` - Get course by ID
  - POST `/courses` - Add new course
  - PUT `/courses/{course_name}` - Update course
  - DELETE `/courses/{course_name}` - Delete course
  - POST `/courses/import/search` - Import course by search
  - POST `/courses/import/file` - Import course from JSON file
  - GET `/courses/import/sources` - List import sources
  - POST `/courses/import/preview` - Preview course import
- **Features**:
  - Component-based logging: `logger = logging.getLogger("app.routers.courses")`
  - Multi-level fallback handling for resilience
  - Schema migration to schemas.py (CourseImportRequest)
  - Tagged for API docs: `tags=["courses"]`
  - All 21 course tests passing

## Remaining Work

### Endpoint Distribution

| Router | Endpoints | Priority | Notes |
|--------|-----------|----------|-------|
| health | 2 | High | Simple, good next step |
| game_flow | 31 | High | Core functionality |
| simulation | 16 | Medium | Separate feature |
| players | 23 | High | Core functionality |
| analytics | 6 | Medium | Depends on players |
| courses | 9 | Medium | Reference data |
| ghin | 4 | Low | External integration |
| admin | 12 | Low | Admin tools |
| scheduling | 14 | Low | Daily signups |
| other | 17 | Low | Misc/legacy |

### Priority Order

**Phase 1 (Completed)**:
1. ✅ health (2) - DONE (Nov 10, 2025)
2. ✅ sheet_integration (7) - DONE
3. ✅ players (23) - DONE (PR #139, Nov 11, 2025)

**Phase 2 (In Progress)**:
4. ✅ courses (9) - DONE (Nov 11, 2025 - commit 86d97e9)
5. analytics (6) - Next, uses players
6. game_flow (31) - Biggest, most complex

**Phase 3 (Lower priority)**:
7. simulation (16)
8. ghin (4)
9. admin (12)
10. scheduling (14)

## Pattern to Follow

### 1. Create Router File

```python
"""
[Router Name] Router

[Description]
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging

from ..database import get_db
from .. import models, schemas
from ..services.[service_name] import [ServiceName]

logger = logging.getLogger("app.routers.[router_name]")

router = APIRouter(
    prefix="/[prefix]",  # e.g., "/players"
    tags=["[router_name]"],
    responses={404: {"description": "Not found"}},
)

# Endpoints here (replace @app. with @router.)
```

### 2. Extract Endpoints from main.py

For each endpoint:
1. Find `@app.[method]("[path]")` in main.py
2. Copy the complete function (decorators + function + docstring)
3. Replace `@app.` with `@router.`
4. Move to appropriate router file
5. Delete from main.py

### 3. Update Imports in Router

Each router needs:
- FastAPI components: `APIRouter, Depends, HTTPException, Query, etc.`
- Database: `get_db`
- Models and schemas: `models, schemas`
- Relevant services: Import only what's needed
- Middleware (if needed): `rate_limiter, cache`

### 4. Update main.py

After extracting routers, update main.py:

```python
# Add router imports
from app.routers import (
    health,
    sheet_integration,
    players,
    game_flow,
    # ...
)

# Register routers (after app creation, before endpoints)
app.include_router(health.router)
app.include_router(sheet_integration.router)
app.include_router(players.router)
app.include_router(game_flow.router)
# ...

logger.info("✅ All routers registered")
```

### 5. Remove Extracted Endpoints from main.py

After each router:
1. Delete the extracted endpoint functions
2. Keep: imports, app creation, startup/shutdown, exception handlers
3. Test that app still starts

## Automation Script

Use `extract_routers.py` for bulk extraction:

```bash
# Dry run (show what would be extracted)
python extract_routers.py --dry-run

# Extract all routers
python extract_routers.py --all

# Extract specific router
python extract_routers.py --router=players
```

## Testing Strategy

After each router extraction:

1. **Import test**: `python -m app.routers.[router_name]`
2. **Startup test**: `python startup.py --verify-setup`
3. **Endpoint test**: `curl http://localhost:8000/[endpoint]`
4. **Integration test**: Run relevant test suite

### Quick Test Commands

```bash
# Test sheet_integration router
python -c "from app.routers import sheet_integration; print('✅ Import OK')"

# Start server and test endpoint
uvicorn app.main:app --reload &
sleep 2
curl http://localhost:8000/sheet-integration/analyze-structure
```

## Benefits

### Before (Monolithic)
- ❌ 9,576 lines in one file
- ❌ Hard to find endpoints
- ❌ Merge conflicts frequent
- ❌ All logs mixed together
- ❌ Can't disable features easily

### After (Routers)
- ✅ ~800 lines per router (manageable)
- ✅ Clear organization
- ✅ Independent modules
- ✅ Component-based logging
- ✅ Feature flags possible

## Migration Checklist

For each router:
- [ ] Create router file in `app/routers/`
- [ ] Extract endpoints from main.py
- [ ] Update imports in router
- [ ] Add component-based logging
- [ ] Update `app/routers/__init__.py`
- [ ] Register router in main.py
- [ ] Delete endpoints from main.py
- [ ] Test import
- [ ] Test endpoints
- [ ] Commit changes

## Next Steps

1. **Review** the `sheet_integration` router
2. **Test** it works (see Testing Strategy above)
3. **Extract** the next router (health recommended)
4. **Iterate** until all routers extracted
5. **Clean up** main.py (should be < 500 lines when done)

## Final State

```
app/
├── routers/
│   ├── __init__.py
│   ├── health.py           (~50 lines, 2 endpoints)
│   ├── sheet_integration.py (~690 lines, 7 endpoints) ✅
│   ├── players.py           (~1200 lines, 23 endpoints)
│   ├── game_flow.py         (~2000 lines, 31 endpoints)
│   ├── simulation.py        (~900 lines, 16 endpoints)
│   ├── analytics.py         (~400 lines, 6 endpoints)
│   ├── courses.py           (~500 lines, 9 endpoints)
│   ├── ghin.py              (~300 lines, 4 endpoints)
│   ├── admin.py             (~700 lines, 12 endpoints)
│   └── scheduling.py        (~800 lines, 14 endpoints)
└── main.py                  (~400 lines, just setup)
```

## Questions?

- **Should I keep going?** Yes if tests pass for sheet_integration
- **Which router next?** `health` - it's simple (2 endpoints)
- **When to commit?** After each working router
- **How to rollback?** Restore from backup: `app/main.py.backup.[timestamp]`

## Resources

- [FastAPI Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Separation of Concerns Guide](ARCHITECTURE_SEPARATION_GUIDE.md)
- [Database Session Guide](DATABASE_SESSION_GUIDE.md)
