from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud, database
# Ensure tables are created before anything else
# Call init_db before importing game_state

database.init_db()

from .game_state import game_state
from .simulation import simulation_engine
from pydantic import BaseModel
from typing import List, Optional
import os
import httpx

app = FastAPI()

# Allow all origins for MVP; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # For development
        "https://wolf-goat-pig.vercel.app",  # Vercel frontend
        "https://wolf-goat-pig-frontend.onrender.com",  # Render frontend
        "http://localhost:3000"  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    database.init_db()

@app.get("/health")
def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "message": "Wolf Goat Pig API is running"}

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
    accept_partnership: bool = False

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
    """Play one hole of the simulation with human decisions (interactive flow)"""
    global game_state
    
    try:
        # Convert decisions to dict
        human_decisions = {
            "action": decisions.action,
            "requested_partner": decisions.requested_partner,
            "offer_double": decisions.offer_double,
            "accept_double": decisions.accept_double,
            "accept_partnership": decisions.accept_partnership
        }
        
        # Simulate the hole (now returns interaction_needed)
        updated_game_state, feedback, interaction_needed = simulation_engine.simulate_hole(
            game_state, 
            human_decisions
        )
        
        # Update global game state
        game_state = updated_game_state
        
        response = {
            "status": "ok",
            "game_state": _serialize_game_state(),
            "feedback": feedback
        }
        
        # If interaction is needed, include it in response
        if interaction_needed:
            response["interaction_needed"] = interaction_needed
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/simulation/test-new-endpoints")
def test_new_endpoints():
    """Test if new endpoints are working"""
    return {"status": "ok", "message": "New interactive endpoints are working!", "timestamp": "2025-01-22"}

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

GHIN_AUTH_URL = "https://api2.ghin.com/api/v1/golfer_login.json"
GHIN_SEARCH_URL = "https://api2.ghin.com/api/v1/golfers/search.json"

@app.get("/ghin/lookup")
def ghin_lookup(
    last_name: str = Query(..., description="Golfer's last name"),
    first_name: str = Query(None, description="Golfer's first name (optional)"),
    page: int = Query(1),
    per_page: int = Query(10)
):
    GHIN_API_USER = os.environ.get("GHIN_API_USER")
    GHIN_API_PASS = os.environ.get("GHIN_API_PASS")
    GHIN_API_STATIC_TOKEN = os.environ.get("GHIN_API_STATIC_TOKEN", "")
    if not GHIN_API_USER or not GHIN_API_PASS:
        return []
    # Step 1: Authenticate to get JWT
    auth_payload = {
        "user": {
            "password": GHIN_API_PASS,
            "email_or_ghin": GHIN_API_USER,
            "remember_me": False
        },
        "token": GHIN_API_STATIC_TOKEN,
        "source": "GHINcom"
    }
    headers = {"User-Agent": "WolfGoatPig/1.0"}
    try:
        auth_resp = httpx.post(GHIN_AUTH_URL, json=auth_payload, headers=headers, timeout=10)
        auth_resp.raise_for_status()
        auth_data = auth_resp.json()
        jwt = auth_data["golfer_user"]["golfer_user_token"]
    except Exception as e:
        print(f"GHIN auth error: {e}")
        return []
    # Step 2: Use JWT for golfer search
    search_headers = {
        "Authorization": f"Bearer {jwt}",
        "User-Agent": "WolfGoatPig/1.0",
        "Accept": "application/json"
    }
    params = {
        "last_name": last_name,
        "first_name": first_name,
        "page": page,
        "per_page": per_page,
        "source": "GHINcom"
    }
    params = {k: v for k, v in params.items() if v is not None}
    try:
        search_resp = httpx.get(GHIN_SEARCH_URL, params=params, headers=search_headers, timeout=10)
        search_resp.raise_for_status()
        data = search_resp.json()
        golfers = data.get("golfers", [])
        return [
            {
                "name": f"{g.get('first_name', '')} {g.get('last_name', '')}",
                "ghin": g.get("ghin_number"),
                "club": g.get("club_name", g.get("primary_club_name", "")),
                "handicap": g.get("handicap_index", g.get("display"))
            }
            for g in golfers
        ]
    except Exception as e:
        print(f"GHIN search error: {e}")
        return []

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
        "hole_yards": getattr(game_state, "hole_yards", []),
        "hole_descriptions": getattr(game_state, "hole_descriptions", []),
        "selected_course": game_state.selected_course,
    } 

@app.post("/simulation/hit-tee-shot")
def hit_tee_shot():
    """Hit tee shot for next player in order"""
    global game_state
    
    try:
        # Get next player to hit
        current_player_idx = getattr(game_state, 'current_tee_player_idx', 0)
        hitting_order = game_state.hitting_order or [p["id"] for p in game_state.players]
        
        if current_player_idx >= len(hitting_order):
            return {"status": "error", "message": "All players have hit tee shots"}
        
        player_id = hitting_order[current_player_idx]
        player = next(p for p in game_state.players if p["id"] == player_id)
        
        # Simulate this player's tee shot
        tee_result = simulation_engine._simulate_individual_tee_shot(player, game_state)
        
        # Store result
        if not hasattr(game_state, 'tee_shot_results'):
            game_state.tee_shot_results = {}
        game_state.tee_shot_results[player_id] = tee_result
        
        # Advance to next player
        game_state.current_tee_player_idx = current_player_idx + 1
        
        # Create shot description
        shot_desc = simulation_engine._create_shot_description(
            tee_result['drive'], tee_result['lie'], 
            tee_result['shot_quality'], tee_result['remaining'], 
            game_state.hole_pars[game_state.current_hole - 1]
        )
        
        all_tee_shots_complete = game_state.current_tee_player_idx >= len(hitting_order)
        
        return {
            "status": "ok",
            "player": player,
            "tee_result": tee_result,
            "shot_description": shot_desc,
            "all_tee_shots_complete": all_tee_shots_complete,
            "next_phase": "captain_decision" if all_tee_shots_complete else "tee_shots",
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/make-captain-decision")
def make_captain_decision(decision: dict):
    """Captain makes partnership decision"""
    global game_state
    
    try:
        captain_id = game_state.captain_id
        
        if decision.get("action") == "go_solo":
            game_state.dispatch_action("go_solo", {"captain_id": captain_id})
            message = f"Captain goes solo! Wager doubled."
            
        elif decision.get("requested_partner"):
            partner_id = decision["requested_partner"]
            game_state.dispatch_action("request_partner", {
                "captain_id": captain_id,
                "partner_id": partner_id
            })
            partner_name = next(p["name"] for p in game_state.players if p["id"] == partner_id)
            message = f"Captain requests {partner_name} as partner."
            
        return {
            "status": "ok",
            "message": message,
            "teams_formed": bool(game_state.teams),
            "next_phase": "partner_response" if decision.get("requested_partner") else "approach_shots",
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/respond-partnership")
def respond_partnership(response: dict):
    """Respond to partnership request"""
    global game_state
    
    try:
        partner_id = response.get("partner_id")
        accept = response.get("accept", False)
        
        if accept:
            game_state.dispatch_action("accept_partner", {"partner_id": partner_id})
            message = "Partnership accepted! Teams formed."
        else:
            game_state.dispatch_action("decline_partner", {"partner_id": partner_id})
            message = "Partnership declined. Captain goes solo!"
            
        return {
            "status": "ok",
            "message": message,
            "teams_formed": True,
            "next_phase": "approach_shots",
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/hit-approach-shots")
def hit_approach_shots():
    """Simulate approach shots for all players"""
    global game_state
    
    try:
        if not hasattr(game_state, 'tee_shot_results'):
            return {"status": "error", "message": "Tee shots not completed"}
            
        # Simulate approach shots and scoring
        approach_feedback = simulation_engine._simulate_remaining_shots_chronological(
            game_state, game_state.tee_shot_results
        )
        
        return {
            "status": "ok",
            "approach_feedback": approach_feedback,
            "next_phase": "doubling",
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/make-doubling-decision")
def make_doubling_decision(decision: dict):
    """Make or respond to doubling decision"""
    global game_state
    
    try:
        if decision.get("offer_double"):
            # Human offers double
            game_state.doubled_status = True
            game_state.base_wager *= 2
            message = "Double offered! Stakes increased."
            
        elif decision.get("accept_double"):
            # Human accepts computer's double
            game_state.doubled_status = True
            message = "Double accepted! Stakes doubled."
            
        else:
            message = "No additional betting this hole."
            
        return {
            "status": "ok", 
            "message": message,
            "next_phase": "hole_completion",
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/complete-hole")
def complete_hole():
    """Calculate hole results and advance to next hole"""
    global game_state
    
    try:
        # Calculate points
        game_state.dispatch_action("calculate_hole_points", {})
        
        # Generate hole summary
        hole_summary = simulation_engine._generate_hole_summary(game_state)
        
        # Advance to next hole if not finished
        if game_state.current_hole < 18:
            game_state.dispatch_action("next_hole", {})
            next_captain_name = next(p["name"] for p in game_state.players if p["id"] == game_state.captain_id)
            next_message = f"Moving to Hole {game_state.current_hole} - {next_captain_name} will be captain"
        else:
            next_message = "Game completed!"
            
        return {
            "status": "ok",
            "hole_summary": hole_summary,
            "next_message": next_message,
            "game_complete": game_state.current_hole > 18,
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) # Deployment check Tue Jul 22 20:10:12 PDT 2025

# Add new shot-based event endpoints after existing simulation endpoints

@app.post("/simulation/next-shot")
def play_next_shot():
    """Play the next individual shot in the hole with probability display"""
    global game_state
    
    try:
        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")
        
        # Determine current shot state
        shot_event = simulation_engine.get_next_shot_event(game_state)
        
        if not shot_event:
            raise HTTPException(status_code=400, detail="No shots available")
        
        # Execute the shot with probabilities
        updated_game_state, shot_result, probabilities = simulation_engine.execute_shot_event(
            game_state, shot_event
        )
        
        # Update global state
        game_state = updated_game_state
        
        # Check if betting decision is available after this shot
        betting_opportunity = simulation_engine.check_betting_opportunity(game_state, shot_result)
        
        return {
            "status": "ok",
            "shot_event": shot_event,
            "shot_result": shot_result,
            "probabilities": probabilities,
            "betting_opportunity": betting_opportunity,
            "game_state": _serialize_game_state(),
            "next_shot_available": simulation_engine.has_next_shot(game_state)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/simulation/shot-probabilities")
def get_shot_probabilities():
    """Get probability calculations for the current shot scenario"""
    global game_state
    
    try:
        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")
        
        probabilities = simulation_engine.calculate_shot_probabilities(game_state)
        
        return {
            "status": "ok",
            "probabilities": probabilities,
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/simulation/betting-decision")
def make_betting_decision(decision: dict):
    """Make a betting decision after seeing shot results with probability context"""
    global game_state
    
    try:
        # Calculate betting probabilities for context
        betting_probs = simulation_engine.calculate_betting_probabilities(game_state, decision)
        
        # Execute the betting decision
        updated_game_state, decision_result = simulation_engine.execute_betting_decision(
            game_state, decision, betting_probs
        )
        
        game_state = updated_game_state
        
        return {
            "status": "ok",
            "decision": decision,
            "decision_result": decision_result,
            "betting_probabilities": betting_probs,
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/simulation/current-shot-state")
def get_current_shot_state():
    """Get detailed information about the current shot state and available actions"""
    global game_state
    
    try:
        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")
        
        shot_state = simulation_engine.get_current_shot_state(game_state)
        
        return {
            "status": "ok",
            "shot_state": shot_state,
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
