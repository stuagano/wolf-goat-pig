# Type Check Error Resolution Plan

## Overview
- **Total Errors**: ~~928~~ **0 mypy errors** (RESOLVED as of Jan 2026)
- **Files Affected**: ~~20+ files~~ All clean
- **Strategy**: Fix in priority order, starting with quick wins

> **Status Update (Jan 2026)**: All mypy type errors have been resolved. Running `mypy app startup.py --ignore-missing-imports` returns success with 0 issues.

---

## HIGH Priority - Core Files (622 errors, ~60% of total)

### 1. main.py (478 errors)
**Main Issues:**
- Union types with `WolfGoatPigGame` - need to narrow types or add assertions
- Attribute access on Optional types - need null checks
- Game state dict typing - need proper TypedDict definitions
- `[union-attr]` errors for game.players, game.hole_states, etc.

**Fix Strategy:**
- Add type guards for WolfGoatPigGame checks
- Create TypedDict for game state structures
- Add Optional checks before attribute access

### 2. wolf_goat_pig.py (89 errors)
**Main Issues:**
- Core game class union types
- Missing attribute definitions on class
- Method return types not annotated
- `[no-untyped-def]` for many methods

**Fix Strategy:**
- Add return type annotations to all methods
- Define proper class attributes with types
- Use Protocol or ABC for interface definitions

### 3. startup.py (55 errors)
**Main Issues:**
- SQLAlchemy inspector types
- Database reflection API typing
- `[attr-defined]` for inspector methods

**Fix Strategy:**
- Add type assertions for inspector
- Use cast() for database reflection results

---

## MEDIUM Priority - Service Layer (97 errors)

### 4. badge_engine.py (41 errors)
**Main Issues:**
- `Column[int]` vs `int` type mismatches
- SQLAlchemy ORM type coercion issues
- Need type annotations for local variables

**Fix Strategy:**
- Use cast() for Column value extraction
- Add explicit type annotations with `[var-annotated]`
- Fix arithmetic operations on Column types

### 5. player_service.py (30 errors)
**Main Issues:**
- Database model Optional attributes
- Missing null checks before attribute access
- Return type mismatches

**Fix Strategy:**
- Add null checks for Optional fields
- Use proper return type annotations
- Cast database results appropriately

### 6. statistics_service.py (26 errors)
**Main Issues:**
- `ColumnElement[float]` vs `float` mismatches
- List type incompatibilities
- Missing type annotations

**Fix Strategy:**
- Cast ColumnElement to primitive types
- Fix list comprehension types
- Add return type annotations

---

## LOW Priority - Routers & Utilities (209 errors)

### 7. players.py router (27 errors)
- Response type annotations
- Return value typing
- Quick fixes with proper annotations

### 8. migrations_routes.py (18 errors)
- Database inspection types
- Type assertions needed

### 9. Other files (~80 errors across 13 files)
- seed_courses.py (11 errors)
- courses.py (11 errors)
- badge_routes.py (10 errors)
- course_import.py (9 errors)
- ghin_service.py (12 errors)
- game_lifecycle_service.py (12 errors)
- And others...

---

## Error Categories Reference

| Error Type | Count | Fix |
|------------|-------|-----|
| `[no-untyped-def]` | 107 | Add return type annotations |
| `[name-defined]` | 97 | Add missing imports |
| `[attr-defined]` | 72 | Fix attribute access |
| `[assignment]` | ~90 | Add type casts |
| `[arg-type]` | ~60 | Fix argument types |
| `[union-attr]` | ~50 | Add null checks |
| `[operator]` | 35 | Fix numeric operations |

---

## Execution Plan

### Phase 1: Quick Wins (LOW priority)
1. Fix missing imports across all files
2. Add return type annotations to small files
3. Fix simple type mismatches

### Phase 2: Service Layer (MEDIUM priority)
1. Fix badge_engine.py SQLAlchemy types
2. Fix player_service.py null checks
3. Fix statistics_service.py type coercion

### Phase 3: Core Files (HIGH priority)
1. Create TypedDict definitions for game state
2. Add type guards for WolfGoatPigGame
3. Refactor wolf_goat_pig.py with proper types
4. Update main.py with narrowed types

---

## Progress Tracking

- [x] Phase 1: Quick Wins ✅
- [x] Phase 2: Service Layer ✅
- [x] Phase 3: Core Files ✅
- [x] Final verification: `mypy app --ignore-missing-imports` ✅ **0 errors**
