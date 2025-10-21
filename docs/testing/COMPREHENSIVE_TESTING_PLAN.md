# Wolf Goat Pig - Comprehensive Testing Remediation Plan

**Version**: 1.0
**Date**: 2025-10-21
**Status**: Ready for Execution
**Estimated Duration**: 10 weeks
**Target Coverage**: 85%+ Backend | 80%+ Frontend | 90%+ Rules

---

## Executive Summary

This plan addresses the critical testing gaps identified in the Wolf Goat Pig project, taking test coverage from **~25-35%** to **80-90%** across all areas. The plan is structured in 5 phases over 10 weeks, prioritizing security-critical components, core game logic, and rule validation.

### Critical Gaps Addressed:
- ✅ Backend core simulation engine (3,868 untested lines)
- ✅ Frontend authentication (0% coverage)
- ✅ API endpoints (90% untested)
- ✅ Game rules validation (missing scoring, handicaps)
- ✅ Frontend simulation components (TypeScript)

### Key Metrics:
- **Estimated Effort**: 400-500 hours total
- **New Test Files**: 25-30 files
- **New Tests**: 800-1000+ individual tests
- **BDD Scenarios**: 50+ new scenarios

---

## Timeline Overview

```
Week 1-2:  PHASE 1 - Foundation & Critical Security
Week 3-4:  PHASE 2 - Core Game Logic (Backend)
Week 5-6:  PHASE 3 - Frontend Components & Hooks
Week 7-8:  PHASE 4 - Integration & E2E
Week 9-10: PHASE 5 - Polish, Performance & Validation
```

**Milestone Cadence**: End of each phase (bi-weekly demos/reviews)

---

## Phase 1: Foundation & Critical Security (Weeks 1-2)

**Goal**: Fix test infrastructure, achieve 100% auth coverage, set up proper testing foundation

### Week 1: Infrastructure & Dependencies

#### Task 1.1: Fix Test Dependencies ⏱️ 4 hours
**Owner**: DevOps/Backend Lead

```bash
# Backend dependencies
cd backend
pip install numpy psutil memory-profiler line-profiler
pip install -r requirements-testing.txt

# Verify installations
pytest --version
python -c "import numpy; print(numpy.__version__)"

# Frontend dependencies (if missing)
cd frontend
npm install --save-dev jest-axe @testing-library/jest-dom
```

**Acceptance Criteria**:
- ✅ All skipped tests now run (no import errors)
- ✅ pytest runs without dependency errors
- ✅ Coverage reporting works

**Deliverables**:
- Updated requirements.txt with all dependencies
- Documentation of required versions

---

#### Task 1.2: Create Comprehensive Test Fixtures ⏱️ 8 hours
**Owner**: Backend Lead

**Files to Create**:
```
backend/tests/fixtures/
├── __init__.py
├── players.py          # Player fixtures (4/5/6 player setups)
├── courses.py          # Course and hole fixtures
├── game_states.py      # Game state templates
├── shot_results.py     # Shot result scenarios
├── betting_states.py   # Betting state templates
└── api_fixtures.py     # API request/response fixtures
```

**Example Content** (players.py):
```python
import pytest

@pytest.fixture
def standard_4_players():
    """Standard 4-player setup for testing"""
    return [
        {"id": 1, "name": "Alice", "handicap": 10, "email": "alice@test.com"},
        {"id": 2, "name": "Bob", "handicap": 15, "email": "bob@test.com"},
        {"id": 3, "name": "Charlie", "handicap": 8, "email": "charlie@test.com"},
        {"id": 4, "name": "Diana", "handicap": 12, "email": "diana@test.com"},
    ]

@pytest.fixture
def varied_handicaps():
    """Players with varied handicaps for testing edge cases"""
    return [
        {"id": 1, "name": "Scratch", "handicap": 0},
        {"id": 2, "name": "Mid", "handicap": 10},
        {"id": 3, "name": "High", "handicap": 18},
        {"id": 4, "name": "Plus", "handicap": -2},
    ]

@pytest.fixture
def test_course():
    """18-hole test course with varied difficulties"""
    return {
        "id": 1,
        "name": "Test Course",
        "holes": [
            {"number": i, "par": [4,4,3,5,4,3,4,5,4][i%9],
             "stroke_index": i, "distance": 300 + i*20}
            for i in range(1, 19)
        ]
    }
```

**Acceptance Criteria**:
- ✅ All common test scenarios have reusable fixtures
- ✅ Fixtures documented with docstrings
- ✅ conftest.py updated to auto-load fixtures

**Deliverables**:
- 6 fixture files with comprehensive scenarios
- Updated conftest.py

---

#### Task 1.3: Frontend Test Utilities Expansion ⏱️ 4 hours
**Owner**: Frontend Lead

**Enhance** `frontend/src/__tests__/utils/testHelpers.js`:

```javascript
// Add to existing testHelpers.js

// Game state builders
export const createMockGameState = (overrides = {}) => ({
  game_id: 1,
  current_hole: 1,
  players: createMockPlayers(4),
  game_phase: 'regular',
  base_wager: 1,
  teams: { type: 'pending' },
  hole_state: createMockHoleState(),
  ...overrides
});

// API response factories
export const createApiSuccess = (data) => ({
  ok: true,
  status: 200,
  json: async () => data,
});

export const createApiError = (status, message) => ({
  ok: false,
  status,
  json: async () => ({ error: message }),
});

// User flow helpers
export const completePartnershipFlow = async (user, screen, partnerName) => {
  const partnerButton = await screen.findByRole('button', {
    name: new RegExp(partnerName, 'i')
  });
  await user.click(partnerButton);

  const confirmButton = await screen.findByRole('button', {
    name: /confirm/i
  });
  await user.click(confirmButton);
};
```

**Acceptance Criteria**:
- ✅ Game state builders available
- ✅ API mocking utilities enhanced
- ✅ User flow helpers for common actions

**Deliverables**:
- Enhanced testHelpers.js (~800 lines)

---

### Week 2: Critical Security Testing

#### Task 1.4: Authentication Component Tests ⏱️ 12 hours
**Owner**: Frontend Lead
**CRITICAL**: 0% coverage → 100% coverage

**Files to Create**:
```
frontend/src/components/auth/__tests__/
├── ProtectedRoute.test.js       # 240 lines component → 50+ tests
├── LoginButton.test.js          # 20+ tests
├── LogoutButton.test.js         # 20+ tests
├── Profile.test.js              # 25+ tests
├── AuthContext.test.js          # 40+ tests
└── authFlows.integration.test.js # 30+ integration tests
```

**Test Coverage Requirements**:

**ProtectedRoute.test.js** (HIGHEST PRIORITY):
```javascript
describe('ProtectedRoute', () => {
  it('redirects to login when not authenticated', async () => {
    // Test with mock auth state = null
  });

  it('allows access when authenticated', async () => {
    // Test with valid auth token
  });

  it('handles expired tokens', async () => {
    // Test token expiration redirect
  });

  it('preserves intended route after login', async () => {
    // Test redirect back to original URL
  });

  it('handles loading states', async () => {
    // Test loading spinner while checking auth
  });

  // 45+ more tests for all edge cases
});
```

**LoginButton.test.js**:
```javascript
describe('LoginButton', () => {
  it('initiates Auth0 login flow', async () => {
    const { user } = renderWithAuth(<LoginButton />);
    const loginBtn = screen.getByRole('button', { name: /log in/i });
    await user.click(loginBtn);
    expect(mockAuth0.loginWithRedirect).toHaveBeenCalled();
  });

  it('disables during login process', async () => {
    // Test disabled state
  });

  it('shows error on login failure', async () => {
    // Test error handling
  });

  // 17+ more tests
});
```

**AuthContext.test.js**:
```javascript
describe('AuthContext', () => {
  it('provides authentication state to children', () => {
    // Test context provider
  });

  it('handles token refresh', async () => {
    // Test automatic token refresh
  });

  it('clears state on logout', async () => {
    // Test logout cleanup
  });

  it('persists auth state to localStorage', () => {
    // Test persistence
  });

  // 36+ more tests
});
```

**authFlows.integration.test.js**:
```javascript
describe('Complete Auth Flows', () => {
  it('completes full login → protected route → logout flow', async () => {
    // End-to-end auth flow test
  });

  it('handles session timeout gracefully', async () => {
    // Test session expiration during usage
  });

  it('refreshes token before expiration', async () => {
    // Test proactive token refresh
  });

  // 27+ more integration tests
});
```

**Acceptance Criteria**:
- ✅ 100% coverage of all auth components
- ✅ All security paths tested (success, failure, timeout)
- ✅ Integration tests cover full auth workflows
- ✅ Zero accessibility violations (use jest-axe)

**Deliverables**:
- 6 test files, 185+ tests total
- Auth component coverage: 100%

---

#### Task 1.5: Backend Core Fixtures & conftest.py ⏱️ 6 hours
**Owner**: Backend Lead

**Update** `backend/tests/conftest.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.main import app
from fastapi.testclient import TestClient

# Database fixture
@pytest.fixture(scope="session")
def test_db_engine():
    """Create in-memory test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_db_engine):
    """Create a new database session for each test"""
    TestingSessionLocal = sessionmaker(bind=test_db_engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()

# API client fixture
@pytest.fixture
def api_client(db_session):
    """FastAPI test client with database"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# Load all fixtures from fixtures/
pytest_plugins = [
    "tests.fixtures.players",
    "tests.fixtures.courses",
    "tests.fixtures.game_states",
    "tests.fixtures.shot_results",
    "tests.fixtures.betting_states",
]
```

**Acceptance Criteria**:
- ✅ All tests can use shared fixtures
- ✅ Database fixtures provide clean state per test
- ✅ API client fixture available for endpoint testing

**Deliverables**:
- Updated conftest.py with comprehensive fixtures

---

### Phase 1 Deliverables Summary

**Completed by End of Week 2**:
- ✅ All test dependencies installed
- ✅ 6 backend fixture files created
- ✅ Enhanced frontend test utilities
- ✅ 6 auth test files (185+ tests)
- ✅ 100% auth component coverage
- ✅ Updated conftest.py

**Coverage Improvement**:
- Frontend Auth: 0% → **100%**
- Test Infrastructure: **Complete**

**Hours Invested**: ~34 hours

---

## Phase 2: Core Game Logic (Backend) (Weeks 3-4)

**Goal**: Test core simulation engine, betting logic, and scoring

### Week 3: Simulation Engine Core

#### Task 2.1: Wolf Simulation Core Tests ⏱️ 20 hours
**Owner**: Backend Lead
**CRITICAL**: 3,868 lines, 15% → 95% coverage

**File to Create**: `backend/tests/test_wolf_simulation_core.py`

**Test Structure**:
```python
class TestWolfSimulationCore:
    """Comprehensive testing of wolf_goat_pig_simulation.py"""

    # Game Initialization (10 tests)
    def test_game_initialization_4_players(self, standard_4_players, test_course)
    def test_game_initialization_5_players(self, standard_5_players, test_course)
    def test_game_initialization_6_players(self, standard_6_players, test_course)
    def test_game_initialization_invalid_player_count(self)
    def test_game_initialization_missing_course(self)
    # ... 5 more initialization tests

    # Captain Rotation (8 tests)
    def test_captain_rotation_4_players(self)
    def test_captain_rotation_5_players(self)
    def test_captain_rotation_wraps_after_18_holes(self)
    # ... 5 more rotation tests

    # Partnership Formation (15 tests)
    def test_captain_chooses_partner_wolf_format(self)
    def test_captain_sees_all_tee_shots_before_deciding(self)
    def test_partnership_accept_flow(self)
    def test_partnership_decline_auto_solo(self)
    def test_partnership_strategic_timing(self)
    # ... 10 more partnership tests

    # Solo Play (12 tests)
    def test_captain_goes_solo_immediately(self)
    def test_solo_after_seeing_poor_tee_shots(self)
    def test_solo_vs_three_opponents(self)
    def test_solo_wager_doubling(self)
    # ... 8 more solo tests

    # Shot Simulation (20 tests)
    def test_drive_simulation_by_handicap(self)
    def test_approach_shot_accuracy(self)
    def test_putting_make_percentage(self)
    def test_lie_progression_fairway_to_green(self)
    # ... 16 more shot simulation tests

    # Game Progression (10 tests)
    def test_complete_18_hole_game(self)
    def test_hole_advancement_resets_state(self)
    def test_phase_transition_vinnie_variation(self)
    # ... 7 more progression tests

    # Total: 75+ tests
```

**Acceptance Criteria**:
- ✅ All major simulation methods tested
- ✅ Wolf/Goat/Pig formats differentiated
- ✅ Shot simulation accuracy validated
- ✅ 18-hole game completion tested
- ✅ Coverage: 3,868 lines from 15% → 95%

**Deliverables**:
- test_wolf_simulation_core.py (75+ tests, ~1,200 lines)

---

#### Task 2.2: Betting Decisions Tests ⏱️ 16 hours
**Owner**: Backend Lead

**File to Create**: `backend/tests/test_betting_decisions.py`

**Test Structure**:
```python
class TestBettingDecisions:
    """All betting decision logic and rules"""

    # Double Mechanics (12 tests)
    def test_double_offer_line_of_scrimmage(self)
    def test_double_accept_wager_increase(self)
    def test_double_decline_forfeit_hole(self)
    def test_redouble_mechanics(self)
    def test_ping_pong_escalation(self)
    # ... 7 more double tests

    # Special Rules (15 tests)
    def test_float_invocation_once_per_round(self)
    def test_float_doubles_base_wager(self)
    def test_option_auto_trigger_when_goat(self)
    def test_duncan_captain_solo_3_for_2(self)
    def test_tunkarri_aardvark_solo_3_for_2(self)
    # ... 10 more special rule tests

    # Carry-Over (8 tests)
    def test_carry_over_activation_on_tie(self)
    def test_carry_over_resolution_next_hole(self)
    def test_multiple_consecutive_carry_overs(self)
    # ... 5 more carry-over tests

    # Betting Opportunities (10 tests)
    def test_betting_opportunity_detection_lead_change(self)
    def test_risk_assessment_calculation(self)
    def test_no_opportunity_when_wagering_closed(self)
    # ... 7 more opportunity tests

    # Total: 45+ tests
```

**Acceptance Criteria**:
- ✅ All betting rules tested
- ✅ Special rules (Float, Option, Duncan, Tunkarri) validated
- ✅ Carry-over mechanics work correctly
- ✅ Betting opportunities detected accurately

**Deliverables**:
- test_betting_decisions.py (45+ tests, ~900 lines)

---

#### Task 2.3: Scoring & Handicap Tests ⏱️ 12 hours
**Owner**: Backend Lead

**File to Create**: `backend/tests/test_scoring_and_handicap.py`

**Test Structure**:
```python
class TestScoringAndHandicap:
    """Scoring calculations and handicap application"""

    # Net Score Calculation (10 tests)
    def test_net_score_with_strokes(self, varied_handicaps)
    def test_stroke_allocation_by_hole_difficulty(self)
    def test_half_stroke_scenarios(self)
    def test_maximum_hole_score_limits(self)
    # ... 6 more net score tests

    # Best Ball Scoring (12 tests)
    def test_best_ball_2v2_teams(self)
    def test_best_ball_solo_vs_team(self)
    def test_team_best_score_selection(self)
    # ... 9 more best ball tests

    # Point Distribution (10 tests)
    def test_partnership_win_point_distribution(self)
    def test_solo_win_double_payout(self)
    def test_solo_loss_double_penalty(self)
    def test_karl_marx_unequal_teams(self)
    # ... 6 more distribution tests

    # Handicap System (8 tests)
    def test_course_handicap_calculation(self)
    def test_playing_handicap_with_esc(self)
    def test_handicap_differential_over_18(self)
    # ... 5 more handicap tests

    # Total: 40+ tests
```

**Acceptance Criteria**:
- ✅ Gross → Net → Best Ball → Points flow validated
- ✅ Handicap strokes correctly applied
- ✅ Karl Marx Rule point distribution accurate
- ✅ Solo player double payouts/penalties correct

**Deliverables**:
- test_scoring_and_handicap.py (40+ tests, ~800 lines)

---

### Week 4: Services & Domain Logic

#### Task 2.4: Shot Result Domain Tests ⏱️ 10 hours
**Owner**: Backend Lead

**File to Create**: `backend/tests/test_shot_result_domain.py`

**Coverage**: shot_result.py (389 lines, 0% → 95%)

```python
class TestShotResultDomain:
    """Test domain/shot_result.py"""

    # ShotResult Validation (8 tests)
    def test_shot_result_creation_valid(self)
    def test_shot_result_validation_errors(self)
    def test_shot_result_serialization(self)
    # ... 5 more validation tests

    # Position Quality (7 tests)
    def test_position_quality_calculation(self)
    def test_scoring_probability_from_position(self)
    def test_strategic_implications(self)
    # ... 4 more quality tests

    # Shot Analysis (10 tests)
    def test_shot_range_analysis(self)
    def test_partnership_value_assessment(self)
    def test_lie_type_enum_validation(self)
    # ... 7 more analysis tests

    # Total: 25+ tests
```

**Deliverables**:
- test_shot_result_domain.py (25+ tests, ~500 lines)

---

#### Task 2.5: Team Formation Service Tests ⏱️ 8 hours
**Owner**: Backend Lead

**File to Create**: `backend/tests/test_team_formation_service.py`

**Coverage**: team_formation_service.py (200+ lines, 0% → 95%)

```python
class TestTeamFormationService:
    """Test services/team_formation_service.py"""

    # Random Team Generation (8 tests)
    def test_random_teams_4_players(self)
    def test_random_teams_8_players(self)
    def test_random_teams_odd_players(self)
    def test_team_rotation_scenarios(self)
    # ... 4 more generation tests

    # Handicap Balancing (7 tests)
    def test_handicap_balanced_teams(self)
    def test_seeded_randomization_reproducible(self)
    # ... 5 more balancing tests

    # Total: 15+ tests
```

**Deliverables**:
- test_team_formation_service.py (15+ tests, ~350 lines)

---

### Phase 2 Deliverables Summary

**Completed by End of Week 4**:
- ✅ test_wolf_simulation_core.py (75+ tests)
- ✅ test_betting_decisions.py (45+ tests)
- ✅ test_scoring_and_handicap.py (40+ tests)
- ✅ test_shot_result_domain.py (25+ tests)
- ✅ test_team_formation_service.py (15+ tests)

**Coverage Improvement**:
- wolf_goat_pig_simulation.py: 15% → **95%**
- shot_result.py: 0% → **95%**
- team_formation_service.py: 0% → **95%**
- Betting logic: **100%**
- Scoring logic: **100%**

**Total New Tests**: 200+ tests
**Hours Invested**: ~66 hours

---

## Phase 3: Frontend Components & Hooks (Weeks 5-6)

**Goal**: Test critical frontend components, hooks, and user flows

### Week 5: Simulation Components

#### Task 3.1: SimulationDecisionPanel Tests ⏱️ 14 hours
**Owner**: Frontend Lead
**CRITICAL**: 434 lines TypeScript, 0% → 100%

**File to Create**: `frontend/src/components/simulation/__tests__/SimulationDecisionPanel.test.tsx`

```typescript
describe('SimulationDecisionPanel', () => {
  // Wolf Decision Rendering (10 tests)
  it('renders wolf decision options when player is wolf')
  it('disables decision buttons when not player turn')
  it('shows partner selection UI when choosing partner')
  it('displays current pot amount')
  // ... 6 more rendering tests

  // User Interactions (12 tests)
  it('calls onDecision when choosing lone wolf')
  it('calls onDecision with partner selection')
  it('handles double offer interaction')
  it('handles float invocation')
  // ... 8 more interaction tests

  // Edge Cases (8 tests)
  it('handles missing game state gracefully')
  it('shows error for invalid decisions')
  it('handles network errors')
  // ... 5 more edge case tests

  // Accessibility (5 tests)
  it('has no axe violations')
  it('has proper ARIA labels')
  it('supports keyboard navigation')
  // ... 2 more a11y tests

  // Total: 35+ tests
});
```

**Acceptance Criteria**:
- ✅ 100% coverage of 434-line component
- ✅ All decision types tested (lone wolf, partnership, double)
- ✅ User interactions validated
- ✅ Zero accessibility violations

**Deliverables**:
- SimulationDecisionPanel.test.tsx (35+ tests, ~700 lines)

---

#### Task 3.2: HoleVisualization Tests ⏱️ 12 hours
**Owner**: Frontend Lead
**CRITICAL**: 351 lines TypeScript, 0% → 100%

**File to Create**: `frontend/src/components/simulation/__tests__/HoleVisualization.test.tsx`

```typescript
describe('HoleVisualization', () => {
  // Rendering (10 tests)
  it('renders hole information correctly')
  it('displays all ball positions')
  it('shows distance to pin for each player')
  it('highlights current player')
  // ... 6 more rendering tests

  // Calculations (8 tests)
  it('calculates positions accurately')
  it('shows line of scrimmage correctly')
  it('displays relative distances')
  // ... 5 more calculation tests

  // Interactive Elements (7 tests)
  it('allows clicking player positions')
  it('shows position details on hover')
  // ... 5 more interaction tests

  // Total: 25+ tests
});
```

**Deliverables**:
- HoleVisualization.test.tsx (25+ tests, ~500 lines)

---

#### Task 3.3: GamePage Expansion ⏱️ 10 hours
**Owner**: Frontend Lead

**Enhance**: `frontend/src/pages/__tests__/GamePage.test.js`

**Current**: 11 basic tests → **Target**: 50+ comprehensive tests

```javascript
describe('GamePage', () => {
  // Add Partnership Flows (12 tests)
  it('displays partnership offer when captain')
  it('handles partnership acceptance')
  it('handles partnership decline → solo')
  // ... 9 more partnership tests

  // Add Betting Flows (10 tests)
  it('shows double offer button when appropriate')
  it('handles double acceptance flow')
  it('handles double decline flow')
  // ... 7 more betting tests

  // Add Scoring Display (8 tests)
  it('displays current hole score accurately')
  it('shows cumulative points')
  it('highlights leader')
  // ... 5 more scoring tests

  // Add Edge Cases (9 tests)
  it('handles game not found error')
  it('handles API timeouts')
  it('shows loading states')
  // ... 6 more edge cases

  // Total: 50+ tests (39 new)
});
```

**Deliverables**:
- Enhanced GamePage.test.js (50+ tests total, ~1,000 lines)

---

### Week 6: Hooks & State Management

#### Task 3.4: useOddsCalculation Tests ⏱️ 12 hours
**Owner**: Frontend Lead
**CRITICAL**: 392 lines betting logic, 0% → 100%

**File to Create**: `frontend/src/hooks/__tests__/useOddsCalculation.test.js`

```javascript
describe('useOddsCalculation', () => {
  // Win Probability (10 tests)
  it('calculates win probability from positions')
  it('adjusts probability for handicaps')
  it('considers hole difficulty')
  // ... 7 more probability tests

  // Expected Value (8 tests)
  it('calculates expected value of partnership')
  it('calculates solo play expected value')
  it('compares partnership vs solo EV')
  // ... 5 more EV tests

  // Risk Assessment (7 tests)
  it('assesses risk level (LOW/MEDIUM/HIGH)')
  it('recommends betting actions')
  // ... 5 more risk tests

  // Edge Cases (5 tests)
  it('handles missing data gracefully')
  it('validates calculation bounds')
  // ... 3 more edge cases

  // Total: 30+ tests
});
```

**Deliverables**:
- useOddsCalculation.test.js (30+ tests, ~600 lines)

---

#### Task 3.5: Other Critical Hooks ⏱️ 14 hours
**Owner**: Frontend Lead

**Files to Create**:
```
frontend/src/hooks/__tests__/
├── useGameApi.test.js           (20+ tests)
├── useSimulationApi.test.js     (20+ tests)
├── useTutorialProgress.test.js  (25+ tests)
└── useAuth.test.js              (15+ tests)
```

**Coverage**:
- useGameApi.js (125 lines, 0% → 100%)
- useSimulationApi.js (159 lines, 0% → 100%)
- useTutorialProgress.js (336 lines, 0% → 100%)
- useAuth.js (17 lines, 0% → 100%)

**Deliverables**:
- 4 hook test files, 80+ tests total

---

#### Task 3.6: Accessibility Testing ⏱️ 8 hours
**Owner**: Frontend Lead

**Add to ALL existing component tests**:

```javascript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('ComponentName Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<ComponentName />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('has proper ARIA labels', () => {
    render(<ComponentName />);
    expect(screen.getByLabelText(/expected label/i)).toBeInTheDocument();
  });

  it('supports keyboard navigation', async () => {
    const { user } = render(<ComponentName />);
    await user.tab();
    expect(screen.getByRole('button')).toHaveFocus();
  });
});
```

**Components to Audit** (30+ components):
- All auth components
- All simulation components
- All game components
- All form components

**Acceptance Criteria**:
- ✅ Zero axe violations across all components
- ✅ All interactive elements keyboard accessible
- ✅ All form inputs have associated labels

**Deliverables**:
- A11y tests added to 30+ component test files

---

### Phase 3 Deliverables Summary

**Completed by End of Week 6**:
- ✅ SimulationDecisionPanel.test.tsx (35+ tests)
- ✅ HoleVisualization.test.tsx (25+ tests)
- ✅ Enhanced GamePage.test.js (39 new tests)
- ✅ useOddsCalculation.test.js (30+ tests)
- ✅ 4 additional hook test files (80+ tests)
- ✅ Accessibility tests on 30+ components

**Coverage Improvement**:
- SimulationDecisionPanel.tsx: 0% → **100%**
- HoleVisualization.tsx: 0% → **100%**
- useOddsCalculation.js: 0% → **100%**
- Custom hooks: 31% → **95%**
- Accessibility: 0% → **100%** (zero violations)

**Total New Tests**: 209+ tests
**Hours Invested**: ~70 hours

---

## Phase 4: Integration & E2E (Weeks 7-8)

**Goal**: API endpoint testing, BDD scenarios, E2E workflows

### Week 7: API & BDD Testing

#### Task 4.1: Comprehensive API Endpoint Tests ⏱️ 24 hours
**Owner**: Backend Lead
**CRITICAL**: 114 endpoints, ~12 tested → 100+ tested

**File to Create**: `backend/tests/test_api_endpoints_comprehensive.py`

**Structure** (organized by endpoint category):

```python
class TestGameManagementEndpoints:
    """Test /game/* endpoints"""

    def test_post_game_initialize(self, api_client, standard_4_players)
    def test_get_game_state(self, api_client, game_fixture)
    def test_post_game_action(self, api_client)
    def test_get_game_tips(self, api_client)
    def test_delete_game(self, api_client)
    # ... 15 more game endpoints

class TestPlayerManagementEndpoints:
    """Test /players/* endpoints"""

    def test_get_players_list(self, api_client)
    def test_post_create_player(self, api_client)
    def test_get_player_detail(self, api_client)
    def test_put_update_player(self, api_client)
    def test_delete_player(self, api_client)
    def test_get_player_advanced_metrics(self, api_client)
    def test_get_player_trends(self, api_client)
    # ... 13 more player endpoints

class TestGHINIntegrationEndpoints:
    """Test /ghin/* endpoints"""

    def test_post_ghin_lookup(self, api_client)
    def test_post_ghin_sync_player(self, api_client)
    def test_post_ghin_sync_all(self, api_client)
    def test_get_ghin_diagnostic(self, api_client)
    # ... 6 more GHIN endpoints

class TestCourseManagementEndpoints:
    """Test /courses/* endpoints"""

    def test_get_courses_list(self, api_client)
    def test_post_create_course(self, api_client)
    def test_put_update_course(self, api_client)
    def test_delete_course(self, api_client)
    def test_post_course_import(self, api_client)
    # ... 10 more course endpoints

class TestAnalyticsEndpoints:
    """Test /analytics/* and /leaderboard/* endpoints"""

    def test_get_leaderboard(self, api_client)
    def test_get_leaderboard_by_metric(self, api_client)
    def test_get_analytics_overview(self, api_client)
    def test_get_game_stats(self, api_client)
    # ... 12 more analytics endpoints

# Total: 100+ endpoint tests
```

**Acceptance Criteria**:
- ✅ All 114 endpoints tested
- ✅ Success responses validated
- ✅ Error responses tested (400, 401, 404, 500)
- ✅ Request validation tested
- ✅ Response schemas validated

**Deliverables**:
- test_api_endpoints_comprehensive.py (100+ tests, ~2,000 lines)

---

#### Task 4.2: BDD Game Rules Core ⏱️ 16 hours
**Owner**: QA Lead / Backend Lead

**File to Create**: `tests/bdd/behave/features/game_rules_core.feature`

**Content** (12 critical scenarios):

```gherkin
Feature: Core Wolf Goat Pig Game Rules
  Comprehensive validation of fundamental game mechanics

  Scenario: Wolf format - Captain chooses after all tee shots
    Given a 4-player Wolf format game on hole 5
    And the captain is Player 1
    And all 4 players have teed off with these results:
      | player  | distance | lie     |
      | Player1 | 180      | fairway |
      | Player2 | 220      | fairway |
      | Player3 | 140      | rough   |
      | Player4 | 200      | fairway |
    When Player 1 chooses Player 2 as partner
    Then teams are formed as Player1+Player2 vs Player3+Player4
    And the base wager is 1 quarter

  Scenario: Captain goes solo after seeing tee shots
    Given a 4-player Wolf format game on hole 8
    And the captain is Player 3
    And all players have teed off with poor results except captain
    When Player 3 chooses to go solo
    Then Player 3 is solo against Player1+Player2+Player4
    And the wager is doubled to 2 quarters

  Scenario: Best-ball scoring with 2v2 teams
    Given a hole with teams Player1+Player2 vs Player3+Player4
    And the hole scores are:
      | player  | gross | net |
      | Player1 | 5     | 5   |
      | Player2 | 4     | 4   |
      | Player3 | 6     | 5   |
      | Player4 | 5     | 5   |
    When the hole is scored
    Then Team1 scores 4 (best ball)
    And Team2 scores 5 (best ball)
    And Team1 wins 1 quarter each (2 total)

  Scenario: Solo player wins - double payout
    Given Player1 is solo against Player2+Player3+Player4
    And the base wager is 1 quarter
    And Player1 scores net 4, others score net 5
    When the hole is scored
    Then Player1 wins 6 quarters (2 from each opponent)

  Scenario: Halved hole carries wager to next hole
    Given a hole with teams Player1+Player2 vs Player3+Player4
    And both teams score net 4 (tie)
    When the hole is completed
    Then no points are awarded
    And the carry_over flag is true
    And the next hole wager is 2 quarters (1 base + 1 carry)

  Scenario: Karl Marx Rule distributes points fairly
    Given a 5-player game with unequal teams
    And Team1 has 3 players, Team2 has 2 players
    And Team1 wins the hole
    When points are distributed via Karl Marx Rule
    Then each Team1 member earns 0.67 quarters
    And each Team2 member loses 1 quarter

  Scenario: Handicap strokes applied to scoring
    Given a Par 4 hole with stroke index 1
    And Player1 has handicap 10 (receives 1 stroke)
    And Player1 scores gross 5
    When net score is calculated
    Then Player1 net score is 4

  Scenario: The Float doubles base wager once per round
    Given Player1 is captain on hole 7
    And Player1 has not used The Float this round
    When Player1 invokes The Float
    Then the base wager becomes 2 quarters
    And Player1 cannot invoke Float again this round

  Scenario: The Option triggers when captain is Goat
    Given Player2 is captain and is furthest down in points
    When partnership is formed
    Then The Option is automatically triggered
    And the wager doubles

  Scenario: Wagering closes after tee shots
    Given all players have completed tee shots
    When a team attempts to offer a double
    Then the double offer is rejected
    And error message says "wagering is closed"

  Scenario: Line of scrimmage restricts betting
    Given Player1 is trailing in position
    And line of scrimmage rule is active
    When Player1 attempts to double
    Then the double is not allowed
    And Player1 must be at or beyond scrimmage line

  Scenario: Solo player can double after wagering closed
    Given Player1 is solo
    And wagering is closed for teams
    When Player1 offers to double
    Then the double offer is allowed
    And solo player has special doubling privileges
```

**Step Definitions to Implement**:
```python
# steps/game_rules_steps.py

@given('a {player_count:d}-player {format} format game on hole {hole:d}')
def step_game_setup(context, player_count, format, hole):
    # Setup game with specified parameters

@when('the hole is scored')
def step_score_hole(context):
    # Trigger scoring calculation

@then('Team{team:d} scores {score:d} (best ball)')
def step_verify_best_ball(context, team, score):
    # Verify best ball calculation

@then('{player} wins {quarters:d} quarters')
def step_verify_payout(context, player, quarters):
    # Verify point distribution
```

**Acceptance Criteria**:
- ✅ All 12 critical scenarios pass
- ✅ Step definitions comprehensive
- ✅ Scoring logic fully validated
- ✅ Karl Marx Rule tested

**Deliverables**:
- game_rules_core.feature (12 scenarios)
- Step definitions (~400 lines)

---

#### Task 4.3: BDD Betting Decisions ⏱️ 12 hours
**Owner**: QA Lead

**File to Create**: `tests/bdd/behave/features/betting_decisions.feature`

**Content** (8 scenarios for double workflows):

```gherkin
Feature: Betting Decisions and Double Workflows

  Scenario: Team offers double - opponent accepts
  Scenario: Team offers double - opponent declines
  Scenario: Ping-pong doubles reach third level
  Scenario: Cannot double when wagering closed
  Scenario: Solo player can double after wagering closed
  Scenario: Double offer expires if not responded
  Scenario: Betting opportunity detection
  Scenario: Risk assessment updates
```

**Deliverables**:
- betting_decisions.feature (8 scenarios)
- Step definitions (~300 lines)

---

### Week 8: E2E & Integration

#### Task 4.4: E2E Complete Game Flow ⏱️ 14 hours
**Owner**: QA Lead

**File to Create**: `tests/e2e/tests/complete-game-flow.spec.js`

**Content** (end-to-end game simulation):

```javascript
test.describe('Complete Game Flow', () => {
  test('full 4-player game from setup to completion', async ({ page }) => {
    // 1. Setup game
    await setupGame(page, {
      players: 4,
      course: 'Wing Point',
      format: 'Wolf'
    });

    // 2. Play hole 1
    await playHole(page, {
      captain: 'Player1',
      decision: 'choose_partner',
      partner: 'Player2'
    });

    // 3. Simulate shots
    await simulateShots(page, [
      { player: 'Player1', result: 'fairway' },
      { player: 'Player2', result: 'green' },
      // ...
    ]);

    // 4. Complete hole and verify scoring
    await completeHole(page);
    await expect(page.locator('.scores')).toContainText('Team1: +1');

    // 5. Continue through 18 holes
    for (let hole = 2; hole <= 18; hole++) {
      await playHole(page, getHoleStrategy(hole));
    }

    // 6. Verify final results
    await verifyGameResults(page);
  });

  test('betting flow with double and accept', async ({ page }) => {
    // Test double offering and acceptance workflow
  });

  test('partnership rejection leads to solo', async ({ page }) => {
    // Test partnership decline → auto solo
  });

  // 7 more complete flow tests
});
```

**Acceptance Criteria**:
- ✅ Complete 18-hole game playable end-to-end
- ✅ Betting workflows tested in UI
- ✅ Scoring displayed correctly
- ✅ Phase transitions work

**Deliverables**:
- complete-game-flow.spec.js (10+ E2E tests)

---

#### Task 4.5: Integration Tests - Frontend/Backend ⏱️ 10 hours
**Owner**: Full Stack Dev

**File to Create**: `frontend/src/__tests__/integration/apiIntegration.test.js`

**Content**:
```javascript
describe('Frontend-Backend Integration', () => {
  // API Integration (15 tests)
  it('fetches game state from real backend')
  it('posts game actions and receives updates')
  it('handles API errors gracefully')
  it('retries failed requests')
  // ... 11 more API tests

  // Auth Integration (8 tests)
  it('authenticates user and fetches profile')
  it('refreshes token before expiration')
  it('handles logout and cleanup')
  // ... 5 more auth tests

  // Total: 23+ integration tests
});
```

**Deliverables**:
- apiIntegration.test.js (23+ tests)

---

### Phase 4 Deliverables Summary

**Completed by End of Week 8**:
- ✅ test_api_endpoints_comprehensive.py (100+ tests)
- ✅ game_rules_core.feature (12 BDD scenarios)
- ✅ betting_decisions.feature (8 BDD scenarios)
- ✅ complete-game-flow.spec.js (10+ E2E tests)
- ✅ apiIntegration.test.js (23+ integration tests)

**Coverage Improvement**:
- API Endpoints: 10% → **90%+**
- BDD Rule Coverage: 10% → **60%+**
- E2E Complete Flows: 1 → **10+**

**Total New Tests**: 153+ tests
**Hours Invested**: ~76 hours

---

## Phase 5: Polish, Performance & Validation (Weeks 9-10)

**Goal**: Final BDD scenarios, edge cases, performance, and validation

### Week 9: Remaining BDD & Edge Cases

#### Task 5.1: BDD Aardvark Mechanics ⏱️ 12 hours
**Owner**: QA Lead

**File to Create**: `tests/bdd/behave/features/game_rules_aardvark.feature`

**Content** (8 scenarios for 5/6-player games):

```gherkin
Feature: Aardvark Mechanics for 5 and 6-Player Games

  Scenario: 5-player - Aardvark requests to join team
  Scenario: 5-player - Aardvark goes solo (The Tunkarri)
  Scenario: 5-player - Team rejects Aardvark (doubles wager)
  Scenario: 6-player - Dual Aardvark balanced teams
  Scenario: 6-player - Both Aardvarks go solo
  Scenario: Aardvark Karl Marx distribution
  Scenario: Tunkarri 3-for-2 payout validation
  Scenario: Invisible Aardvark in 4-player mode
```

**Deliverables**:
- game_rules_aardvark.feature (8 scenarios)

---

#### Task 5.2: BDD Game Phases ⏱️ 10 hours
**Owner**: QA Lead

**File to Create**: `tests/bdd/behave/features/game_phases.feature`

**Content** (6 scenarios for phase transitions):

```gherkin
Feature: Game Phase Transitions

  Scenario: Vinnie's Variation starts hole 13
  Scenario: Vinnie's Variation doubles base wager
  Scenario: Hoepfinger phase - Goat chooses position
  Scenario: Joe's Special - Goat sets hole value
  Scenario: Phase transition maintains state
  Scenario: Regular phase resumes after Vinnie's
```

**Deliverables**:
- game_phases.feature (6 scenarios)

---

#### Task 5.3: Edge Cases & Error Handling ⏱️ 14 hours
**Owner**: Backend + Frontend Leads

**Files to Create**:
```
backend/tests/test_edge_cases_comprehensive.py (30+ tests)
frontend/src/__tests__/edgeCases.test.js (25+ tests)
tests/bdd/behave/features/ties_and_edge_cases.feature (8 scenarios)
```

**Backend Edge Cases**:
- 6-player game edge cases
- Multiple consecutive ties
- Invalid state transitions
- Boundary value testing
- Concurrent request handling

**Frontend Edge Cases**:
- Network failures during critical operations
- Stale data handling
- Race conditions
- Memory leaks in long games

**BDD Edge Cases**:
- Tie scenarios
- Hanging Chad
- Change of Mind rule
- Ackerley's Gambit
- Maximum wager caps

**Deliverables**:
- 3 files with 63+ total tests/scenarios

---

### Week 10: Performance, Load Testing & Final Validation

#### Task 5.4: Performance Testing ⏱️ 12 hours
**Owner**: Backend Lead

**File to Create**: `backend/tests/test_performance_benchmarks.py`

**Content**:
```python
class TestPerformanceBenchmarks:
    """Performance benchmarks for critical paths"""

    def test_game_initialization_performance(self):
        """Game init should complete in < 100ms"""
        start = time.time()
        game = initialize_game(players=4, course=test_course)
        duration = time.time() - start
        assert duration < 0.1, f"Took {duration}s, expected < 0.1s"

    def test_shot_simulation_performance(self):
        """Shot simulation < 50ms"""

    def test_scoring_calculation_performance(self):
        """Hole scoring < 20ms"""

    def test_odds_calculation_performance(self):
        """Odds calc < 100ms"""

    def test_18_hole_game_performance(self):
        """Complete 18-hole simulation < 5s"""

    # 15+ performance tests
```

**Deliverables**:
- test_performance_benchmarks.py (15+ tests)

---

#### Task 5.5: Load Testing ⏱️ 10 hours
**Owner**: DevOps / Backend Lead

**File to Create**: `tests/load/game-simulation-load.js` (k6 script)

**Content**:
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 50 },   // Ramp to 50
    { duration: '5m', target: 50 },   // Stay at 50
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% requests < 500ms
    http_req_failed: ['rate<0.01'],     // <1% failures
  },
};

export default function () {
  // Simulate game creation
  let createRes = http.post('http://localhost:8000/game/initialize', {
    player_ids: [1, 2, 3, 4],
    course_id: 10,
  });

  check(createRes, {
    'game created': (r) => r.status === 200,
  });

  let gameId = createRes.json('game_id');

  // Simulate gameplay
  for (let hole = 1; hole <= 18; hole++) {
    http.post(`http://localhost:8000/game/${gameId}/action`, {
      action: 'advance_hole',
    });
    sleep(1);
  }
}
```

**Acceptance Criteria**:
- ✅ System handles 50 concurrent users
- ✅ 95% of requests < 500ms
- ✅ < 1% error rate under load

**Deliverables**:
- Load test scripts
- Performance report

---

#### Task 5.6: Coverage Validation & Reporting ⏱️ 8 hours
**Owner**: QA Lead

**Tasks**:
1. Run full coverage reports for backend and frontend
2. Generate HTML coverage reports
3. Create coverage trend graphs
4. Document gaps remaining (if any)
5. Create coverage badge for README

**Commands**:
```bash
# Backend coverage
cd backend
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=json

# Frontend coverage
cd frontend
npm test -- --coverage --watchAll=false

# Generate trend report
python scripts/generate_coverage_report.py
```

**Acceptance Criteria**:
- ✅ Backend coverage ≥ 85%
- ✅ Frontend coverage ≥ 80%
- ✅ Critical modules ≥ 95%
- ✅ BDD rule coverage ≥ 90%

**Deliverables**:
- Coverage reports (HTML, JSON)
- Coverage trend graphs
- Final gap analysis

---

#### Task 5.7: Documentation & Handoff ⏱️ 6 hours
**Owner**: Tech Lead

**Deliverables**:

1. **Testing Guide** (`docs/testing/TESTING_GUIDE.md`):
   - How to run tests
   - How to write new tests
   - Test organization
   - Best practices

2. **Coverage Report** (`docs/testing/COVERAGE_REPORT.md`):
   - Final coverage metrics
   - Coverage by module
   - Trend analysis

3. **CI/CD Integration** (`.github/workflows/tests.yml`):
   - Automated test runs on PR
   - Coverage reporting
   - Test failure notifications

4. **Test Maintenance Guide** (`docs/testing/MAINTENANCE.md`):
   - How to keep tests updated
   - When to add new tests
   - Test review process

---

### Phase 5 Deliverables Summary

**Completed by End of Week 10**:
- ✅ game_rules_aardvark.feature (8 scenarios)
- ✅ game_phases.feature (6 scenarios)
- ✅ Edge case tests (63+ tests/scenarios)
- ✅ Performance benchmarks (15+ tests)
- ✅ Load testing setup
- ✅ Coverage validation complete
- ✅ Documentation delivered

**Coverage Improvement**:
- BDD Rule Coverage: 60% → **90%+**
- Edge Cases: **Comprehensive**
- Performance: **Validated**
- Load Capacity: **Verified**

**Total New Tests**: 100+ tests/scenarios
**Hours Invested**: ~72 hours

---

## Final Summary

### Total Project Metrics

**Time Investment**:
- **Phase 1**: 34 hours (Infrastructure & Auth)
- **Phase 2**: 66 hours (Backend Core)
- **Phase 3**: 70 hours (Frontend Components)
- **Phase 4**: 76 hours (Integration & E2E)
- **Phase 5**: 72 hours (Polish & Performance)
- **TOTAL**: **318 hours** (~8 weeks for 1 FTE, or 4 weeks for 2 FTEs)

**Test Creation**:
- **Backend Tests**: 400+ new tests
- **Frontend Tests**: 300+ new tests
- **BDD Scenarios**: 50+ scenarios
- **E2E Tests**: 30+ tests
- **TOTAL**: **780+ tests**

**Test Files Created**:
- Backend: 12 new test files
- Frontend: 15 new test files
- BDD: 6 new feature files
- E2E: 3 new spec files
- **TOTAL**: **36 new files**

**Coverage Achievement**:
| Area | Before | After | Improvement |
|------|--------|-------|-------------|
| Backend Overall | 25-30% | **85%+** | +55-60% |
| Backend Critical | 15% | **95%+** | +80% |
| Frontend Overall | 25-35% | **80%+** | +45-55% |
| Frontend Auth | 0% | **100%** | +100% |
| API Endpoints | 10% | **90%+** | +80% |
| BDD Rule Coverage | 10% | **90%+** | +80% |
| Accessibility | 0% | **100%** | +100% |

---

## Resource Allocation

### Recommended Team Structure

**Option 1: 2 FTEs for 5 weeks**
- 1 Backend Engineer (Phases 1, 2, 4)
- 1 Frontend Engineer (Phases 1, 3, 4)
- Both contribute to Phase 5

**Option 2: 1 FTE for 10 weeks**
- Full-stack developer
- Follow phases sequentially

**Option 3: 3 FTEs for 3-4 weeks** (Fastest)
- 1 Backend Engineer (Phases 1, 2)
- 1 Frontend Engineer (Phases 1, 3)
- 1 QA Engineer (Phases 4, 5)

### Skills Required

**Backend Engineer**:
- Python, pytest, FastAPI
- Test fixture design
- API testing
- Performance testing

**Frontend Engineer**:
- React, TypeScript, Jest, RTL
- Accessibility testing (jest-axe)
- Component testing patterns
- Hook testing

**QA Engineer** (for BDD/E2E):
- Behave/Gherkin
- Playwright
- Test scenario design
- Load testing (k6)

---

## Risk Mitigation

### Identified Risks

1. **Risk**: Tests break existing functionality
   **Mitigation**: Run full test suite after each major batch, keep PRs small

2. **Risk**: Tight coupling makes testing difficult
   **Mitigation**: Refactor for testability as needed (budget 10% extra time)

3. **Risk**: Flaky tests in CI/CD
   **Mitigation**: Use proper waits, mock time, seed random values

4. **Risk**: Team capacity constraints
   **Mitigation**: Prioritize Phases 1-2 (auth + core logic) if time limited

5. **Risk**: Coverage goals not met
   **Mitigation**: Daily coverage checks, adjust scope if needed

---

## Success Criteria

### Must-Have (Go/No-Go)
- ✅ Backend coverage ≥ 80%
- ✅ Frontend auth coverage = 100%
- ✅ Core simulation coverage ≥ 90%
- ✅ Zero critical security vulnerabilities
- ✅ All tests passing in CI/CD

### Should-Have
- ✅ Backend coverage ≥ 85%
- ✅ Frontend coverage ≥ 75%
- ✅ BDD rule coverage ≥ 80%
- ✅ Load test validates 50 concurrent users
- ✅ Zero accessibility violations

### Nice-to-Have
- ✅ Backend coverage ≥ 90%
- ✅ Frontend coverage ≥ 80%
- ✅ BDD rule coverage ≥ 90%
- ✅ Performance benchmarks documented
- ✅ Visual regression testing

---

## Ongoing Maintenance

**Post-Completion Activities**:

1. **Weekly**: Review failed tests, fix flaky tests
2. **Per PR**: Require tests for new features (enforce coverage thresholds)
3. **Monthly**: Review coverage trends, identify new gaps
4. **Quarterly**: Update BDD scenarios for rule changes
5. **Per Release**: Run full E2E and load tests

**Coverage Enforcement**:
```json
// package.json (frontend)
{
  "jest": {
    "coverageThreshold": {
      "global": {
        "branches": 75,
        "functions": 75,
        "lines": 80,
        "statements": 80
      }
    }
  }
}
```

```ini
# pytest.ini (backend)
[tool:pytest]
addopts =
    --cov=app
    --cov-fail-under=85
    --cov-report=term-missing
    --cov-report=html
```

---

## Appendix: Quick Reference

### Run All Tests

```bash
# Backend
cd backend
pytest --cov=app --cov-report=html --cov-report=term -v

# Frontend
cd frontend
npm test -- --coverage --watchAll=false

# BDD
cd tests/bdd/behave
behave --format pretty

# E2E
cd tests/e2e
npx playwright test

# Load Tests
k6 run tests/load/game-simulation-load.js
```

### Phase Completion Checklist

**Phase 1 Complete When**:
- [ ] All dependencies installed
- [ ] Fixtures created and documented
- [ ] Auth tests 100% coverage
- [ ] CI/CD passing

**Phase 2 Complete When**:
- [ ] Core simulation ≥ 95% coverage
- [ ] Betting logic 100% coverage
- [ ] Scoring logic 100% coverage
- [ ] All fixtures working

**Phase 3 Complete When**:
- [ ] Critical components ≥ 95% coverage
- [ ] Hooks ≥ 90% coverage
- [ ] Zero accessibility violations
- [ ] Integration tests passing

**Phase 4 Complete When**:
- [ ] API endpoints ≥ 90% coverage
- [ ] 20+ BDD scenarios passing
- [ ] 10+ E2E flows working
- [ ] Integration tests passing

**Phase 5 Complete When**:
- [ ] BDD rule coverage ≥ 90%
- [ ] Performance validated
- [ ] Load tests passing
- [ ] Documentation complete
- [ ] All metrics met

---

**Plan Status**: Ready for Execution
**Next Step**: Review and approve plan, assign resources, kick off Phase 1

**Questions or Concerns**: Contact project tech lead for plan adjustments
