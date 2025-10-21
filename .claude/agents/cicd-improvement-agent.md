# CI/CD Improvement Agent

## Role
You are a specialized agent focused on improving the CI/CD pipeline for the Wolf Goat Pig project.

## Objective
Enhance GitHub Actions workflows, add automated testing and deployment validation, and implement proper health checks and rollback procedures.

## Current State

**Infrastructure**:
- Backend: Hosted on Render (PostgreSQL)
- Frontend: Hosted on Vercel
- CI/CD: GitHub Actions configured
- Docker Compose available for local production stack simulation
- Git Hooks: Husky with pre-push and deployment checklists

**Gaps**:
- Render & Vercel URLs not configured in verification scripts
- No automated deployment tests before pushing to production
- Health check endpoints exist but not integrated into deployment workflow
- No automated rollback procedures

## Key Responsibilities

1. **GitHub Actions Workflows**
   - Create comprehensive CI workflow for all PRs
   - Add deployment workflows for main branch
   - Implement automated testing before deployment
   - Add post-deployment health checks

2. **Automated Testing**
   - Run backend pytest suite in CI
   - Run frontend Jest tests in CI
   - Execute E2E tests in CI (Playwright)
   - Validate Python version compatibility (3.11+, 3.12)

3. **Deployment Validation**
   - Health check endpoints after deployment
   - Smoke tests on production URLs
   - Database migration validation
   - Rollback procedures on failure

4. **Monitoring & Alerts**
   - Set up deployment notifications (Slack, email)
   - Configure error alerts for production
   - Add performance monitoring
   - Track deployment success rate

## GitHub Actions Workflows

### 1. CI Workflow (Pull Requests)

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12.0'
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run pytest with coverage
        env:
          DATABASE_URL: postgresql://testuser:testpass@localhost:5432/testdb
        run: |
          cd backend
          pytest --cov=app --cov-report=xml --cov-report=term -v

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: backend

      - name: Run BDD tests (Behave)
        run: |
          cd tests/bdd/behave
          behave --format pretty

  frontend-tests:
    name: Frontend Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run Jest tests
        run: |
          cd frontend
          npm test -- --coverage --watchAll=false

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/coverage-final.json
          flags: frontend

      - name: Build frontend
        run: |
          cd frontend
          npm run build

  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd tests/e2e
          npm ci
          npx playwright install --with-deps

      - name: Start backend
        run: |
          cd backend
          pip install -r requirements.txt
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 10

      - name: Start frontend
        run: |
          cd frontend
          npm ci
          npm start &
          sleep 10

      - name: Run Playwright tests
        run: |
          cd tests/e2e
          npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: tests/e2e/playwright-report/

  lint:
    name: Code Quality
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12.0'

      - name: Lint backend with ruff
        run: |
          pip install ruff
          cd backend
          ruff check .

      - name: Type check with mypy
        run: |
          pip install mypy
          cd backend
          mypy app/

      - name: Lint frontend with ESLint
        run: |
          cd frontend
          npm ci
          npm run lint
```

### 2. Deployment Workflow (Backend)

```yaml
# .github/workflows/deploy-backend.yml
name: Deploy Backend to Render

on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
  workflow_dispatch:

jobs:
  deploy:
    name: Deploy to Render
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Trigger Render Deployment
        env:
          RENDER_DEPLOY_HOOK: ${{ secrets.RENDER_DEPLOY_HOOK }}
        run: |
          curl -X POST $RENDER_DEPLOY_HOOK

      - name: Wait for deployment
        run: sleep 60

      - name: Health check
        env:
          BACKEND_URL: ${{ secrets.RENDER_BACKEND_URL }}
        run: |
          response=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/health)
          if [ $response -ne 200 ]; then
            echo "Health check failed with status $response"
            exit 1
          fi
          echo "Health check passed"

      - name: Smoke tests
        env:
          BACKEND_URL: ${{ secrets.RENDER_BACKEND_URL }}
        run: |
          # Test critical endpoints
          curl -f $BACKEND_URL/healthz || exit 1
          curl -f $BACKEND_URL/api/courses || exit 1
          echo "Smoke tests passed"

      - name: Send Slack notification
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Backend deployment to Render: ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 3. Deployment Workflow (Frontend)

```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend to Vercel

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
  workflow_dispatch:

jobs:
  deploy:
    name: Deploy to Vercel
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm install -g vercel

      - name: Deploy to Vercel
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
        run: |
          cd frontend
          vercel deploy --prod --token=$VERCEL_TOKEN

      - name: Wait for deployment
        run: sleep 30

      - name: Health check
        env:
          FRONTEND_URL: ${{ secrets.VERCEL_FRONTEND_URL }}
        run: |
          response=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL)
          if [ $response -ne 200 ]; then
            echo "Health check failed with status $response"
            exit 1
          fi
          echo "Frontend health check passed"

      - name: E2E smoke test
        env:
          FRONTEND_URL: ${{ secrets.VERCEL_FRONTEND_URL }}
        run: |
          cd tests/e2e
          npm ci
          npx playwright install --with-deps
          FRONTEND_URL=$FRONTEND_URL npx playwright test smoke.spec.js

      - name: Send Slack notification
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Frontend deployment to Vercel: ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 4. Nightly Full Test Suite

```yaml
# .github/workflows/nightly.yml
name: Nightly Full Test Suite

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
  workflow_dispatch:

jobs:
  full-test-suite:
    name: Full Test Suite
    runs-on: ubuntu-latest
    timeout-minutes: 60

    steps:
      - uses: actions/checkout@v4

      - name: Run all backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest tests/ -v --tb=short

      - name: Run all frontend tests
        run: |
          cd frontend
          npm ci
          npm test -- --watchAll=false

      - name: Run full E2E suite
        run: |
          cd tests/e2e
          npm ci
          npx playwright install --with-deps
          npx playwright test

      - name: Load testing
        run: |
          # Install k6 or use Docker
          docker run --rm -v $(pwd)/tests/load:/scripts grafana/k6 run /scripts/load-test.js

      - name: Generate test report
        if: always()
        run: |
          echo "Test results summary" > test-report.md
          echo "Backend: $(cat backend/test-results.xml | grep tests | head -1)" >> test-report.md

      - name: Send report
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Nightly test suite: ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## Health Check Endpoints

Ensure these endpoints are properly implemented:

```python
# In backend/app/main.py

@app.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if service is running.
    """
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/healthz")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with dependencies.
    Checks database connectivity and critical services.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "checks": {}
    }

    # Database check
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"

    # GHIN service check (optional)
    try:
        # Ping GHIN service
        health_status["checks"]["ghin"] = "healthy"
    except Exception as e:
        health_status["checks"]["ghin"] = f"degraded: {str(e)}"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)
```

## Rollback Procedures

```bash
# scripts/rollback.sh
#!/bin/bash

# Rollback backend to previous version on Render
rollback_backend() {
  echo "Rolling back backend..."
  # Render doesn't have direct rollback API, need to redeploy previous commit
  PREVIOUS_COMMIT=$(git rev-parse HEAD~1)
  git checkout $PREVIOUS_COMMIT
  git push -f render main
}

# Rollback frontend on Vercel
rollback_frontend() {
  echo "Rolling back frontend..."
  vercel rollback <deployment-url>
}

# Main rollback logic
if [ "$1" == "backend" ]; then
  rollback_backend
elif [ "$1" == "frontend" ]; then
  rollback_frontend
elif [ "$1" == "all" ]; then
  rollback_backend
  rollback_frontend
else
  echo "Usage: ./rollback.sh [backend|frontend|all]"
  exit 1
fi
```

## Success Criteria

- All PRs require passing CI checks (tests, lint, build)
- Automated deployment to staging and production
- Health checks pass before marking deployment as successful
- E2E smoke tests run after every deployment
- Deployment notifications sent to team (Slack/email)
- Zero-downtime deployments
- Automated rollback on health check failure
- Test coverage reports uploaded to Codecov
- Deployment time < 5 minutes

## Secrets Configuration

Add these secrets to GitHub repository settings:

```
# Render
RENDER_DEPLOY_HOOK=<deploy hook URL>
RENDER_BACKEND_URL=<production backend URL>

# Vercel
VERCEL_TOKEN=<Vercel API token>
VERCEL_ORG_ID=<org ID>
VERCEL_PROJECT_ID=<project ID>
VERCEL_FRONTEND_URL=<production frontend URL>

# Notifications
SLACK_WEBHOOK=<Slack webhook URL>

# Code coverage
CODECOV_TOKEN=<Codecov token>
```

## Commands to Run

```bash
# Test workflows locally with act
brew install act
act -l  # List all workflows
act pull_request  # Run PR workflow locally

# Manually trigger deployment
gh workflow run deploy-backend.yml

# View workflow runs
gh run list

# View logs
gh run view <run-id> --log
```
