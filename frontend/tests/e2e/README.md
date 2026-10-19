# Wolf Goat Pig - E2E Testing Suite

End-to-end testing infrastructure for the Wolf Goat Pig test game mode using Playwright.

### Post a Score layout regression

From this directory, run `npx playwright test --config playwright.layout.config.js`.
It starts an isolated frontend on port 3107, seeds the existing Auth0 cache, and
intercepts API calls without starting a backend or writing data. It checks rendered
control bounds at 320/375/390px in iPhone WebKit and 1280px in desktop Chromium,
including six-player groups, long names, focus, date entry, and negative quarters.
This emulates iPhone WebKit; it does not test a physical iPhone keyboard.

**Status**: 🚧 Foundation Complete - Implementation In Progress

---

## 📋 Overview

This E2E testing suite provides comprehensive testing for the Wolf Goat Pig application, focusing on the test game mode user flow from homepage navigation through game completion.

### Testing Strategy: **Hybrid Approach**

- **UI Testing**: Critical paths (holes 1-3, 16-18) for user interaction validation
- **API Fast-Forward**: Middle game holes (4-15) for performance
- **Result**: ~3-5 minute test execution vs ~10 minutes for full UI testing

---

## 🎯 What's Been Accomplished

### ✅ Infrastructure (Tasks 1-3)

**Playwright Configuration** (`playwright.config.js`)
- Auto-start backend (port 8000) + frontend (port 3000)
- 2-minute timeout, 2 retries, serial execution
- Multiple reporters: HTML, JUnit, list
- 5 npm scripts for different test modes

**Test Fixtures** (`fixtures/game-fixtures.js`)
- Complete test data for 4-man game with all 18 holes
- Expected points calculations for validation
- Special rules data (Float, Joe's Special, Hoepfinger)

**API Helpers** (`fixtures/api-helpers.js`)
- Fast-forward holes 4-15 via API
- Game cleanup utilities
- Error handling with response bodies

**Custom Assertions** (`utils/assertions.js`)
- `assertPointsBalanceToZero()` - Zero-sum validation
- `assertHoleHistory()` - Hole completion verification
- `assertGameCompleted()` - Game status validation

**Test Helpers** (`utils/test-helpers.js`)
- `cleanupTestGame()` - localStorage + backend cleanup
- `waitForGameState()` - Condition-based waiting
- `waitForHoleCompletion()` - Hole advancement verification

### ✅ Page Objects (Tasks 4-7)

**HomePage** (`page-objects/HomePage.js`)
- Homepage navigation and verification
- Splash screen handling ("Browse Without Login")
- Hamburger menu interaction
- Test game navigation

**GameCreationPage** (`page-objects/GameCreationPage.js`)
- Test game creation with player count + course selection
- Game ID extraction from URL
- Defensive programming with optional selectors

**ScorekeeperPage** (`page-objects/ScorekeeperPage.js`)
- Complete hole workflow (scores → teams → submit)
- Score entry, partner selection, solo mode
- Special rules support (Float, Joe's Special)
- Hole verification and state checks

**GameCompletionPage** (`page-objects/GameCompletionPage.js`)
- Final standings verification
- Zero-sum point validation
- Winner determination
- Game status checks

### ✅ Tests (Task 8)

**4-Man Happy Path Test** (`tests/test-game-4-man.spec.js`)
- Complete 18-hole test from homepage to game completion
- UI testing on holes 1-3 and 16-18
- API fast-forward for holes 4-15
- State persistence verification (page reload)
- Zero-sum validation

**Smoke Tests** (`tests/smoke-test.spec.js`)
- Backend health checks
- API game creation tests
- Hole completion via API
- Game state persistence
- Frontend rendering validation

### ✅ UI Enhancements (Tasks 9-10)

**data-testid Attributes Added**:
- `SimpleScorekeeper.jsx`: 9 attributes (scorekeeper-container, current-hole, score inputs, partner buttons, solo button, complete hole, player points)
- `HomePage.js`: 2 attributes (hamburger menu, test multiplayer menu item)

**GameCompletionView Component Created** (`components/game/GameCompletionView.jsx`):
- Winner announcement with trophy emoji
- Rankings with medal emojis (🥇🥈🥉)
- Complete final standings table
- Stroke totals and usage stats (Solo, Float, Options)
- Game statistics panel
- Action buttons (Start New Game, View Scorecard)
- 5 data-testid attributes for E2E testing

---

## 🚧 Known Issues & Blockers

### ⚠️ Current Blockers

1. **Chromium Permissions**: Browser automation blocked on Mac OS
   - **Impact**: Can't run full E2E tests in headed or headless mode locally
   - **Solution**: Use Podman container (see "Running with Podman" below)
   - **Alternative**: Smoke tests use minimal browser interaction

2. **API Endpoint Mismatches**: Smoke tests assume endpoints that may not exist
   - `/` returns HTML not JSON (expected)
   - `/games/test` endpoint structure needs verification
   - `/games/{id}/holes/complete` confirmed correct

3. **HomePage Selectors**: Fixed but initial implementation had issues
   - Was looking for hidden/generic "Wolf Goat Pig" text
   - Now looks for visible "Home" button + "Welcome to Wolf Goat Pig"

### 📝 Tests Need Adjustment

**test-game-4-man.spec.js**:
- Status: WIP - needs actual test run validation
- Reason: Can't run due to Chromium blocking
- Next: Run on different machine or CI/CD environment

**smoke-test.spec.js**:
- Status: Failing - API endpoint assumptions incorrect
- Fixes needed:
  - Update backend health check (or remove)
  - Verify `/games/test` endpoint structure
  - Check actual API response formats

---

## 📦 File Structure

```
frontend/tests/e2e/
├── playwright.config.js          # Playwright configuration
├── README.md                      # This file
├── fixtures/
│   ├── game-fixtures.js          # Test data for 4-man game (all 18 holes)
│   └── api-helpers.js            # API utilities for fast-forwarding
├── page-objects/
│   ├── HomePage.js                # Homepage navigation
│   ├── GameCreationPage.js        # Test game creation
│   ├── ScorekeeperPage.js         # Scorekeeper interactions
│   └── GameCompletionPage.js      # Game completion verification
├── tests/
│   ├── test-game-4-man.spec.js   # Full 18-hole happy path test
│   └── smoke-test.spec.js         # Quick smoke tests
└── utils/
    ├── assertions.js              # Custom Playwright assertions
    └── test-helpers.js            # Test utility functions
```

---

## 🚀 Running Tests

### Prerequisites

```bash
# Install dependencies
npm install

# Install Playwright browsers (if not already installed)
npx playwright install
```

### Test Commands

```bash
# Run all E2E tests
npm run test:e2e

# iOS read-after-write specs (emulated iPhone/WebKit; runs in CI as "iOS E2E")
# Add new iPhone specs under tests/ios/
npx playwright install webkit
npx playwright test --config playwright.config.js --project=iphone

# Run specific test file
npm run test:e2e -- test-game-4-man.spec.js
npm run test:e2e -- smoke-test.spec.js

# Run tests in headed mode (watch browser)
npm run test:e2e:headed -- test-game-4-man.spec.js

# Run tests in debug mode (step through)
npm run test:e2e:debug -- test-game-4-man.spec.js

# View test report
npm run test:e2e:report
```

### Environment

The Playwright config auto-starts:
- **Backend**: `http://localhost:8000` (FastAPI)
- **Frontend**: `http://localhost:3000` (React)

Ensure no other services are using these ports.

### Running with Podman (Recommended for Mac OS)

If Chromium is blocked on your system, use Podman to run tests in a container:

**Prerequisites**:
```bash
# Start backend and frontend manually first
cd backend && uvicorn app.main:app --reload  # Terminal 1
cd frontend && npm start                      # Terminal 2
```

**Run tests in Podman**:
```bash
cd frontend/tests/e2e

# Run all tests
./run-in-podman.sh

# Run specific test
./run-in-podman.sh smoke-test.spec.js
./run-in-podman.sh test-game-4-man.spec.js
```

**How it works**:
- Uses official Playwright Docker image (`mcr.microsoft.com/playwright:v1.48.1-jammy`)
- Mounts frontend directory into container
- Uses `--network=host` to access localhost:8000 and localhost:3000
- Runs tests inside container, outputs results to your terminal
- Test reports saved to `frontend/playwright-report/`

**Benefits**:
- ✅ Bypasses local Chromium permission issues
- ✅ Consistent environment across all machines
- ✅ Same Playwright version as CI/CD
- ✅ No local browser installation needed

---

## 🎯 Next Steps (Future Work)

### Immediate (Required for Full E2E Tests)

1. **Resolve Chromium Blocking**
   - Test on different machine
   - Use CI/CD environment (GitHub Actions)
   - Try different browser (Firefox, WebKit)

2. **Fix API Endpoint Assumptions**
   - Document actual backend endpoints
   - Update smoke tests to match reality
   - Verify `/games/test` or create it if missing

3. **Run Full E2E Test**
   - Execute `test-game-4-man.spec.js` in working environment
   - Debug any selector or timing issues
   - Verify all 18 holes complete successfully

### Enhancements (Nice to Have)

4. **Add More Test Scenarios**
   - 5-man game with Aardvark mechanics
   - Solo vs Partnership strategies
   - Float and Joe's Special rules
   - Hoepfinger double points validation

5. **Improve Test Data**
   - Add fixtures for 5-man and 6-man games
   - Create edge case scenarios (ties, perfect scores)
   - Add negative test cases

6. **CI/CD Integration**
   - GitHub Actions workflow for automated testing
   - Run smoke tests on every PR
   - Run full E2E suite nightly

7. **Test Reporting**
   - Screenshot comparison for UI changes
   - Performance metrics tracking
   - Test coverage reports

---

## 📚 Design Documents

- **Design Doc**: `/Users/stuartgano/Documents/wolf-goat-pig/docs/plans/2025-01-08-e2e-test-game-mode-design.md`
- **Implementation Plan**: `/Users/stuartgano/Documents/wolf-goat-pig/docs/plans/2025-01-08-e2e-test-game-mode-implementation.md`

---

## 🤝 Contributing

When adding new tests:

1. **Use Page Object Model**: Don't put selectors in test files
2. **Use data-testid**: Add to UI components, don't rely on text or classes
3. **Condition-based waits**: Use `waitForFunction`, `waitForResponse`, not `sleep()`
4. **Clean up after tests**: Use `afterEach` hooks to delete test games
5. **Document assumptions**: Comment any API endpoint assumptions

### Example Test Structure

```javascript
test('my new test', async ({ page }) => {
  // 1. Setup
  const homePage = new HomePage(page);

  // 2. Execute
  await homePage.goto();
  await homePage.clickTestGame();

  // 3. Verify
  await expect(page).toHaveURL(/\/game\/.+/);

  // 4. Cleanup (automatic via afterEach hook)
});
```

---

## 🐛 Troubleshooting

### "Error: page.waitForSelector: Test timeout"
- Check if element has correct `data-testid` attribute
- Verify element is actually visible (not `display: none`)
- Check if page loaded correctly (backend/frontend running?)

### "Backend not responding"
- Ensure backend is running: `cd backend && uvicorn app.main:app --reload`
- Check port 8000 is not in use: `lsof -i :8000`

### "Chromium blocked by permissions"
- Run on different machine or CI/CD
- Check Mac OS security settings
- Try Firefox: `npx playwright test --browser=firefox`

### "Test failed but I don't know why"
- Use debug mode: `npm run test:e2e:debug -- test-name.spec.js`
- Check screenshots in `test-results/` directory
- View trace: `npx playwright show-trace test-results/.../trace.zip`

---

## 📊 Test Coverage

### Current Coverage

| Feature | UI Test | API Test | Status |
|---------|---------|----------|--------|
| Homepage Navigation | ✅ | N/A | Complete |
| Test Game Creation | ✅ | ⚠️ | Needs verification |
| Holes 1-3 (UI) | ✅ | N/A | Ready (untested) |
| Holes 4-15 (API) | N/A | ✅ | Ready (untested) |
| Holes 16-18 (UI) | ✅ | N/A | Ready (untested) |
| Game Completion | ✅ | N/A | Ready (untested) |
| Zero-Sum Validation | ✅ | ✅ | Ready (untested) |
| State Persistence | ✅ | ⚠️ | Needs verification |

### Rule Coverage Goals

- **4-Man Games**: 95-98% (target with full E2E)
- **5-Man Games**: 0% (future work)
- **6-Man Games**: 0% (future work)

---

## 🏆 Success Criteria

An E2E test run is considered successful when:

1. ✅ All tests pass (green checkmarks)
2. ✅ Zero-sum validation passes (points balance to 0)
3. ✅ State persists across page reloads
4. ✅ Game completion view displays correctly
5. ✅ Test execution completes in <5 minutes
6. ✅ No console errors (except deprecation warnings)
7. ✅ All cleanup hooks run successfully

---

**Generated**: January 8, 2025
**Status**: Foundation Complete - Awaiting full test execution
**Next Milestone**: Run full E2E test suite in CI/CD or on unblocked machine
