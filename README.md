# Wolf Goat Pig MVP

🌐 **Live Demo**: [https://wolf-goat-pig.vercel.app](https://wolf-goat-pig.vercel.app)

This is a full-stack MVP web app for tracking a 4-man Wolf Goat Pig golf game, with all core rules, betting, and scoring logic.

---

## Prerequisites
- **Python 3.8+** (for backend)
- **Node.js 16+ & npm** (for frontend)

---

## Local Development

### 1. Backend (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
- The backend will run at `http://localhost:8000`

### 2. Frontend (React)

```bash
cd frontend
npm install
npm start
```
- The frontend will run at `http://localhost:3000` and proxy API requests to the backend.

---

## Project Architecture

### Backend Structure
```
backend/
├── app/
│   ├── main.py              # FastAPI application and routes
│   ├── game_state.py        # Core game state management
│   ├── simulation.py        # Event-driven simulation engine
│   ├── domain/              # Domain models and logic
│   │   ├── player.py        # Player class with handicap/scoring
│   │   └── shot_result.py   # Shot result modeling
│   ├── state/               # State management classes
│   │   ├── betting_state.py # Betting logic and team management
│   │   └── __init__.py      
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── database.py          # Database configuration
├── requirements.txt
└── venv/
```

### Key Architectural Improvements

#### 🎯 **Modular State Management**
The application now uses a clean separation of concerns with dedicated state classes:

- **`GameState`**: Core game flow, hole progression, and player management
- **`BettingState`**: All betting logic including partnerships, doubling, and team management
- **`Player`**: Individual player state with handicap calculations and scoring
- **`ShotResult`**: Shot modeling and probability calculations

#### 🏌️ **Domain-Driven Design**
- **Domain Models**: `Player` and `ShotResult` classes encapsulate golf-specific logic
- **State Classes**: Clean separation between game state and betting state
- **Simulation Engine**: Event-driven architecture for realistic shot-by-shot gameplay

#### ⚡ **Benefits of New Architecture**
- **Maintainability**: Betting logic is isolated from game flow logic
- **Testability**: Each component can be tested independently
- **Reusability**: State classes can be used in different contexts
- **Extensibility**: Easy to add new betting rules or game modes

---

## Deployment

### Backend (Render.com)
- Create a new **Web Service** on [Render](https://render.com/)
- Use the `backend/` folder as the root
- Set the start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
- Add a build command: `pip install -r requirements.txt`
- Expose port `10000`

### Frontend (Vercel/Netlify)
- Deploy the `frontend/` folder
- For **Vercel**: Just import the repo, set root to `frontend/`
- For **Netlify**: Set build command to `npm run build` and publish directory to `build/`
- Set environment variable (if needed) to point to backend API URL

---

## Free-Tier Cloud Deployment Tips

This project is ready for free-tier deployment on popular cloud services:

| Service   | Free Tier? | Used For   | Notes                                 |
|-----------|------------|------------|---------------------------------------|
| Render    | Yes        | FastAPI    | Web Service, may sleep after idle     |
| Vercel    | Yes        | React      | Static, instant, custom domains       |
| Netlify   | Yes        | React      | Static, instant, custom domains       |

### Backend (Render.com)
- Free web service tier is perfect for FastAPI.xx
- Service may "sleep" after 15 minutes of inactivity (cold start delay).
- No credit card required for free tier.

### Frontend (Vercel/Netlify)
- Both have generous free tiers for static React apps.
- No sleep, instant static hosting.
- Generous bandwidth and build minutes for small projects.

### CORS and API URLs
- Make sure your backend allows CORS from your frontend domain (Render and Vercel/Netlify).
- In production, set the frontend API base URL to your deployed backend (e.g., `https://your-backend.onrender.com`).
- You can use an environment variable like `REACT_APP_API_URL` in your frontend and reference it in your code (e.g., `process.env.REACT_APP_API_URL`).

---

## Helper Scripts

- If you want to automate setup, you can create a script like `dev.sh`:

```bash
#!/bin/bash
# Start backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload &
# Start frontend
cd ../frontend && npm start
```

- Make it executable: `chmod +x dev.sh`
- Run with: `./dev.sh`

---

## Game Features

### 🎮 Core Wolf Goat Pig Rules
- **4-Player Format**: Human vs 3 computer opponents with different personalities
- **Captain Rotation**: Rotates each hole in hitting order
- **Partnership Decisions**: Request partners or go solo after seeing tee shots
- **Doubling**: Increase stakes with strategic doubling decisions
- **Karl Marx Rule**: Fair distribution of odd quarters to lowest scorers
- **Handicap Integration**: Full USGA handicap support with stroke allocation

### 🏌️ Realistic Golf Simulation
- **Shot-by-Shot Progression**: Event-driven simulation with probability calculations
- **Course Management**: Multiple courses with detailed hole descriptions
- **Handicap-Based Difficulty**: Shots adjusted based on player skill and hole difficulty
- **Interactive Decision Points**: Real-time betting decisions with context

### 🧠 Computer AI Personalities
- **Aggressive**: Takes risks, likely to go solo or accept doubles
- **Conservative**: Plays it safe, only bets with strong advantages
- **Strategic**: Makes calculated decisions based on game state
- **Balanced**: Mix of strategies with moderate risk tolerance

---

## 🏌️ Simulation Mode: Event-Driven Shot-by-Shot Flow

Wolf Goat Pig Simulation Mode uses a fully event-driven, shot-by-shot architecture for realistic, interactive golf gameplay and betting practice.

### Key Concepts
- **Chronological, shot-by-shot simulation**: Each shot is its own event, with visible probability calculations and betting opportunities.
- **Interactive Decisions**: The backend returns `interaction_needed` flags when human input is required (e.g., captain choices, partnership responses, doubling decisions).
- **Stateful Progression**: The backend maintains a persistent `GameState` with all shot, team, and betting context, updated after every API call.
- **Frontend Integration**: The frontend advances the simulation by calling the next-shot endpoint and rendering all context, probabilities, and decision UIs.

### Core Backend Endpoints

#### 1. `/simulation/setup` (POST)
Initializes a new simulation with player and course selection.
- **Payload:**
  ```json
  {
    "human_player": {"id": "p1", "name": "Bob", "handicap": 10.5},
    "computer_players": [
      {"id": "p2", "name": "Scott", "handicap": 15, "personality": "aggressive"},
      {"id": "p3", "name": "Vince", "handicap": 8, "personality": "strategic"},
      {"id": "p4", "name": "Mike", "handicap": 20.5, "personality": "conservative"}
    ],
    "course_name": "Wing Point"
  }
  ```
- **Returns:** `{ "status": "ok", "game_state": { ... } }`

#### 2. `/simulation/next-shot` (POST)
Plays the next individual shot event (tee or approach) and returns all context, probabilities, and any betting opportunities.
- **Returns:**
  ```json
  {
    "status": "ok",
    "shot_event": { ... },
    "shot_result": { ... },
    "probabilities": { ... },
    "betting_opportunity": { ... },
    "game_state": { ... },
    "next_shot_available": true
  }
  ```

#### 3. `/simulation/shot-probabilities` (GET)
Returns probability calculations for the current shot scenario.
- **Returns:** `{ "status": "ok", "probabilities": { ... }, "game_state": { ... } }`

#### 4. `/simulation/betting-decision` (POST)
Submit a betting/partnership/solo decision after a shot, with probability context.
- **Payload:**
  ```json
  { "action": "request_partner", "partner_id": "p3" }
  ```
- **Returns:** `{ "status": "ok", "decision_result": { ... }, "betting_probabilities": { ... }, "game_state": { ... } }`

#### 5. `/simulation/current-shot-state` (GET)
Returns detailed information about the current shot state and available actions.
- **Returns:** `{ "status": "ok", "shot_state": { ... }, "game_state": { ... } }`

### State Management & Architecture
The application uses a modular state management system:

- **`GameState`**: Manages overall game flow, hole progression, and player state
- **`BettingState`**: Handles all betting logic including:
  - Team formation (partnerships vs solo)
  - Doubling decisions and stake management
  - Karl Marx rule for point distribution
  - Betting tips and strategy advice
- **`Player`**: Encapsulates individual player data with handicap calculations
- **Event-Driven Simulation**: Shot-by-shot progression with interactive decision points

State is serialized and persisted between API calls, ensuring consistent gameplay and the ability to resume sessions.

### Frontend Usage Pattern
- On simulation setup, immediately call `/simulation/next-shot` to start the first shot event.
- After each shot, update UI with returned `shot_event`, `shot_result`, `probabilities`, and any `betting_opportunity`.
- When `betting_opportunity` is present, show decision UI and submit the user's choice to `/simulation/betting-decision`.
- Use `/simulation/shot-probabilities` and `/simulation/current-shot-state` to display real-time context and probabilities.
- Continue calling `/simulation/next-shot` until the hole/game is complete.

### Example Flow
1. **Setup**: POST to `/simulation/setup` with player/course config.
2. **First Shot**: POST to `/simulation/next-shot` → returns tee shot event, probabilities.
3. **Betting Opportunity**: If present, POST to `/simulation/betting-decision`.
4. **Next Shot**: POST to `/simulation/next-shot` again.
5. **Repeat**: Continue until hole/game complete.

### Developer Notes
- All endpoints are documented in `/docs` (Swagger UI).
- See `backend/app/simulation.py` for event-driven engine logic.
- See `backend/app/state/betting_state.py` for betting logic implementation.
- See `frontend/src/SimulationMode.js` for frontend integration.
- GameState serialization/deserialization includes all event-driven fields for robust state management.

---

## 🧪 Functional Testing

After deployment, you can run comprehensive functional tests to verify everything is working:

### Quick Test (Recommended)
```bash
./run_tests.sh
```

### Manual Setup and Test
```bash
# Setup testing environment
python3 setup_testing.py

# Run functional tests
python3 functional_test_suite.py
```

### What the Tests Check
- ✅ **Deployment Status**: Polls Render and Vercel services until ready
- ✅ **Frontend Loading**: Tests both Vercel and Render frontend URLs
- ✅ **API Connectivity**: Verifies frontend can connect to backend
- ✅ **Simulation Mode**: Tests course selection and UI elements
- ✅ **Course Data**: Verifies sample courses are loaded

### Test Report
Tests generate a detailed report at `functional_test_report.json` with:
- Service health status
- Frontend functionality
- API connectivity
- Error details and timestamps

---

## Development Notes

### Recent Architectural Improvements
- **✅ Modular State Management**: Extracted `BettingState` from `GameState` for better separation of concerns
- **✅ Domain Models**: Refactored `Player` class with proper encapsulation
- **✅ Event-Driven Simulation**: Shot-by-shot gameplay with interactive decision points
- **✅ Defensive Coding**: Comprehensive error handling and null checks

### Future Enhancements
- **Course Data Modeling**: Extract course/hole logic into dedicated classes
- **Shot State Management**: Further modularize shot sequence state
- **Monte Carlo Analysis**: Enhanced statistical analysis features
- **GHIN Integration**: Real golfer handicap lookup and validation

---

## Questions?
Open an issue or contact the maintainer. 