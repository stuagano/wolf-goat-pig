from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path, Query, UploadFile, File
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from . import models, schemas, crud, database
# Ensure tables are created before anything else
database.init_db()

from .game_state import game_state
from .wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer
from .course_import import CourseImporter, import_course_by_name, import_course_from_json, save_course_to_database
from .domain.shot_result import ShotResult
from .domain.player import Player
from .domain.shot_range_analysis import analyze_shot_decision
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
import os
import httpx
import logging
import traceback
import json
import tempfile
import random
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Wolf Goat Pig Simulation (will be replaced when game starts)
wgp_simulation = WolfGoatPigSimulation(player_count=4)

# Response model classes for Action API
class ActionRequest(BaseModel):
    """Unified action request for all game interactions"""
    action_type: str  # INITIALIZE_GAME, PLAY_SHOT, REQUEST_PARTNERSHIP, etc.
    payload: Optional[Dict[str, Any]] = None

class ActionResponse(BaseModel):
    """Standard response structure for all actions"""
    game_state: Dict[str, Any]
    log_message: str
    available_actions: List[Dict[str, Any]]
    timeline_event: Optional[Dict[str, Any]] = None

# Course management models
class CourseCreate(BaseModel):
    name: str
    holes: List[Dict[str, Any]]

class CourseUpdate(BaseModel):
    holes: List[Dict[str, Any]]

class CourseImportRequest(BaseModel):
    course_name: str
    state: Optional[str] = None
    city: Optional[str] = None

app = FastAPI(
    title="Wolf Goat Pig Golf Simulation API",
    description="A comprehensive golf betting simulation API with unified Action API",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Trusted host middleware for security
# Temporarily disable TrustedHostMiddleware during development/testing for easier debugging
# if os.getenv("ENVIRONMENT") != "development":
#     app.add_middleware(
#         TrustedHostMiddleware, 
#         allowed_hosts=[
#             "localhost",
#             "127.0.0.1",
#             "wolf-goat-pig-api.onrender.com",
#             "wolf-goat-pig.onrender.com",
#             "wolf-goat-pig-frontend.onrender.com"
#         ]
#     )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") == "development" else [
        "https://wolf-goat-pig-frontend.onrender.com",
        "https://wolf-goat-pig.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions and preserve their status codes"""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    # Add logging for host header during exceptions
    logger.error(f"Request Host header: {request.headers.get('host')}")
    logger.error(f"Request Client host: {request.client.host}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP error", "detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

@app.on_event("startup")
def startup():
    logger.info("Wolf Goat Pig API starting up...")
    logger.info(f"ENVIRONMENT: {os.getenv('ENVIRONMENT')}")

@app.get("/health")
def health_check():
    """Enhanced health check endpoint with database connectivity test"""
    try:
        # Test database connection
        db = database.SessionLocal()
        try:
            # Simple query to test DB connectivity
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "disconnected"
            raise HTTPException(status_code=503, detail="Database unavailable")
        finally:
            db.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": db_status,
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "version": "1.0.0"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/rules", response_model=list[schemas.Rule])
def get_rules():
    """Get Wolf Goat Pig rules"""
    try:
        db = database.SessionLocal()
        rules = crud.get_rules(db)
        return rules
    except Exception as e:
        logger.error(f"Error getting rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rules")
    finally:
        db.close()

# Course Management Endpoints
@app.get("/courses")
def get_courses():
    """Get all available courses"""
    try:
        return game_state.get_courses()
    except Exception as e:
        logger.error(f"Error getting courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to get courses")

@app.post("/courses", response_model=dict)
def add_course(course: CourseCreate):
    """Add a new course"""
    try:
        result = game_state.add_course(course.dict())
        return {"status": "success", "message": f"Course '{course.name}' added successfully", "data": result}
    except Exception as e:
        logger.error(f"Error adding course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add course: {str(e)}")

@app.put("/courses/{course_name}")
def update_course(course_name: str, course_update: CourseUpdate):
    """Update an existing course"""
    try:
        result = game_state.update_course(course_name, course_update.dict())
        return {"status": "success", "message": f"Course '{course_name}' updated successfully", "data": result}
    except Exception as e:
        logger.error(f"Error updating course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update course: {str(e)}")

@app.delete("/courses/{course_name}")
def delete_course(course_name: str = Path(...)):
    """Delete a course"""
    try:
        result = game_state.delete_course(course_name)
        return {"status": "success", "message": f"Course '{course_name}' deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete course: {str(e)}")

# Course Import Endpoints
@app.post("/courses/import/search")
async def import_course_by_search(request: CourseImportRequest):
    """Search and import a course by name"""
    try:
        result = await import_course_by_name(request.course_name, request.state, request.city)
        return result
    except Exception as e:
        logger.error(f"Error importing course by search: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import course: {str(e)}")

@app.post("/courses/import/file")
async def import_course_from_file(file: UploadFile = File(...)):
    """Import a course from uploaded JSON file"""
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be a JSON file")
        
        content = await file.read()
        course_data = json.loads(content.decode('utf-8'))
        
        result = await import_course_from_json(course_data)
        return result
    except Exception as e:
        logger.error(f"Error importing course from file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import course: {str(e)}")

@app.get("/courses/import/sources")
def get_import_sources():
    """Get available course import sources"""
    try:
        return {
            "sources": [
                {
                    "name": "USGA Course Database",
                    "description": "Official USGA course database with ratings and slopes",
                    "endpoint": "/courses/import/search"
                },
                {
                    "name": "JSON File Upload",
                    "description": "Upload custom course data in JSON format",
                    "endpoint": "/courses/import/file"
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error getting import sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to get import sources")

@app.post("/courses/import/preview")
async def preview_course_import(request: CourseImportRequest):
    """Preview course data before importing"""
    try:
        # This would typically search the external database and return preview data
        # For now, return a mock preview
        return {
            "course_name": request.course_name,
            "preview_data": {
                "holes": 18,
                "par": 72,
                "rating": 72.5,
                "slope": 135,
                "sample_holes": [
                    {"hole": 1, "par": 4, "yards": 400, "stroke_index": 7},
                    {"hole": 2, "par": 3, "yards": 175, "stroke_index": 15}
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error previewing course import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview course: {str(e)}")

# GHIN Integration Endpoints
@app.get("/ghin/lookup")
def ghin_lookup(
    last_name: str = Query(..., description="Golfer's last name"),
    first_name: str = Query(None, description="Golfer's first name (optional)"),
    page: int = Query(1),
    per_page: int = Query(10)
):
    """Look up golfers by name using GHIN API"""
    try:
        # Get GHIN credentials from environment
        email = os.getenv("GHIN_API_USER")
        password = os.getenv("GHIN_API_PASS")
        static_token = os.getenv("GHIN_API_STATIC_TOKEN", "ghincom")
        
        if not email or not password:
            return {"error": "GHIN credentials not configured"}
        
        # GHIN API endpoints
        GHIN_AUTH_URL = "https://www.ghin.com/api/v1/authenticate"
        GHIN_SEARCH_URL = "https://www.ghin.com/api/v1/golfer_search"
        
        # Authenticate with GHIN
        auth_data = {
            "user": {
                "email_or_ghin": email,
                "password": password
            },
            "token": static_token,
            "source": "GHINcom"
        }
        
        with httpx.Client() as client:
            auth_response = client.post(GHIN_AUTH_URL, json=auth_data)
            auth_response.raise_for_status()
            
            jwt = auth_response.json()["golfer_user"]["golfer_user_token"]
            
            # Search for golfers
            search_params = {
                "last_name": last_name,
                "page": page,
                "per_page": per_page
            }
            if first_name:
                search_params["first_name"] = first_name
            
            search_response = client.get(
                GHIN_SEARCH_URL,
                headers={"Authorization": f"Bearer {jwt}"},
                params=search_params
            )
            search_response.raise_for_status()
            
            return search_response.json()
            
    except httpx.HTTPStatusError as e:
        logger.error(f"GHIN API error: {e.response.status_code} - {e.response.text}")
        return {"error": f"GHIN API error: {e.response.status_code}"}
    except Exception as e:
        logger.error(f"Error in GHIN lookup: {e}")
        return {"error": f"Failed to lookup golfer: {str(e)}"}

@app.get("/ghin/diagnostic")
def ghin_diagnostic():
    """Diagnostic endpoint for GHIN API configuration"""
    email = os.getenv("GHIN_API_USER")
    password = os.getenv("GHIN_API_PASS")
    static_token = os.getenv("GHIN_API_STATIC_TOKEN")
    
    return {
        "email_configured": bool(email),
        "password_configured": bool(password),
        "static_token_configured": bool(static_token),
        "all_configured": bool(email and password),
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Legacy Game Endpoints (for backward compatibility)
@app.get("/game/state")
def get_game_state():
    """Get current game state (legacy endpoint)"""
    try:
        return game_state.get_state()
    except Exception as e:
        logger.error(f"Error getting game state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game state")

@app.get("/game/tips")
def get_betting_tips():
    """Get betting tips (legacy endpoint)"""
    try:
        return {"tips": [
            "Consider your handicap advantage on this hole",
            "Watch for partnership opportunities",
            "Doubling can be risky but rewarding"
        ]}
    except Exception as e:
        logger.error(f"Error getting betting tips: {e}")
        raise HTTPException(status_code=500, detail="Failed to get betting tips")

@app.get("/game/player_strokes")
def get_player_strokes():
    """Get player stroke information (legacy endpoint)"""
    try:
        state = game_state.get_state()
        players = state.get("players", [])
        return {
            "players": [
                {
                    "name": player.get("name", "Unknown"),
                    "strokes": player.get("strokes", 0),
                    "handicap": player.get("handicap", 0)
                }
                for player in players
            ]
        }
    except Exception as e:
        logger.error(f"Error getting player strokes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get player strokes")

@app.post("/game/action")
def legacy_game_action(action: Dict[str, Any]):
    """Legacy game action endpoint"""
    try:
        action_type = action.get("action")
        if not action_type:
            raise HTTPException(status_code=400, detail="Action type required")
        
        # Convert legacy actions to unified action API
        if action_type == "next_hole":
            return {"status": "success", "message": "Hole advanced"}
        elif action_type == "start_game":
            return {"status": "success", "message": "Game started"}
        else:
            return {"status": "success", "message": f"Action {action_type} completed"}
    except Exception as e:
        logger.error(f"Error in legacy game action: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute action: {str(e)}")

@app.post("/game/start")
def start_game():
    """Start a new game (legacy endpoint)"""
    try:
        return {"status": "success", "message": "Game started"}
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        raise HTTPException(status_code=500, detail="Failed to start game")

@app.post("/game/setup")
def setup_game(setup_data: Dict[str, Any]):
    """Setup game with players (legacy endpoint)"""
    try:
        players = setup_data.get("players", [])
        course_name = setup_data.get("course_name", "Wing Point Golf & Country Club")
        
        # Use the unified action API internally
        action_request = ActionRequest(
            action_type="INITIALIZE_GAME",
            payload={"players": players, "course_name": course_name}
        )
        
        # This would need to be called in an async context
        # For now, just return success
        return {"status": "success", "message": "Game setup completed"}
    except Exception as e:
        logger.error(f"Error setting up game: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup game")

# Unified Action API - Main Game Logic Endpoint
@app.post("/wgp/{game_id}/action", response_model=ActionResponse)
async def unified_action(game_id: str, action: ActionRequest):
    """Unified action endpoint for all Wolf Goat Pig game interactions"""
    try:
        action_type = action.action_type
        payload = action.payload or {}
        
        # Route to appropriate handler based on action type
        if action_type == "INITIALIZE_GAME":
            return await handle_initialize_game(payload)
        elif action_type == "PLAY_SHOT":
            return await handle_play_shot(payload)
        elif action_type == "REQUEST_PARTNERSHIP":
            return await handle_request_partnership(payload)
        elif action_type == "RESPOND_PARTNERSHIP":
            return await handle_respond_partnership(payload)
        elif action_type == "DECLARE_SOLO":
            return await handle_declare_solo()
        elif action_type == "OFFER_DOUBLE":
            return await handle_offer_double(payload)
        elif action_type == "ACCEPT_DOUBLE":
            return await handle_accept_double(payload)
        elif action_type == "CONCEDE_PUTT":
            return await handle_concede_putt(payload)
        elif action_type == "ADVANCE_HOLE":
            return await handle_advance_hole()
        elif action_type == "OFFER_BIG_DICK":
            return await handle_offer_big_dick(payload)
        elif action_type == "ACCEPT_BIG_DICK":
            return await handle_accept_big_dick(payload)
        elif action_type == "AARDVARK_JOIN_REQUEST":
            return await handle_aardvark_join_request(payload)
        elif action_type == "AARDVARK_TOSS":
            return await handle_aardvark_toss(payload)
        elif action_type == "AARDVARK_GO_SOLO":
            return await handle_aardvark_go_solo(payload)
        elif action_type == "PING_PONG_AARDVARK":
            return await handle_ping_pong_aardvark(payload)
        elif action_type == "INVOKE_JOES_SPECIAL":
            return await handle_joes_special(payload)
        elif action_type == "GET_POST_HOLE_ANALYSIS":
            return await handle_get_post_hole_analysis(payload)
        elif action_type == "ENTER_HOLE_SCORES":
            return await handle_enter_hole_scores(payload)
        elif action_type == "GET_ADVANCED_ANALYTICS":
            return await handle_get_advanced_analytics(payload)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")
            
    except HTTPException:
        # Re-raise HTTPExceptions to preserve their status codes
        raise
    except Exception as e:
        logger.error(f"Error in unified action: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")

# Action Handlers
async def handle_initialize_game(payload: Dict[str, Any]) -> ActionResponse:
    """Handle game initialization"""
    try:
        players = payload.get("players", [])
        course_name = payload.get("course_name", "Wing Point Golf & Country Club")
        
        # Validate player count (support 4, 5, 6 players)
        if len(players) not in [4, 5, 6]:
            raise HTTPException(status_code=400, detail="4, 5, or 6 players required.")
        
        # Ensure all players have required fields
        for i, player in enumerate(players):
            if "name" not in player or "handicap" not in player:
                raise HTTPException(status_code=400, detail="Each player must have id, name, handicap, and strength.")
            
            # Add missing fields if not present
            if "id" not in player:
                player["id"] = f"p{i+1}"
            if "strength" not in player:
                # Default strength based on handicap (lower handicap = higher strength)
                player["strength"] = max(1, 10 - int(player["handicap"]))
        
        # Initialize game state with players
        game_state.setup_players(players, course_name)
        
        # Initialize WGP simulation with the players
        # Create WGPPlayer objects
        wgp_players = []
        for player in players:
            wgp_players.append(WGPPlayer(
                id=player["id"],
                name=player["name"],
                handicap=player["handicap"]
            ))
        
        # Initialize the simulation with these players
        wgp_simulation.__init__(player_count=len(wgp_players), players=wgp_players)
        
        # Set computer players (all except first)
        computer_player_ids = [p["id"] for p in players[1:]]
        wgp_simulation.set_computer_players(computer_player_ids)
        
        # Initialize the first hole
        wgp_simulation._initialize_hole(1)
        
        # Enable shot progression and timeline tracking
        wgp_simulation.enable_shot_progression()
        
        # Add initial timeline event
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            wgp_simulation.hole_progression.add_timeline_event(
                event_type="game_start",
                description=f"Game started with {len(players)} players on {course_name}",
                details={"players": players, "course": course_name}
            )
        
        # Get initial game state
        current_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=current_state,
            log_message=f"Game initialized with {len(players)} players on {course_name}",
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Start first hole", "player_turn": players[0]["name"]}
            ],
            timeline_event={
                "id": "init_1",
                "timestamp": datetime.now().isoformat(),
                "type": "game_start",
                "description": f"Game started with {len(players)} players",
                "details": {"players": players, "course": course_name}
            }
        )
    except Exception as e:
        logger.error(f"Error initializing game: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize game: {str(e)}")

async def handle_play_shot(payload: Dict[str, Any] = None) -> ActionResponse:
    """Handle playing a shot"""
    try:
        # Get current game state
        current_state = wgp_simulation.get_game_state()
        
        # Determine next player to hit
        next_player = wgp_simulation._get_next_shot_player()
        if not next_player:
            return ActionResponse(
                game_state=current_state,
                log_message="No players available to hit",
                available_actions=[],
                timeline_event={
                    "id": f"shot_{datetime.now().timestamp()}",
                    "timestamp": datetime.now().isoformat(),
                    "type": "shot",
                    "description": "No players available to hit",
                    "player_name": None
                }
            )
        
        # Simulate the shot
        shot_response = wgp_simulation.simulate_shot(next_player)
        shot_result = shot_response.get("shot_result", {})
        
        # Update game state  
        updated_state = wgp_simulation.get_game_state()
        hole_state = wgp_simulation.hole_states[wgp_simulation.current_hole]
        
        # Check if this was a tee shot and update invitation windows
        is_tee_shot = next_player not in hole_state.ball_positions or hole_state.ball_positions[next_player].shot_count == 1
        if is_tee_shot:
            # Create a WGPShotResult object from the shot_result dictionary
            from app.wolf_goat_pig_simulation import WGPShotResult
            shot_obj = WGPShotResult(
                player_id=shot_result.get("player_id", next_player),
                shot_number=shot_result.get("shot_number", 1),
                lie_type=shot_result.get("lie_type", "fairway"),
                distance_to_pin=shot_result.get("distance_to_pin", 0.0),
                shot_quality=shot_result.get("shot_quality", "average"),
                made_shot=shot_result.get("made_shot", False),
                penalty_strokes=shot_result.get("penalty_strokes", 0)
            )
            hole_state.process_tee_shot(next_player, shot_obj)
        
        # Determine next available actions based on shot progression and partnership timing
        available_actions = []
        
        if shot_response.get("hole_complete"):
            # Hole is complete - offer scoring options
            available_actions.append({"action_type": "ENTER_HOLE_SCORES", "prompt": "Enter hole scores"})
        elif hole_state.teams.type == "pending":
            # Teams not formed yet - check partnership opportunities
            captain_id = hole_state.teams.captain
            captain_name = wgp_simulation._get_player_name(captain_id)
            
            # Get available partners based on timing rules
            available_partners = []
            for player in wgp_simulation.players:
                if player.id != captain_id and hole_state.can_request_partnership(captain_id, player.id):
                    available_partners.append({
                        "id": player.id,
                        "name": player.name,
                        "handicap": player.handicap
                    })
            
            if available_partners:
                # Add partnership actions for captain with available partners
                for partner in available_partners:
                    available_actions.append({
                        "action_type": "REQUEST_PARTNERSHIP",
                        "prompt": f"Request {partner['name']} as partner",
                        "payload": {"target_player_name": partner['name']},
                        "player_turn": captain_name,
                        "context": f"Choose a partner for this hole. {partner['name']} has a {partner['handicap']} handicap."
                    })
                
                # Add solo option
                available_actions.append({
                    "action_type": "DECLARE_SOLO", 
                    "prompt": "Go solo (1v3)",
                    "player_turn": captain_name,
                    "context": "Play alone against all three opponents. High risk, high reward!"
                })
            else:
                # Partnership deadline has passed - captain must go solo
                available_actions.append({
                    "action_type": "DECLARE_SOLO", 
                    "prompt": "Go solo (deadline passed)",
                    "player_turn": captain_name,
                    "context": "Partnership deadline has passed. Must play solo."
                })
        else:
            # Continue with shot progression
            next_shot_player = wgp_simulation._get_next_shot_player()
            if next_shot_player:
                next_shot_player_name = wgp_simulation._get_player_name(next_shot_player)
                
                # Determine shot type for better UX
                current_ball = hole_state.get_player_ball_position(next_shot_player)
                shot_type = "tee shot" if not current_ball else f"shot #{current_ball.shot_count + 1}"
                
                available_actions.append({
                    "action_type": "PLAY_SHOT", 
                    "prompt": f"{next_shot_player_name} hits {shot_type}", 
                    "player_turn": next_shot_player_name,
                    "context": f"Continue hole progression with {next_shot_player_name}'s {shot_type}"
                })
            elif not hole_state.hole_complete:
                # All players have played but hole not complete - might need scoring
                available_actions.append({
                    "action_type": "ENTER_HOLE_SCORES", 
                    "prompt": "Enter final scores for hole"
                })
            
            # Check for betting opportunities (line of scrimmage and approach shots)
            if not hole_state.wagering_closed:
                # Get approach shot betting opportunities
                betting_opportunities = hole_state.get_approach_shot_betting_opportunities()
                
                # Only offer doubles if there are strategic opportunities and not already doubled
                if betting_opportunities and not hole_state.betting.doubled:
                    # Find players who can offer doubles (not past line of scrimmage)
                    for player in wgp_simulation.players:
                        if hole_state.can_offer_double(player.id):
                            # Add context about why this is a good time to bet
                            context_info = []
                            for opp in betting_opportunities:
                                if opp.get("strategic_value") == "high":
                                    context_info.append(f"🔥 {opp['description']}")
                                else:
                                    context_info.append(f"⚡ {opp['description']}")
                            
                            context = f"Double the wager from {hole_state.betting.current_wager} to {hole_state.betting.current_wager * 2} quarters. " + " ".join(context_info)
                            
                            available_actions.append({
                                "action_type": "OFFER_DOUBLE",
                                "prompt": f"{player.name} offers to double the wager",
                                "payload": {"player_id": player.id},
                                "player_turn": player.name,
                                "context": context
                            })
        
        # Create timeline event from shot response
        player_name = wgp_simulation._get_player_name(next_player)
        shot_description = f"{player_name} hits a {shot_result.get('shot_quality', 'average')} shot"
        if shot_result.get('made_shot'):
            shot_description += " and holes out!"
        else:
            shot_description += f" - {shot_result.get('distance_to_pin', 0):.0f} yards to pin"
        
        timeline_event = {
            "id": f"shot_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "type": "shot",
            "description": shot_description,
            "player_name": player_name,
            "details": shot_result
        }
        
        return ActionResponse(
            game_state=updated_state,
            log_message=shot_description,
            available_actions=available_actions,
            timeline_event=timeline_event
        )
    except Exception as e:
        logger.error(f"Error playing shot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to play shot: {str(e)}")

async def handle_request_partnership(payload: Dict[str, Any]) -> ActionResponse:
    """Handle partnership request"""
    try:
        target_player = payload.get("target_player_name")
        if not target_player:
            raise HTTPException(status_code=400, detail="target_player_name is required")
        
        # Get current game state
        current_state = wgp_simulation.get_game_state()
        
        # Get the actual captain ID from the current hole state
        hole_state = wgp_simulation.hole_states[wgp_simulation.current_hole]
        captain_id = hole_state.teams.captain
        
        # Convert player name to player ID
        partner_id = None
        for player in wgp_simulation.players:
            if player.name == target_player:
                partner_id = player.id
                break
        
        if not partner_id:
            raise HTTPException(status_code=400, detail=f"Player '{target_player}' not found")
        
        # Request the partnership
        result = wgp_simulation.request_partner(captain_id, partner_id)
        
        # Get updated game state
        updated_state = wgp_simulation.get_game_state()
        
        # Determine next available actions
        available_actions = []
        
        # If partnership was requested, the target player needs to respond
        if result.get("partnership_requested"):
            captain_name = wgp_simulation._get_player_name(captain_id)
            partner_name = target_player
            
            available_actions.append({
                "action_type": "RESPOND_PARTNERSHIP",
                "prompt": f"Accept partnership with {captain_name}",
                "payload": {"accepted": True},
                "player_turn": partner_name,
                "context": f"{captain_name} has requested you as a partner"
            })
            
            available_actions.append({
                "action_type": "RESPOND_PARTNERSHIP", 
                "prompt": f"Decline partnership with {captain_name}",
                "payload": {"accepted": False},
                "player_turn": partner_name,
                "context": f"{captain_name} has requested you as a partner"
            })
        
        return ActionResponse(
            game_state=updated_state,
            log_message=result.get("message", f"Partnership requested with {target_player}"),
            available_actions=available_actions,
            timeline_event={
                "id": f"partnership_request_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "partnership_request",
                "description": f"Partnership requested with {target_player}",
                "player_name": wgp_simulation._get_player_name(captain_id),
                "details": {
                    "captain": wgp_simulation._get_player_name(captain_id),
                    "requested_partner": target_player,
                    "status": "pending_response"
                }
            }
        )
    except Exception as e:
        logger.error(f"Error requesting partnership: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to request partnership: {str(e)}")

async def handle_respond_partnership(payload: Dict[str, Any]) -> ActionResponse:
    """Handle partnership response"""
    try:
        accepted = payload.get("accepted", False)
        
        # Get current game state
        current_state = wgp_simulation.get_game_state()
        
        # Get the partner ID from the pending request
        hole_state = wgp_simulation.hole_states[wgp_simulation.current_hole]
        partner_id = hole_state.teams.pending_request.get("requested") if hole_state.teams.pending_request else None
        
        if not partner_id:
            raise HTTPException(status_code=400, detail="No pending partnership request")
        
        # Respond to partnership
        if accepted:
            result = wgp_simulation.respond_to_partnership(partner_id, True)
            message = "Partnership accepted! Teams are formed."
        else:
            result = wgp_simulation.respond_to_partnership(partner_id, False)
            message = "Partnership declined. Captain goes solo."
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            wgp_simulation.hole_progression.add_timeline_event(
                event_type="partnership_response",
                description=f"Partnership {'accepted' if accepted else 'declined'}",
                player_name="Partner",
                details={"accepted": accepted}
            )
        
        # Update game state
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=message,
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}
            ],
            timeline_event={
                "id": f"partnership_response_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "partnership_response",
                "description": f"Partnership {'accepted' if accepted else 'declined'}",
                "player_name": "Partner",
                "details": {"accepted": accepted}
            }
        )
    except Exception as e:
        logger.error(f"Error responding to partnership: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to respond to partnership: {str(e)}")

async def handle_declare_solo() -> ActionResponse:
    """Handle captain going solo"""
    try:
        # Get current game state
        current_state = wgp_simulation.get_game_state()
        
        # Get the actual captain ID from the current hole state
        hole_state = wgp_simulation.hole_states.get(wgp_simulation.current_hole)
        if not hole_state or not hole_state.teams.captain:
            raise HTTPException(status_code=400, detail="No captain found for current hole")
        
        captain_id = hole_state.teams.captain
        
        # Captain goes solo
        result = wgp_simulation.captain_go_solo(captain_id)
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            wgp_simulation.hole_progression.add_timeline_event(
                event_type="partnership_decision",
                description="Captain goes solo - 1 vs 3",
                player_name="Captain",
                details={"solo": True}
            )
        
        # Update game state
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message="Captain declares solo! It's 1 vs 3.",
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}
            ],
            timeline_event={
                "id": f"solo_declaration_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "partnership_decision",
                "description": "Captain goes solo - 1 vs 3",
                "player_name": "Captain",
                "details": {"solo": True}
            }
        )
    except Exception as e:
        logger.error(f"Error declaring solo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to declare solo: {str(e)}")

async def handle_offer_double(payload: Dict[str, Any]) -> ActionResponse:
    """Handle double offer"""
    try:
        player_id = payload.get("player_id")
        if not player_id:
            raise ValueError("Player ID required for double offer")
        
        # Get current game state
        current_state = wgp_simulation.get_game_state()
        
        # Offer double
        result = wgp_simulation.offer_double(player_id)
        
        player_name = wgp_simulation._get_player_name(player_id)
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            wgp_simulation.hole_progression.add_timeline_event(
                event_type="double_offer",
                description=f"{player_name} offered to double the wager",
                player_name=player_name,
                details={"double_offered": True, "player_id": player_id}
            )
        
        # Update game state
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message="Double offered! Wager increases.",
            available_actions=[
                {"action_type": "ACCEPT_DOUBLE", "prompt": "Accept/Decline double"}
            ],
            timeline_event={
                "id": f"double_offer_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "double_offer",
                "description": f"{player_name} offered to double the wager",
                "player_name": player_name,
                "details": {"double_offered": True, "player_id": player_id}
            }
        )
    except Exception as e:
        logger.error(f"Error offering double: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to offer double: {str(e)}")

async def handle_accept_double(payload: Dict[str, Any]) -> ActionResponse:
    """Handle double acceptance/decline"""
    try:
        accepted = payload.get("accepted", False)
        
        # Get current game state
        current_state = wgp_simulation.get_game_state()
        
        # Respond to double
        if accepted:
            result = wgp_simulation.respond_to_double("responding_team", True)
            message = "Double accepted! Wager doubled."
        else:
            result = wgp_simulation.respond_to_double("responding_team", False)
            message = "Double declined. Original wager maintained."
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            wgp_simulation.hole_progression.add_timeline_event(
                event_type="double_response",
                description=f"Double {'accepted' if accepted else 'declined'}",
                player_name="Responding Team",
                details={"accepted": accepted}
            )
        
        # Update game state
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=message,
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}
            ],
            timeline_event={
                "id": f"double_response_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "double_response",
                "description": f"Double {'accepted' if accepted else 'declined'}",
                "player_name": "Responding Team",
                "details": {"accepted": accepted}
            }
        )
    except Exception as e:
        logger.error(f"Error responding to double: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to respond to double: {str(e)}")

async def handle_concede_putt(payload: Dict[str, Any]) -> ActionResponse:
    """Handle putt concession"""
    try:
        conceding_player = payload.get("conceding_player")
        conceded_player = payload.get("conceded_player")
        
        if not conceding_player or not conceded_player:
            raise HTTPException(status_code=400, detail="conceding_player and conceded_player are required")
        
        # Get current game state
        current_state = wgp_simulation.get_game_state()
        
        # Update game state to reflect concession
        # This would typically update the hole state to mark the putt as conceded
        
        return ActionResponse(
            game_state=current_state,
            log_message=f"{conceding_player} concedes putt to {conceded_player}",
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}
            ],
            timeline_event={
                "id": f"concession_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "concession",
                "description": f"Putt conceded to {conceded_player}",
                "player_name": conceding_player,
                "details": {"conceded_to": conceded_player}
            }
        )
    except Exception as e:
        logger.error(f"Error conceding putt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to concede putt: {str(e)}")

async def handle_advance_hole() -> ActionResponse:
    """Handle advancing to the next hole"""
    try:
        # Advance to next hole
        result = wgp_simulation.advance_to_next_hole()
        
        # Get updated game state
        current_state = wgp_simulation.get_game_state()
        
        # Add timeline event for hole advancement
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            wgp_simulation.hole_progression.add_timeline_event(
                event_type="hole_start",
                description=f"Started hole {wgp_simulation.current_hole}",
                details={"hole_number": wgp_simulation.current_hole}
            )
        
        # Enable shot progression for the new hole
        wgp_simulation.enable_shot_progression()
        
        # Get the next player to hit
        next_player = wgp_simulation._get_next_shot_player()
        next_player_name = wgp_simulation._get_player_name(next_player) if next_player else "Unknown"
        
        return ActionResponse(
            game_state=current_state,
            log_message=f"Advanced to hole {wgp_simulation.current_hole}",
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": f"Start hole {wgp_simulation.current_hole}", "player_turn": next_player_name}
            ],
            timeline_event={
                "id": f"hole_start_{wgp_simulation.current_hole}",
                "timestamp": datetime.now().isoformat(),
                "type": "hole_start",
                "description": f"Started hole {wgp_simulation.current_hole}",
                "details": {"hole_number": wgp_simulation.current_hole}
            }
        )
    except Exception as e:
        logger.error(f"Error advancing hole: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to advance hole: {str(e)}")

async def handle_offer_big_dick(payload: Dict[str, Any]) -> ActionResponse:
    """Handle Big Dick challenge on hole 18"""
    try:
        player_id = payload.get("player_id", "default_player")
        
        result = wgp_simulation.offer_big_dick(player_id)
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[
                {"action_type": "ACCEPT_BIG_DICK", "prompt": "Accept/Decline Big Dick challenge"}
            ],
            timeline_event={
                "id": f"big_dick_offer_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "big_dick_offer",
                "description": result["message"],
                "player_name": result["challenger_name"],
                "details": {"wager_amount": result["wager_amount"]}
            }
        )
    except Exception as e:
        logger.error(f"Error offering Big Dick: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to offer Big Dick: {str(e)}")

async def handle_accept_big_dick(payload: Dict[str, Any]) -> ActionResponse:
    """Handle Big Dick challenge response"""
    try:
        accepting_players = payload.get("accepting_players", [])
        
        result = wgp_simulation.accept_big_dick(accepting_players)
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}
            ],
            timeline_event={
                "id": f"big_dick_response_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "big_dick_response",
                "description": result["message"],
                "details": result
            }
        )
    except Exception as e:
        logger.error(f"Error accepting Big Dick: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to accept Big Dick: {str(e)}")

async def handle_ping_pong_aardvark(payload: Dict[str, Any]) -> ActionResponse:
    """Handle Ping Pong Aardvark"""
    try:
        team_id = payload.get("team_id", "team1")
        aardvark_id = payload.get("aardvark_id", "default_aardvark")
        
        result = wgp_simulation.ping_pong_aardvark(team_id, aardvark_id)
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}
            ],
            timeline_event={
                "id": f"ping_pong_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "ping_pong_aardvark",
                "description": result["message"],
                "details": {
                    "new_wager": result["new_wager"],
                    "ping_pong_count": result.get("ping_pong_count", 0)
                }
            }
        )
    except Exception as e:
        logger.error(f"Error ping ponging Aardvark: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ping pong Aardvark: {str(e)}")

async def handle_aardvark_join_request(payload: Dict[str, Any]) -> ActionResponse:
    """Handle Aardvark requesting to join a team"""
    try:
        aardvark_id = payload.get("aardvark_id")
        target_team = payload.get("target_team", "team1")
        
        if not aardvark_id:
            raise HTTPException(status_code=400, detail="aardvark_id is required")
        
        result = wgp_simulation.aardvark_request_team(aardvark_id, target_team)
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[
                {"action_type": "AARDVARK_TOSS", "prompt": f"Accept or toss {result['aardvark_name']}"}
            ],
            timeline_event={
                "id": f"aardvark_request_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "aardvark_request",
                "description": result["message"],
                "details": {
                    "aardvark_id": aardvark_id,
                    "target_team": target_team
                }
            }
        )
    except Exception as e:
        logger.error(f"Error handling Aardvark join request: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to handle Aardvark join request: {str(e)}")

async def handle_aardvark_toss(payload: Dict[str, Any]) -> ActionResponse:
    """Handle team response to Aardvark request (accept or toss)"""
    try:
        team_id = payload.get("team_id", "team1")
        accept = payload.get("accept", False)
        
        result = wgp_simulation.respond_to_aardvark(team_id, accept)
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}
            ],
            timeline_event={
                "id": f"aardvark_toss_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "aardvark_toss",
                "description": result["message"],
                "details": {
                    "team_id": team_id,
                    "accepted": accept,
                    "status": result["status"]
                }
            }
        )
    except Exception as e:
        logger.error(f"Error handling Aardvark toss: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to handle Aardvark toss: {str(e)}")

async def handle_aardvark_go_solo(payload: Dict[str, Any]) -> ActionResponse:
    """Handle Aardvark deciding to go solo"""
    try:
        aardvark_id = payload.get("aardvark_id")
        use_tunkarri = payload.get("use_tunkarri", False)
        
        if not aardvark_id:
            raise HTTPException(status_code=400, detail="aardvark_id is required")
        
        result = wgp_simulation.aardvark_go_solo(aardvark_id, use_tunkarri)
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=result["message"],
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}
            ],
            timeline_event={
                "id": f"aardvark_solo_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "aardvark_solo",
                "description": result["message"],
                "details": {
                    "aardvark_id": aardvark_id,
                    "use_tunkarri": use_tunkarri,
                    "status": result["status"]
                }
            }
        )
    except Exception as e:
        logger.error(f"Error handling Aardvark go solo: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to handle Aardvark go solo: {str(e)}")

async def handle_joes_special(payload: Dict[str, Any]) -> ActionResponse:
    """Handle Joe's Special wager selection in Hoepfinger"""
    try:
        selected_value = payload.get("selected_value", 2)
        
        # Apply Joe's Special value to current hole betting
        hole_state = wgp_simulation.hole_states[wgp_simulation.current_hole]
        hole_state.betting.joes_special_value = selected_value
        hole_state.betting.base_wager = selected_value
        hole_state.betting.current_wager = selected_value
        
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=f"Joe's Special invoked! Hole starts at {selected_value} quarters.",
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue with hole"}
            ],
            timeline_event={
                "id": f"joes_special_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "joes_special",
                "description": f"Joe's Special: Hole value set to {selected_value} quarters",
                "details": {"selected_value": selected_value}
            }
        )
    except Exception as e:
        logger.error(f"Error invoking Joe's Special: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invoke Joe's Special: {str(e)}")

async def handle_get_post_hole_analysis(payload: Dict[str, Any]) -> ActionResponse:
    """Handle post-hole analysis request"""
    try:
        hole_number = payload.get("hole_number", wgp_simulation.current_hole)
        
        analysis = wgp_simulation.get_post_hole_analysis(hole_number)
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=f"Post-hole analysis generated for hole {hole_number}",
            available_actions=[
                {"action_type": "ADVANCE_HOLE", "prompt": "Continue to next hole"}
            ],
            timeline_event={
                "id": f"post_hole_analysis_{hole_number}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "post_hole_analysis",
                "description": f"Comprehensive analysis of hole {hole_number}",
                "details": analysis
            }
        )
    except Exception as e:
        logger.error(f"Error getting post-hole analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get post-hole analysis: {str(e)}")

async def handle_enter_hole_scores(payload: Dict[str, Any]) -> ActionResponse:
    """Handle entering hole scores"""
    try:
        scores = payload.get("scores", {})
        
        result = wgp_simulation.enter_hole_scores(scores)
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=result.get("message", "Hole scores entered and points calculated"),
            available_actions=[
                {"action_type": "GET_POST_HOLE_ANALYSIS", "prompt": "View Hole Analysis"},
                {"action_type": "ADVANCE_HOLE", "prompt": "Continue to Next Hole"}
            ],
            timeline_event={
                "id": f"scores_entered_{wgp_simulation.current_hole}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "scores_entered",
                "description": f"Scores entered for hole {wgp_simulation.current_hole}",
                "details": {
                    "scores": scores,
                    "points_result": result
                }
            }
        )
    except Exception as e:
        logger.error(f"Error entering hole scores: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enter hole scores: {str(e)}")

async def handle_get_advanced_analytics(payload: Dict[str, Any]) -> ActionResponse:
    """Handle getting advanced analytics dashboard data"""
    try:
        analytics = wgp_simulation.get_advanced_analytics()
        updated_state = wgp_simulation.get_game_state()
        
        # Include analytics data in the updated game state
        updated_state["analytics"] = analytics
        
        return ActionResponse(
            game_state=updated_state,
            log_message="Advanced analytics data retrieved",
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": "Continue Game"},
                {"action_type": "GET_ADVANCED_ANALYTICS", "prompt": "Refresh Analytics"}
            ],
            timeline_event={
                "id": f"analytics_viewed_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "analytics_viewed",
                "description": "Advanced analytics dashboard accessed",
                "details": analytics  # Include full analytics data here
            }
        )
    except Exception as e:
        logger.error(f"Error getting advanced analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get advanced analytics: {str(e)}")

# Helper function to serialize game state
def _serialize_game_state():
    """Convert game state to serializable format"""
    try:
        # Get the current game state from the WGP simulation
        state = wgp_simulation.get_game_state()
        return state
    except Exception as e:
        logger.error(f"Error serializing game state: {e}")
        return {}


# Shot Range Analysis Endpoint
class ShotRangeAnalysisRequest(BaseModel):
    """Request model for shot range analysis"""
    lie_type: str = Field(..., description="Current lie (fairway, rough, bunker, etc)")
    distance_to_pin: float = Field(..., description="Distance to pin in yards")
    player_handicap: float = Field(..., description="Player's handicap")
    hole_number: int = Field(..., description="Current hole number")
    team_situation: str = Field(default="solo", description="Team situation (solo, partners)")
    score_differential: int = Field(default=0, description="Current score differential")
    opponent_styles: List[str] = Field(default=[], description="Opponent playing styles")


@app.post("/wgp/shot-range-analysis")
async def get_shot_range_analysis(request: ShotRangeAnalysisRequest):
    """Get poker-style shot range analysis for decision making"""
    try:
        # Perform shot range analysis
        analysis = analyze_shot_decision(
            current_lie=request.lie_type,
            distance=request.distance_to_pin,
            player_handicap=request.player_handicap,
            hole_number=request.hole_number,
            team_situation=request.team_situation,
            score_differential=request.score_differential,
            opponent_styles=request.opponent_styles
        )
        
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in shot range analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze shot range: {str(e)}")


