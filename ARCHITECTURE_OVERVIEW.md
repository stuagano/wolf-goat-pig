# Wolf-Goat-Pig Architecture Overview

## Two Separate Issues, Two Solutions

This document clarifies the architecture and separates two distinct concerns:

### Issue #1: Database Schema Problems (Backend Issue)
**Problem:** Database has wrong schema (missing `game_id` column)
**Solution:** Automatic migrations on startup
**Location:** Backend only

### Issue #2: Poor Golf Course Connectivity (User Issue)
**Problem:** Spotty cell signal while playing golf
**Solution:** Progressive Web App with offline capability
**Location:** Frontend with backend sync

---

## Issue #1: Database Schema Migrations

### The Problem
```
Backend is running ✅
Database is connected ✅
Schema is outdated ❌ ← This was your error

Error: column game_state.game_id does not exist
```

### The Solution
**Primary:** Automatic migrations on app startup

```python
# backend/app/main.py - Runs on every startup
@app.on_event("startup")
async def startup():
    # 1. Initialize database
    database.init_db()

    # 2. Run migrations (NEW!)
    logger.info("🔄 Running database migrations...")

    # Check for missing columns
    if 'game_id' not in columns:
        db.execute("ALTER TABLE game_state ADD COLUMN game_id VARCHAR")
        # Also adds created_at, updated_at

    # 3. Continue with app startup
```

**Backup:** Fallback mode if migration fails

```python
# If migration fails for any reason
try:
    save_to_database(game)
except SchemaError:
    fallback_manager.save_to_memory(game)
    return {"game": game, "fallback_mode": True}
```

### How It Works

```
App Starts
    ↓
Initialize DB Tables
    ↓
Check Schema ←─────────── This is the key part!
    ↓
Missing Columns?
    ├─ Yes → Add them (ALTER TABLE)
    └─ No → Continue
    ↓
App Ready ✅
```

### Files Involved
- `backend/app/main.py` (lines 296-367) - Migration logic
- `backend/startup.py` (lines 360-451) - Standalone migration
- `backend/fix_game_state_schema.py` - Manual migration script
- `backend/MIGRATION_GUIDE.md` - Full documentation

### When It Runs
- ✅ Every app startup (automatic)
- ✅ On demand (manual script)
- ✅ After deployment (initial migration)

### What It Fixes
- Missing `game_id` column
- Missing `created_at` column
- Missing `updated_at` column
- Any future schema changes

---

## Issue #2: Golf Course Offline Support

### The Problem
```
Backend is running ✅
Database is correct ✅
Cell signal is bad ❌ ← Golf course reality

User: "Can't load the app on hole 7"
```

### The Solution
**Progressive Web App (PWA)** with offline-first architecture

### Architecture

```
┌──────────────────────────────────────┐
│  User's Phone (On Golf Course)      │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Service Worker (PWA)          │ │
│  │  • Caches app files            │ │
│  │  • Handles offline requests    │ │
│  │  • Background sync             │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  React App                     │ │
│  │  • Game logic runs locally     │ │
│  │  • Saves to localStorage       │ │
│  │  • Queues API calls            │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  localStorage                  │ │
│  │  • Current game state          │ │
│  │  • Scores                      │ │
│  │  • Pending syncs               │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
         ↕ (sync when online)
┌──────────────────────────────────────┐
│  Backend Server (Clubhouse)          │
│  • Stores final game data            │
│  • Provides multi-device sync        │
│  • Generates leaderboards            │
└──────────────────────────────────────┘
```

### How It Works

#### 1. At Home/Clubhouse (Good WiFi):
```
User opens app
    ↓
Service Worker downloads app files
    ↓
Caches everything needed
    ↓
"Ready for Offline Use" ✅
```

#### 2. On Golf Course (No Signal):
```
User enters score
    ↓
Saves to localStorage immediately
    ↓
Tries to sync to server
    ↓
Network fails → Queue for later
    ↓
Shows "Offline" indicator 🟠
    ↓
Game continues normally ✅
```

#### 3. Back at Clubhouse (WiFi Returns):
```
App detects connection
    ↓
Processes sync queue
    ↓
Uploads all pending data
    ↓
"Sync Complete" ✅
    ↓
Shows "Online" indicator 🟢
```

### Files Involved
- `frontend/public/service-worker.js` - PWA caching logic
- `frontend/public/manifest.json` - App installation config
- `frontend/src/serviceWorkerRegistration.js` - SW registration
- `frontend/src/components/OfflineIndicator.js` - UI indicator
- `frontend/src/hooks/useGamePersistence.js` - localStorage hook
- `frontend/src/services/offlineGameManager.js` - Offline game logic
- `GOLF_COURSE_OFFLINE_GUIDE.md` - User guide

### What Gets Cached (Works Offline)
- ✅ All HTML, CSS, JavaScript
- ✅ Images and logos
- ✅ Game logic and rules
- ✅ Score calculation
- ✅ Wolf rotation
- ✅ Betting math

### What Needs Connection (Optional)
- ⚠️ Creating new games
- ⚠️ Joining existing games
- ⚠️ Real-time updates from other players
- ⚠️ Final sync to server

### User Experience

| Scenario | User Sees | What Happens |
|----------|-----------|--------------|
| Normal (online) | 🟢 Green indicator | Full sync to server |
| Spotty signal | 🟠 Orange indicator | Saves locally, syncs later |
| Back online | 🟡 Yellow "Syncing..." | Uploads queued data |
| Schema issue | 🟡 "Temporary storage" | Backend fallback mode |

---

## Combined Architecture

### The Full Stack

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                         │
│                                                     │
│  Install as PWA on Phone                           │
│    ↓                                                │
│  Service Worker Caches App                         │
│    ↓                                                │
│  Works Offline on Golf Course                      │
│    ↓                                                │
│  localStorage Persistence                          │
│    ↓                                                │
│  Queue API Calls for Later                        │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ HTTP/HTTPS (when online)
                  │
┌─────────────────▼───────────────────────────────────┐
│                    BACKEND API                      │
│                                                     │
│  Receives Requests                                 │
│    ↓                                                │
│  Try: Save to Database                             │
│    ↓                                                │
│  Catch: Use Fallback Mode                         │
│    ↓                                                │
│  Return: Game State + Status                       │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ SQL Queries
                  │
┌─────────────────▼───────────────────────────────────┐
│                   DATABASE                          │
│                                                     │
│  On Startup: Check Schema                          │
│    ↓                                                │
│  Missing Columns? Add Them                         │
│    ↓                                                │
│  Store: Game Data                                  │
└─────────────────────────────────────────────────────┘
```

### Request Flow Examples

#### Example 1: Everything Works (Happy Path)
```
User: "Enter score: 4"
  ↓
Frontend: Save to localStorage ✅
  ↓
Frontend: POST to /api/games/{id}/score
  ↓
Backend: Save to database ✅
  ↓
Frontend: Show 🟢 "Saved" ✅
```

#### Example 2: No Cell Signal (Offline)
```
User: "Enter score: 4"
  ↓
Frontend: Save to localStorage ✅
  ↓
Frontend: POST to /api/games/{id}/score → Network Error
  ↓
Service Worker: Intercept, return cached response
  ↓
Frontend: Queue for sync, Show 🟠 "Offline - Will sync later"
  ↓
[Later, when online]
  ↓
Frontend: Process sync queue
  ↓
Backend: Save to database ✅
  ↓
Frontend: Show 🟢 "Synced" ✅
```

#### Example 3: Database Schema Issue
```
User: "Create game"
  ↓
Frontend: POST to /api/games/create
  ↓
Backend: Try save to database
  ↓
Database: ERROR - column game_id does not exist
  ↓
Backend: Enable fallback mode
  ↓
Backend: Save to memory ✅
  ↓
Backend: Return {game, fallback_mode: true}
  ↓
Frontend: Save to localStorage ✅
  ↓
Frontend: Show 🟡 "Temporary storage - restart server to fix"
```

---

## Key Differences

### Database Schema Fix (Issue #1)
- **Runs:** On server startup
- **Fixes:** Missing columns in database
- **Automatic:** Yes, every startup
- **User Impact:** None (transparent)
- **One-time:** After fix, schema stays correct

### Offline Support (Issue #2)
- **Runs:** On user's phone
- **Enables:** Playing without connection
- **Automatic:** Yes, after PWA install
- **User Impact:** Can play on golf course
- **Ongoing:** Works every round

---

## Developer Workflow

### Backend Developer:
```bash
# 1. Start backend
cd backend
python -m uvicorn app.main:app

# Migrations run automatically ✅
# Check logs for:
# "🔄 Running database migrations..."
# "✅ Successfully applied X migration(s)"

# 2. If migrations failed, run manual fix
python fix_game_state_schema.py

# 3. Verify schema
python -c "from app.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_columns('game_state'))"
```

### Frontend Developer:
```bash
# 1. Start frontend
cd frontend
npm start

# 2. Install as PWA (Chrome DevTools)
# Application → Manifest → Install

# 3. Test offline
# Application → Service Workers → Offline checkbox

# 4. Verify caching
# Application → Cache Storage → wolf-goat-pig-v1
```

### Testing Scenarios:
```bash
# Scenario 1: Schema Issue
# - Corrupt database schema
# - Start backend
# - Expect: Automatic migration OR fallback mode

# Scenario 2: Offline Mode
# - Install PWA
# - Enable offline in DevTools
# - Create game
# - Expect: Works, saves to localStorage

# Scenario 3: Normal Operation
# - Good connection
# - Good database
# - Expect: Full sync to database
```

---

## Monitoring

### Backend Logs to Watch:

```bash
# Good:
✅ Database migrations completed
✅ Created test game <id> in database

# Warning (Fallback):
⚠️ Database save failed: <error>
⚠️ Created test game <id> in FALLBACK MODE

# Error:
❌ Migration failed: <error>
❌ Both database and fallback mode failed
```

### Frontend Console:

```javascript
// Good:
[PWA] Service Worker registered
[PWA] Content cached for offline use
[Persistence] Game state saved to localStorage

// Offline:
[SW] Network request failed, returning cached response
[Offline] Created offline game: <id>

// Syncing:
[PWA] Back online
[PWA] Syncing game state to backend...
[PWA] Sync complete
```

---

## Summary

### Issue #1: Database Schema (Backend)
**What:** Missing columns in database
**Fix:** Automatic migrations
**When:** App startup
**Impact:** Games can be created even with schema issues

### Issue #2: Golf Course Connectivity (Frontend)
**What:** Poor cell signal
**Fix:** PWA with offline support
**When:** Always (after PWA install)
**Impact:** App works without any connection

### Together
These two features combine to create a **resilient, offline-first architecture** that works in both backend failure scenarios AND user connectivity scenarios.

**The app never breaks.** ✅
