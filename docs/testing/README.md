# Testing Documentation

**Complete testing remediation plan for Wolf Goat Pig**

---

## 📁 Documentation Structure

```
docs/testing/
├── README.md                              # This file
├── COMPREHENSIVE_TESTING_PLAN.md          # Full 10-week plan (detailed)
├── QUICK_START_GUIDE.md                   # Get started in 15 minutes
└── PROGRESS_TRACKER.md                    # Track your progress
```

---

## 🎯 Quick Links

### **New to Testing Remediation?**
→ Start with **[QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md)**

### **Need the Full Plan?**
→ Read **[COMPREHENSIVE_TESTING_PLAN.md](./COMPREHENSIVE_TESTING_PLAN.md)**

### **Ready to Execute?**
→ Use **[PROGRESS_TRACKER.md](./PROGRESS_TRACKER.md)**

---

## 📊 Current State Summary

**Baseline Coverage** (Before Remediation):
- Backend: ~25-30%
- Frontend: ~25-35%
- Auth Components: 0%
- API Endpoints: ~10% (12 of 114)
- BDD Scenarios: 41 scenarios
- Total Tests: ~300

**Critical Gaps**:
1. 🚨 **Backend Core Simulation** (3,868 lines, 15% coverage)
2. 🚨 **Frontend Authentication** (355 lines, 0% coverage)
3. 🚨 **API Endpoints** (90% untested)
4. 🚨 **Game Rules Validation** (missing critical scenarios)

---

## 🎯 Target State (After 10 Weeks)

**Target Coverage**:
- ✅ Backend: 85%+
- ✅ Frontend: 80%+
- ✅ Auth Components: 100%
- ✅ API Endpoints: 90%+ (100+ of 114)
- ✅ BDD Scenarios: 91+ scenarios
- ✅ Total Tests: 1,000+

**Quality Goals**:
- ✅ Zero accessibility violations
- ✅ Zero security vulnerabilities
- ✅ All critical modules > 95% coverage
- ✅ Load tested (50 concurrent users)

---

## 🚀 Getting Started

### 1. Read the Quick Start Guide (15 min)
```bash
cat docs/testing/QUICK_START_GUIDE.md
```

**You'll learn**:
- How to set up your environment
- Quick wins you can achieve today
- Daily checklists
- Essential commands

### 2. Review the Comprehensive Plan (30 min)
```bash
cat docs/testing/COMPREHENSIVE_TESTING_PLAN.md
```

**You'll understand**:
- 5 phases over 10 weeks
- Detailed task breakdowns
- Acceptance criteria
- Resource allocation

### 3. Start Tracking Progress (10 min)
```bash
cp docs/testing/PROGRESS_TRACKER.md docs/testing/MY_PROGRESS.md
# Edit MY_PROGRESS.md as you go
```

**You'll track**:
- Coverage trends
- Daily standups
- Blockers
- Milestone completion

---

## 📅 10-Week Roadmap

| Phase | Weeks | Focus | Deliverables |
|-------|-------|-------|--------------|
| **Phase 1** | 1-2 | Foundation & Security | Auth tests (185+), Fixtures |
| **Phase 2** | 3-4 | Backend Core Logic | Simulation tests (200+) |
| **Phase 3** | 5-6 | Frontend Components | Component tests (209+) |
| **Phase 4** | 7-8 | Integration & E2E | API tests (153+), BDD (20+) |
| **Phase 5** | 9-10 | Performance & Validation | Edge cases, load tests |

**Total Effort**: ~318 hours (8 weeks for 1 FTE, or 4 weeks for 2 FTEs)

---

## 🎯 Phase Overview

### Phase 1: Foundation & Critical Security (Weeks 1-2)

**Goal**: Fix infrastructure, 100% auth coverage

**Key Tasks**:
- Install dependencies (numpy, psutil, jest-axe)
- Create comprehensive test fixtures
- Test all auth components
- Update conftest.py

**Deliverables**: 6 test files, 185+ tests, 100% auth coverage

**Time**: 34 hours

---

### Phase 2: Core Game Logic (Weeks 3-4)

**Goal**: Test simulation engine, betting, scoring

**Key Tasks**:
- Wolf simulation core (75+ tests)
- Betting decisions (45+ tests)
- Scoring & handicap (40+ tests)
- Shot result domain (25+ tests)
- Team formation (15+ tests)

**Deliverables**: 5 test files, 200+ tests, 95% core coverage

**Time**: 66 hours

---

### Phase 3: Frontend Components & Hooks (Weeks 5-6)

**Goal**: Test critical components and hooks

**Key Tasks**:
- SimulationDecisionPanel (35+ tests)
- HoleVisualization (25+ tests)
- GamePage expansion (39+ tests)
- useOddsCalculation (30+ tests)
- Other hooks (80+ tests)
- Accessibility audit (30+ components)

**Deliverables**: 8 test files, 209+ tests, 80% frontend coverage

**Time**: 70 hours

---

### Phase 4: Integration & E2E (Weeks 7-8)

**Goal**: API endpoints, BDD scenarios, E2E flows

**Key Tasks**:
- API endpoints comprehensive (100+ tests)
- BDD game rules core (12 scenarios)
- BDD betting decisions (8 scenarios)
- E2E complete game flow (10+ tests)
- API integration (23+ tests)

**Deliverables**: 5 files, 153+ tests, 20+ BDD scenarios

**Time**: 76 hours

---

### Phase 5: Performance & Validation (Weeks 9-10)

**Goal**: Final scenarios, edge cases, performance

**Key Tasks**:
- BDD Aardvark mechanics (8 scenarios)
- BDD game phases (6 scenarios)
- Edge cases comprehensive (63+ tests)
- Performance benchmarks (15+ tests)
- Load testing (50 concurrent users)
- Coverage validation

**Deliverables**: 6 files, 100+ tests, final validation

**Time**: 72 hours

---

## 🛠️ Essential Commands

### Run Tests

```bash
# Backend - all tests with coverage
cd backend
pytest --cov=app --cov-report=html --cov-report=term -v

# Frontend - all tests with coverage
cd frontend
npm test -- --coverage --watchAll=false

# BDD - all scenarios
cd tests/bdd/behave
behave --format pretty

# E2E - all tests
cd tests/e2e
npx playwright test
```

### Check Coverage

```bash
# Backend coverage report
open backend/htmlcov/index.html

# Frontend coverage report
open frontend/coverage/lcov-report/index.html

# Quick terminal summary
cd backend && pytest --cov=app --cov-report=term | grep TOTAL
cd frontend && npm test -- --coverage --watchAll=false | grep "All files"
```

---

## 📈 Success Metrics

### Coverage Targets

| Category | Before | After | Target |
|----------|--------|-------|--------|
| Backend Overall | 28% | → | **85%** |
| Backend Critical | 15% | → | **95%** |
| Frontend Overall | 30% | → | **80%** |
| Frontend Auth | 0% | → | **100%** |
| API Endpoints | 10% | → | **90%** |
| BDD Rules | 10% | → | **90%** |

### Quality Metrics

- ✅ Zero accessibility violations (jest-axe)
- ✅ Zero high/critical security issues
- ✅ All tests passing in CI/CD
- ✅ Load test: 50 concurrent users @ < 500ms p95
- ✅ No flaky tests

---

## 👥 Team Recommendations

### Solo Developer (10 weeks)
Follow phases sequentially, 30-35 hours/week

### 2 Developers (5 weeks)
- Dev 1: Backend (Phases 1, 2, 4)
- Dev 2: Frontend (Phases 1, 3, 4)
- Both: Phase 5

### 3 Developers (3-4 weeks)
- Backend Dev: Phases 1-2
- Frontend Dev: Phases 1, 3
- QA Engineer: Phases 4-5
- All: Integration

---

## 📚 Additional Resources

### Testing Agents (Claude Code)
Specialized agents to help with testing:
- `/.claude/agents/test-coverage-agent.md` - Backend testing
- `/.claude/agents/component-testing-agent.md` - Frontend testing
- `/.claude/agents/rules-validation-agent.md` - BDD scenarios

### Testing Skills (Claude Code)
Reusable skills for common tasks:
- `/.claude/skills/run-all-tests.md` - Run complete test suite
- `/.claude/skills/analyze-test-coverage.md` - Coverage analysis
- `/.claude/skills/check-code-quality.md` - Linting & formatting

### Project Documentation
- `/docs/prd.md` - Product requirements
- `/docs/architecture/` - Architecture docs
- `/docs/status/` - Current status

---

## 🆘 Troubleshooting

### Dependencies
**Problem**: Tests skipped with "Required imports not available"
**Solution**: `pip install numpy psutil pytest-cov`

### Coverage
**Problem**: Coverage shows 0%
**Solution**: Ensure `--cov=app` not `--cov=.`

### BDD
**Problem**: Step definitions not found
**Solution**: Check `tests/bdd/behave/steps/__init__.py` imports

### E2E
**Problem**: Playwright tests fail
**Solution**: `npx playwright install --with-deps`

---

## ✅ Quick Checklist Before Starting

- [ ] Python 3.11+ or 3.12 installed
- [ ] Node.js 18+ installed
- [ ] Git repo cloned and up to date
- [ ] Read QUICK_START_GUIDE.md
- [ ] Reviewed COMPREHENSIVE_TESTING_PLAN.md
- [ ] Copied PROGRESS_TRACKER.md to track progress
- [ ] Created feature branch: `feature/testing-remediation`
- [ ] Team aligned on approach

---

## 🎉 Let's Go!

**Ready to start?**

1. 📖 Read the [Quick Start Guide](./QUICK_START_GUIDE.md)
2. 📋 Review the [Comprehensive Plan](./COMPREHENSIVE_TESTING_PLAN.md)
3. 📊 Use the [Progress Tracker](./PROGRESS_TRACKER.md)
4. 🚀 Pick a quick win and start coding!

**Questions?** Contact the project tech lead or open an issue.

---

**Last Updated**: 2025-10-21
**Plan Version**: 1.0
**Status**: Ready for Execution
