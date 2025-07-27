from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path, Query, UploadFile, File
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

# Initialize Wolf Goat Pig Simulation
wgp_simulation = WolfGoatPigSimulation()

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
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"] if os.getenv("ENVIRONMENT") == "development" else [
        "localhost",
        "127.0.0.1",
        "wolf-goat-pig.onrender.com",
        "wolf-goat-pig-frontend.onrender.com"
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") == "development" else [
        "https://wolf-goat-pig-frontend.onrender.com",
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

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
    """Look up golfer information from GHIN database"""
    try:
        # GHIN API credentials from environment
        ghin_user = os.getenv("GHIN_API_USER")
        ghin_pass = os.getenv("GHIN_API_PASS")
        ghin_token = os.getenv("GHIN_API_STATIC_TOKEN", "ghincom")
        
        if not ghin_user or not ghin_pass:
            return {
                "error": "GHIN API credentials not configured",
                "message": "Please set GHIN_API_USER and GHIN_API_PASS environment variables"
            }
        
        # GHIN API endpoints
        auth_url = "https://www.ghin.com/api/v1/authenticate"
        search_url = "https://www.ghin.com/api/v1/golfer_search"
        
        # Authenticate with GHIN
        auth_data = {
            "user": {
                "email_or_ghin": ghin_user,
                "password": ghin_pass
            },
            "token": ghin_token,
            "source": "GHINcom"
        }
        
        with httpx.Client() as client:
            auth_response = client.post(auth_url, json=auth_data)
            if auth_response.status_code != 200:
                return {
                    "error": "GHIN authentication failed",
                    "status_code": auth_response.status_code
                }
            
            auth_json = auth_response.json()
            jwt_token = auth_json.get("golfer_user", {}).get("golfer_user_token")
            
            if not jwt_token:
                return {
                    "error": "No JWT token received from GHIN"
                }
            
            # Search for golfer
            search_params = {
                "last_name": last_name,
                "page": page,
                "per_page": per_page
            }
            if first_name:
                search_params["first_name"] = first_name
            
            headers = {"Authorization": f"Bearer {jwt_token}"}
            search_response = client.get(search_url, headers=headers, params=search_params)
            
            if search_response.status_code != 200:
                return {
                    "error": "GHIN search failed",
                    "status_code": search_response.status_code
                }
            
            search_data = search_response.json()
            return {
                "status": "success",
                "data": search_data,
                "search_params": search_params
            }
            
    except Exception as e:
        logger.error(f"Error in GHIN lookup: {e}")
        return {
            "error": "GHIN lookup failed",
            "detail": str(e)
        }

@app.get("/ghin/diagnostic")
def ghin_diagnostic():
    """Diagnostic endpoint for GHIN API configuration"""
    try:
        ghin_user = os.getenv("GHIN_API_USER")
        ghin_pass = os.getenv("GHIN_API_PASS")
        ghin_token = os.getenv("GHIN_API_STATIC_TOKEN", "ghincom")
        
        return {
            "ghin_configured": bool(ghin_user and ghin_pass),
            "ghin_user_set": bool(ghin_user),
            "ghin_pass_set": bool(ghin_pass),
            "ghin_token": ghin_token,
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        logger.error(f"Error in GHIN diagnostic: {e}")
        return {
            "error": "GHIN diagnostic failed",
            "detail": str(e)
        }

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
            return await handle_play_shot()
        elif action_type == "REQUEST_PARTNERSHIP":
            return await handle_request_partnership(payload)
        elif action_type == "RESPOND_PARTNERSHIP":
            return await handle_respond_partnership(payload)
        elif action_type == "DECLARE_SOLO":
            return await handle_declare_solo()
        elif action_type == "OFFER_DOUBLE":
            return await handle_offer_double()
        elif action_type == "ACCEPT_DOUBLE":
            return await handle_accept_double(payload)
        elif action_type == "CONCEDE_PUTT":
            return await handle_concede_putt(payload)
        elif action_type == "ADVANCE_HOLE":
            return await handle_advance_hole()
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
        course_name = payload.get("course_name", "Wing Point")
        
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

async def handle_play_shot() -> ActionResponse:
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
        shot_result = wgp_simulation.simulate_shot(next_player)
        
        # Get timeline events from the simulation
        timeline_events = []
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            timeline_events = wgp_simulation.hole_progression.get_timeline_events()
        
        # Update game state
        updated_state = wgp_simulation.get_game_state()
        
        # Determine next available actions
        available_actions = []
        if shot_result.get("hole_complete"):
            available_actions.append({"action_type": "OFFER_DOUBLE", "prompt": "Offer double"})
        else:
            # Check if all tee shots have been completed
            hole_state = wgp_simulation.hole_states[wgp_simulation.current_hole]
            all_tee_shots_complete = all(
                player_id in hole_state.ball_positions 
                for player_id in hole_state.hitting_order
            )
            

            
            if all_tee_shots_complete and hole_state.teams.type == "pending":
                # All tee shots complete, captain can make partnership decisions
                captain_id = hole_state.teams.captain
                captain_name = wgp_simulation._get_player_name(captain_id)
                
                # Add partnership actions for captain
                available_actions.extend([
                    {"action_type": "REQUEST_PARTNERSHIP", "prompt": "Request partner", "captain": captain_name},
                    {"action_type": "DECLARE_SOLO", "prompt": "Go solo", "captain": captain_name}
                ])
            else:
                # Continue with shot progression
                next_player = wgp_simulation._get_next_shot_player()
                if next_player:
                    available_actions.append({"action_type": "PLAY_SHOT", "prompt": "Next shot", "player_turn": next_player})
        
        # Get the latest timeline event if available
        latest_event = None
        if timeline_events:
            latest_event = timeline_events[-1]
        
        return ActionResponse(
            game_state=updated_state,
            log_message=shot_result.get("message", f"{next_player} takes a shot"),
            available_actions=available_actions,
            timeline_event=latest_event or {
                "id": f"shot_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "shot",
                "description": shot_result.get("shot_description", f"{next_player} hits the ball"),
                "player_name": next_player,
                "details": shot_result
            }
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
        
        # Make partnership request
        result = wgp_simulation.request_partner(captain_id, partner_id)
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            wgp_simulation.hole_progression.add_timeline_event(
                event_type="partnership_request",
                description=f"Partnership requested with {target_player}",
                player_name="Captain",
                details={"target_player": target_player}
            )
        
        # Update game state
        updated_state = wgp_simulation.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=f"Partnership requested with {target_player}",
            available_actions=[
                {"action_type": "RESPOND_PARTNERSHIP", "prompt": f"Accept/Decline partnership with {target_player}"}
            ],
            timeline_event={
                "id": f"partnership_request_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "partnership_request",
                "description": f"Partnership requested with {target_player}",
                "player_name": "Captain",
                "details": {"target_player": target_player}
            }
        )
    except HTTPException:
        # Re-raise HTTPExceptions to preserve their status codes
        raise
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

async def handle_offer_double() -> ActionResponse:
    """Handle double offer"""
    try:
        # Get current game state
        current_state = wgp_simulation.get_game_state()
        
        # Offer double
        result = wgp_simulation.offer_double("offering_player_id")
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            wgp_simulation.hole_progression.add_timeline_event(
                event_type="double_offer",
                description="Double offered - wager increases",
                player_name="Offering Player",
                details={"double_offered": True}
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
                "description": "Double offered - wager increases",
                "player_name": "Offering Player",
                "details": {"double_offered": True}
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


