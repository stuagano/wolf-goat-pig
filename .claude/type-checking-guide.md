# Type Checking Guide for Wolf Goat Pig

## Overview

This project uses comprehensive type checking for both backend (Python) and frontend (TypeScript) to catch bugs early, improve IDE support, and make the codebase more maintainable.

## Quick Start

Run type checking anytime:

```bash
# Check both backend and frontend
npm run typecheck

# Or check individually
npm run typecheck:backend   # Python with mypy
npm run typecheck:frontend  # TypeScript with tsc
```

## Backend Type Checking (Python + mypy)

### Configuration

**File**: `/backend/mypy.ini`

Key settings:
- `python_version = 3.9`
- `disallow_incomplete_defs = True` - Require complete type hints where provided
- `warn_return_any = True` - Warn about Any returns
- `check_untyped_defs = True` - Type check function bodies even without annotations
- `ignore_errors = False` - Type checking enabled by default

### Running mypy

```bash
cd backend

# Check all files
mypy app

# Check specific file
mypy app/routers/health.py

# See error codes for easier debugging
mypy app --show-error-codes

# Generate HTML report
mypy app --html-report mypy-report
```

### Common Type Annotations

#### Function Return Types

```python
# Always annotate return types
def get_player(player_id: str) -> Optional[Player]:
    """Get player by ID."""
    return db.query(Player).filter_by(id=player_id).first()

# Use None for void functions
def update_score(player_id: str, score: int) -> None:
    """Update player score."""
    db.query(Player).filter_by(id=player_id).update({"score": score})

# Dict return types
def get_stats() -> Dict[str, Any]:
    """Get player statistics."""
    return {"total": 100, "average": 25.5}
```

#### Optional Parameters

```python
from typing import Optional

# Correct: Use Optional for nullable parameters
def search_course(name: str, state: Optional[str] = None) -> List[Course]:
    pass

# Wrong: str = None causes "implicit Optional" error
def search_course(name: str, state: str = None) -> List[Course]:  # ❌
    pass
```

#### List and Dict Types

```python
from typing import List, Dict, Any

def get_holes() -> List[Dict[str, Any]]:
    """Return list of hole data."""
    return [
        {"number": 1, "par": 4, "yards": 350},
        {"number": 2, "par": 3, "yards": 165}
    ]
```

#### Any Type (Use Sparingly)

```python
from typing import Any

# Use Any when type is truly dynamic
def process_sheet_data(data: Any) -> Dict[str, Any]:
    """Process Google Sheets data of unknown structure."""
    # Any is appropriate here since sheet structure varies
    pass
```

### Excluding Files from Type Checking

In `mypy.ini`:

```ini
# Ignore specific module
[mypy-app.models]
ignore_errors = True

# Ignore third-party imports
[mypy-sqlalchemy.*]
ignore_missing_imports = True
```

### Common mypy Errors and Fixes

#### 1. Missing Return Type Annotation

```python
# Error: Function is missing a return type annotation
def calculate_score(shots: int):  # ❌
    return shots * 10

# Fix: Add return type
def calculate_score(shots: int) -> int:  # ✅
    return shots * 10
```

#### 2. Incompatible Types

```python
# Error: Incompatible types (expression has type "None", variable has type "str")
name: str = None  # ❌

# Fix: Use Optional
name: Optional[str] = None  # ✅
```

#### 3. Implicit Optional (PEP 484)

```python
# Error: Incompatible default for argument
def greet(name: str = None):  # ❌

# Fix: Use Optional explicitly
def greet(name: Optional[str] = None):  # ✅
```

#### 4. No Attribute on Object

```python
# Error: "object" has no attribute "append"
result = some_dict.get("items")  # Returns Any/object
result.append(item)  # ❌

# Fix: Type cast or check
result: List[Any] = some_dict.get("items", [])
result.append(item)  # ✅
```

## Frontend Type Checking (TypeScript)

### Configuration

**File**: `/frontend/tsconfig.json`

Key settings enabled:
- `strict: true` - All strict type checks enabled
- `noImplicitAny: true` - Errors on implicit any
- `strictNullChecks: true` - Null safety
- `noUnusedLocals: true` - Catch unused variables
- `noImplicitReturns: true` - All code paths must return

### Running TypeScript Checks

```bash
cd frontend

# Type check (no output on success)
tsc --noEmit

# Watch mode for development
tsc --noEmit --watch

# See all errors, not just first 50
tsc --noEmit --maxNodeModuleJsDepth 0
```

### Mixed JavaScript/TypeScript

The frontend currently uses both `.js`/`.jsx` and `.ts`/`.tsx` files.

**TypeScript files** get strict checking:
- `tests/e2e/tests/*.spec.ts`
- Future migrated components

**JavaScript files** allowed via `allowJs: true`:
- Most React components currently in `.jsx`
- Gradually migrate to TypeScript

### Migrating JS to TypeScript

```typescript
// Before (GamePage.jsx)
function GamePage({ gameId }) {
  const [score, setScore] = useState(0);
  return <div>{score}</div>;
}

// After (GamePage.tsx)
interface GamePageProps {
  gameId: string;
}

function GamePage({ gameId }: GamePageProps): JSX.Element {
  const [score, setScore] = useState<number>(0);
  return <div>{score}</div>;
}
```

## Integration with Development Workflow

### Pre-commit Hooks

Add to `.husky/pre-commit`:

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Run type checks before commit
npm run typecheck || exit 1
```

### CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
- name: Type Check Backend
  run: |
    cd backend
    pip install mypy types-requests
    mypy app

- name: Type Check Frontend
  run: |
    cd frontend
    npm run typecheck
```

### VS Code Integration

Add to `.vscode/settings.json`:

```json
{
  "python.linting.mypyEnabled": true,
  "python.linting.enabled": true,
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true
}
```

## Type Checking Stats

### Current Status

**Backend (Python)**:
- Total files: 100+
- Files with type errors: ~30
- Total errors: 874 (down from 958!)
- Clean files: 13 core modules ✅

**Frontend (TypeScript)**:
- Configuration: ✅ Strict mode enabled
- TypeScript files: 3 files (E2E tests)
- JavaScript files: Most components (gradual migration)

### Fully Type-Safe Modules

These modules pass mypy with zero errors:

1. ✅ `app/validators/exceptions.py`
2. ✅ `app/state/shot_state.py`
3. ✅ `app/state/player_manager.py`
4. ✅ `app/domain/player.py`
5. ✅ `app/routes/betting_events.py`
6. ✅ `app/post_hole_analytics.py`
7. ✅ `app/data/wing_point_course_data.py`
8. ✅ `app/middleware/caching.py`
9. ✅ `app/middleware/rate_limiting.py`
10. ✅ `app/database.py`
11. ✅ `app/course_import.py`
12. ✅ `app/services/notification_service_example.py`
13. Partially: `app/routers/courses.py`, `app/routers/sheet_integration.py`

## Best Practices

### 1. Type Everything You Can

```python
# Good: Full typing
def calculate_odds(
    player_skill: float,
    course_difficulty: float,
    weather: Optional[str] = None
) -> Dict[str, float]:
    """Calculate win probability."""
    base_odds = player_skill / course_difficulty
    return {"win": base_odds, "place": base_odds * 1.5}

# Avoid: No types
def calculate_odds(player_skill, course_difficulty, weather=None):  # ❌
    base_odds = player_skill / course_difficulty
    return {"win": base_odds, "place": base_odds * 1.5}
```

### 2. Use Type Aliases for Complex Types

```python
from typing import TypeAlias, Dict, List, Any

# Create reusable type aliases
HoleData: TypeAlias = Dict[str, Any]
CourseData: TypeAlias = List[HoleData]
PlayerStats: TypeAlias = Dict[str, int | float]

def get_course() -> CourseData:
    """Much clearer than List[Dict[str, Any]]"""
    pass
```

### 3. Prefer Specific Types Over Any

```python
# Avoid Any when possible
def process_data(data: Any) -> Any:  # ❌
    return data.get("value")

# Better: Be specific
def process_data(data: Dict[str, int]) -> int:  # ✅
    return data.get("value", 0)
```

### 4. Document with Docstrings AND Types

```python
def import_course(
    name: str,
    state: Optional[str] = None
) -> Optional[CourseImportData]:
    """
    Import course data from external sources.

    Args:
        name: Course name to search for
        state: State abbreviation (optional, helps narrow search)

    Returns:
        CourseImportData if found, None if not found

    Raises:
        HTTPException: If API request fails
    """
    pass
```

### 5. Use Protocols for Duck Typing

```python
from typing import Protocol

class HasScore(Protocol):
    score: int

    def update_score(self, points: int) -> None:
        ...

# Works with any object that has score and update_score
def award_points(player: HasScore, points: int) -> None:
    player.update_score(points)
```

## Troubleshooting

### "Cannot find implementation or library stub"

**Problem**: Third-party library has no type stubs

**Solution**: Install type stubs or ignore

```bash
# Install type stubs
pip install types-requests types-redis

# Or in mypy.ini
[mypy-some_library.*]
ignore_missing_imports = True
```

### "Incompatible types" with SQLAlchemy

**Problem**: SQLAlchemy's dynamic Base class confuses mypy

**Solution**: Already configured in `mypy.ini`

```ini
[mypy-app.models]
ignore_errors = True
```

### Too Many Errors

**Strategy**: Fix incrementally
1. Start with critical modules (validators, domain)
2. Fix files with fewest errors first
3. Add type hints to new code
4. Gradually improve legacy code

## Resources

- [mypy Documentation](https://mypy.readthedocs.io/)
- [Python typing module](https://docs.python.org/3/library/typing.html)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)

## Maintenance

Update this guide when:
- Type checking configuration changes
- New patterns emerge
- Common errors are discovered
- Migration strategies evolve

---

**Last Updated**: 2025-01-23

For questions about type checking, run `npm run typecheck` and see error messages, or check this guide.
