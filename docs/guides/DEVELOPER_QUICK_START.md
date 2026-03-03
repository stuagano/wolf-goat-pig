# Wolf Goat Pig - Developer Quick Start Guide

**Last Updated:** November 3, 2025

---

## Quick Navigation

- **New to the project?** → Read [Overview](#overview)
- **Where is class X?** → Check [CLASS_DOCUMENTATION.md](./CLASS_DOCUMENTATION.md)
- **How does the game engine work?** → See [Game Engine Architecture](#game-engine-architecture)
- **How do I add a feature?** → Read [Common Tasks](#common-tasks)
- **What's the API structure?** → See [API Patterns](#api-patterns)
- **What changed recently?** → Check [CONSOLIDATION_PROGRESS.md](./CONSOLIDATION_PROGRESS.md)

---

## Overview

Wolf Goat Pig is a poker-inspired golf game with:
- 4-player format with dynamic partnerships
- Betting system with multiple rules (doubles, Duncan, Tunkarri, etc.)
- Monte Carlo shot simulation
- Badge/achievement system
- Multiplayer support with join codes
- Database persistence for game state

**Tech Stack:**
- **Backend:** FastAPI (Python 3.9+)
- **Frontend:** React + Redux
- **Database:** SQLite (SQLAlchemy ORM)
- **Auth:** Auth0
- **Testing:** pytest, Playwright

---

## Project Structure

```
wolf-goat-pig/
├── backend/
│   └── app/
│       ├── main.py                    # FastAPI app, API endpoints
│       ├── wolf_goat_pig_simulation.py # Main game engine
│       ├── mixins/
│       │   └── persistence_mixin.py   # Database persistence
│       ├── state/                     # State management
│       ├── domain/                    # Domain models
│       ├── services/                  # Business logic services
│       ├── models.py                  # SQLAlchemy models
│       ├── schemas.py                 # Pydantic schemas
│       └── database.py                # DB configuration
├── frontend/
│   └── src/
│       ├── components/                # React components
│       ├── redux/                     # Redux state management
│       └── services/                  # API client
├── tests/
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   └── e2e/                           # Playwright E2E tests
└── docs/
    ├── CLASS_DOCUMENTATION.md         # All classes documented
    ├── CONSOLIDATION_PROGRESS.md      # Recent changes
    ├── ARCHITECTURE_STATUS.md         # Current architecture
    └── DEVELOPER_QUICK_START.md       # This file
```

---

## Game Engine Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     WolfGoatPigSimulation                    │
│  (Main Game Engine - wolf_goat_pig_simulation.py)           │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ PlayerManager   │  │ CourseManager   │                  │
│  │ - Player roster │  │ - Course data   │                  │
│  │ - Hitting order │  │ - Hole info     │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                              │
│  ┌─────────────────────────────────────────────┐           │
│  │           HoleState                          │           │
│  │  - Ball positions (all players)             │           │
│  │  - BettingState (wagers, doubles, rules)    │           │
│  │  - TeamFormation (partnerships)             │           │
│  │  - StrokeAdvantage (handicaps)              │           │
│  │  - ShotState (chronological shots)          │           │
│  └─────────────────────────────────────────────┘           │
│                                                              │
│  ┌─────────────────────────────────────────────┐           │
│  │         Timeline (list of events)            │           │
│  │  - Shot results, betting actions, etc.      │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ inherits
                            ▼
                 ┌─────────────────────┐
                 │  PersistenceMixin    │
                 │  - Save to DB        │
                 │  - Load from DB      │
                 │  - Complete game     │
                 └─────────────────────┘
```

### Data Flow

```
1. User Action (Frontend)
   ↓
2. API Request → main.py unified_action()
   ↓
3. Load game from active_games dict or DB
   ↓
4. Execute action on WolfGoatPigSimulation
   ↓
5. Game engine updates state (players, betting, shots, etc.)
   ↓
6. PersistenceMixin._save_to_db() persists state
   ↓
7. Return ActionResponse with updated game_state
   ↓
8. Frontend updates Redux store
```

---

## API Patterns

### Unified Action Endpoint

**All game actions use the same pattern:**

```python
POST /unified_action

Request:
{
  "game_id": "abc123",
  "action_type": "execute_shot",
  "payload": {
    "player_id": "p1",
    "club": "driver"
  }
}

Response:
{
  "game_state": { ... },         # Complete game state
  "log_message": "...",          # Human-readable message
  "available_actions": [...],    # Next possible actions
  "timeline_event": { ... }      # Optional event for timeline
}
```

### Action Types

Common action_type values:
- `start_game` - Initialize new game
- `execute_shot` - Player takes a shot
- `form_partnership` - Accept/decline partnership
- `apply_double` - Double the wager
- `use_float` - Invoke float rule
- `use_duncan` - Invoke Duncan rule
- `complete_hole` - Finish current hole
- `advance_hole` - Move to next hole

### Resource Endpoints

Standard REST endpoints for resources:
- `GET /courses` - List courses
- `POST /courses` - Create course
- `GET /players` - List players
- `POST /players` - Create player
- `GET /games/history` - Game history
- `GET /badges` - List badges

---

## Common Tasks

### 1. Add a New Game Action

**Example:** Add a new betting rule called "SuperDouble"

1. **Add action handler in main.py:**
   ```python
   async def _handle_super_double(game: WolfGoatPigSimulation, payload: dict):
       """Apply super double (triples the wager)."""
       # Validate game state
       if game.current_hole is None:
           raise HTTPException(400, "No active hole")

       # Apply the rule
       game.current_hole.betting_state.super_double_invoked = True
       game.current_hole.betting_state.current_wager *= 3

       # Log the event
       game._add_timeline_event(
           "betting",
           "Super Double invoked - wager tripled!",
           {"wager": game.current_hole.betting_state.current_wager}
       )

       # Save to database
       game._save_to_db()

       return "Super Double invoked - wager is now tripled!"
   ```

2. **Register in unified_action:**
   ```python
   # In unified_action() function
   elif action_type == "super_double":
       message = await _handle_super_double(game, payload)
   ```

3. **Update BettingState dataclass (if needed):**
   ```python
   @dataclass
   class BettingState:
       # ... existing fields ...
       super_double_invoked: bool = False
   ```

4. **Add frontend button/action:**
   ```jsx
   const applySuperDouble = () => {
     dispatch(executeAction('super_double', {}));
   };
   ```

### 2. Add a Database Model

**Example:** Add a "Tournaments" feature

1. **Create model in models.py:**
   ```python
   class Tournament(Base):
       __tablename__ = "tournaments"

       id = Column(Integer, primary_key=True)
       name = Column(String, nullable=False)
       start_date = Column(String)
       end_date = Column(String)
       status = Column(String, default="upcoming")
       settings = Column(JSON)
       created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
   ```

2. **Create Pydantic schemas in schemas.py:**
   ```python
   class TournamentCreate(BaseModel):
       name: str
       start_date: str
       settings: Optional[Dict] = {}

   class TournamentResponse(TournamentCreate):
       id: int
       status: str
       created_at: str
   ```

3. **Create database migration:**
   ```bash
   # Run Alembic migration (if using Alembic)
   alembic revision --autogenerate -m "Add tournaments table"
   alembic upgrade head
   ```

4. **Add API endpoints in main.py:**
   ```python
   @app.post("/tournaments", response_model=TournamentResponse)
   async def create_tournament(tournament: TournamentCreate, db: Session = Depends(get_db)):
       db_tournament = Tournament(**tournament.dict())
       db.add(db_tournament)
       db.commit()
       db.refresh(db_tournament)
       return db_tournament
   ```

### 3. Add a Badge

**Example:** Add "Hat Trick" badge for 3 birdies in a row

1. **Create badge in database (migration or seed script):**
   ```python
   badge = Badge(
       badge_id="hat_trick",
       name="Hat Trick",
       description="Make 3 birdies in a row",
       category="scoring",
       rarity="rare",
       trigger_type="real_time",  # Check after each hole
       trigger_condition={
           "type": "consecutive_birdies",
           "count": 3
       },
       points_value=50,
       is_active=True
   )
   db.add(badge)
   db.commit()
   ```

2. **Add detection logic in badge_engine.py:**
   ```python
   def check_hat_trick(self, player_id: int, recent_scores: List[int], pars: List[int]):
       """Check if player made 3 consecutive birdies."""
       if len(recent_scores) < 3:
           return False

       # Check last 3 scores
       last_three = recent_scores[-3:]
       last_three_pars = pars[-3:]

       birdies = [
           score == par - 1
           for score, par in zip(last_three, last_three_pars)
       ]

       return all(birdies)
   ```

3. **Call detection after each hole:**
   ```python
   # In WolfGoatPigSimulation after hole completes
   if badge_engine.check_hat_trick(player.id, player.hole_scores, pars):
       badge_engine.award_badge(player.id, "hat_trick", game_record_id)
   ```

### 4. Add a Service

**Example:** Create a NotificationService

1. **Create service file:**
   ```python
   # backend/app/services/notification_service.py
   from typing import List, Dict, Any
   from ..models import PlayerProfile
   from .email_service import EmailService

   class NotificationService:
       def __init__(self):
           self.email_service = EmailService()

       def send_notification(
           self,
           player_id: int,
           notification_type: str,
           message: str,
           data: Dict[str, Any] = None
       ):
           """Send notification via appropriate channel."""
           # Get player preferences
           player = self._get_player(player_id)

           # Send via enabled channels
           if player.email_enabled:
               self.email_service.send(player.email, message)

           if player.push_enabled:
               self._send_push(player.device_token, message)

           # Store in-app notification
           self._create_in_app_notification(player_id, message, data)
   ```

2. **Use in game logic:**
   ```python
   # In main.py or other handlers
   notification_service = NotificationService()

   # After game action
   notification_service.send_notification(
       player_id=player.id,
       notification_type="game_invite",
       message="You've been invited to a game!",
       data={"game_id": game.game_id}
   )
   ```

---

## Database Schema

### Key Tables

**GameStateModel** - In-progress game state
- `game_id` (UUID, unique)
- `join_code` (optional, for multiplayer)
- `state` (JSON, complete game state)
- `created_at`, `updated_at`

**GameRecord** - Completed game record
- `game_id` (UUID, links to GameStateModel)
- `course_name`, `game_mode`, `player_count`
- `final_scores` (JSON)
- `completed_at`

**PlayerProfile** - Player account
- `id`, `name`, `email`, `handicap`
- `ghin_id` (GHIN integration)
- `is_ai` (AI player flag)
- `preferences` (JSON)

**PlayerStatistics** - Player performance metrics
- `player_id` (FK to PlayerProfile)
- `games_played`, `games_won`, `total_earnings`
- `betting_success_rate`, `partnership_success_rate`
- Performance trends (JSON)

**Badge** - Badge definitions
- `badge_id`, `name`, `description`
- `category`, `rarity`
- `trigger_condition` (JSON)

**PlayerBadgeEarned** - Badges earned by players
- `player_profile_id`, `badge_id`
- `earned_at`, `game_record_id`

### Database Connections

```python
# Get database session
from .database import SessionLocal

db = SessionLocal()
try:
    # Do database operations
    result = db.query(PlayerProfile).filter_by(id=player_id).first()
    db.commit()
finally:
    db.close()

# Or use FastAPI dependency injection
from fastapi import Depends
from .database import get_db

@app.get("/players/{player_id}")
def get_player(player_id: int, db: Session = Depends(get_db)):
    return db.query(PlayerProfile).filter_by(id=player_id).first()
```

---

## Testing

### Run Tests

```bash
# Backend unit tests
cd backend
pytest

# Backend with coverage
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test

# E2E tests
cd tests/e2e
npx playwright test
```

### Write Unit Tests

```python
# tests/unit/test_game_logic.py
import pytest
from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
from app.domain.player import Player

def test_partnership_formation():
    """Test that partnerships are formed correctly."""
    # Setup
    players = [
        Player(id="p1", name="Alice", handicap=10),
        Player(id="p2", name="Bob", handicap=15),
        Player(id="p3", name="Charlie", handicap=20),
        Player(id="p4", name="Dave", handicap=5)
    ]
    game = WolfGoatPigSimulation(players=players, course_name="Test Course")

    # Action
    game.start_hole(1)
    game.offer_partnership("p1", "p2")
    game.accept_partnership("p2")

    # Assert
    assert game.current_hole.teams.team1 == ["p1", "p2"]
    assert game.current_hole.teams.team2 == ["p3", "p4"]
```

### Write E2E Tests

```javascript
// tests/e2e/game-flow.spec.js
const { test, expect } = require('@playwright/test');

test('complete game flow', async ({ page }) => {
  // Navigate to app
  await page.goto('http://localhost:3000');

  // Create game
  await page.click('text=New Game');
  await page.fill('input[name="player1"]', 'Alice');
  await page.fill('input[name="handicap1"]', '10');
  await page.click('button:has-text("Start Game")');

  // Verify game started
  await expect(page.locator('text=Hole 1')).toBeVisible();

  // Execute shot
  await page.click('button:has-text("Hit Shot")');
  await expect(page.locator('.shot-result')).toBeVisible();
});
```

---

## Environment Setup

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run development server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with API URL

# Run development server
npm start
```

### Database Setup

```bash
# Initialize database (if using migrations)
cd backend
alembic upgrade head

# Or let app create tables automatically
# (SQLAlchemy will create tables on first run)

# Seed data (optional)
python scripts/seed_data.py
```

---

## Configuration

### Backend Environment Variables

```bash
# .env file
DATABASE_URL=sqlite:///./wolf_goat_pig.db
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
GHIN_API_KEY=your-ghin-key
EMAIL_FROM=noreply@wolfgoatpig.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

### Frontend Environment Variables

```bash
# .env file
REACT_APP_API_URL=http://localhost:8000
REACT_APP_AUTH0_DOMAIN=your-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id
```

---

## Debugging Tips

### Backend Debugging

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

logger.info(f"Game state: {game.to_dict()}")
logger.error(f"Error occurred: {e}")

# Use pdb for breakpoints
import pdb; pdb.set_trace()

# Check database state
from app.database import SessionLocal
db = SessionLocal()
games = db.query(GameStateModel).all()
for game in games:
    print(f"Game {game.game_id}: {game.state}")
```

### Frontend Debugging

```javascript
// Redux DevTools
// Install Redux DevTools Extension in Chrome/Firefox

// Console logging
console.log('Game state:', gameState);
console.log('Available actions:', availableActions);

// React DevTools
// Install React DevTools Extension
// Inspect component state and props
```

### Common Issues

**Issue:** Game state not persisting
- Check database connection
- Verify `_save_to_db()` is called after actions
- Check error logs for serialization issues

**Issue:** Auth errors
- Verify Auth0 configuration
- Check token expiration
- Ensure Auth0 domain/client ID match

**Issue:** Tests failing
- Clear test database: `rm test.db`
- Check for async/await issues
- Verify mock data matches expected format

---

## Code Style

### Python (Backend)

```python
# Follow PEP 8
# Use type hints
def execute_shot(player_id: str, club: str) -> ShotResult:
    """Execute a golf shot.

    Args:
        player_id: Unique player identifier
        club: Club used for shot

    Returns:
        ShotResult with distance and lie type
    """
    # Implementation
    pass

# Use dataclasses for data structures
from dataclasses import dataclass

@dataclass
class BallPosition:
    player_id: str
    distance_to_pin: float
    lie_type: str = "fairway"

# Use enums for constants
from enum import Enum

class ShotQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
```

### JavaScript (Frontend)

```javascript
// Use ES6+ features
const executeShot = async (playerId, club) => {
  const response = await api.post('/unified_action', {
    action_type: 'execute_shot',
    payload: { player_id: playerId, club }
  });
  return response.data;
};

// Use Redux Toolkit
import { createSlice } from '@reduxjs/toolkit';

const gameSlice = createSlice({
  name: 'game',
  initialState: { ... },
  reducers: { ... }
});
```

---

## Useful Commands

```bash
# Backend
python -m pytest                       # Run tests
python -m pytest --cov                 # Run with coverage
uvicorn app.main:app --reload          # Run dev server
python scripts/seed_data.py            # Seed database
alembic revision --autogenerate        # Create migration
alembic upgrade head                   # Run migrations

# Frontend
npm start                              # Run dev server
npm test                               # Run tests
npm run build                          # Build for production
npm run lint                           # Run linter

# Database
sqlite3 wolf_goat_pig.db ".tables"     # List tables
sqlite3 wolf_goat_pig.db ".schema courses"  # Show schema

# Git
git status                             # Check status
git add .                              # Stage changes
git commit -m "message"                # Commit
git push origin main                   # Push to remote
```

---

## Resources

### Documentation
- **CLASS_DOCUMENTATION.md** - All classes documented
- **ARCHITECTURE_STATUS.md** - Current architecture state
- **CONSOLIDATION_PROGRESS.md** - Recent changes
- **API Documentation** - http://localhost:8000/docs (when server running)

### External Docs
- **FastAPI:** https://fastapi.tiangolo.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **React:** https://react.dev/
- **Redux Toolkit:** https://redux-toolkit.js.org/
- **Playwright:** https://playwright.dev/

### Getting Help
- Check existing tests for examples
- Search CLASS_DOCUMENTATION.md for class locations
- Review similar existing code
- Ask team members

---

## Quick Reference

### Find a Class
```bash
# Search for class definition
grep -rn "^class ClassName" backend/app/

# Or check CLASS_DOCUMENTATION.md
```

### Find API Endpoint
```bash
# Search for route definition
grep -rn "@app\.(get|post)" backend/app/main.py
```

### Find Where Something is Used
```bash
# Search for usage
grep -rn "function_or_class_name" backend/app/
```

### Debug a Test
```bash
# Run single test with output
pytest tests/unit/test_file.py::test_name -v -s
```

---

**For more detailed information, see:**
- [CLASS_DOCUMENTATION.md](./CLASS_DOCUMENTATION.md) - Complete class reference
- [ARCHITECTURE_STATUS.md](./ARCHITECTURE_STATUS.md) - Architecture details
- [CONSOLIDATION_PROGRESS.md](./CONSOLIDATION_PROGRESS.md) - Recent changes

---

**Last Updated:** November 3, 2025
