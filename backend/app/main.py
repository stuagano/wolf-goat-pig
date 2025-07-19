from fastapi import FastAPI, Depends, Body, Request, Path
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud, database
# Ensure tables are created before anything else
# Call init_db before importing game_state

database.init_db()

from .game_state import game_state
from .simulation import simulation_engine
from .exceptions import APIException, handle_game_exception
from .utils import SerializationUtils, CourseUtils, SimulationUtils
from .constants import PERSONALITY_DESCRIPTIONS, SUGGESTED_OPPONENTS, VALIDATION_LIMITS
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


class APIResponseHandler:
    """Centralized API response handling to eliminate DRY violations"""
    
    @staticmethod
    def success_response(message: str = "Success", data: any = None) -> dict:
        """Standard success response format"""
        response = {"status": "success", "message": message}
        if data is not None:
            response.update(data)
        return response
    
    @staticmethod
    def game_state_response(message: str = "ok") -> dict:
        """Standard game state response format"""
        return {
            "status": message, 
            "game_state": SerializationUtils.serialize_game_state(game_state)
        }
    
    @staticmethod
    def game_state_with_result(result: any, message: str = "ok") -> dict:
        """Game state response with additional result data"""
        return {
            "status": message,
            "game_state": SerializationUtils.serialize_game_state(game_state),
            "result": result
        }


@app.on_event("startup")
def startup():
    database.init_db()

@app.get("/rules", response_model=list[schemas.Rule])
def get_rules():
    return crud.get_rules()

@app.post("/game/start")
def start_game():
    game_state.reset()
    return APIResponseHandler.game_state_response()

@app.get("/game/state")
def get_game_state():
    return SerializationUtils.serialize_game_state(game_state)

@app.post("/game/action")
def game_action(data: dict = Body(...)):
    action = data.get("action")
    payload = data.get("payload", {})
    try:
        result = game_state.dispatch_action(action, payload)
        return APIResponseHandler.game_state_with_result(result)
    except Exception as e:
        raise handle_game_exception(e)

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
        raise APIException.missing_required_field("players")
    
    try:
        game_state.setup_players(players, course_name=course_name)
        return APIResponseHandler.game_state_response()
    except Exception as e:
        raise handle_game_exception(e)

from .schemas import CourseCreate, CourseUpdate, CourseResponse, CourseStats, CourseComparison, HoleInfo

@app.post("/courses", response_model=dict)
def add_course(course: CourseCreate):
    """Add a new course with validation"""
    try:
        course_data = CourseUtils.convert_course_create_to_dict(course)
        game_state.add_course(course_data)
        return APIResponseHandler.success_response(
            "Course created successfully", 
            {"courses": game_state.get_courses()}
        )
    except ValueError as e:
        raise APIException.bad_request(str(e))

@app.put("/courses/{course_name}")
def update_course(course_name: str, course_update: CourseUpdate):
    """Update an existing course"""
    try:
        update_data = CourseUtils.convert_course_update_to_dict(course_update)
        game_state.update_course(course_name, update_data)
        return APIResponseHandler.success_response(
            "Course updated successfully",
            {"courses": game_state.get_courses()}
        )
    except ValueError as e:
        raise APIException.bad_request(str(e))

@app.delete("/courses/{course_name}")
def delete_course(course_name: str = Path(...)):
    """Delete a course"""
    try:
        game_state.delete_course(course_name)
        return APIResponseHandler.success_response(
            "Course deleted successfully",
            {"courses": game_state.get_courses()}
        )
    except ValueError as e:
        raise APIException.resource_not_found("Course", course_name)

@app.get("/courses/{course_name}/stats")
def get_course_stats(course_name: str):
    """Get statistics for a specific course"""
    try:
        stats = game_state.get_course_stats(course_name)
        return stats
    except ValueError as e:
        raise APIException.resource_not_found("Course", course_name)

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
        raise APIException.resource_not_found("Course", f"{course1} or {course2}")

@app.get("/game/current-hole")
def get_current_hole_info():
    """Get detailed information about the current hole"""
    hole_info = game_state.get_current_hole_info()
    if hole_info is None:
        raise APIException.not_found("No current hole information available")
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


class SimulationManager:
    """Manages simulation-related operations to eliminate DRY violations"""
    
    @staticmethod
    def validate_simulation_setup(computer_players: List[ComputerPlayerConfig], 
                                num_simulations: Optional[int] = None) -> None:
        """Validate simulation setup parameters"""
        if len(computer_players) != 3:
            raise APIException.bad_request("Need exactly 3 computer players")
        
        if num_simulations is not None:
            if not (VALIDATION_LIMITS["MIN_SIMULATIONS"] <= num_simulations <= VALIDATION_LIMITS["MAX_SIMULATIONS"]):
                raise APIException.invalid_range(
                    "Number of simulations", 
                    VALIDATION_LIMITS["MIN_SIMULATIONS"], 
                    VALIDATION_LIMITS["MAX_SIMULATIONS"]
                )
    
    @staticmethod
    def setup_simulation_game(setup: SimulationSetup):
        """Setup a simulation game with proper error handling"""
        SimulationManager.validate_simulation_setup(setup.computer_players)
        
        computer_configs = SimulationUtils.convert_computer_player_configs(setup.computer_players)
        sim_game_state = simulation_engine.setup_simulation(setup.human_player, computer_configs)
        
        if setup.course_name and setup.course_name in sim_game_state.courses:
            course = sim_game_state.courses[setup.course_name]
            sim_game_state.selected_course = setup.course_name
            sim_game_state.hole_stroke_indexes = [h["stroke_index"] for h in course]
            sim_game_state.hole_pars = [h["par"] for h in course]
            sim_game_state._save_to_db()
        
        return sim_game_state


@app.post("/simulation/setup")
def setup_simulation(setup: SimulationSetup):
    """Setup a new simulation game with one human and three computer players"""
    global game_state
    
    try:
        sim_game_state = SimulationManager.setup_simulation_game(setup)
        game_state = sim_game_state
        
        return {
            "status": "ok", 
            "game_state": SerializationUtils.serialize_game_state(game_state),
            "message": "Simulation setup complete! You're playing against 3 computer opponents."
        }
    except Exception as e:
        raise handle_game_exception(e)

@app.post("/simulation/monte-carlo")
def run_monte_carlo_simulation(setup: MonteCarloSetup):
    """Run Monte Carlo simulation with specified number of games"""
    try:
        SimulationManager.validate_simulation_setup(setup.computer_players, setup.num_simulations)
        
        computer_configs = SimulationUtils.convert_computer_player_configs(setup.computer_players)
        
        # Run Monte Carlo simulation
        results = simulation_engine.run_monte_carlo_simulation(
            setup.human_player,
            computer_configs,
            setup.num_simulations,
            setup.course_name
        )
        
        # Get summary statistics
        summary = results.get_summary()
        
        # Generate insights using centralized logic
        insights = SimulationInsightGenerator.generate_insights(summary, setup.human_player["id"])
        
        return {
            "results": summary,
            "insights": insights,
            "total_simulations": setup.num_simulations
        }
    except Exception as e:
        raise handle_game_exception(e)


class SimulationInsightGenerator:
    """Generates insights for Monte Carlo simulations to eliminate duplicate logic"""
    
    @staticmethod
    def generate_insights(summary: dict, human_id: str) -> List[str]:
        """Generate insights based on simulation results"""
        insights = []
        human_stats = summary["player_statistics"][human_id]
        
        # Win rate analysis
        win_rate = human_stats["win_percentage"]
        if win_rate > 30:
            insights.append(f"🎯 Strong performance! You won {win_rate:.1f}% of games")
        elif win_rate > 20:
            insights.append(f"👍 Decent performance. You won {win_rate:.1f}% of games")
        else:
            insights.append(f"📚 Room for improvement. You won {win_rate:.1f}% of games")
        
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
            insights.append("📊 You finished 4th in average scoring")
        
        return insights


@app.get("/simulation/monte-carlo/detailed/{num_games}")
def get_monte_carlo_detailed_results(num_games: int, setup: MonteCarloSetup):
    """Get detailed results from Monte Carlo simulation"""
    try:
        if not (VALIDATION_LIMITS["MIN_DETAILED_GAMES"] <= num_games <= VALIDATION_LIMITS["MAX_DETAILED_GAMES"]):
            raise APIException.invalid_range(
                "Number of detailed games",
                VALIDATION_LIMITS["MIN_DETAILED_GAMES"], 
                VALIDATION_LIMITS["MAX_DETAILED_GAMES"]
            )
        
        SimulationManager.validate_simulation_setup(setup.computer_players)
        
        computer_configs = SimulationUtils.convert_computer_player_configs(setup.computer_players)
        
        results = simulation_engine.run_monte_carlo_simulation(
            setup.human_player,
            computer_configs,
            num_games,
            setup.course_name
        )
        
        return {
            "detailed_results": results.detailed_results,
            "summary": results.get_summary()
        }
    except Exception as e:
        raise handle_game_exception(e)

@app.post("/simulation/hole")
def play_simulation_hole(decisions: HumanDecisions):
    """Play a single hole in simulation mode"""
    try:
        decisions_dict = {
            "action": decisions.action,
            "requested_partner": decisions.requested_partner,
            "offer_double": decisions.offer_double,
            "accept_double": decisions.accept_double
        }
        
        updated_state, feedback = simulation_engine.simulate_hole(game_state, decisions_dict)
        
        global game_state
        game_state = updated_state
        
        return {
            "status": "ok",
            "game_state": SerializationUtils.serialize_game_state(game_state),
            "feedback": feedback
        }
    except Exception as e:
        raise handle_game_exception(e)

@app.get("/simulation/personalities")
def get_available_personalities():
    """Get available computer player personalities"""
    return {
        "personalities": [
            {"name": name, "description": desc}
            for name, desc in PERSONALITY_DESCRIPTIONS.items()
        ]
    }

@app.get("/simulation/suggested-opponents")
def get_suggested_opponents():
    """Get suggested computer opponents with different skill levels"""
    return {"opponents": SUGGESTED_OPPONENTS} 