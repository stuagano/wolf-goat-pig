from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud, database
# Ensure tables are created before anything else
# Call init_db before importing game_state

database.init_db()

from .game_state import game_state
from pydantic import BaseModel

app = FastAPI()

# Allow all origins for MVP; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    database.init_db()

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