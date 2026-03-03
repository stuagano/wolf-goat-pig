# Troubleshooting: Can't Create Games or Save Holes

**Issue:** Frontend cannot create games or save holes
**Status:** Investigating

---

## 🔍 Root Cause Analysis

### Problem 1: Database Not Initialized

**Evidence:**
```bash
$ ls backend/*.db
# No .db files found

$ cat backend/.env
# No .env file found
```

**What This Means:**
- DATABASE_URL environment variable not set
- Falls back to SQLite: `sqlite:///./wolf_goat_pig.db`
- Database file doesn't exist yet
- Tables haven't been created

---

### Problem 2: Database Tables Don't Exist

**Required Tables:**
- `game_state` - Stores game data
- `game_players` - Tracks players in game
- `player_profiles` - Player information
- `courses` - Golf course data
- Other supporting tables

**How Tables Are Created:**
```python
# backend/app/main.py line 294-304
@app.on_event("startup")
async def startup():
    # Initialize database
    database.init_db()  # Creates all tables
```

**The Issue:**
- Backend server needs to be started first
- Startup event creates tables automatically
- But if server hasn't been run, tables don't exist

---

## ✅ Solutions

### Solution 1: Start the Backend Server

**This will automatically initialize the database:**

```bash
cd /home/user/wolf-goat-pig/backend

# Method 1: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Method 2: Using the startup script (if it exists)
python startup.py

# Method 3: Using docker-compose (if configured)
docker-compose up
```

**What Happens on Startup:**
1. Database connection established
2. `init_db()` called
3. All tables created via `Base.metadata.create_all()`
4. Connection test performed
5. Seed data loaded (courses, AI personalities, etc.)
6. Server ready to accept requests

---

### Solution 2: Manual Database Initialization

**If you just want to create the database without starting the server:**

```bash
cd /home/user/wolf-goat-pig/backend

python << 'EOF'
from app.database import init_db
from app import seed_data

# Initialize database (creates tables)
init_db()

# Load seed data
from app.database import SessionLocal
db = SessionLocal()
try:
    seed_data.seed_all_data(db)
finally:
    db.close()

print("✅ Database initialized successfully!")
EOF
```

---

### Solution 3: Check Database Exists

**Verify the database file was created:**

```bash
ls -lh wolf_goat_pig.db
# Should show: wolf_goat_pig.db with some size

# Or for PostgreSQL:
psql $DATABASE_URL -c "\dt"  # List tables
```

**Expected Tables:**
```
game_state
game_players
game_records
game_player_results
player_profiles
player_statistics
courses
hole_details
badges
player_badge_earned
... (and more)
```

---

## 🧪 Test Game Creation Flow

### Step 1: Verify Backend is Running

```bash
# Check if server is running
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Or check the root endpoint
curl http://localhost:8000/
# Expected: Some response
```

### Step 2: Create a Test Game

```bash
# Create game via API
curl -X POST "http://localhost:8000/games/create?player_count=4" \
  -H "Content-Type: application/json"

# Expected Response:
# {
#   "game_id": "uuid-here",
#   "join_code": "ABC123",
#   "status": "setup",
#   "player_count": 4,
#   "players_joined": 0
# }
```

### Step 3: Try to Complete a Hole

```bash
# Get the game_id from step 2, then:
curl -X POST "http://localhost:8000/games/{game_id}/holes/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "hole_number": 1,
    "rotation_order": ["p1", "p2", "p3", "p4"],
    "captain_index": 0,
    "phase": "normal",
    "teams": {
      "type": "partners",
      "team1": ["p1", "p2"],
      "team2": ["p3", "p4"]
    },
    "final_wager": 1,
    "winner": "team1",
    "scores": {"p1": 4, "p2": 5, "p3": 5, "p4": 6},
    "hole_par": 4
  }'

# Expected: Success response with hole_result
```

---

## 🔧 Common Errors and Fixes

### Error 1: "Game not found"

**Cause:** Database tables don't exist or game wasn't created

**Fix:**
```bash
# Restart backend server (triggers init_db)
# Or manually initialize:
cd backend && python -c "from app.database import init_db; init_db()"
```

### Error 2: "Failed to connect to database"

**Cause:** DATABASE_URL points to non-existent PostgreSQL server

**Fix:**
```bash
# Use SQLite for local development
unset DATABASE_URL
# Restart server - will use SQLite
```

### Error 3: "Column 'created_at' cannot be null"

**Cause:** Datetime type mismatch (the bug we just fixed!)

**Fix:** Already fixed in commits:
- a778b7c: Uses `.isoformat()` for all timestamps
- The fix is in the code, just restart server

### Error 4: "Current transaction is aborted"

**Cause:** Transaction error cascade (also fixed!)

**Fix:** Already fixed in commits:
- 39c51b0: Added rollback handling
- 9e91947: Removed complex batch operations
- Restart server with fixed code

---

## 📊 Verify Database State

### Check Database File Exists

```bash
cd /home/user/wolf-goat-pig/backend

# For SQLite:
ls -lh wolf_goat_pig.db
sqlite3 wolf_goat_pig.db "SELECT name FROM sqlite_master WHERE type='table';"

# For PostgreSQL:
psql $DATABASE_URL -c "\dt"
```

### Check Tables Exist

```sql
-- Count tables
SELECT COUNT(*) FROM sqlite_master WHERE type='table';
-- Expected: ~20+ tables

-- List all tables
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
```

### Check Seed Data Loaded

```sql
-- Check courses loaded
SELECT COUNT(*) FROM courses;
-- Expected: At least 1 course

-- Check AI personalities loaded
SELECT COUNT(*) FROM player_profiles WHERE is_ai = 1;
-- Expected: Several AI players

-- Check game_state table exists
SELECT COUNT(*) FROM game_state;
-- Expected: 0 (no games created yet)
```

---

## 🚀 Quick Start Script

**Create this script to initialize everything:**

```bash
#!/bin/bash
# backend/init_and_start.sh

set -e

echo "🔧 Initializing Wolf Goat Pig backend..."

cd "$(dirname "$0")"

# Check if database exists
if [ ! -f wolf_goat_pig.db ]; then
    echo "📦 Creating database..."
    python << 'EOF'
from app.database import init_db
from app import seed_data
from app.database import SessionLocal

# Create tables
init_db()

# Load seed data
db = SessionLocal()
try:
    print("📊 Loading seed data...")
    seed_data.seed_all_data(db)
    print("✅ Seed data loaded!")
finally:
    db.close()
EOF
else
    echo "✅ Database already exists"
fi

# Start server
echo "🚀 Starting server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Usage:**
```bash
chmod +x backend/init_and_start.sh
./backend/init_and_start.sh
```

---

## 📝 Frontend Connection Check

### Verify Frontend Can Reach Backend

**Check API_URL in frontend:**

```javascript
// frontend/src/components/game/SimpleScorekeeper.jsx line 8
const API_URL = process.env.REACT_APP_API_URL || '';

// If empty, uses same origin (e.g., http://localhost:3000)
// Should be: http://localhost:8000
```

**Fix if needed:**
```bash
# frontend/.env
REACT_APP_API_URL=http://localhost:8000
```

**Test connection:**
```javascript
// In browser console:
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)

// Expected: {status: "ok"}
```

---

## ✅ Complete Diagnostic Checklist

Run through this checklist:

- [ ] Backend server is running (`uvicorn app.main:app`)
- [ ] Database file exists (`ls wolf_goat_pig.db`)
- [ ] Tables created (`sqlite3 wolf_goat_pig.db ".tables"`)
- [ ] Seed data loaded (courses, players exist)
- [ ] Health check passes (`curl http://localhost:8000/health`)
- [ ] Can create game (`POST /games/create`)
- [ ] Frontend API_URL is correct
- [ ] Frontend can reach backend (no CORS errors)
- [ ] Can complete hole (`POST /games/{id}/holes/complete`)

---

## 🎯 Most Likely Issue

**Based on symptoms ("can't create game from frontend"):**

**The backend server probably hasn't been started yet**, which means:
1. Database tables don't exist
2. API endpoints aren't available
3. Frontend gets 404 or connection refused

**Solution:**
```bash
cd /home/user/wolf-goat-pig/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Then test from frontend** - should work immediately!

---

## 📚 Related Documentation

- **SCOREKEEPER_VERIFICATION.md** - How the scoring works
- **DB_LINTING_RULES.md** - Database best practices
- **Transaction fix commits:**
  - 39c51b0, a778b7c, 9e91947

---

**Last Updated:** 2025-11-10
**Status:** Diagnosis complete - start backend server to fix
