from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud, database
# Ensure tables are created before anything else
# Call init_db before importing game_state

database.init_db()

from .game_state import game_state
from .simulation import simulation_engine
from .course_import import CourseImporter, import_course_by_name, import_course_from_json, save_course_to_database
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
import os
import httpx
import logging
import traceback
import json
import tempfile

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
    """Get all Wolf Goat Pig rules with defensive error handling"""
    try:
        rules = crud.get_rules()
        if not rules:
            # Return default rules if database is empty
            return [
                {"id": 1, "title": "Basic Game (4 Players)", "description": "Played with four players. Hitting order is determined randomly at the first tee. The first player is the Captain."},
                {"id": 2, "title": "Order of Play", "description": "The Captain is determined randomly on the first tee. The order rotates each hole."},
                {"id": 3, "title": "Partnership", "description": "The Captain may request a partner for that hole (best ball). A player becomes ineligible to be requested once the next player in order has hit their shot."}
            ]
        return rules
    except Exception as e:
        print(f"⚠️ Rules endpoint error: {e}")
        # Return safe default rules
        return [
            {"id": 1, "title": "Basic Game (4 Players)", "description": "Played with four players. Hitting order is determined randomly at the first tee. The first player is the Captain."},
            {"id": 2, "title": "Order of Play", "description": "The Captain is determined randomly on the first tee. The order rotates each hole."},
            {"id": 3, "title": "Partnership", "description": "The Captain may request a partner for that hole (best ball). A player becomes ineligible to be requested once the next player in order has hit their shot."}
        ]

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
    """Get all available courses with defensive error handling"""
    try:
        if not game_state:
            # Return default courses if no game state
            return {
                "Executive Course": {
                    "name": "Executive Course",
                    "holes": [
                        {"hole_number": 1, "par": 4, "yards": 320, "stroke_index": 7, "description": "Short par 4 with water hazard"},
                        {"hole_number": 2, "par": 3, "yards": 145, "stroke_index": 15, "description": "Uphill par 3"},
                        {"hole_number": 3, "par": 4, "yards": 380, "stroke_index": 3, "description": "Long par 4 with bunkers"}
                    ]
                }
            }
        return game_state.get_courses()
    except Exception as e:
        print(f"⚠️ Courses endpoint error: {e}")
        # Return safe default courses
        return {
            "Executive Course": {
                "name": "Executive Course",
                "holes": [
                    {"hole_number": 1, "par": 4, "yards": 320, "stroke_index": 7, "description": "Short par 4 with water hazard"},
                    {"hole_number": 2, "par": 3, "yards": 145, "stroke_index": 15, "description": "Uphill par 3"},
                    {"hole_number": 3, "par": 4, "yards": 380, "stroke_index": 3, "description": "Long par 4 with bunkers"}
                ]
            }
        }

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

# Course Import Endpoints
class CourseImportRequest(BaseModel):
    course_name: str
    state: Optional[str] = None
    city: Optional[str] = None

@app.post("/courses/import/search")
async def import_course_by_search(request: CourseImportRequest):
    """Import a course by searching external databases"""
    try:
        logger.info(f"Importing course: {request.course_name}")
        
        # Import course from external sources
        course_data = await import_course_by_name(
            request.course_name, 
            request.state, 
            request.city
        )
        
        if not course_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Course '{request.course_name}' not found in any external database"
            )
        
        # Save to database
        success = save_course_to_database(course_data)
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Failed to save course to database"
            )
        
        # Convert to response format
        holes = []
        for hole in course_data.holes_data:
            holes.append({
                "hole_number": hole["hole_number"],
                "par": hole["par"],
                "yards": hole["yards"],
                "handicap": hole["handicap"],
                "description": hole.get("description", ""),
                "tee_box": hole.get("tee_box", "regular")
            })
        
        return {
            "status": "success",
            "message": f"Course '{course_data.name}' imported successfully from {course_data.source}",
            "course": {
                "name": course_data.name,
                "description": course_data.description,
                "total_par": course_data.total_par,
                "total_yards": course_data.total_yards,
                "course_rating": course_data.course_rating,
                "slope_rating": course_data.slope_rating,
                "holes": holes,
                "source": course_data.source,
                "last_updated": course_data.last_updated,
                "location": course_data.location,
                "website": course_data.website,
                "phone": course_data.phone
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Course import error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Import failed: {str(e)}"
        )

@app.post("/courses/import/file")
async def import_course_from_file(file: UploadFile = File(...)):
    """Import a course from a JSON file upload"""
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(
                status_code=400, 
                detail="Only JSON files are supported"
            )
        
        # Read file content
        content = await file.read()
        try:
            course_json = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, 
                detail="Invalid JSON format"
            )
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(course_json, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Import from file
            course_data = await import_course_from_json(temp_file_path)
            
            if not course_data:
                raise HTTPException(
                    status_code=400, 
                    detail="Failed to parse course data from file"
                )
            
            # Save to database
            success = save_course_to_database(course_data)
            if not success:
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to save course to database"
                )
            
            # Convert to response format
            holes = []
            for hole in course_data.holes_data:
                holes.append({
                    "hole_number": hole["hole_number"],
                    "par": hole["par"],
                    "yards": hole["yards"],
                    "handicap": hole["handicap"],
                    "description": hole.get("description", ""),
                    "tee_box": hole.get("tee_box", "regular")
                })
            
            return {
                "status": "success",
                "message": f"Course '{course_data.name}' imported successfully from file",
                "course": {
                    "name": course_data.name,
                    "description": course_data.description,
                    "total_par": course_data.total_par,
                    "total_yards": course_data.total_yards,
                    "course_rating": course_data.course_rating,
                    "slope_rating": course_data.slope_rating,
                    "holes": holes,
                    "source": course_data.source,
                    "last_updated": course_data.last_updated,
                    "location": course_data.location,
                    "website": course_data.website,
                    "phone": course_data.phone
                }
            }
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File import error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"File import failed: {str(e)}"
        )

@app.get("/courses/import/sources")
def get_import_sources():
    """Get available import sources and their status"""
    api_keys = {
        "usga_api_key": bool(os.getenv("USGA_API_KEY")),
        "ghin_api_key": bool(os.getenv("GHIN_API_KEY")),
        "golf_now_api_key": bool(os.getenv("GOLF_NOW_API_KEY")),
        "thegrint_api_key": bool(os.getenv("THEGRINT_API_KEY"))
    }
    
    sources = [
        {
            "name": "USGA",
            "description": "United States Golf Association course database",
            "available": api_keys["usga_api_key"],
            "requires_api_key": True,
            "endpoint": "/courses/import/search"
        },
        {
            "name": "GHIN",
            "description": "Golf Handicap and Information Network",
            "available": True,  # GHIN doesn't require API key for basic search
            "requires_api_key": False,
            "endpoint": "/courses/import/search"
        },
        {
            "name": "GolfNow",
            "description": "GolfNow course database",
            "available": api_keys["golf_now_api_key"],
            "requires_api_key": True,
            "endpoint": "/courses/import/search"
        },
        {
            "name": "TheGrint",
            "description": "TheGrint golf course database",
            "available": api_keys["thegrint_api_key"],
            "requires_api_key": True,
            "endpoint": "/courses/import/search"
        },
        {
            "name": "JSON File",
            "description": "Import from JSON file upload",
            "available": True,
            "requires_api_key": False,
            "endpoint": "/courses/import/file"
        }
    ]
    
    return {
        "sources": sources,
        "configured_sources": sum(1 for source in sources if source["available"]),
        "total_sources": len(sources)
    }

@app.post("/courses/import/preview")
async def preview_course_import(request: CourseImportRequest):
    """Preview course data before importing (doesn't save to database)"""
    try:
        logger.info(f"Previewing course import: {request.course_name}")
        
        # Import course from external sources
        course_data = await import_course_by_name(
            request.course_name, 
            request.state, 
            request.city
        )
        
        if not course_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Course '{request.course_name}' not found in any external database"
            )
        
        # Convert to response format
        holes = []
        for hole in course_data.holes_data:
            holes.append({
                "hole_number": hole["hole_number"],
                "par": hole["par"],
                "yards": hole["yards"],
                "handicap": hole["handicap"],
                "description": hole.get("description", ""),
                "tee_box": hole.get("tee_box", "regular")
            })
        
        return {
            "status": "preview",
            "message": f"Course '{course_data.name}' found in {course_data.source}",
            "course": {
                "name": course_data.name,
                "description": course_data.description,
                "total_par": course_data.total_par,
                "total_yards": course_data.total_yards,
                "course_rating": course_data.course_rating,
                "slope_rating": course_data.slope_rating,
                "holes": holes,
                "source": course_data.source,
                "last_updated": course_data.last_updated,
                "location": course_data.location,
                "website": course_data.website,
                "phone": course_data.phone
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Course preview error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Preview failed: {str(e)}"
        )

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
    """Setup a simulation game with defensive error handling"""
    global game_state
    
    try:
        # Validate input
        if not setup.human_player or not setup.computer_players:
            raise HTTPException(status_code=400, detail="Missing human player or computer players")
        
        if len(setup.computer_players) != 3:
            raise HTTPException(status_code=400, detail="Need exactly 3 computer players")
        
        print(f"🎯 /simulation/setup called")
        print(f"🎯 Human player: {setup.human_player}")
        print(f"🎯 Computer players: {[cp.dict() for cp in setup.computer_players]}")
        
        # Convert to dict format expected by simulation engine
        human_player = {
            "id": setup.human_player.get("id", "human"),
            "name": setup.human_player.get("name", "Human Player"),
            "handicap": setup.human_player.get("handicap", 18)
        }
        
        computer_configs = [
            {
                "id": cp.id,
                "name": cp.name,
                "handicap": cp.handicap,
                "personality": cp.personality
            }
            for cp in setup.computer_players
        ]
        
        print(f"🎯 Converted human_player: {human_player}")
        print(f"🎯 Converted computer_configs: {computer_configs}")
        
        # Setup simulation
        game_state = simulation_engine.setup_simulation(
            human_player, computer_configs, setup.course_name
        )
        
        return {
            "status": "ok",
            "message": "Simulation setup successfully",
            "game_state": _serialize_game_state()
        }
        
    except Exception as e:
        print(f"⚠️ Simulation setup error: {e}")
        raise HTTPException(status_code=400, detail=f"Setup failed: {str(e)}")

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
    """Play a hole with interactive decision points"""
    try:
        if not game_state:
            raise HTTPException(status_code=400, detail="No active simulation. Please set up a simulation first.")
        
        # Convert Pydantic model to dict for simulation engine
        human_decisions = {
            "action": decisions.action,
            "requested_partner": decisions.requested_partner,
            "offer_double": decisions.offer_double,
            "accept_double": decisions.accept_double,
            "accept_partnership": decisions.accept_partnership
        }
        
        # Remove None values
        human_decisions = {k: v for k, v in human_decisions.items() if v is not None}
        
        # Run simulation with enhanced error handling
        try:
            updated_game_state, feedback, interaction_needed = simulation_engine.simulate_hole(
                game_state, human_decisions
            )
        except Exception as e:
            logging.error(f"Simulation error: {str(e)}")
            logging.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")
        
        # Prepare response with consistent structure
        response = {
            "status": "ok",
            "game_state": _serialize_game_state(),
            "feedback": feedback or [],
            "next_shot_available": True  # Default for hole-based simulation
        }
        
        # Add interaction needed if present
        if interaction_needed:
            response["interaction_needed"] = interaction_needed
            response["next_shot_available"] = False  # Pause for decision
        
        # Add probabilities if available
        try:
            probabilities = simulation_engine.calculate_shot_probabilities(game_state)
            if probabilities:
                response["probabilities"] = probabilities
        except Exception as e:
            logging.warning(f"Could not calculate probabilities: {e}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in play_simulation_hole: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/simulation/next-shot", response_model=ShotEventResponse)
def play_next_shot() -> ShotEventResponse:
    """Play the next shot in the event-driven simulation"""
    try:
        if not game_state:
            raise HTTPException(status_code=400, detail="No active simulation")
        
        # Get next shot event
        shot_event = simulation_engine.get_next_shot_event(game_state)
        
        if not shot_event:
            # No more shots available
            return ShotEventResponse(
                status="ok",
                shot_event=None,
                shot_result=None,
                probabilities=None,
                betting_opportunity=None,
                game_state=_serialize_game_state(),
                next_shot_available=False
            )
        
        # Execute the shot event
        try:
            updated_game_state, shot_result, betting_opportunity = simulation_engine.execute_shot_event(
                game_state, shot_event
            )
        except Exception as e:
            logging.error(f"Shot execution error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Shot execution error: {str(e)}")
        
        # Calculate probabilities for next shot
        probabilities = None
        try:
            probabilities = simulation_engine.calculate_shot_probabilities(game_state)
        except Exception as e:
            logging.warning(f"Could not calculate probabilities: {e}")
        
        # Check if there are more shots available
        has_next_shot = simulation_engine.has_next_shot(game_state)
        
        # Check for interaction needed
        interaction_needed = None
        if betting_opportunity and betting_opportunity.get("requires_decision"):
            interaction_needed = {
                "type": "betting_opportunity",
                "message": "A betting opportunity has arisen!",
                "opportunity": betting_opportunity
            }
        
        return ShotEventResponse(
            status="ok",
            shot_event=shot_event,
            shot_result=shot_result,
            probabilities=probabilities,
            betting_opportunity=betting_opportunity,
            game_state=_serialize_game_state(),
            next_shot_available=has_next_shot and not interaction_needed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in play_next_shot: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/simulation/betting-decision", response_model=BettingDecisionResponse)
def make_betting_decision(decision: BettingDecisionRequest) -> BettingDecisionResponse:
    """Make a betting decision (partnership, doubling, etc.)"""
    try:
        if not game_state:
            raise HTTPException(status_code=400, detail="No active simulation")
        
        # Validate decision
        if not decision.action:
            raise HTTPException(status_code=400, detail="Decision action is required")
        
        # Calculate betting probabilities
        try:
            betting_probs = simulation_engine.calculate_betting_probabilities(game_state, decision.dict())
        except Exception as e:
            logging.warning(f"Could not calculate betting probabilities: {e}")
            betting_probs = {}
        
        # Execute the decision
        try:
            updated_game_state, decision_result = simulation_engine.execute_betting_decision(
                game_state, decision.dict(), betting_probs
            )
        except Exception as e:
            logging.error(f"Decision execution error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Decision execution error: {str(e)}")
        
        return BettingDecisionResponse(
            status="ok",
            decision=decision.dict(),
            decision_result=decision_result,
            betting_probabilities=betting_probs,
            game_state=_serialize_game_state()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in make_betting_decision: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/simulation/shot-probabilities", response_model=ShotProbabilitiesResponse)
def get_shot_probabilities() -> ShotProbabilitiesResponse:
    """Get current shot probabilities"""
    try:
        if not game_state:
            raise HTTPException(status_code=400, detail="No active simulation")
        
        probabilities = simulation_engine.calculate_shot_probabilities(game_state)
        
        return ShotProbabilitiesResponse(
            status="ok",
            probabilities=probabilities or {},
            game_state=_serialize_game_state()
        )
        
    except Exception as e:
        logging.error(f"Error getting shot probabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/simulation/current-shot-state", response_model=CurrentShotStateResponse)
def get_current_shot_state() -> CurrentShotStateResponse:
    """Get current shot state information"""
    try:
        if not game_state:
            raise HTTPException(status_code=400, detail="No active simulation")
        
        shot_state = simulation_engine.get_current_shot_state(game_state)
        
        return CurrentShotStateResponse(
            status="ok",
            shot_state=shot_state or {},
            game_state=_serialize_game_state()
        )
        
    except Exception as e:
        logging.error(f"Error getting shot state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/simulation/test-new-endpoints")
def test_new_endpoints():
    """Test if new endpoints are working"""
    return {"status": "ok", "message": "New interactive endpoints are working!", "timestamp": "2025-01-22"}

@app.get("/simulation/available-personalities")
def get_available_personalities():
    """Get available computer player personalities with defensive error handling"""
    try:
        return {
            "personalities": [
                {
                    "id": "aggressive",
                    "name": "Aggressive",
                    "description": "Takes risks, goes for birdies, aggressive betting"
                },
                {
                    "id": "conservative", 
                    "name": "Conservative",
                    "description": "Plays safe, avoids big numbers, careful betting"
                },
                {
                    "id": "balanced",
                    "name": "Balanced", 
                    "description": "Mix of aggressive and conservative play"
                },
                {
                    "id": "strategic",
                    "name": "Strategic",
                    "description": "Analyzes situations, adapts to course conditions"
                }
            ]
        }
    except Exception as e:
        print(f"⚠️ Personalities endpoint error: {e}")
        return {"personalities": []}

@app.get("/simulation/suggested-opponents")
def get_suggested_opponents():
    """Get suggested computer opponents with defensive error handling"""
    try:
        return {
            "opponents": [
                {
                    "id": "comp1",
                    "name": "Tiger Woods",
                    "handicap": 2,
                    "personality": "aggressive",
                    "description": "Former world #1, aggressive player"
                },
                {
                    "id": "comp2", 
                    "name": "Jack Nicklaus",
                    "handicap": 5,
                    "personality": "strategic",
                    "description": "Golden Bear, strategic master"
                },
                {
                    "id": "comp3",
                    "name": "Arnold Palmer",
                    "handicap": 8,
                    "personality": "aggressive", 
                    "description": "The King, aggressive style"
                },
                {
                    "id": "comp4",
                    "name": "Ben Hogan",
                    "handicap": 3,
                    "personality": "conservative",
                    "description": "The Hawk, precise and conservative"
                },
                {
                    "id": "comp5",
                    "name": "Sam Snead",
                    "handicap": 6,
                    "personality": "balanced",
                    "description": "Slammin' Sammy, well-rounded game"
                },
                {
                    "id": "comp6",
                    "name": "Gary Player",
                    "handicap": 4,
                    "personality": "strategic",
                    "description": "The Black Knight, strategic player"
                }
            ]
        }
    except Exception as e:
        print(f"⚠️ Opponents endpoint error: {e}")
        return {"opponents": []}

GHIN_AUTH_URL = "https://api2.ghin.com/api/v1/golfer_login.json"
GHIN_SEARCH_URL = "https://api2.ghin.com/api/v1/golfers/search.json"

@app.get("/ghin/lookup")
def ghin_lookup(
    last_name: str = Query(..., description="Golfer's last name"),
    first_name: str = Query(None, description="Golfer's first name (optional)"),
    page: int = Query(1),
    per_page: int = Query(10)
):
    """Lookup golfer by name in GHIN database with defensive error handling"""
    try:
        # Check if GHIN credentials are available
        ghin_user = os.environ.get("GHIN_API_USER")
        ghin_pass = os.environ.get("GHIN_API_PASS")
        ghin_token = os.environ.get("GHIN_API_STATIC_TOKEN")
        
        if not ghin_user or not ghin_pass:
            return {
                "status": "error",
                "message": "GHIN API credentials not configured",
                "golfers": [],
                "suggestion": "Set GHIN_API_USER and GHIN_API_PASS environment variables"
            }
        
        # Authenticate with GHIN
        auth_response = httpx.post(GHIN_AUTH_URL, json={
            "user": {"email_or_ghin": ghin_user, "password": ghin_pass},
            "token": ghin_token or "dummy_token",
            "source": "GHINcom"
        }, timeout=10.0)
        
        if not auth_response.is_success:
            return {
                "status": "error", 
                "message": f"GHIN authentication failed: {auth_response.status_code}",
                "golfers": []
            }
        
        auth_data = auth_response.json()
        jwt = auth_data.get("golfer_user", {}).get("golfer_user_token")
        
        if not jwt:
            return {
                "status": "error",
                "message": "No JWT token received from GHIN",
                "golfers": []
            }
        
        # Search for golfers
        search_params = {"last_name": last_name}
        if first_name:
            search_params["first_name"] = first_name
        
        search_response = httpx.get(
            GHIN_SEARCH_URL,
            headers={"Authorization": f"Bearer {jwt}"},
            params=search_params,
            timeout=10.0
        )
        
        if not search_response.is_success:
            return {
                "status": "error",
                "message": f"GHIN search failed: {search_response.status_code}",
                "golfers": []
            }
        
        search_data = search_response.json()
        golfers = search_data.get("golfers", [])
        
        # Format results
        formatted_golfers = []
        for golfer in golfers:
            formatted_golfers.append({
                "ghin": golfer.get("ghin"),
                "first_name": golfer.get("first_name"),
                "last_name": golfer.get("last_name"),
                "handicap_index": golfer.get("handicap_index"),
                "club_name": golfer.get("club_name"),
                "state": golfer.get("state")
            })
        
        return {
            "status": "success",
            "golfers": formatted_golfers,
            "total": len(formatted_golfers)
        }
        
    except httpx.TimeoutException:
        return {
            "status": "error",
            "message": "GHIN API request timed out",
            "golfers": []
        }
    except Exception as e:
        print(f"⚠️ GHIN lookup error: {e}")
        return {
            "status": "error",
            "message": f"GHIN lookup failed: {str(e)}",
            "golfers": []
        }

@app.get("/ghin/diagnostic")
def ghin_diagnostic():
    """Diagnostic endpoint to check GHIN API configuration and connectivity"""
    GHIN_API_USER = os.environ.get("GHIN_API_USER")
    GHIN_API_PASS = os.environ.get("GHIN_API_PASS")
    GHIN_API_STATIC_TOKEN = os.environ.get("GHIN_API_STATIC_TOKEN", "")
    
    diagnostic_info = {
        "status": "checking",
        "environment_variables": {
            "GHIN_API_USER": "SET" if GHIN_API_USER else "MISSING",
            "GHIN_API_PASS": "SET" if GHIN_API_PASS else "MISSING",
            "GHIN_API_STATIC_TOKEN": "SET" if GHIN_API_STATIC_TOKEN else "MISSING"
        },
        "api_urls": {
            "auth_url": GHIN_AUTH_URL,
            "search_url": GHIN_SEARCH_URL
        }
    }
    
    # Test basic connectivity if credentials are available
    if GHIN_API_USER and GHIN_API_PASS:
        try:
            # Test authentication
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
            
            auth_resp = httpx.post(GHIN_AUTH_URL, json=auth_payload, headers=headers, timeout=10)
            
            if auth_resp.status_code == 200:
                auth_data = auth_resp.json()
                if "golfer_user" in auth_data and "golfer_user_token" in auth_data["golfer_user"]:
                    diagnostic_info["auth_test"] = "SUCCESS"
                    diagnostic_info["jwt_received"] = "YES"
                    
                    # Test a simple search
                    jwt = auth_data["golfer_user"]["golfer_user_token"]
                    search_headers = {
                        "Authorization": f"Bearer {jwt}",
                        "User-Agent": "WolfGoatPig/1.0",
                        "Accept": "application/json"
                    }
                    search_params = {
                        "last_name": "Smith",
                        "first_name": "John",
                        "page": 1,
                        "per_page": 5,
                        "source": "GHINcom"
                    }
                    
                    search_resp = httpx.get(GHIN_SEARCH_URL, params=search_params, headers=search_headers, timeout=10)
                    diagnostic_info["search_test"] = {
                        "status_code": search_resp.status_code,
                        "response_length": len(search_resp.text),
                        "contains_golfers": "golfers" in search_resp.text
                    }
                    
                    if search_resp.status_code == 200:
                        search_data = search_resp.json()
                        diagnostic_info["search_test"]["golfers_found"] = len(search_data.get("golfers", []))
                        diagnostic_info["status"] = "WORKING"
                    else:
                        diagnostic_info["search_test"]["error"] = search_resp.text[:200]
                        diagnostic_info["status"] = "AUTH_OK_SEARCH_FAILED"
                else:
                    diagnostic_info["auth_test"] = "FAILED - No JWT in response"
                    diagnostic_info["auth_response_keys"] = list(auth_data.keys()) if isinstance(auth_data, dict) else "Not dict"
                    diagnostic_info["status"] = "AUTH_FAILED"
            else:
                diagnostic_info["auth_test"] = f"FAILED - Status {auth_resp.status_code}"
                diagnostic_info["auth_error"] = auth_resp.text[:200]
                diagnostic_info["status"] = "AUTH_FAILED"
                
        except Exception as e:
            diagnostic_info["auth_test"] = f"EXCEPTION - {str(e)}"
            diagnostic_info["status"] = "ERROR"
    else:
        diagnostic_info["status"] = "CREDENTIALS_MISSING"
    
    return diagnostic_info

# Helper to serialize game state for API

def _serialize_game_state():
    # Convert Player objects to dicts for API serialization
    players_data = [p.to_dict() if hasattr(p, 'to_dict') else p for p in game_state.players]
    
    return {
        "players": players_data,
        "current_hole": game_state.current_hole,
        "hitting_order": game_state.hitting_order,
        "captain_id": game_state.captain_id,
        "teams": game_state.betting_state.teams,
        "base_wager": game_state.betting_state.base_wager,
        "doubled_status": game_state.betting_state.doubled_status,
        "game_phase": game_state.betting_state.game_phase,
        "hole_scores": game_state.hole_scores,
        "game_status_message": game_state.game_status_message,
        "player_float_used": game_state.player_float_used,
        "carry_over": game_state.carry_over,
        "hole_history": game_state.get_hole_history(),
                    "hole_stroke_indexes": game_state.course_manager.hole_stroke_indexes,
            "hole_pars": game_state.course_manager.hole_pars,
            "hole_yards": game_state.course_manager.hole_yards,
            "hole_descriptions": [h.get("description", "") for h in game_state.course_manager.course_data.get(game_state.course_manager.selected_course, [])] if game_state.course_manager.selected_course else [],
            "selected_course": game_state.course_manager.selected_course,
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
        
        # Create shot description - handle both ShotResult objects and dictionaries
        if hasattr(tee_result, 'drive'):
            # ShotResult object
            shot_desc = simulation_engine._create_shot_description(
                tee_result.drive, tee_result.lie,
                tee_result.shot_quality, tee_result.remaining,
                game_state.course_manager.hole_pars[game_state.current_hole - 1]
            )
        else:
            # Dictionary fallback
            shot_desc = simulation_engine._create_shot_description(
                tee_result['drive'], tee_result['lie'], 
                tee_result['shot_quality'], tee_result['remaining'], 
                game_state.course_manager.hole_pars[game_state.current_hole - 1]
            )
        
        all_tee_shots_complete = game_state.current_tee_player_idx >= len(hitting_order)
        
        # Convert ShotResult to dict for JSON serialization
        tee_result_dict = tee_result.to_dict() if hasattr(tee_result, 'to_dict') else tee_result
        
        return {
            "status": "ok",
            "player": player,
            "tee_result": tee_result_dict,
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
            "teams_formed": bool(game_state.betting_state.teams),
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
            game_state.betting_state.doubled_status = True
            game_state.betting_state.base_wager *= 2
            message = "Double offered! Stakes increased."
            
        elif decision.get("accept_double"):
            # Human accepts computer's double
            game_state.betting_state.doubled_status = True
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

class ShotEventResponse(BaseModel):
    status: str
    shot_event: Optional[dict]
    shot_result: Optional[dict]
    probabilities: Optional[dict]
    betting_opportunity: Optional[dict]
    game_state: dict
    next_shot_available: bool

class ShotProbabilitiesResponse(BaseModel):
    status: str
    probabilities: dict
    game_state: dict

class BettingDecisionRequest(BaseModel):
    action: str
    partner_id: Optional[str] = None
    # Add other fields as needed for betting/solo/doubling

class BettingDecisionResponse(BaseModel):
    status: str
    decision: dict
    decision_result: dict
    betting_probabilities: dict
    game_state: dict

class CurrentShotStateResponse(BaseModel):
    status: str
    shot_state: dict
    game_state: dict
