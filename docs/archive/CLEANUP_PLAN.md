# Legacy Code Cleanup Plan

**Goal**: Remove complexity and legacy code now that GameLifecycleService is integrated

---

## Phase 1: Remove Safe Backup Files ✅ (Can do NOW)

### Files to Delete
```bash
backend/tests/test_game_state.py.backup
backend/tests/test_betting_state.py.backup
backend/app/state/betting_state.py.backup
backend/app/game_state.py.backup
```

**Why**: These are backup files from Phase 2-3 consolidation (completed months ago). No longer needed.

**Risk**: None - they're backup files not used by any code

---

## Phase 2: Remove Dual Storage Pattern 🔄 (Can do NOW with caution)

### Current State
Endpoints are storing games in BOTH places:
```python
# Line 1289 - start_game_from_lobby
service._active_games[game_id] = simulation  # NEW
active_games[game_id] = simulation           # OLD (redundant)
```

### What to Remove
1. Remove all `active_games[game_id] = simulation` assignments
2. Keep only `service._active_games[game_id] = simulation`
3. Remove `global active_games` declarations from endpoints

**Affected Lines** in main.py:
- Line 1236: `global active_games` declaration
- Line 1289: `active_games[game_id] = simulation`
- Line 1384: `global active_games` declaration
- Line 1434: `active_games[game_id] = simulation`

**Risk**: Low - service already handles storage, this is just redundancy

---

## Phase 3: Simplify get_or_load_game() 🔄 (Can do NOW)

### Current State
The `get_or_load_game()` function (lines 65-104) is deprecated but still called once.

### Option A: Replace the ONE remaining call
**Line 1702** in `unified_action` endpoint:
```python
# Current (line 1702)
game = get_or_load_game(game_id)

# Replace with
game = get_game_lifecycle_service().get_game(db, game_id)
```

**Then DELETE** `get_or_load_game()` function entirely (lines 65-104)

### Option B: Keep as thin wrapper
Make it call the service:
```python
def get_or_load_game(game_id: str, db: Session = None) -> WolfGoatPigSimulation:
    """DEPRECATED: Wrapper around GameLifecycleService for backward compatibility."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
    return get_game_lifecycle_service().get_game(db, game_id)
```

**Recommendation**: **Option A** - Remove completely, it's only used once

**Risk**: Low - only one callsite to update

---

## Phase 4: Remove Global active_games Dict 🔄 (After Phase 2)

### What to Remove
**Line 63** in main.py:
```python
active_games = {}
```

### Dependencies
Must complete Phase 2 first (remove dual storage)

**Risk**: Low - after Phase 2, nothing uses it

---

## Phase 5: Deal with wgp_simulation ⚠️ (FUTURE - Complex)

### Current State
Global `wgp_simulation` is used in ~18 places for legacy single-game endpoints

### Why Complex
These endpoints expect a global singleton:
```python
# Line 996 - get_game_state
global wgp_simulation
if wgp_simulation:
    return wgp_simulation.game_state
```

### Strategy (Future Work)
1. **Identify** all endpoints using `wgp_simulation`
2. **Migrate** each to accept `game_id` parameter
3. **Update** to use GameLifecycleService
4. **Remove** global instance

**Affected Lines**: 996, 999, 1000, 1443-1446, 1474, 1715, 1923, 2345, 2392, 2445, 2492, 2566, 2870, 2945, 2977, 3096

**Risk**: **HIGH** - major refactor, many endpoints, potential breaking changes

**Recommendation**: **Defer to separate project** - this is Phase 7 material

---

## Immediate Action Plan

### Step 1: Remove Backup Files ✅
```bash
rm backend/tests/test_game_state.py.backup
rm backend/tests/test_betting_state.py.backup
rm backend/app/state/betting_state.py.backup
rm backend/app/game_state.py.backup
```

### Step 2: Remove Dual Storage (5 min) 🔄

**File**: `backend/app/main.py`

**Changes**:
1. **Line 1236**: Remove `global active_games` declaration
2. **Line 1289**: Remove `active_games[game_id] = simulation`
3. **Line 1318**: Remove `global active_games` declaration
4. **Line 1384**: Remove `global active_games` declaration
5. **Line 1434**: Remove `active_games[game_id] = simulation`

Keep only the service storage lines.

### Step 3: Remove get_or_load_game() (2 min) 🔄

**File**: `backend/app/main.py`

1. **Line 1702**: Update unified_action to use service directly
2. **Lines 65-104**: Delete entire `get_or_load_game()` function

### Step 4: Remove active_games Dict (1 min) 🔄

**File**: `backend/app/main.py`

**Line 63**: Delete entire declaration:
```python
# DELETE these lines
# Multi-game management - track multiple concurrent games
# Key: game_id (str), Value: WolfGoatPigSimulation instance
# DEPRECATED: Use GameLifecycleService instead (via get_game_lifecycle_service())
# This will be removed in a future version
active_games = {}
```

---

## Expected Results

### Before Cleanup
- 4 backup files
- Dual storage (service + global dict)
- Deprecated `get_or_load_game()` function
- Global `active_games` dict
- **Complexity**: HIGH

### After Cleanup
- 0 backup files ✅
- Single storage (service only) ✅
- No `get_or_load_game()` function ✅
- No `active_games` dict ✅
- **Complexity**: **REDUCED**

### Lines Removed
- **Backup files**: 4 files
- **Code**: ~100 lines from main.py
  - `active_games = {}` declaration (~5 lines)
  - `get_or_load_game()` function (~40 lines)
  - Dual storage lines (~4 lines)
  - Global declarations (~4 lines)

---

## Risk Assessment

| Phase | Risk Level | Testing Required | Reversibility |
|-------|-----------|------------------|---------------|
| Phase 1 (Backup files) | **None** | None | N/A (backups) |
| Phase 2 (Dual storage) | **Low** | Manual test game creation | Easy (git revert) |
| Phase 3 (get_or_load_game) | **Low** | Test unified_action endpoint | Easy (git revert) |
| Phase 4 (active_games) | **None** | None (unused after Phase 2) | Easy (git revert) |
| Phase 5 (wgp_simulation) | **HIGH** | Comprehensive endpoint testing | **Complex** |

---

## Testing Plan

### After Each Phase
1. **Server restart test**: Verify server starts
2. **Import test**: No import errors
3. **Functionality test**: Create/join game works
4. **Endpoint test**: Test modified endpoints

### Specific Tests
```bash
# Test game creation
POST /games/create

# Test game retrieval
GET /games/{game_id}/state

# Test unified action
POST /wgp/{game_id}/action

# Test game start
POST /games/{game_id}/start
```

---

## Recommendation

**DO NOW** (15 minutes total):
- ✅ Phase 1: Remove backup files (immediate)
- 🔄 Phase 2: Remove dual storage (5 min)
- 🔄 Phase 3: Remove get_or_load_game() (2 min)
- 🔄 Phase 4: Remove active_games dict (1 min)

**DEFER** (Future project):
- ⚠️ Phase 5: Migrate wgp_simulation endpoints (major refactor)

This will:
- Remove ~100 lines of legacy code
- Simplify the codebase significantly
- Maintain full backward compatibility
- Reduce complexity for future developers

**Total time investment**: ~15 minutes
**Complexity reduction**: **HIGH**
**Risk**: **LOW**

---

## Execution Order

```bash
# 1. Remove backup files (0 risk)
rm backend/tests/test_game_state.py.backup
rm backend/tests/test_betting_state.py.backup
rm backend/app/state/betting_state.py.backup
rm backend/app/game_state.py.backup

# 2. Edit main.py (use subagent or manual)
# - Remove dual storage lines
# - Remove get_or_load_game() function
# - Remove active_games declaration

# 3. Test server
# Verify server starts and endpoints work

# 4. Commit
git add -A
git commit -m "chore: remove legacy code after GameLifecycleService integration"
```

Ready to proceed? 🚀
