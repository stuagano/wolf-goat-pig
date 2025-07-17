from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud, database
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure tables are created before anything else
# Call init_db before importing game_state

try:
    database.init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

from .game_state import game_state
from pydantic import BaseModel

app = FastAPI(title="Wolf Goat Pig API", version="1.0.0")

# Production-ready CORS configuration
ENVIRONMENT = os.getenv("NODE_ENV", "development")
logger.info(f"Starting application in {ENVIRONMENT} mode")

if ENVIRONMENT == "production":
    # In production, restrict CORS to your frontend domain
    allowed_origins = [
        "https://wgp-frontend.onrender.com",  # Frontend static site URL
        "https://wgp-frontend.netlify.app",   # Alternative if using Netlify
        "https://wgp-frontend.vercel.app",    # Alternative if using Vercel
    ]
else:
    # In development, allow localhost
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Health check endpoint for Render
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": ENVIRONMENT,
        "database_url": "***" if os.getenv("DATABASE_URL") else "sqlite (local)"
    }

@app.on_event("startup")
def startup():
    try:
        database.init_db()
        logger.info("Startup: Database initialized successfully")
    except Exception as e:
        logger.error(f"Startup: Failed to initialize database: {e}")
        raise

@app.get("/rules", response_model=list[schemas.Rule])
def get_rules():
    return crud.get_rules()

@app.post("/game/start")
def start_game():
    game_state.reset()
    return {"status": "ok", "game_state": _serialize_game_state()}

@app.get("/game/state")
def get_game_state():
    return _serialize_game_state()

@app.post("/game/action")
def game_action(data: dict = Body(...)):
    action = data.get("action")
    payload = data.get("payload", {})
    try:
        result = game_state.dispatch_action(action, payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "game_state": _serialize_game_state(), "result": result}

@app.get("/game/tips")
def get_betting_tips():
    return {"tips": game_state.get_betting_tips()}

@app.get("/game/player_strokes")
def get_player_strokes():
    return game_state.get_player_strokes()

@app.get("/courses")
def get_courses():
    return game_state.get_courses()

@app.post("/game/setup")
async def setup_game_players(request: Request):
    data = await request.json()
    players = data.get("players")
    course_name = data.get("course_name")
    if not players:
        raise HTTPException(status_code=400, detail="Missing players list.")
    try:
        game_state.setup_players(players, course_name=course_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "game_state": _serialize_game_state()}

class HoleInfo(BaseModel):
    stroke_index: int
    par: int

class CourseCreate(BaseModel):
    name: str
    holes: list[HoleInfo]  # 18 items, each with stroke_index and par

@app.post("/courses")
def add_course(course: CourseCreate):
    name = course.name.strip()
    if not name or len(course.holes) != 18:
        raise HTTPException(status_code=400, detail="Course name and 18 holes required.")
    if name in game_state.courses:
        raise HTTPException(status_code=400, detail="Course already exists.")
    # Store as list of dicts
    game_state.courses[name] = [dict(stroke_index=h.stroke_index, par=h.par) for h in course.holes]
    return game_state.get_courses()

@app.delete("/courses/{name}")
def delete_course(name: str = Path(...)):
    if name not in game_state.courses:
        raise HTTPException(status_code=404, detail="Course not found.")
    del game_state.courses[name]
    return game_state.get_courses()

# Helper to serialize game state for API

def _serialize_game_state():
    return {
        "players": game_state.players,
        "current_hole": game_state.current_hole,
        "hitting_order": game_state.hitting_order,
        "captain_id": game_state.captain_id,
        "teams": game_state.teams,
        "base_wager": game_state.base_wager,
        "doubled_status": game_state.doubled_status,
        "game_phase": game_state.game_phase,
        "hole_scores": game_state.hole_scores,
        "game_status_message": game_state.game_status_message,
        "player_float_used": game_state.player_float_used,
        "carry_over": game_state.carry_over,
        "hole_history": game_state.get_hole_history(),
        "hole_stroke_indexes": game_state.hole_stroke_indexes,
        "hole_pars": game_state.hole_pars,
        "selected_course": game_state.selected_course,
    } 