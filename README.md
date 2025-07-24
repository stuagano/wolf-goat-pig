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
- Free web service tier is perfect for FastAPI.
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

## Notes
- The backend uses in-memory state for the MVP (no persistent DB needed).
- All game logic is in `backend/app/game_state.py`.
- The frontend is in `frontend/src/App.js`.
- For production, set up CORS and environment variables as needed.

---

## 🏌️ Simulation Mode: Event-Driven Shot-by-Shot Flow

Wolf Goat Pig Simulation Mode now uses a fully event-driven, shot-by-shot architecture for realistic, interactive golf gameplay and betting practice.

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

### GameState & State Management
- The backend serializes all simulation state, including:
  - `shot_sequence`: Current phase, player index, completed shots, pending decisions
  - `tee_shot_results`: Results and context for all tee shots
  - `hitting_order`, `captain_id`, `teams`, `doubled_status`, etc.
- State is updated and returned after every event, so the frontend can always render the latest context.

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
- All new endpoints are documented in `/docs` (Swagger UI).
- See `backend/app/simulation.py` for event-driven engine logic.
- See `frontend/src/SimulationMode.js` for frontend integration.
- GameState serialization/deserialization includes all new event-driven fields for robust state management.

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

## Questions?
Open an issue or contact the maintainer. 