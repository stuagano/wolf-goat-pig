# Codebase Organization Review

**Date:** 2026-02-25
**Scope:** Full repository structure, LLM-parsability, maintainability, and organic growth debt

---

## Executive Summary

Wolf Goat Pig is a ~135K LOC golf wagering simulation (FastAPI + React). The codebase has solid foundational architecture — clear backend/frontend split, proper service layers, and good test infrastructure — but organic growth has introduced significant structural debt that hurts both human navigation and LLM comprehension.

**Top 5 issues by impact:**

| # | Issue | Severity | Impact |
|---|-------|----------|--------|
| 1 | `backend/app/main.py` is 9,043 lines with 112 endpoints | CRITICAL | LLMs truncate/lose context; devs can't navigate |
| 2 | Tests fragmented across 4+ locations with diverged duplicates | CRITICAL | Tests silently drift out of sync |
| 3 | 42 loose component files in `frontend/src/components/` root | HIGH | No discoverability; feature boundaries unclear |
| 4 | Root directory cluttered with 11 markdown files + 7 shell scripts + 2 test files | HIGH | Unclear entry points; violates project conventions |
| 5 | Scoring logic duplicated across 4 backend files | HIGH | Risk of calculation mismatches |

---

## 1. Repository Root (50+ files)

### What's there

```
ROOT (selected files)
├── 11 markdown files (89.6 KB)     ← sprawl
├── 7 shell scripts                  ← 3 do roughly the same thing
├── 2 Python test files              ← violates CLAUDE.md rules
├── 3 docker-compose variants
├── 2 Python utility scripts
├── package.json, vercel.json, render.yaml
└── settings.json
```

### Problems

**Misplaced test files:**
- `test_multi_hole_tracking.py` (9.2 KB) — should be in `tests/`
- `test_sheet_sync_fix.py` (4.2 KB) — should be in `tests/`

**Shell script duplication — 3 dev startup scripts doing the same thing:**

| Script | Size | Approach |
|--------|------|----------|
| `dev.sh` | 1.5 KB | Wrapper delegating to `scripts/development/dev.sh` |
| `dev-local.sh` | 1.0 KB | Direct background process startup |
| `start-local.sh` | 2.0 KB | Venv-aware startup with more setup |

Similarly, `docker-dev.sh` (3.9 KB) and `podman-test.sh` (5.8 KB) duplicate the same container orchestration for different engines.

**Markdown sprawl — 11 files totaling 89.6 KB:**
- README.md, ARCHITECTURE_OVERVIEW.md, CLAUDE.md are appropriate at root
- DEPLOYMENT.md, DEPLOYMENT_CHECKLIST.md, DEVELOPER_QUICK_START.md, DOCKER-SETUP.md, README-DOCKER.md, GOLF_COURSE_OFFLINE_GUIDE.md, GOOGLE_SHEETS_LEADERBOARD_SETUP.md, RESILIENCE_GUIDE.md could live in `docs/guides/`
- DEPLOYMENT.md also exists in `docs/` with different content (neither is canonical)

### Recommendations

1. Move `test_*.py` files to `tests/integration/`
2. Consolidate dev scripts: keep one canonical `dev.sh` and document variants in its `--help`
3. Consolidate container scripts into one with a `--engine docker|podman` flag
4. Move guide-level markdown into `docs/guides/`, keep only README.md, CLAUDE.md, and ARCHITECTURE_OVERVIEW.md at root

---

## 2. Backend (`backend/`) — 66,732 lines Python

### Structure overview

```
backend/
├── app/
│   ├── main.py              9,043 lines  ← CRITICAL: monolithic
│   ├── wolf_goat_pig.py     3,999 lines  ← core game engine
│   ├── models.py              539 lines
│   ├── schemas.py             740 lines
│   ├── crud.py                  5 lines  ← stub, unused
│   ├── database.py             129 lines
│   ├── routers/             2,468 lines  (8 files — partial migration)
│   ├── routes/              EMPTY        ← dead directory
│   ├── services/           12,751 lines  (25 files)
│   ├── managers/            1,388 lines  (3 files)
│   ├── validators/          1,171 lines  (4 files + 1 misplaced test)
│   ├── domain/                806 lines  (3 files)
│   ├── state/                 406 lines  (3 files)
│   ├── middleware/             241 lines  (2 files)
│   ├── utils/                 694 lines  (3 files)
│   ├── migrations/             411 lines
│   ├── mixins/                 216 lines
│   ├── data/                   269 lines
│   └── [seed files, migration scripts, manual tests scattered in root]
├── archived/                4,229 lines  ← superseded game engine
├── tests/                  14,245 lines  (41 files — PRIMARY test location)
├── 27 markdown files at backend root
└── 19 Python scripts at backend root
```

### Critical: main.py is 9,043 lines

This single file contains **112 route decorators** — virtually every API endpoint. A partial migration to `routers/` was started (8 router files exist covering courses, players, sheets, health), but the vast majority of endpoints remain in main.py.

**LLM impact:** Any LLM asked to modify an endpoint must ingest or search through 9K lines. Context windows get consumed by irrelevant routes. Semantic boundaries between features are invisible.

**Recommendation:** Complete the router extraction. Group endpoints by domain:
- `routers/games.py` — game CRUD, lifecycle
- `routers/scoring.py` — score entry, calculations
- `routers/betting.py` — odds, wagers
- `routers/analytics.py` — stats, leaderboards
- `routers/admin.py` — admin operations
- (Keep existing: courses, players, sheets, health)

### Dead directory: `app/routes/`

The `app/routes/__init__.py` contains only `# Routes package`. All actual routing lives in `app/routers/`. This is confusing — delete `routes/`.

### Misplaced files in production code

| File | Location | Should be |
|------|----------|-----------|
| `notification_service_example.py` | `app/services/` | `docs/examples/` or deleted |
| `manual_test_simplified_scoring.py` | `app/` | `tests/manual/` |
| `manual_test_game_state_validator.py` | `app/validators/` | `tests/manual/` |
| `oauth2_email_service.py` (25 lines, deprecated) | `app/services/` | deleted |
| `crud.py` (5-line stub) | `app/` | deleted |

### Scoring logic duplication (4 implementations)

| File | Lines | Role |
|------|-------|------|
| `wolf_goat_pig.py` | 3,999 | Original game engine with `_calculate_partners_points`, `_calculate_solo_points` |
| `simplified_scoring.py` | 220 | Alternative "streamlined" scoring |
| `managers/scoring_manager.py` | 928 | Dedicated scoring manager |
| `services/score_calculation_service.py` | 596 | Unified scoring service (consolidation attempt) |

A consolidation effort was started with `score_calculation_service.py` but the old implementations remain. Risk of calculation mismatches between paths.

**Recommendation:** Audit which scoring path is actually called at runtime. Deprecate/remove the others. Single source of truth for score calculations.

### Backend root clutter (46 files)

The `backend/` root contains 27 markdown files and 19 Python utility scripts that should be organized:
- `startup.py` (1,261 lines), `render-startup.py` (226 lines) — entry points, OK at root
- `smoke_tests.py`, `test_rule_manager.py`, `test_complete_game.py` — move to `tests/`
- `manual_test_full_round_api.py`, `manual_test_scoring_mode.py`, `manual_ghin_check.py` — move to `tests/manual/`
- `extract_routers.py`, `lint_db_transactions.py`, `verify_phase1_features.py` — move to `scripts/`
- `example_rule_manager_integration.py` — move to `docs/examples/` or delete

---

## 3. Frontend (`frontend/`) — ~68,289 lines JS/JSX/TS/TSX

### Structure overview

```
frontend/src/
├── components/           42 loose files + 11 subdirectories
│   ├── game/            13 files, 9,411 LOC  (SimpleScorekeeper.jsx = 3,944!)
│   ├── auth/             8 files
│   ├── tutorial/         8 files, 2,715 LOC
│   ├── signup/           6 files, 2,744 LOC
│   ├── admin/            1 file
│   ├── analytics/        1 file
│   ├── practice/         1 file
│   ├── common/           1 file
│   ├── email/            1 file
│   ├── ui/               4 TypeScript files
│   └── __tests__/       11 test files
├── pages/               14 files, 8,054 LOC
├── hooks/               20 files (some very large)
├── services/             6 files
├── context/              3 files
├── constants/            3 files
├── utils/                5 files
└── config/               2 files
```

### 42 loose component files

The `components/` root has 42 files that aren't organized into feature directories. These include:
- 3 betting components (BettingOddsPanel 881 LOC, EnhancedBettingWidget 462 LOC, BettingOpportunityWidget 124 LOC)
- 3 analytics components (AnalyticsDashboard 567 LOC, WGPAnalyticsDashboard 461 LOC, PerformanceAnalytics 451 LOC)
- 3 visualization components (HoleVisualization 432 LOC, ShotVisualizationOverlay 435 LOC, ProbabilityVisualization 403 LOC)
- Navigation.js (618 LOC), EnhancedWGPInterface.js (893 LOC), PlayerStatistics.js (651 LOC), etc.

**LLM impact:** When an LLM is asked "fix the betting display", it has no directory signal for where betting code lives. It must search 42+ files by name pattern.

**Recommendation:** Create feature directories:
- `components/betting/` — BettingOddsPanel, EnhancedBettingWidget, BettingOpportunityWidget
- `components/analytics/` — AnalyticsDashboard, WGPAnalyticsDashboard, PerformanceAnalytics
- `components/visualization/` — Hole, Shot, Probability visualizations
- `components/scoring/` — EnhancedScoringWidget, ScoreInputField
- `components/layout/` — Navigation, GameBanner, etc.

### Oversized files

| File | Lines | Issue |
|------|-------|-------|
| `SimpleScorekeeper.jsx` | 3,944 | Should be decomposed into sub-components |
| `AdminPage.js` | 1,628 | Should extract admin sections into feature components |
| `useOddsCalculation.js` | 11,477 | Hook is larger than most entire modules |
| `TutorialContext.js` | 15,220 | Context provider doing too much |
| `useGameState.js` | 10,852 | Very large hook |
| `useTutorialProgress.js` | 9,754 | Very large hook |
| `colors.js` | 9,427 | Extremely large constants file |
| `cacheManager.js` | 7,951 | Service doing too much |
| `offlineGameManager.js` | 7,944 | Service doing too much |

Several hooks and services are 7K-15K lines — these are effectively entire modules crammed into single files. LLMs will struggle to hold these in context alongside the components that use them.

### Near-duplicate components

- **Betting:** BettingOddsPanel vs EnhancedBettingWidget — overlapping UI with different sizes
- **Analytics:** AnalyticsDashboard vs WGPAnalyticsDashboard vs PerformanceAnalytics — three dashboard variants
- **Scoring:** EnhancedScoringWidget vs ScoreInputField vs scoring logic in SimpleScorekeeper

---

## 4. Test Organization — CRITICAL FRAGMENTATION

### Test locations (4+ places)

| Location | Files | Role | Status |
|----------|-------|------|--------|
| `backend/tests/` | 41 | Primary backend tests | ACTIVE, most complete |
| `tests/backend/` | 35 | Secondary backend tests | OUTDATED copies |
| `tests/bdd/` | BDD features | Behave/Gherkin tests | Active |
| `tests/integration/` | Integration tests | Cross-boundary tests | Active |
| `frontend/src/__tests__/` | 39 | Frontend unit tests | Active |
| `frontend/tests/e2e/` | E2E specs | Playwright E2E | Active |
| Root directory | 2 | Ad-hoc test files | Misplaced |
| `backend/` root | 4+ | Manual test scripts | Misplaced |

### Diverged duplicate tests

**CRITICAL:** Two test files exist in both `backend/tests/` and `tests/backend/` with different content:

| Test file | `backend/tests/` | `tests/backend/` | Drift |
|-----------|-------------------|-------------------|-------|
| `test_aardvark.py` | 331 lines | 182 lines | 149 lines missing from copy |
| `test_post_hole_analytics.py` | 590 lines | 349 lines | 241 lines missing from copy |

This means running tests from different directories produces different results. The `tests/backend/` copies are incomplete/outdated.

### Recommendations

1. **Choose one backend test home.** `backend/tests/` is more complete — make it canonical.
2. **Audit `tests/backend/`:** Diff every file against `backend/tests/`. Merge any unique tests into the canonical location, then remove the duplicate directory.
3. **Move root test files:** `test_multi_hole_tracking.py` and `test_sheet_sync_fix.py` into `tests/integration/`.
4. **Move backend manual tests:** `manual_test_*.py` and `smoke_tests.py` into `backend/tests/manual/`.

---

## 5. Documentation — 385 Markdown Files

### Distribution

| Location | Files | Size | Purpose |
|----------|-------|------|---------|
| Root | 11 | 89.6 KB | Top-level guides |
| `docs/` | 66 | 841 KB | Reference documentation |
| `backend/` root | 27 | ~200 KB | Backend-specific docs |
| `.claude/` | 242 | 1.9 MB | Auto-generated agent configs |
| `product/` | ~13 | 80 KB | Product specs & component designs |

### Key issues

1. **DEPLOYMENT.md exists in both root and `docs/`** with different content (root: 265 lines, docs: 315 lines). Neither is canonical.

2. **Stale docs:**
   - `docs/status/current-state.md` — last updated Oct 2025 (4+ months old)
   - `docs/TODO.md` — last updated Aug 2025, references deprecated "BMad Method"

3. **Root markdown sprawl:** 8 of the 11 root markdown files are guides that belong in `docs/guides/`.

4. **Backend root has 27 markdown files** — most are architecture/implementation notes that should be in `docs/architecture/` or `docs/development/`.

---

## 6. LLM-Parsability Score Card

How well can an LLM navigate and understand this codebase?

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Directory naming** | 7/10 | Good names, but `routers/` vs `routes/` and dual test dirs confuse |
| **File sizes** | 3/10 | main.py (9K), hooks (7-15K), SimpleScorekeeper (4K) blow context windows |
| **Feature boundaries** | 4/10 | 42 loose components, scoring in 4 places, no clear ownership |
| **Dead code clarity** | 5/10 | `archived/` dir is good, but stubs, examples, and deprecated files linger in production paths |
| **Test discoverability** | 3/10 | 4+ test locations, diverged duplicates, misplaced files |
| **Entry point clarity** | 6/10 | README is solid, but monolithic main.py obscures API structure |
| **Import structure** | 6/10 | Services/managers are clean, but main.py imports from everywhere |
| **Documentation findability** | 5/10 | Good content, but spread across root + docs/ + backend/ with duplicates |

**Overall: 4.9/10** — Functional but significantly hampered by organic growth debt.

---

## 7. Prioritized Action Plan

### Phase 1: Quick Wins (no logic changes, low risk)

- [ ] Delete `backend/app/routes/` (empty dead directory)
- [ ] Delete `backend/app/crud.py` (5-line stub)
- [ ] Delete `backend/app/services/oauth2_email_service.py` (deprecated 25-line wrapper)
- [ ] Move `test_multi_hole_tracking.py`, `test_sheet_sync_fix.py` from root to `tests/integration/`
- [ ] Move `backend/app/services/notification_service_example.py` to `docs/examples/` or delete
- [ ] Move `backend/app/manual_test_simplified_scoring.py` to `backend/tests/manual/`
- [ ] Move `backend/app/validators/manual_test_game_state_validator.py` to `backend/tests/manual/`
- [ ] Move backend root test scripts (`smoke_tests.py`, `test_rule_manager.py`, etc.) to `backend/tests/`

### Phase 2: Test Consolidation (medium risk, needs careful diffing)

- [ ] Diff every file in `tests/backend/` against `backend/tests/` counterpart
- [ ] Merge any unique test logic from `tests/backend/` into `backend/tests/`
- [ ] Remove `tests/backend/` once fully merged
- [ ] Update pytest config / CI workflows to point to canonical test location

### Phase 3: Documentation Consolidation

- [ ] Move root guide-level markdown (DEPLOYMENT.md, DOCKER-SETUP.md, etc.) into `docs/guides/`
- [ ] Resolve the dual DEPLOYMENT.md (root vs docs/) — merge into single canonical file
- [ ] Move backend root markdown files into `docs/architecture/` or `docs/development/`
- [ ] Update `docs/status/current-state.md`
- [ ] Archive or remove `docs/TODO.md` (references deprecated BMad methodology)

### Phase 4: Backend Decomposition (higher effort, significant impact)

- [ ] Extract remaining endpoints from `main.py` into domain-specific routers
- [ ] Audit scoring logic: determine canonical path, deprecate alternatives
- [ ] Move backend root utility scripts into `backend/scripts/`
- [ ] Organize seed files into `backend/app/seeds/` directory

### Phase 5: Frontend Reorganization

- [ ] Create feature directories under `components/` (betting/, analytics/, visualization/, scoring/, layout/)
- [ ] Move the 42 loose component files into appropriate feature dirs
- [ ] Split `SimpleScorekeeper.jsx` (3,944 lines) into sub-components
- [ ] Evaluate consolidation of near-duplicate components (betting, analytics)
- [ ] Consider splitting oversized hooks (useOddsCalculation 11K, useGameState 10K, etc.)

### Phase 6: Script Cleanup

- [ ] Consolidate `dev.sh`, `dev-local.sh`, `start-local.sh` into one script with flags
- [ ] Merge `docker-dev.sh` and `podman-test.sh` into one script with `--engine` flag
- [ ] Move remaining root shell scripts into `scripts/` subdirectories
