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

from .schemas import CourseCreate, CourseUpdate, CourseResponse, CourseStats, CourseComparison, HoleInfo

@app.post("/courses", response_model=dict)
def add_course(course: CourseCreate):
    """Add a new course with validation"""
    try:
        # Convert Pydantic models to dict format expected by game_state
        course_data = {
            "name": course.name,
            "holes": [
                {
                    "hole_number": hole.hole_number,
                    "par": hole.par,
                    "yards": hole.yards,
                    "stroke_index": hole.handicap,  # Note: handicap in schema = stroke_index in game_state
                    "description": hole.description or ""
                }
                for hole in course.holes
            ]
        }
        game_state.add_course(course_data)
        return {"status": "success", "message": "Course created successfully", "courses": game_state.get_courses()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/courses/{course_name}")
def update_course(course_name: str, course_update: CourseUpdate):
    """Update an existing course"""
    try:
        update_data = {}
        if course_update.name:
            update_data["name"] = course_update.name
        if course_update.holes:
            update_data["holes"] = [
                {
                    "hole_number": hole.hole_number,
                    "par": hole.par,
                    "yards": hole.yards,
                    "stroke_index": hole.handicap,
                    "description": hole.description or ""
                }
                for hole in course_update.holes
            ]
        
        game_state.update_course(course_name, update_data)
        return {"status": "success", "message": "Course updated successfully", "courses": game_state.get_courses()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/courses/{course_name}")
def delete_course(course_name: str = Path(...)):
    """Delete a course"""
    try:
        game_state.delete_course(course_name)
        return {"status": "success", "message": "Course deleted successfully", "courses": game_state.get_courses()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/courses/{course_name}/stats")
def get_course_stats(course_name: str):
    """Get statistics for a specific course"""
    try:
        stats = game_state.get_course_stats(course_name)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/courses/{course1}/compare/{course2}")
def compare_courses(course1: str, course2: str):
    """Compare two courses"""
    try:
        stats1 = game_state.get_course_stats(course1)
        stats2 = game_state.get_course_stats(course2)
        
        return {
            "course1": {"name": course1, "stats": stats1},
            "course2": {"name": course2, "stats": stats2},
            "difficulty_difference": stats1["difficulty_rating"] - stats2["difficulty_rating"],
            "yard_difference": stats1["total_yards"] - stats2["total_yards"],
            "par_difference": stats1["total_par"] - stats2["total_par"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/game/current-hole")
def get_current_hole_info():
    """Get detailed information about the current hole"""
    hole_info = game_state.get_current_hole_info()
    if hole_info is None:
        raise HTTPException(status_code=404, detail="No current hole information available")
    return hole_info

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

class MonteCarloSetup(BaseModel):
    human_player: dict
    computer_players: List[ComputerPlayerConfig]
    num_simulations: int = 100
    course_name: Optional[str] = None

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
            computer_configs,
            setup.course_name
        )
        
        # Update the global game state with simulation
        game_state = sim_game_state
        
        return {
            "status": "ok", 
            "game_state": _serialize_game_state(),
            "message": "Simulation setup complete! You're playing against 3 computer opponents."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/monte-carlo")
def run_monte_carlo_simulation(setup: MonteCarloSetup):
    """Run Monte Carlo simulation with specified number of games"""
    try:
        if len(setup.computer_players) != 3:
            raise HTTPException(status_code=400, detail="Need exactly 3 computer players")
        
        if setup.num_simulations < 1 or setup.num_simulations > 1000:
            raise HTTPException(status_code=400, detail="Number of simulations must be between 1 and 1000")
        
        # Convert computer player configs to dict format
        computer_configs = [
            {
                "id": cp.id,
                "name": cp.name,
                "handicap": cp.handicap,
                "personality": cp.personality
            } for cp in setup.computer_players
        ]
        
        # Run Monte Carlo simulation
        results = simulation_engine.run_monte_carlo_simulation(
            setup.human_player,
            computer_configs,
            setup.num_simulations,
            setup.course_name
        )
        
        # Get summary statistics
        summary = results.get_summary()
        
        # Add additional insights
        human_id = setup.human_player["id"]
        human_stats = summary["player_statistics"][human_id]
        
        # Generate insights
        insights = []
        
        # Win rate analysis
        if human_stats["win_percentage"] > 30:
            insights.append(f"🎯 Strong performance! You won {human_stats['win_percentage']:.1f}% of games")
        elif human_stats["win_percentage"] > 20:
            insights.append(f"👍 Decent performance. You won {human_stats['win_percentage']:.1f}% of games")
        else:
            insights.append(f"📚 Room for improvement. You won {human_stats['win_percentage']:.1f}% of games")
        
        # Score analysis
        avg_score = human_stats["average_score"]
        if avg_score > 0:
            insights.append(f"💰 You averaged +{avg_score:.1f} points per game")
        else:
            insights.append(f"📉 You averaged {avg_score:.1f} points per game")
        
        # Comparative analysis
        all_players = list(summary["player_statistics"].keys())
        human_rank = sorted(all_players, 
                          key=lambda p: summary["player_statistics"][p]["average_score"], 
                          reverse=True).index(human_id) + 1
        
        if human_rank == 1:
            insights.append("🏆 You had the highest average score!")
        elif human_rank == 2:
            insights.append("🥈 You finished 2nd in average scoring")
        elif human_rank == 3:
            insights.append("🥉 You finished 3rd in average scoring")
        else:
            insights.append("🎯 You finished 4th in average scoring")
        
        # Consistency analysis
        score_range = human_stats["best_score"] - human_stats["worst_score"]
        if score_range < 8:
            insights.append("📊 Very consistent performance across games")
        elif score_range < 15:
            insights.append("📈 Reasonably consistent performance")
        else:
            insights.append("🎢 Variable performance - work on consistency")
        
        return {
            "status": "ok",
            "summary": summary,
            "insights": insights,
            "simulation_details": {
                "total_games": setup.num_simulations,
                "course": setup.course_name or "Standard Course",
                "human_player": setup.human_player["name"],
                "opponents": [cp.name for cp in setup.computer_players]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/monte-carlo-detailed/{num_games}")
def get_monte_carlo_detailed_results(num_games: int, setup: MonteCarloSetup):
    """Get detailed game-by-game results from Monte Carlo simulation"""
    try:
        if num_games < 1 or num_games > 100:
            raise HTTPException(status_code=400, detail="Number of detailed games must be between 1 and 100")
        
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
        
        # Run Monte Carlo simulation
        results = simulation_engine.run_monte_carlo_simulation(
            setup.human_player,
            computer_configs,
            num_games,
            setup.course_name
        )
        
        return {
            "status": "ok",
            "detailed_results": results.detailed_results,
            "summary": results.get_summary()
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