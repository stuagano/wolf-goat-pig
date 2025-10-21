# Skill: Run All Tests

## Description
Runs the complete test suite for the Wolf Goat Pig project including backend pytest, frontend Jest, and E2E Playwright tests.

## Usage
Invoke this skill when you need to verify that all tests pass across the entire project before committing or deploying changes.

## Prerequisites
- Python 3.12.0 installed (or 3.11+ with compatibility mode)
- Node.js 18+ installed
- All dependencies installed (backend and frontend)
- PostgreSQL running (for integration tests) or SQLite for unit tests

## Steps

### 1. Run Backend Tests
```bash
cd backend

# Install dependencies if needed
pip install -r requirements.txt

# Run all pytest tests with coverage
pytest --cov=app --cov-report=term --cov-report=html -v

# Check coverage report
echo "Backend test coverage report generated at backend/htmlcov/index.html"
```

### 2. Run BDD Tests
```bash
cd tests/bdd/behave

# Run Behave tests
behave --format pretty --no-capture

# Run specific feature if needed
# behave features/wolf_betting.feature
```

### 3. Run Frontend Tests
```bash
cd frontend

# Install dependencies if needed
npm ci

# Run Jest tests with coverage
npm test -- --coverage --watchAll=false

# Check coverage report
echo "Frontend test coverage report generated at frontend/coverage/index.html"
```

### 4. Run E2E Tests
```bash
cd tests/e2e

# Install dependencies if needed
npm ci
npx playwright install --with-deps

# Run Playwright tests
npx playwright test

# Show report
npx playwright show-report
```

### 5. Generate Summary Report
```bash
echo "=== TEST SUMMARY ==="
echo "Backend: Check backend/htmlcov/index.html"
echo "Frontend: Check frontend/coverage/index.html"
echo "E2E: Check tests/e2e/playwright-report/index.html"
```

## Expected Results
- All backend tests pass (pytest exit code 0)
- All BDD scenarios pass (behave exit code 0)
- All frontend tests pass (Jest exit code 0)
- All E2E tests pass (Playwright exit code 0)
- Backend coverage > 80%
- Frontend coverage > 75%

## Troubleshooting

### Python Version Mismatch
If tests fail due to Python version:
```bash
# Install Python 3.12.0 with pyenv
pyenv install 3.12.0
pyenv local 3.12.0

# Or update Python version in tests
# Edit pyproject.toml or pytest.ini
```

### Missing Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm ci
```

### Database Connection Issues
```bash
# Use SQLite for local testing
export DATABASE_URL="sqlite:///./test.db"

# Or start PostgreSQL with Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=testpass postgres:15
```

## Success Indicators
- ✅ All test suites complete without errors
- ✅ Coverage reports generated
- ✅ No flaky tests
- ✅ Total execution time < 5 minutes
