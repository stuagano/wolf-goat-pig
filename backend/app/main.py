from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud, database
# Ensure tables are created before anything else
# Call init_db before importing game_state

database.init_db()

from .game_state import game_state
from .simulation import simulation_engine
from pydantic import BaseModel
from typing import List, Optional

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

# Simulation endpoints
class ComputerPlayerConfig(BaseModel):
    id: str
    name: str
    handicap: float
    personality: str = "balanced"  # aggressive, conservative, balanced, strategic

class SimulationSetup(BaseModel):
    human_player: dict
    computer_players: List[ComputerPlayerConfig]
    course_name: Optional[str] = None

class HumanDecisions(BaseModel):
    action: Optional[str] = None  # "go_solo" or None
    requested_partner: Optional[str] = None
    offer_double: bool = False
    accept_double: bool = False

@app.post("/simulation/setup")
def setup_simulation(setup: SimulationSetup):
    """Setup a new simulation game with one human and three computer players"""
    global game_state
    
    try:
        if len(setup.computer_players) != 3:
            raise HTTPException(status_code=400, detail="Need exactly 3 computer players")
        
        # Convert computer player configs to dict format
        computer_configs = [
            {
                "id": cp.id,
                "name": cp.name,
                "handicap": cp.handicap,
                "personality": cp.personality
            } for cp in setup.computer_players
        ]
        
        # Setup simulation
        sim_game_state = simulation_engine.setup_simulation(
            setup.human_player, 
            computer_configs
        )
        
        # Set course if provided
        if setup.course_name and setup.course_name in sim_game_state.courses:
            course = sim_game_state.courses[setup.course_name]
            sim_game_state.selected_course = setup.course_name
            sim_game_state.hole_stroke_indexes = [h["stroke_index"] for h in course]
            sim_game_state.hole_pars = [h["par"] for h in course]
            sim_game_state._save_to_db()
        
        # Update the global game state with simulation
        game_state = sim_game_state
        
        return {
            "status": "ok", 
            "game_state": _serialize_game_state(),
            "message": "Simulation setup complete! You're playing against 3 computer opponents."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/play-hole")
def play_simulation_hole(decisions: HumanDecisions):
    """Play one hole of the simulation with human decisions"""
    global game_state
    
    try:
        # Convert decisions to dict
        human_decisions = {
            "action": decisions.action,
            "requested_partner": decisions.requested_partner,
            "offer_double": decisions.offer_double,
            "accept_double": decisions.accept_double
        }
        
        # Simulate the hole
        updated_game_state, feedback = simulation_engine.simulate_hole(
            game_state, 
            human_decisions
        )
        
        # Update global game state
        game_state = updated_game_state
        
        return {
            "status": "ok",
            "game_state": _serialize_game_state(),
            "feedback": feedback
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/simulation/available-personalities")
def get_available_personalities():
    """Get list of available computer player personalities"""
    return {
        "personalities": [
            {
                "name": "aggressive",
                "description": "Takes risks, offers doubles frequently, goes solo when behind"
            },
            {
                "name": "conservative", 
                "description": "Plays it safe, selective about partnerships and doubles"
            },
            {
                "name": "balanced",
                "description": "Makes steady, reasonable decisions with some variance"
            },
            {
                "name": "strategic",
                "description": "Considers game situation, hole difficulty, and position carefully"
            }
        ]
    }

@app.get("/simulation/suggested-opponents")
def get_suggested_opponents():
    """Get suggested computer opponents with different skill levels"""
    return {
        "opponents": [
            {
                "name": "Tiger Bot",
                "handicap": 2.0,
                "personality": "aggressive",
                "description": "Low handicap player who takes risks and puts pressure on opponents"
            },
            {
                "name": "Strategic Sam",
                "handicap": 8.5,
                "personality": "strategic", 
                "description": "Mid-handicap player who makes calculated decisions"
            },
            {
                "name": "Conservative Carl",
                "handicap": 15.0,
                "personality": "conservative",
                "description": "Higher handicap player who plays it safe and steady"
            },
            {
                "name": "Balanced Betty",
                "handicap": 12.0,
                "personality": "balanced",
                "description": "Well-rounded player with consistent decision making"
            },
            {
                "name": "Risky Rick",
                "handicap": 18.5,
                "personality": "aggressive",
                "description": "High handicap player who compensates with bold betting"
            },
            {
                "name": "Steady Steve",
                "handicap": 10.0,
                "personality": "conservative", 
                "description": "Reliable mid-handicap player who avoids unnecessary risks"
            }
        ]
    }

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