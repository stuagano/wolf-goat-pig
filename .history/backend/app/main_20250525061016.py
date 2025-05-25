from fastapi import FastAPI, Depends, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud, database
from .game_state import game_state

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
    } 