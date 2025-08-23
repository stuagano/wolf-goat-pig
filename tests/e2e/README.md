# Wolf-Goat-Pig End-to-End Tests

This directory contains comprehensive end-to-end tests for the Wolf-Goat-Pig golf betting game using Playwright.

## Setup

### 1. Install Dependencies

Navigate to the e2e tests directory and install Playwright:

```bash
cd tests/e2e
npm install
```

### 2. Install Playwright Browsers

```bash
npm run install-browsers
```

This installs Chromium, Firefox, and WebKit browsers needed for testing.

## Running Tests

### Prerequisites

Before running tests, make sure both frontend and backend servers are running:

**Backend (Terminal 1):**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm start
```

### Run All Tests

```bash
npm test
```

### Run Tests with UI Mode (Recommended for Development)

```bash
npm run test:ui
```

This opens the Playwright UI where you can:
- See tests running in real-time
- Debug failed tests
- View screenshots and videos
- Inspect network requests

### Run Tests in Headed Mode (See Browser)

```bash
npm run test:headed
```

### Debug a Specific Test

```bash
npm run test:debug -- --grep "should load the main game interface"
```

## Test Structure

### Test Files

1. **game-flow.spec.js** - Core game functionality tests
   - Game initialization
   - Shot simulation
   - Player rotation
   - Hole progression
   - UI consistency

2. **betting-partnership.spec.js** - Betting and partnership system tests
   - Partnership timing after tee shots
   - Betting opportunities
   - Double/flush mechanics
   - Team formation

3. **api-integration.spec.js** - Backend API integration tests
   - API connectivity
   - Game creation
   - Shot simulation via API
   - Partnership requests
   - Betting actions

### Test Coverage

The tests cover:
- ✅ Game setup and initialization
- ✅ Shot simulation and player rotation
- ✅ Partnership decisions after tee shots
- ✅ Betting system functionality
- ✅ API endpoint integration
- ✅ Error handling and edge cases
- ✅ UI responsiveness and consistency

## Configuration

### Browser Support

Tests run on multiple browsers:
- Chromium (Chrome/Edge)
- Firefox
- WebKit (Safari)
- Mobile Chrome (Pixel 5)
- Mobile Safari (iPhone 12)

### Automatic Server Management

The tests automatically start and stop the frontend and backend servers if they're not already running. See `playwright.config.js` for configuration.

## Debugging

### View Test Reports

After running tests:

```bash
npm run report
```

This opens an HTML report showing:
- Test results
- Screenshots of failures
- Network logs
- Console output

### Common Issues

1. **Servers not starting**: Make sure ports 3000 and 8000 are available
2. **Tests timing out**: Check if backend API is responding at http://localhost:8000
3. **UI elements not found**: Frontend may need time to load - tests include waits

### Screenshot and Video

Failed tests automatically capture:
- Screenshots at the point of failure
- Full test execution videos (in CI mode)

## Extending Tests

### Adding New Tests

1. Create new test files in the `tests/` directory
2. Follow existing patterns for page interactions
3. Use data-testid attributes in frontend for reliable element selection
4. Test both happy path and error scenarios

### Best Practices

- Use Page Object Model for complex interactions
- Wait for elements to be visible before interacting
- Test user journeys end-to-end
- Verify both frontend UI and backend state changes
- Include edge cases and error handling

## CI/CD Integration

The tests are configured to run in GitHub Actions. See the main project's workflow files for CI configuration.

For local CI-like testing:
```bash
CI=true npm test
```

This runs tests in headless mode with full reporting.