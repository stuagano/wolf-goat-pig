# Database Session Management Guide

## Problem

The codebase has inconsistent database session management, with many endpoints manually calling `db.close()` in `finally` blocks. This is problematic because:

1. **FastAPI dependency injection already manages session lifecycle** - When you use `db: Session = Depends(database.get_db)`, FastAPI automatically closes the session
2. **Double-closing can cause issues** - Manually closing an already-closed session can lead to errors
3. **Inconsistent patterns** - Makes the code harder to maintain

## Three Patterns of Database Session Management

### ✅ Pattern 1: FastAPI Dependency Injection (Recommended for Endpoints)

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db

@app.get("/players")
def get_players(db: Session = Depends(get_db)):
    """
    FastAPI automatically:
    1. Creates session before function
    2. Passes it as db parameter
    3. Closes it after function returns
    """
    players = db.query(PlayerProfile).all()
    return players
    # ✅ NO finally block needed - FastAPI handles cleanup
```

**DO NOT** add `finally: db.close()` to these endpoints!

### ✅ Pattern 2: Context Manager (Recommended for Background Tasks)

```python
from app.database import get_isolated_session

def background_task():
    """For background tasks, scheduled jobs, or utility functions"""
    with get_isolated_session() as db:
        player = db.query(PlayerProfile).filter_by(id=1).first()
        player.score += 10
        db.commit()
        # ✅ Session automatically closed when exiting 'with' block
```

### ✅ Pattern 3: Manual Management (Only When Necessary)

```python
from app.database import SessionLocal

def complex_operation():
    """Only use when you need explicit control"""
    db = SessionLocal()
    try:
        # Do work
        result = db.query(Player).all()
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()  # ✅ MUST close manually when creating session manually
```

## Migration Strategy

### Step 1: Identify Endpoints Using Depends

Run this to find all endpoints that use FastAPI dependency injection:

```bash
grep -n "db: Session = Depends" app/main.py
```

### Step 2: Remove Unnecessary finally Blocks

For each endpoint found in Step 1, remove the `finally: db.close()` block:

**Before:**
```python
@app.get("/endpoint")
def endpoint(db: Session = Depends(get_db)):
    try:
        return db.query(Model).all()
    finally:
        db.close()  # ❌ Remove this
```

**After:**
```python
@app.get("/endpoint")
def endpoint(db: Session = Depends(get_db)):
    return db.query(Model).all()  # ✅ Clean and simple
```

### Step 3: Convert Manual SessionLocal to Context Managers

**Before:**
```python
def utility_function():
    db = SessionLocal()
    try:
        result = db.query(Model).all()
        return result
    finally:
        db.close()
```

**After:**
```python
def utility_function():
    with get_isolated_session() as db:
        result = db.query(Model).all()
        db.commit()  # Explicit commit when needed
        return result
```

## Quick Reference

| Scenario | Pattern | Close Session? |
|----------|---------|----------------|
| FastAPI endpoint | `Depends(get_db)` | ❌ No - FastAPI handles it |
| Background task | `with get_isolated_session()` | ❌ No - context manager handles it |
| Manual control needed | `db = SessionLocal()` + try/finally | ✅ Yes - you must close manually |

## Common Mistakes

### ❌ Mistake 1: Closing Depends() Sessions
```python
@app.get("/endpoint")
def endpoint(db: Session = Depends(get_db)):
    try:
        return result
    finally:
        db.close()  # ❌ Don't do this!
```

### ❌ Mistake 2: Forgetting to Close Manual Sessions
```python
def utility():
    db = SessionLocal()  # ❌ Never closed!
    return db.query(Model).all()
```

### ❌ Mistake 3: Not Using Context Managers
```python
# ❌ Manual management when context manager would be better
db = SessionLocal()
try:
    result = db.query(Model).all()
finally:
    db.close()

# ✅ Use context manager instead
with get_isolated_session() as db:
    result = db.query(Model).all()
```

## Automated Fix Script

To automatically remove unnecessary `db.close()` calls from endpoints using `Depends`:

```bash
python fix_db_close.py
```

This will:
1. Identify all endpoints with `db: Session = Depends(get_db)`
2. Remove their `finally: db.close()` blocks
3. Preserve manual session management where appropriate

## Testing After Migration

After removing unnecessary `db.close()` calls:

1. Run unit tests: `pytest tests/`
2. Check for session leaks: Monitor connection pool size
3. Test under load: Ensure no "connection pool exhausted" errors

## Further Reading

- [FastAPI Dependencies Documentation](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [Context Managers in Python](https://docs.python.org/3/library/contextlib.html)
