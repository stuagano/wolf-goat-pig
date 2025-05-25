# Wolf Goat Pig MVP

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

## Questions?
Open an issue or contact the maintainer. 