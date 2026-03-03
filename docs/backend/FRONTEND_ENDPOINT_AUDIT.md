# Frontend Endpoint Usage Audit

**Audit Date:** 2025-11-10
**Frontend Directory:** `/home/user/wolf-goat-pig/frontend/src`

---

## ✅ Endpoints ACTIVELY USED by Frontend

### Production Multiplayer Flow (6 endpoints - KEEP)

```javascript
// Game creation & joining
POST /games/create                           // CreateGamePage.js, TestMultiplayerPage.js
POST /games/join/{join_code}                 // JoinGamePage.js, TestMultiplayerPage.js

// Lobby & game lifecycle
GET  /games/{gameId}/lobby                   // GameLobbyPage.js
POST /games/{gameId}/start                   // GameLobbyPage.js

// Game state & scoring
GET  /games/{gameId}/state                   // UnifiedGameInterface.js, SimpleScorekeeperPage.js
POST /games/{gameId}/holes/complete          // SimpleScorekeeper.jsx ✅ MAIN SCORING ENDPOINT

// Helper endpoints
GET  /games/{gameId}/next-rotation           // SimpleScorekeeper.jsx
GET  /games/{gameId}/next-hole-wager         // SimpleScorekeeper.jsx
PATCH /games/{gameId}/players/{id}/name      // SimpleScorekeeper.jsx
```

**Status:** ✅ **KEEP ALL** - These form the clean production flow

---

### Simulation Mode (12 endpoints - REVIEW)

```javascript
// Setup & play
POST /simulation/setup                       // SimulationMode.js, ScorerMode.js, GamePage.js
POST /simulation/play-hole                   // SimulationMode.js, ScorerMode.js
POST /simulation/next-hole                   // SimulationMode.js, ScorerMode.js
POST /simulation/play-next-shot              // SimulationMode.js, useSimulationApi.js

// AI & decision support
GET  /simulation/available-personalities     // SimulationMode.js, useSimulationApi.js
GET  /simulation/suggested-opponents         // SimulationMode.js, useSimulationApi.js
GET  /simulation/shot-probabilities          // useSimulationApi.js
POST /simulation/betting-decision            // SimulationMode.js, useSimulationApi.js

// State views
GET  /simulation/poker-state                 // SimulationMode.js, ScorerMode.js
GET  /simulation/timeline                    // SimulationMode.js
GET  /simulation/post-hole-analytics/{hole}  // usePostHoleAnalytics.js

// Save results
POST /simulation/save-results                // RoundSummary.jsx

// Monte Carlo
POST /simulation/monte-carlo                 // MonteCarloSimulation.js
```

**Question:** Are simulation endpoints still needed or can this be merged with production flow?

---

### Legacy Endpoints (5 endpoints - USED BUT DEPRECATED)

```javascript
// OLD GamePage.js still uses these:
GET  /game/state                             // GamePage.js, useGameApi.js
GET  /game/tips                              // GamePage.js, useGameApi.js
GET  /game/player_strokes                    // GamePage.js, useGameApi.js
POST /game/start                             // useGameApi.js
POST /game/action                            // GamePage.js, useGameApi.js
```

**Status:** ⚠️ **DELETE** - GamePage.js appears to be old code, replaced by UnifiedGameInterface.js

---

### Simplified Mode (2 endpoints - USED)

```javascript
POST /wgp/simplified/start-game              // GameScorerPage.js
POST /wgp/simplified/score-hole              // (implied by GameScorerPage.js)
```

**Question:** Is this different from `/games/{gameId}/holes/complete`? Can they be merged?

---

### Unified Action API (1 endpoint - USED)

```javascript
POST /wgp/{game_id}/action                   // EnhancedWGPInterface.js, AnalyticsDashboard.js
```

**Question:** What's the difference vs `/games/{gameId}/action`?

---

### Other APIs (USED)

```javascript
// Betting
POST /api/games/{gameId}/betting-events      // bettingApi.js

// Odds calculation
POST /api/wgp/calculate-odds                 // BettingOddsPanel.js, useOddsCalculation.js
POST /api/wgp/quick-odds                     // useOddsCalculation.js

// Shot analysis
POST /wgp/shot-range-analysis                // ShotRangeAnalyzer.js, ShotAnalysisWidget.js

// Course & player data
GET  /courses                                // GameSetup.tsx, SimulationMode.js
GET  /personalities                          // GameSetup.tsx
GET  /suggested_opponents                    // GameSetup.tsx
GET  /ghin/lookup?...                        // GameSetup.tsx

// Offline sync
POST /game/import-offline                    // offlineGameManager.js
```

---

## ❌ Endpoints NOT USED by Frontend

### Legacy Stubs (SAFE TO DELETE)

```python
# Backend defines these but frontend doesn't call them:
POST /game/setup                             # ❌ NOT USED
GET  /simulation/turn-based-state            # ❌ NOT USED
GET  /wgp/simplified/{game_id}/hole-history  # ❌ NOT USED (endpoint exists but not called)
```

---

## 📊 Summary by Category

| Category | Used | Not Used | Total | Action |
|----------|------|----------|-------|--------|
| **Production /games/\*** | 9 | 0 | 9 | ✅ KEEP |
| **Simulation /simulation/\*** | 13 | 1 | 14 | ❓ REVIEW |
| **Legacy /game/\*** | 5 | 2 | 7 | ⚠️ DELETE |
| **Simplified /wgp/simplified/\*** | 2 | 1 | 3 | ❓ MERGE? |
| **Unified /wgp/{id}/action** | 1 | 0 | 1 | ❓ CLARIFY |
| **Other APIs** | ~10 | ? | ? | ✅ KEEP |

---

## 🎯 Recommended Actions

### Phase 1: Delete Legacy Stubs (SAFE - Not Used)

**Remove these from backend:**
```python
POST /game/setup                    # Line 2860
GET  /simulation/turn-based-state   # Find and remove
GET  /wgp/simplified/{game_id}/hole-history  # Not called
```

**Remove from frontend:**
```javascript
// Delete or update GamePage.js (appears to be old)
// It still calls:
//   /game/state
//   /game/tips
//   /game/player_strokes
//   /game/action
//
// These should use /games/{gameId}/* equivalents instead
```

---

### Phase 2: Consolidate Simulation (REVIEW NEEDED)

**Questions:**
1. Can `/simulation/*` endpoints be merged with `/games/*` flow?
2. Is simulation mode a separate feature or can it use same endpoints?
3. Are poker-state and timeline views actually used in production?

**If simulation is just "practice mode":**
- Use POST /games/create-test (already exists!)
- Use same /games/{gameId}/holes/complete for scoring
- Remove all 12+ simulation-specific endpoints

---

### Phase 3: Merge Simplified Mode (REVIEW NEEDED)

**Currently:**
```javascript
// Simplified mode
POST /wgp/simplified/start-game
POST /wgp/simplified/score-hole

// Production mode
POST /games/create
POST /games/{gameId}/holes/complete
```

**These do the same thing!** Merge into one:
- Remove `/wgp/simplified/*`
- Update GameScorerPage.js to use `/games/*` endpoints

---

### Phase 4: Clarify Unified Action API

**Currently have:**
```javascript
POST /wgp/{game_id}/action          // EnhancedWGPInterface
POST /games/{game_id}/action         // (does this exist in backend?)
POST /game/action                    // Legacy (GamePage.js)
```

**Action:** Pick one, remove others.

---

## 📈 Expected Reduction

**Current:**
- ~126 total endpoints
- Multiple overlapping systems

**After cleanup:**
- ~35-40 core endpoints
- Single clear pattern

**Endpoints to KEEP:**
```
Production Flow (9):
  POST /games/create
  POST /games/create-test
  POST /games/join/{code}
  GET  /games/{id}/lobby
  POST /games/{id}/start
  GET  /games/{id}/state
  POST /games/{id}/holes/complete        ← Main scoring (works perfectly!)
  GET  /games/{id}/next-rotation
  GET  /games/{id}/next-hole-wager

Supporting APIs (~10):
  POST /api/wgp/calculate-odds
  POST /api/wgp/quick-odds
  GET  /courses
  GET  /personalities
  GET  /ghin/*
  ... etc
```

**Endpoints to REMOVE:**
```
Legacy (5):
  /game/state
  /game/tips
  /game/player_strokes
  /game/start
  /game/action
  /game/setup

Duplicates (if not needed):
  All /simulation/* if can use /games/* instead
  All /wgp/simplified/* if can use /games/* instead
```

---

## 🚀 Impact

**Code:**
- Delete ~60-80 endpoint handlers
- Delete ~1000+ lines of backend code
- Update ~10 frontend files to use consistent endpoints

**Performance:**
- Simpler routing
- Less code to maintain
- Fewer transaction edge cases
- Single clear pattern (commit-per-hole)

**Developer Experience:**
- One way to create games
- One way to score holes
- One way to get state
- Clear, obvious API

---

## 📝 Next Steps

1. **Confirm simulation mode usage:**
   - Is it actively used in production?
   - Can it share endpoints with main game?

2. **Update GamePage.js:**
   - Replace with UnifiedGameInterface.js
   - Or update to use /games/* endpoints

3. **Create deprecation PR:**
   - Mark legacy endpoints with warnings
   - Add "DEPRECATED" comments
   - Log warnings when called

4. **Execute cleanup:**
   - Delete unused endpoints
   - Update frontend to use consistent APIs
   - Update documentation

---

## ✅ Files That Need Updates

### Frontend Files Using Legacy Endpoints:
```
src/pages/GamePage.js              → DELETE or update to use /games/*
src/hooks/useGameApi.js            → UPDATE to use /games/*
src/pages/GameScorerPage.js        → UPDATE to use /games/* instead of /wgp/simplified/*
```

### Frontend Files Already Using Correct Pattern:
```
src/pages/CreateGamePage.js        ✅ Uses /games/create
src/pages/JoinGamePage.js          ✅ Uses /games/join
src/pages/GameLobbyPage.js         ✅ Uses /games/{id}/lobby & start
src/components/game/UnifiedGameInterface.js   ✅ Uses /games/{id}/state
src/components/game/SimpleScorekeeper.jsx     ✅ Uses /games/{id}/holes/complete
```

**Pattern:** The newer code already uses the right endpoints! Just need to remove old code.
