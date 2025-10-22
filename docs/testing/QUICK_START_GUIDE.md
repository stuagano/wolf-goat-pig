# Testing Remediation - Quick Start Guide

**Get started fixing Wolf Goat Pig testing gaps in 15 minutes**

---

## 🚀 Getting Started Immediately

### Step 1: Choose Your Starting Point (5 minutes)

Based on your role and priorities, pick your entry point:

**For Security-First Approach** → Start with [Auth Testing](#auth-testing-day-1)
**For Game Logic Focus** → Start with [Core Simulation](#core-simulation-week-3)
**For Full Coverage** → Follow the [10-Week Plan](#10-week-roadmap)

### Step 2: Set Up Environment (10 minutes)

```bash
# Clone repo (if not already)
cd wolf-goat-pig

# Install backend dependencies
cd backend
pip install -r requirements.txt
pip install -r requirements-testing.txt
pip install numpy psutil pytest-cov

# Install frontend dependencies
cd ../frontend
npm install
npm install --save-dev jest-axe @testing-library/jest-dom

# Verify setup
cd ../backend && pytest --version
cd ../frontend && npm test -- --version
```

**Success Check**:
- ✅ `pytest --version` shows 7.4.0+
- ✅ `npm test` starts Jest
- ✅ No import errors

---

## 📅 10-Week Roadmap (Visual)

```
WEEK 1-2: FOUNDATION & SECURITY
┌─────────────────────────────────────────────┐
│ ✓ Install dependencies                      │
│ ✓ Create test fixtures                      │
│ ✓ Test all auth components (100% coverage)  │
└─────────────────────────────────────────────┘
        ↓
WEEK 3-4: BACKEND CORE LOGIC
┌─────────────────────────────────────────────┐
│ ✓ Wolf simulation engine (75+ tests)        │
│ ✓ Betting decisions (45+ tests)             │
│ ✓ Scoring & handicap (40+ tests)            │
└─────────────────────────────────────────────┘
        ↓
WEEK 5-6: FRONTEND COMPONENTS
┌─────────────────────────────────────────────┐
│ ✓ Simulation components (60+ tests)         │
│ ✓ Critical hooks (110+ tests)               │
│ ✓ Accessibility audit (30+ components)      │
└─────────────────────────────────────────────┘
        ↓
WEEK 7-8: INTEGRATION & E2E
┌─────────────────────────────────────────────┐
│ ✓ API endpoints (100+ tests)                │
│ ✓ BDD game rules (20+ scenarios)            │
│ ✓ E2E complete flows (10+ tests)            │
└─────────────────────────────────────────────┘
        ↓
WEEK 9-10: PERFORMANCE & VALIDATION
┌─────────────────────────────────────────────┐
│ ✓ Edge cases (63+ tests)                    │
│ ✓ Performance benchmarks                    │
│ ✓ Load testing (50 concurrent users)        │
│ ✓ Final validation & docs                   │
└─────────────────────────────────────────────┘
```

---

## 🎯 Quick Wins (Pick Any)

### Auth Testing (Day 1)

**Impact**: Close critical security gap (0% → 100%)
**Time**: 12 hours
**File**: `frontend/src/components/auth/__tests__/ProtectedRoute.test.js`

```bash
# Create the test file
cd frontend/src/components/auth
mkdir -p __tests__
touch __tests__/ProtectedRoute.test.js

# Copy template from plan (Section: Phase 1, Task 1.4)
# Run tests
npm test ProtectedRoute
```

**Template**:
```javascript
import { render, screen } from '@testing-library/react';
import { ProtectedRoute } from '../ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';

jest.mock('@/hooks/useAuth');

describe('ProtectedRoute', () => {
  it('redirects to login when not authenticated', () => {
    useAuth.mockReturnValue({ isAuthenticated: false });
    render(<ProtectedRoute><div>Protected</div></ProtectedRoute>);
    expect(screen.queryByText('Protected')).not.toBeInTheDocument();
  });

  it('allows access when authenticated', () => {
    useAuth.mockReturnValue({ isAuthenticated: true });
    render(<ProtectedRoute><div>Protected</div></ProtectedRoute>);
    expect(screen.getByText('Protected')).toBeInTheDocument();
  });

  // Add 48 more tests from plan...
});
```

---

### Fix Skipped Backend Tests (Day 1)

**Impact**: Get current tests running
**Time**: 4 hours

```bash
cd backend

# Install missing dependencies
pip install numpy psutil

# Run tests to see current state
pytest tests/test_simulation_unit.py -v

# You should see tests running instead of skipped!
```

**Before**: 27 tests, 20 skipped
**After**: 27 tests, all running

---

### Create Test Fixtures (Day 2)

**Impact**: Foundation for all future tests
**Time**: 8 hours
**Files**: 6 fixture files

```bash
cd backend/tests
mkdir -p fixtures
cd fixtures

# Create each fixture file
touch __init__.py players.py courses.py game_states.py shot_results.py betting_states.py api_fixtures.py
```

**Template** (players.py):
```python
import pytest

@pytest.fixture
def standard_4_players():
    return [
        {"id": 1, "name": "Alice", "handicap": 10, "email": "alice@test.com"},
        {"id": 2, "name": "Bob", "handicap": 15, "email": "bob@test.com"},
        {"id": 3, "name": "Charlie", "handicap": 8, "email": "charlie@test.com"},
        {"id": 4, "name": "Diana", "handicap": 12, "email": "diana@test.com"},
    ]
```

---

## 📊 Track Your Progress

### Daily Checklist

```markdown
## Week 1 - Day 1
- [ ] Install all dependencies (backend + frontend)
- [ ] Run existing tests to establish baseline
- [ ] Create fixtures directory structure
- [ ] Start ProtectedRoute.test.js (20+ tests)

## Week 1 - Day 2
- [ ] Complete ProtectedRoute tests (50+ tests total)
- [ ] Create players.py fixture
- [ ] Create courses.py fixture
- [ ] Start LoginButton.test.js

## Week 1 - Day 3
- [ ] Complete all auth component tests
- [ ] Create remaining fixtures
- [ ] Update conftest.py
- [ ] Run full test suite - verify passing

## Week 1 - Day 4
- [ ] Create AuthContext.test.js
- [ ] Create authFlows.integration.test.js
- [ ] Verify 100% auth coverage
- [ ] Start Week 2 planning

## Week 1 - Day 5
- [ ] Buffer day for fixes
- [ ] Documentation updates
- [ ] Review Phase 1 completion criteria
- [ ] Demo to team
```

### Coverage Tracking

```bash
# Check backend coverage
cd backend
pytest --cov=app --cov-report=term-missing | grep TOTAL

# Check frontend coverage
cd frontend
npm test -- --coverage --watchAll=false | grep "All files"

# Track in spreadsheet or tool:
# Date | Backend % | Frontend % | New Tests | Notes
# 2025-10-21 | 28% | 30% | 0 | Baseline
# 2025-10-22 | 28% | 45% | 50 | Auth tests added
# ...
```

---

## 🛠️ Tools & Commands

### Essential Commands

```bash
# Backend: Run specific test file
pytest tests/test_wolf_simulation_core.py -v

# Backend: Run with coverage
pytest --cov=app --cov-report=html

# Frontend: Run specific test
npm test ProtectedRoute

# Frontend: Watch mode
npm test -- --watch

# Frontend: Coverage
npm test -- --coverage --watchAll=false

# BDD: Run all scenarios
cd tests/bdd/behave && behave

# BDD: Run specific feature
behave features/game_rules_core.feature

# E2E: Run all tests
cd tests/e2e && npx playwright test

# E2E: Run specific test
npx playwright test complete-game-flow

# E2E: Debug mode
npx playwright test --debug
```

### Coverage Reports

```bash
# Generate HTML reports
cd backend && pytest --cov=app --cov-report=html
cd frontend && npm test -- --coverage

# Open in browser
open backend/htmlcov/index.html
open frontend/coverage/lcov-report/index.html
```

---

## 👥 Team Collaboration

### Option 1: Solo Developer (10 weeks)

**Week 1-2**: You handle Foundation & Auth
**Week 3-4**: You handle Backend Core
**Week 5-6**: You handle Frontend Components
**Week 7-8**: You handle Integration
**Week 9-10**: You handle Performance & Validation

### Option 2: 2 Developers (5 weeks)

**Week 1**: Both on Foundation
**Week 2**: Dev 1 → Backend, Dev 2 → Frontend Auth
**Week 3**: Dev 1 → Backend Core, Dev 2 → Frontend Components
**Week 4**: Both on Integration
**Week 5**: Both on Performance & Validation

### Option 3: 3 Developers (3-4 weeks)

**Week 1**: All on Foundation
**Week 2**: Backend Dev, Frontend Dev, QA (BDD prep)
**Week 3**: Continue roles, integrate
**Week 4**: Performance, validation, handoff

---

## 📋 Pre-Flight Checklist

Before starting each phase:

### Phase 1 Ready?
- [ ] Python 3.11+ or 3.12 installed
- [ ] Node.js 18+ installed
- [ ] All dependencies installed (no errors)
- [ ] Existing tests running
- [ ] Git branch created: `feature/testing-remediation`

### Phase 2 Ready?
- [ ] Phase 1 complete (fixtures, auth tests)
- [ ] conftest.py updated
- [ ] Backend coverage baseline measured
- [ ] Simulation code reviewed

### Phase 3 Ready?
- [ ] Phase 2 complete (backend core tests)
- [ ] Frontend test helpers reviewed
- [ ] Component structure understood
- [ ] TypeScript types available

### Phase 4 Ready?
- [ ] Phases 2 & 3 complete
- [ ] API endpoints documented
- [ ] BDD step definitions understood
- [ ] E2E infrastructure working

### Phase 5 Ready?
- [ ] All previous phases complete
- [ ] Coverage near targets
- [ ] Performance baselines measured
- [ ] Load testing infrastructure ready

---

## 🆘 Troubleshooting

### "Tests are still skipped after installing numpy"

```bash
# Ensure numpy is in the right environment
python -c "import numpy; print(numpy.__version__)"

# If that fails, reinstall
pip uninstall numpy
pip install numpy

# Check pytest can find it
pytest --collect-only tests/test_simulation_unit.py
```

### "Frontend tests fail with module not found"

```bash
# Clear cache
rm -rf node_modules
npm install

# Verify Jest config
cat package.json | grep -A 10 "jest"

# Check imports in test file
```

### "Coverage report shows 0%"

```bash
# Backend: Ensure --cov points to right directory
pytest --cov=app --cov-report=term  # Not --cov=.

# Frontend: Ensure coverage config correct
cat package.json | grep -A 5 "coveragePathIgnorePatterns"
```

### "BDD steps not found"

```bash
cd tests/bdd/behave

# Check step files exist
ls steps/

# Run with verbose
behave --verbose

# Check imports in steps/__init__.py
```

---

## 🎉 Quick Wins Summary

**Day 1 Wins**:
1. ✅ All dependencies installed
2. ✅ Baseline coverage measured
3. ✅ First 20 auth tests written

**Week 1 Wins**:
1. ✅ Auth coverage 0% → 100%
2. ✅ Test fixtures created
3. ✅ Infrastructure solid

**Week 2 Wins**:
1. ✅ Backend core 15% → 60%
2. ✅ 120+ new backend tests
3. ✅ Simulation engine tested

**Week 4 Wins**:
1. ✅ Backend 60% → 85%
2. ✅ All critical modules > 90%
3. ✅ 200+ backend tests total

**Week 6 Wins**:
1. ✅ Frontend 30% → 75%
2. ✅ All components tested
3. ✅ Zero a11y violations

**Week 8 Wins**:
1. ✅ Integration complete
2. ✅ API endpoints 90% tested
3. ✅ BDD scenarios passing

**Week 10 Wins**:
1. ✅ 85%+ backend coverage
2. ✅ 80%+ frontend coverage
3. ✅ Production ready!

---

## 📚 Reference Links

- **Full Plan**: [COMPREHENSIVE_TESTING_PLAN.md](./COMPREHENSIVE_TESTING_PLAN.md)
- **Testing Agents**: [/.claude/agents/](../../.claude/agents/)
- **Testing Skills**: [/.claude/skills/](../../.claude/skills/)
- **Project Docs**: [/docs/](../)

---

## 🚦 Status Dashboard

Track your progress:

```
OVERALL PROGRESS: ████░░░░░░ 40%

PHASE 1 (Foundation):        ██████████ 100% ✅
PHASE 2 (Backend Core):      ██████░░░░  60% 🔄
PHASE 3 (Frontend):          ███░░░░░░░  30% 📝
PHASE 4 (Integration):       ░░░░░░░░░░   0% ⏸️
PHASE 5 (Performance):       ░░░░░░░░░░   0% ⏸️

CRITICAL GAPS CLOSED:
✅ Auth Testing (was 0%)
✅ Test Infrastructure
🔄 Simulation Engine (was 15%, now 60%)
📝 API Endpoints (was 10%)
⏸️ BDD Scenarios (10%)

NEXT MILESTONE: Complete Phase 2 (Backend Core to 85%)
```

---

**Ready to start? Pick a Quick Win above and dive in!** 🚀
