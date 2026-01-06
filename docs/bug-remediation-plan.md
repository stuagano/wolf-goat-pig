# Bug Remediation Plan - Wolf Goat Pig

## Executive Summary

Comprehensive analysis identified **17 issues** across the codebase requiring attention. This plan prioritizes fixes by severity and provides step-by-step remediation instructions.

---

## Phase 1: CRITICAL FIXES (Immediate - Days 1-3)

### Step 1.1: Fix Bare Except Clauses in Backend

**Files to fix:**
- `backend/app/wolf_goat_pig.py` (lines 803, 1619)
- `backend/app/main.py` (lines 831, 3708)
- `backend/app/mixins/persistence_mixin.py` (lines 87, 214, 223)

**Action:**
```python
# BEFORE:
except:
    pass

# AFTER:
except (KeyError, ValueError, TypeError) as e:
    logger.warning(f"Error handling state: {e}")
```

**Verification:** Run `grep -r "except:" backend/app/ --include="*.py" | grep -v "except Exception"`

---

### Step 1.2: Fix Database Session Management

**File:** `backend/app/mixins/persistence_mixin.py`

**Action:**
1. Replace bare excepts with specific exception handling
2. Add proper logging for rollback/close failures
3. Ensure connections are always properly closed

```python
# In close_db_session():
except Exception as e:
    logger.error(f"Failed to close DB session: {e}")
    raise  # Or handle appropriately
```

---

## Phase 2: HIGH PRIORITY FIXES (Week 1)

### Step 2.1: Add Error Boundaries to React Components

**Files:**
- `frontend/src/App.js`
- `frontend/src/pages/SimpleScorekeeperPage.js`

**Action:**
1. Create an ErrorBoundary component
2. Wrap main game components with error boundary
3. Add fallback UI for error states

```jsx
// Create frontend/src/components/common/ErrorBoundary.jsx
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

---

### Step 2.2: Fix Array Operations Bounds Checking

**File:** `frontend/src/components/game/SimpleScorekeeper.jsx` (lines 637-642)

**Action:**
```jsx
// BEFORE:
team1Net = Math.min(...team1.map(id => netScores[id]));

// AFTER:
const team1Scores = team1.map(id => netScores[id]).filter(s => s !== undefined);
team1Net = team1Scores.length > 0 ? Math.min(...team1Scores) : 0;
```

---

### Step 2.3: Complete TODO Tests for Betting

**File:** `frontend/src/components/game/__tests__/SimpleScorekeeper.betting.test.js`

**Action:**
1. Implement offer/accept flow test (line 184)
2. Add wager button interaction tests (line 202)
3. Remove `.skip` and `TODO` comments after implementation

---

### Step 2.4: Fix Type Safety Issues

**File:** `backend/app/main.py`

**Action:**
1. Replace `# type: ignore` with proper type annotations
2. Create TypedDict for complex game state objects
3. Add Union types for nullable fields

```python
from typing import TypedDict, Optional, List

class GameState(TypedDict):
    current_hole: int
    scores: List[int]
    players: List[PlayerInfo]
```

---

## Phase 3: MEDIUM PRIORITY (Week 2)

### Step 3.1: Refactor SimpleScorekeeper State Management

**File:** `frontend/src/components/game/SimpleScorekeeper.jsx`

**Problem:** 50+ useState hooks making component hard to maintain

**Action:**
1. Create a game state reducer:

```jsx
// frontend/src/components/game/gameReducer.js
const initialState = {
  currentHole: 1,
  teamMode: 'partners',
  teams: { team1: [], team2: [] },
  captain: null,
  bets: {},
  scores: {}
};

function gameReducer(state, action) {
  switch (action.type) {
    case 'SET_CURRENT_HOLE':
      return { ...state, currentHole: action.payload };
    case 'UPDATE_SCORE':
      return { ...state, scores: { ...state.scores, ...action.payload } };
    // ... other actions
  }
}
```

2. Replace useState calls with useReducer
3. Extract betting logic to custom hook `useBettingState()`

---

### Step 3.2: Fix ESLint Dependency Issues

**File:** `frontend/src/components/game/SimpleScorekeeper.jsx` (line 511)

**Action:**
1. Review all `eslint-disable` comments
2. Either fix the dependency arrays or document why the disable is necessary
3. Move disable comment BEFORE the offending line with explanation

```jsx
// BEFORE (incorrect):
}, [currentHoleBettingEvents]);
// eslint-disable-next-line react-hooks/exhaustive-deps

// AFTER (correct):
// We intentionally only run this when betting events change,
// not when derived values update, to prevent infinite loops
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [currentHoleBettingEvents]);
```

---

### Step 3.3: Add API Error Handling

**File:** `frontend/src/App.js` (lines 65-72)

**Action:**
```jsx
// BEFORE:
fetch(`${API_URL}/rules`)
  .then(res => res.json())
  .then(data => {})
  .catch(err => console.warn('Could not load rules:', err));

// AFTER:
fetch(`${API_URL}/rules`)
  .then(res => {
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  })
  .then(data => {
    setRules(data);
    setRulesLoaded(true);
  })
  .catch(err => {
    console.error('Failed to load rules:', err);
    setRulesError(err.message);
    // Show user-friendly error notification
  });
```

---

### Step 3.4: Implement Structured Logging

**Action:**
1. Create a logging utility:

```jsx
// frontend/src/utils/logger.js
const LOG_LEVELS = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 };
const currentLevel = process.env.NODE_ENV === 'production' ? LOG_LEVELS.WARN : LOG_LEVELS.DEBUG;

export const logger = {
  debug: (...args) => currentLevel <= LOG_LEVELS.DEBUG && console.log('[DEBUG]', ...args),
  info: (...args) => currentLevel <= LOG_LEVELS.INFO && console.info('[INFO]', ...args),
  warn: (...args) => currentLevel <= LOG_LEVELS.WARN && console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};
```

2. Replace console.log/warn/error with logger calls

---

## Phase 4: LOW PRIORITY (Week 3+)

### Step 4.1: Clean Up Unused Variables

**File:** `frontend/src/components/game/SimpleScorekeeper.jsx`

**Action:**
1. Search for `// eslint-disable-next-line no-unused-vars`
2. Either use the variable or remove it entirely
3. Remove the eslint-disable comment

---

### Step 4.2: Improve PropTypes Specificity

**File:** `frontend/src/components/game/SimpleScorekeeper.jsx` (lines 2821-2834)

**Action:**
```jsx
// BEFORE:
initialHoleHistory: PropTypes.arrayOf(PropTypes.object),

// AFTER:
initialHoleHistory: PropTypes.arrayOf(PropTypes.shape({
  hole: PropTypes.number.isRequired,
  scores: PropTypes.objectOf(PropTypes.number),
  bets: PropTypes.arrayOf(PropTypes.object),
  timestamp: PropTypes.string
})),
```

---

### Step 4.3: Add Backend Type Validation

**File:** `backend/app/routers/sheet_integration.py`

**Action:**
```python
def safe_float(value, default=0.0):
    """Safely convert value to float with bounds checking."""
    try:
        result = float(value)
        if result < -1e10 or result > 1e10:
            return default
        return result
    except (ValueError, TypeError):
        return default
```

---

## Testing Checklist

After each phase, verify:

- [ ] `npm run build` - No build errors
- [ ] `npm run test` - All tests pass
- [ ] `npm run lint` - No new lint warnings
- [ ] `npm run typecheck` - No type errors (if applicable)
- [ ] Backend: `pytest backend/` - All tests pass

---

## Issue Tracking Table

| # | Issue | Severity | File | Status |
|---|-------|----------|------|--------|
| 1 | Bare except clauses | Critical | wolf_goat_pig.py | ⬜ TODO |
| 2 | DB session leaks | Critical | persistence_mixin.py | ⬜ TODO |
| 3 | Type ignoring | High | main.py | ⬜ TODO |
| 4 | Array bounds | High | SimpleScorekeeper.jsx | ⬜ TODO |
| 5 | TODO tests | High | betting.test.js | ⬜ TODO |
| 6 | Missing error handling | Medium | App.js | ⬜ TODO |
| 7 | ESLint deps | Medium | SimpleScorekeeper.jsx | ⬜ TODO |
| 8 | Dict defaults | Medium | Various | ⬜ TODO |
| 9 | No logging | Medium | SimpleScorekeeper.jsx | ⬜ TODO |
| 10 | DB null checks | Medium | ghin_service.py | ⬜ TODO |
| 11 | No error boundary | Medium | SimpleScorekeeperPage.js | ⬜ TODO |
| 12 | State complexity | Medium | SimpleScorekeeper.jsx | ⬜ TODO |
| 13 | Vague PropTypes | Low | SimpleScorekeeper.jsx | ⬜ TODO |
| 14 | Mobile CSS | Low | App.js | ⬜ TODO |
| 15 | Test coverage | Medium | Various | ⬜ TODO |
| 16 | Unused vars | Low | SimpleScorekeeper.jsx | ⬜ TODO |
| 17 | Type coercion | Medium | sheet_integration.py | ⬜ TODO |

---

## Estimated Effort

| Phase | Issues | Estimated Time |
|-------|--------|----------------|
| Phase 1 - Critical | 2 | 4-6 hours |
| Phase 2 - High | 4 | 8-12 hours |
| Phase 3 - Medium | 4 | 8-12 hours |
| Phase 4 - Low | 4 | 4-6 hours |
| **Total** | **17** | **24-36 hours** |

---

## Next Steps

1. Start with Phase 1 critical fixes immediately
2. Create feature branches for each phase
3. Run full test suite after each fix
4. Code review before merging
5. Update this document as issues are resolved
