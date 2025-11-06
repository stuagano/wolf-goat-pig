# Wolf-Goat-Pig Resilience & Fallback Architecture

## Overview

The Wolf-Goat-Pig application is designed to be resilient and work even when the backend database is unavailable or experiencing issues. This document explains the multi-layered resilience architecture.

## Architecture Layers

```
┌─────────────────────────────────────────┐
│   Frontend (Client-Side First)         │
│  ┌─────────────────────────────────┐   │
│  │  React State (GameProvider)     │   │
│  │  + localStorage persistence     │   │
│  │  + Offline Game Manager         │   │
│  └─────────────────────────────────┘   │
└───────────────┬─────────────────────────┘
                │ API Calls (optional)
┌───────────────▼─────────────────────────┐
│   Backend API (FastAPI)                 │
│  ┌─────────────────────────────────┐   │
│  │  Try: Database Persistence      │   │
│  │  Catch: Fallback Memory Mode    │   │
│  │  Always: Return game state      │   │
│  └─────────────────────────────────┘   │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│   Database (PostgreSQL/SQLite)          │
│   Optional - game works without it      │
└─────────────────────────────────────────┘
```

## Resilience Features

### 1. Client-Side Persistence (Frontend)

**Location:** `frontend/src/hooks/useGamePersistence.js`

**Features:**
- Automatically saves game state to `localStorage` every second (debounced)
- Keeps a backup of the previous state
- Detects abandoned games (games saved within last 24 hours)
- Works completely offline

**Usage:**
```javascript
import { useGamePersistence } from './hooks/useGamePersistence';

const { saveToLocal, loadFromLocal, getAbandonedGame } = useGamePersistence(gameState, isActive);

// On component mount, check for abandoned games
const abandoned = getAbandonedGame();
if (abandoned) {
  // Prompt user to continue
}

// Manual save/load
saveToLocal(gameState);
const loaded = loadFromLocal();
```

### 2. Offline Game Manager (Frontend)

**Location:** `frontend/src/services/offlineGameManager.js`

**Features:**
- Creates games entirely client-side without backend
- Manages game state locally
- Can sync to backend when it becomes available
- Generates unique game IDs and join codes

**Usage:**
```javascript
import offlineGameManager from './services/offlineGameManager';

// Create offline game
const gameState = offlineGameManager.createOfflineGame({
  players: [...],
  player_count: 4,
  course_name: 'Pebble Beach'
});

// Complete a hole offline
const updated = offlineGameManager.completeOfflineHole(gameState, {
  hole_number: 1,
  player_scores: {...},
  winner: 'player1',
  wager: 2
});

// Try to sync when backend is available
const result = await offlineGameManager.syncOfflineGame(gameState, API_URL);
if (result.success) {
  console.log('Synced to backend:', result.backend_game_id);
}
```

### 3. Fallback Memory Mode (Backend)

**Location:** `backend/app/fallback_game_manager.py`

**Features:**
- In-memory game storage when database fails
- Automatic fallback on database errors
- Games persist until server restart
- All game operations continue to work

**Automatic Usage:**
When any database operation fails, the backend automatically:
1. Logs the database error as a warning
2. Enables fallback mode
3. Creates/updates the game in memory
4. Returns success with a `fallback_mode: true` flag

**Manual Control:**
```python
from app.fallback_game_manager import get_fallback_manager

fallback = get_fallback_manager()

# Manually enable fallback mode
fallback.enable()

# Check status
stats = fallback.get_stats()
print(stats)  # {'enabled': True, 'total_games': 5, ...}

# Disable (clears all games)
fallback.disable()
```

### 4. Graceful Degradation (Backend)

**Location:** `backend/app/main.py` (updated endpoints)

**Features:**
- API endpoints try database first, fallback to memory on error
- Clear warnings in responses when using fallback mode
- Game functionality never breaks due to database issues

**Example Response (Fallback Mode):**
```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "join_code": "ABC123",
  "status": "in_progress",
  "warning": "Game created in memory only - will be lost on server restart",
  "fallback_mode": true,
  "persistence": "memory"
}
```

**Example Response (Normal Mode):**
```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "join_code": "ABC123",
  "status": "in_progress",
  "persistence": "database"
}
```

## When Each Layer Activates

### Scenario 1: Database Schema Issue (e.g., missing column)
```
1. User creates game via frontend
2. Frontend calls POST /games/create-test
3. Backend tries database save → FAILS (missing column)
4. Backend enables fallback mode → SUCCESS (memory)
5. Backend returns game with fallback_mode: true
6. Frontend receives game and saves to localStorage
7. ✅ Game works! User sees warning about memory-only storage
```

### Scenario 2: Backend is Down
```
1. User creates game via frontend
2. Frontend calls POST /games/create-test → FAILS (network error)
3. Frontend catches error and uses offlineGameManager
4. offlineGameManager creates game client-side → SUCCESS
5. Frontend saves to localStorage
6. ✅ Game works completely offline!
7. When backend comes back online, game can be synced
```

### Scenario 3: Everything Works Normally
```
1. User creates game via frontend
2. Frontend calls POST /games/create-test
3. Backend saves to database → SUCCESS
4. Backend returns game with persistence: "database"
5. Frontend also saves to localStorage (for offline recovery)
6. ✅ Game works with full persistence!
```

## Migration Resilience

The application includes automatic database migrations that run on startup. If migrations fail:

1. **Development:** App continues in fallback mode (games work in memory)
2. **Production:** App fails fast and logs the error (prevents data corruption)

See [MIGRATION_GUIDE.md](backend/MIGRATION_GUIDE.md) for details.

## Testing Resilience

### Test Fallback Mode

```bash
# Start the backend
cd backend
python -m uvicorn app.main:app

# In another terminal, force fallback mode
curl -X POST http://localhost:8000/games/create-test?player_count=4

# Check if it worked - you should see fallback_mode: true in response
```

### Test Offline Mode (Frontend)

```javascript
// In your browser console
// 1. Disable network (Developer Tools → Network → Offline)
// 2. Try to create a game
// 3. Check localStorage
localStorage.getItem('wolf-goat-pig-game-state');

// 4. Re-enable network
// 5. Try to sync
```

### Test Database Migration Failure

```bash
# Temporarily make the database read-only or corrupt schema
# The app should:
# 1. Log migration failure
# 2. Enable fallback mode
# 3. Continue to accept game creation requests
# 4. Return fallback_mode: true in responses
```

## Monitoring & Alerts

### Backend Logs to Monitor

```bash
# Database is working normally
✅ Created test game <id> in database with 4 mock players

# Fallback mode activated
⚠️ Database save failed: (psycopg2.errors.UndefinedColumn) column game_state.game_id does not exist
🔄 Attempting fallback mode...
⚠️ Created test game <id> in FALLBACK MODE (memory only)

# Both failed (rare)
❌ Both database and fallback mode failed: <error>
```

### Frontend Logs to Monitor

```javascript
// Check browser console for:
'[Persistence] Game state saved to localStorage'
'[Offline] Created offline game: <id>'
'[Offline] Successfully synced game to backend: <id>'
```

## Best Practices

### For Development

1. **Use fallback mode liberally** - don't let database issues block development
2. **Test offline mode** - ensure all features work client-side
3. **Mock API failures** - test resilience regularly

### For Production

1. **Monitor fallback mode activation** - it should be rare
2. **Alert on database failures** - fix schema issues immediately
3. **Provide user feedback** - show warnings when in fallback/offline mode

### For Users

The app shows clear indicators:
- **Green indicator**: Full persistence (database + localStorage)
- **Yellow indicator**: Fallback mode (memory + localStorage)
- **Orange indicator**: Offline mode (localStorage only)

## Environment Variables

```bash
# Force fallback mode (useful for testing)
FORCE_FALLBACK_MODE=true

# Disable fallback mode (fail fast on database errors)
DISABLE_FALLBACK_MODE=true

# Enable verbose logging for resilience
RESILIENCE_LOG_LEVEL=DEBUG
```

## Troubleshooting

### "Game lost after server restart"

**Cause:** Game was created in fallback mode (memory only)

**Solution:**
1. Check if database is working: `python backend/fix_game_state_schema.py`
2. Restart application to trigger migrations
3. If game is in localStorage, it can still be loaded client-side

### "Cannot sync offline game to backend"

**Cause:** Backend endpoint `/game/import-offline` might not exist or database is still broken

**Solution:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check database schema: see [MIGRATION_GUIDE.md](backend/MIGRATION_GUIDE.md)
3. Game still works offline - users can continue playing

### "localStorage quota exceeded"

**Cause:** Too many games saved locally (rare, ~5MB limit)

**Solution:**
```javascript
// Clear old games from localStorage
const games = JSON.parse(localStorage.getItem('wolf-goat-pig-game-state'));
// Keep only recent game
localStorage.removeItem('wolf-goat-pig-game-backup');
```

## Future Enhancements

- [ ] IndexedDB support for larger storage (can store 100s of games)
- [ ] Progressive Web App (PWA) for true offline support
- [ ] Background sync when backend becomes available
- [ ] Multi-device sync via WebSockets
- [ ] Conflict resolution for concurrent edits

## Related Files

- `frontend/src/hooks/useGamePersistence.js` - localStorage persistence
- `frontend/src/services/offlineGameManager.js` - Offline game creation
- `backend/app/fallback_game_manager.py` - Memory-based fallback
- `backend/app/main.py` - API endpoints with fallback logic
- `backend/MIGRATION_GUIDE.md` - Database migration documentation
