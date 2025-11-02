from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path, Query, UploadFile, File, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from . import models, schemas, crud, database

from .game_state import game_state
from .wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer, BallPosition, TeamFormation
from .post_hole_analytics import PostHoleAnalyzer
from .simulation_timeline_enhancements import (
    enhance_simulation_with_timeline, 
    format_poker_betting_state, 
    create_betting_options
)
from .course_import import CourseImporter, import_course_by_name, import_course_from_json, save_course_to_database
from .domain.shot_result import ShotResult
from .domain.player import Player
from .domain.shot_range_analysis import analyze_shot_decision
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Tuple
import os
import httpx
import logging
import traceback
import json
import tempfile
import random
from datetime import datetime

from .services.player_service import PlayerService # Import PlayerService
from .services.email_service import EmailService, get_email_service
from .services.oauth2_email_service import OAuth2EmailService, get_oauth2_email_service
from .services.team_formation_service import TeamFormationService
from .services.sunday_game_service import generate_sunday_pairings
from .services.legacy_signup_service import get_legacy_signup_service
# Email scheduler will be initialized on-demand to prevent startup blocking
# from .services.email_scheduler import email_scheduler
from .services.auth_service import get_current_user
from .badge_routes import router as badge_router

# Global variable for email scheduler (initialized on demand)
email_scheduler = None

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Wolf Goat Pig Simulation (will be replaced when game starts)
wgp_simulation = WolfGoatPigSimulation(player_count=4)
# Initialize Post-Hole Analyzer
post_hole_analyzer = PostHoleAnalyzer()

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


class BallSeed(BaseModel):
    """Testing helper payload for manually positioning a ball."""

    player_id: str = Field(..., description="Unique player identifier")
    distance_to_pin: float = Field(..., ge=0, description="Distance remaining in yards")
    lie_type: str = Field("fairway", description="Current lie type for the ball")
    shot_count: int = Field(1, ge=0, description="Number of strokes taken on the hole")
    holed: bool = Field(False, description="Whether the ball is in the hole")
    conceded: bool = Field(False, description="If the putt has been conceded")
    penalty_strokes: int = Field(0, ge=0, description="Penalty strokes assessed on the shot")


class BettingSeed(BaseModel):
    """Testing helper payload for adjusting betting metadata."""

    base_wager: Optional[int] = Field(None, ge=0)
    current_wager: Optional[int] = Field(None, ge=0)
    doubled: Optional[bool] = None
    redoubled: Optional[bool] = None
    carry_over: Optional[bool] = None
    float_invoked: Optional[bool] = None
    option_invoked: Optional[bool] = None
    duncan_invoked: Optional[bool] = None
    tunkarri_invoked: Optional[bool] = None
    big_dick_invoked: Optional[bool] = None
    joes_special_value: Optional[int] = None
    line_of_scrimmage: Optional[str] = None
    ping_pong_count: Optional[int] = Field(None, ge=0)


class SimulationSeedRequest(BaseModel):
    """Parameters accepted by the test seeding endpoint."""

    current_hole: Optional[int] = Field(
        None, description="Hole number to switch the active simulation to"
    )
    shot_order: Optional[List[str]] = Field(
        None, description="Explicit hitting order for the active hole"
    )
    ball_positions: List[BallSeed] = Field(default_factory=list)
    ball_positions_replace: bool = Field(False, description="Replace all ball positions when True")
    line_of_scrimmage: Optional[str] = None
    next_player_to_hit: Optional[str] = None
    current_order_of_play: Optional[List[str]] = None
    wagering_closed: Optional[bool] = None
    betting: Optional[BettingSeed] = None
    team_formation: Optional[Dict[str, Any]] = Field(
        None, description="Override the current TeamFormation dataclass"
    )
    clear_balls_in_hole: bool = Field(False, description="Clear recorded holed balls before applying seed")
    reset_doubles_history: bool = Field(True, description="Clear double-offer history to avoid stale offers")

app = FastAPI(
    title="Wolf Goat Pig Golf Simulation API",
    description="A comprehensive golf betting simulation API with unified Action API",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

ENABLE_TEST_ENDPOINTS = os.getenv("ENABLE_TEST_ENDPOINTS", "false").lower() in {"1", "true", "yes"}
ADMIN_EMAILS = {"stuagano@gmail.com", "admin@wgp.com"}


def require_admin(x_admin_email: Optional[str] = Header(None)) -> None:
    if not x_admin_email or x_admin_email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

# Database initialization moved to main startup handler

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
# Configure origins based on environment
allowed_origins = [
    "https://wolf-goat-pig.vercel.app",  # Production frontend
    "https://wolf-goat-pig-frontend.onrender.com",  # Alternative frontend URL
]

# Add localhost for development and local testing
# Note: localhost is safe for local Podman/Docker testing even with ENVIRONMENT=production
if os.getenv("ENVIRONMENT") != "production" or os.getenv("FRONTEND_URL", "").startswith("http://localhost"):
    allowed_origins.extend([
        "http://localhost:3000",             # Local development
        "http://localhost:3001",             # Alternative local port
        "http://127.0.0.1:3000",            # Alternative localhost
        "http://127.0.0.1:3001",            # Alternative localhost
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Admin-Email",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"]
)

# Include badge system routes
app.include_router(badge_router)

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
async def startup():
    """Enhanced startup event handler with comprehensive bootstrapping."""
    logger.info("🐺 Wolf Goat Pig API starting up...")
    logger.info(f"ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
    
    # Initialize database first
    try:
        # Ensure all models are imported before creating tables
        from . import models
        database.init_db()
        logger.info("Database initialized successfully")
        
        # Verify game_state table exists
        db = database.SessionLocal()
        try:
            db.execute(text("SELECT COUNT(*) FROM game_state"))
            logger.info("game_state table verified")
        except Exception as table_error:
            logger.error(f"game_state table verification failed: {table_error}")
            # Try to create tables again
            database.Base.metadata.create_all(bind=database.engine)
            logger.info("Tables recreated")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Don't continue if database fails in production
        if os.getenv("ENVIRONMENT") == "production":
            raise
    
    # Email scheduler initialization moved to on-demand/UI configuration
    # This prevents email issues from blocking app startup
    logger.info("📧 Email scheduler will be initialized on-demand")
    
    try:
        # Import seeding functionality
        from .seed_data import seed_all_data, get_seeding_status
        
        # Check if we should skip seeding (for testing or when explicitly disabled)
        skip_seeding = os.getenv("SKIP_SEEDING", "false").lower() == "true"
        
        if skip_seeding:
            logger.info("⏭️ Seeding skipped due to SKIP_SEEDING environment variable")
        else:
            # Check current seeding status first
            logger.info("🔍 Checking existing data status...")
            status = get_seeding_status()
            
            if status["status"] == "success":
                # Verify all critical components are present
                verification = status.get("verification", {})
                overall_status = verification.get("overall", {}).get("status", "unknown")
                
                if overall_status == "success":
                    logger.info("✅ All required data already present, skipping seeding")
                else:
                    logger.info("⚠️ Some data missing, running seeding process...")
                    await run_seeding_process()
            else:
                logger.info("🌱 No existing data found, running initial seeding...")
                await run_seeding_process()
        
        # Initialize game state and course manager
        logger.info("🎯 Initializing game state...")
        try:
            # Ensure game_state is properly initialized with courses
            courses = game_state.get_courses()
            if not courses:
                logger.warning("⚠️ No courses found in game state, attempting to reload...")
                game_state.course_manager.__init__()  # Reinitialize course manager
                courses = game_state.get_courses()
            
            logger.info(f"📚 Game state initialized with {len(courses)} courses")
        except Exception as e:
            logger.error(f"❌ Failed to initialize game state: {e}")
            # Continue startup - game state will use fallback data
        
        # Verify simulation can be created
        logger.info("🔧 Verifying simulation initialization...")
        try:
            # Test creating a basic simulation
            test_players = [
                {"id": "p1", "name": "Test1", "handicap": 10},
                {"id": "p2", "name": "Test2", "handicap": 15},
                {"id": "p3", "name": "Test3", "handicap": 8},
                {"id": "p4", "name": "Test4", "handicap": 20}
            ]
            test_simulation = WolfGoatPigSimulation(player_count=4)
            logger.info("✅ Simulation initialization verified")
        except Exception as e:
            logger.warning(f"⚠️ Simulation test failed (non-critical): {e}")
        
        # Initialize email scheduler if email notifications enabled
        if os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "true").lower() == "true":
            try:
                logger.info("📧 Initializing email scheduler...")
                result = await initialize_email_scheduler()
                if result["status"] == "success":
                    logger.info("✅ Email scheduler initialized")
                else:
                    logger.warning(f"⚠️ Email scheduler: {result['message']}")
            except Exception as e:
                logger.error(f"❌ Email scheduler initialization failed: {e}")
        else:
            logger.info("📧 Email notifications disabled")
        
        logger.info("🚀 Wolf Goat Pig API startup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}")
        logger.error("⚠️ Application may not function properly")
        # Don't raise - allow app to start with limited functionality

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("🛑 Wolf Goat Pig API shutting down...")
    
    # Stop email scheduler if it was started
    try:
        if email_scheduler is not None and hasattr(email_scheduler, 'stop'):
            email_scheduler.stop()
            logger.info("📧 Email scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop email scheduler: {str(e)}")

async def run_seeding_process():
    """Run the data seeding process during startup."""
    try:
        from .seed_data import seed_all_data
        
        logger.info("🌱 Starting data seeding process...")
        
        # Run seeding in a try-catch to prevent startup failure
        seeding_results = seed_all_data(force_reseed=False)
        
        if seeding_results["status"] == "success":
            logger.info("✅ Data seeding completed successfully")
            
            # Log seeding summary
            if "results" in seeding_results:
                for component, result in seeding_results["results"].items():
                    added_count = result.get("added", 0)
                    if added_count > 0:
                        logger.info(f"  📊 {component}: {added_count} items added")
                    
        elif seeding_results["status"] == "warning":
            logger.warning(f"⚠️ Data seeding completed with warnings: {seeding_results.get('message')}")
            
        else:
            logger.error(f"❌ Data seeding failed: {seeding_results.get('message')}")
            logger.warning("🔄 Application will continue with fallback data")
            
    except Exception as e:
        logger.error(f"❌ Critical error during seeding: {e}")
        logger.warning("🔄 Application will continue with fallback data")

@app.get("/health")
def health_check():
    """Comprehensive health check endpoint verifying all critical systems"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "version": "1.0.0",
        "components": {}
    }
    
    # During initial deployment, be more lenient with health checks
    is_initial_deployment = os.getenv("ENVIRONMENT") == "production"
    overall_healthy = True
    
    try:
        # 1. Database connectivity test
        db = database.SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            health_status["components"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
            overall_healthy = False
        finally:
            db.close()
        
        # 2. Course data availability check
        try:
            courses = game_state.get_courses()
            course_count = len(courses) if courses else 0
            
            if course_count >= 1:
                health_status["components"]["courses"] = {
                    "status": "healthy",
                    "message": f"{course_count} courses available",
                    "courses": list(courses.keys()) if courses else []
                }
            else:
                health_status["components"]["courses"] = {
                    "status": "warning" if is_initial_deployment else "unhealthy",
                    "message": "No courses available (may be initializing)"
                }
                if not is_initial_deployment:
                    overall_healthy = False
                
        except Exception as e:
            logger.error(f"Course availability check failed: {e}")
            health_status["components"]["courses"] = {
                "status": "warning" if is_initial_deployment else "unhealthy",
                "message": f"Course check failed: {str(e)}"
            }
            if not is_initial_deployment:
                overall_healthy = False
        
        # 3. Rules availability check
        try:
            db = database.SessionLocal()
            try:
                from . import models
                rule_count = db.query(models.Rule).count()
                
                if rule_count >= 5:  # Minimum reasonable number of rules
                    health_status["components"]["rules"] = {
                        "status": "healthy",
                        "message": f"{rule_count} rules loaded"
                    }
                else:
                    health_status["components"]["rules"] = {
                        "status": "warning",
                        "message": f"Only {rule_count} rules found, may be incomplete"
                    }
            except Exception as e:
                health_status["components"]["rules"] = {
                    "status": "warning",
                    "message": f"Rules check failed: {str(e)}"
                }
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Rules availability check failed: {e}")
            health_status["components"]["rules"] = {
                "status": "warning",
                "message": f"Rules check error: {str(e)}"
            }
        
        # 4. AI Players availability check
        try:
            db = database.SessionLocal()
            try:
                from . import models
                ai_player_count = (
                    db.query(models.PlayerProfile)
                    .filter(models.PlayerProfile.is_ai == 1)
                    .filter(models.PlayerProfile.is_active == 1)
                    .count()
                )

                if ai_player_count >= 4:  # Need at least 4 for a game
                    health_status["components"]["ai_players"] = {
                        "status": "healthy",
                        "message": f"{ai_player_count} AI players available"
                    }
                elif ai_player_count >= 1:
                    health_status["components"]["ai_players"] = {
                        "status": "warning",
                        "message": f"Only {ai_player_count} AI players available, need at least 4 for full game"
                    }
                else:
                    health_status["components"]["ai_players"] = {
                        "status": "warning",
                        "message": "No AI players available (may be initializing)"
                    }
                    # Don't fail health check for missing AI players during initial deployment
                    if not is_initial_deployment:
                        overall_healthy = False
            finally:
                db.close()

        except Exception as e:
            logger.error(f"AI players availability check failed: {e}")
            health_status["components"]["ai_players"] = {
                "status": "warning",
                "message": f"AI players check failed: {str(e)}"
            }
        
        # 5. Simulation initialization test
        try:
            # Test basic simulation creation
            test_simulation = WolfGoatPigSimulation(player_count=4)
            health_status["components"]["simulation"] = {
                "status": "healthy",
                "message": "Simulation engine operational"
            }
        except Exception as e:
            logger.error(f"Simulation initialization test failed: {e}")
            health_status["components"]["simulation"] = {
                "status": "warning" if is_initial_deployment else "unhealthy",
                "message": f"Simulation test failed: {str(e)}"
            }
            if not is_initial_deployment:
                overall_healthy = False
        
        # 6. Game state check
        try:
            state = game_state.get_state()
            if state:
                health_status["components"]["game_state"] = {
                    "status": "healthy",
                    "message": "Game state manager operational"
                }
            else:
                health_status["components"]["game_state"] = {
                    "status": "warning",
                    "message": "Game state appears empty but functional"
                }
        except Exception as e:
            logger.error(f"Game state check failed: {e}")
            health_status["components"]["game_state"] = {
                "status": "warning" if is_initial_deployment else "unhealthy",
                "message": f"Game state check failed: {str(e)}"
            }
            if not is_initial_deployment:
                overall_healthy = False
        
        # 7. Import seeding status check
        try:
            from .seed_data import get_seeding_status
            seeding_status = get_seeding_status()
            
            if seeding_status["status"] == "success":
                overall_verification = seeding_status.get("verification", {}).get("overall", {})
                if overall_verification.get("status") == "success":
                    health_status["components"]["data_seeding"] = {
                        "status": "healthy",
                        "message": "All required data properly seeded"
                    }
                else:
                    health_status["components"]["data_seeding"] = {
                        "status": "warning",
                        "message": "Some seeded data may be incomplete"
                    }
            else:
                health_status["components"]["data_seeding"] = {
                    "status": "warning",
                    "message": f"Data seeding status: {seeding_status.get('message', 'Unknown')}"
                }
                
        except Exception as e:
            logger.error(f"Data seeding status check failed: {e}")
            health_status["components"]["data_seeding"] = {
                "status": "warning",
                "message": f"Seeding status check failed: {str(e)}"
            }
        
        # Set overall status
        if not overall_healthy:
            health_status["status"] = "unhealthy"
            raise HTTPException(status_code=503, detail="Critical system components are unhealthy")
        
        # Check for warnings
        warning_count = sum(1 for comp in health_status["components"].values() 
                          if comp["status"] == "warning")
        
        if warning_count > 0:
            health_status["status"] = "degraded"
            health_status["warnings"] = f"{warning_count} component(s) with warnings"
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.get("/healthz")
def health_check_render_alias():
    """Simplified health endpoint for Render monitoring."""
    try:
        # Reuse the comprehensive health check; Render only needs 200/503.
        health_check()
        return {"status": "ok"}
    except HTTPException as exc:
        # Mirror original status code to keep behaviour consistent.
        raise exc

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
@app.get("/players/all", response_model=List[schemas.PlayerProfileResponse])
def get_all_players(
    active_only: bool = Query(True, description="Only return active players"),
    db: Session = Depends(database.get_db)
):
    """Get all player profiles."""
    player_service = PlayerService(db)
    return player_service.get_all_player_profiles(active_only=active_only)

@app.get("/courses")
def get_courses():
    """Get all available courses with robust fallback handling"""
    try:
        courses = game_state.get_courses()
        
        # Ensure we always return at least one default course
        if not courses:
            logger.warning("No courses found in game state, attempting to reload from database")
            
            # Try to reload from database
            try:
                from .seed_data import get_seeding_status
                seeding_status = get_seeding_status()
                
                if seeding_status["status"] == "success":
                    # Reinitialize course manager
                    game_state.course_manager.__init__()
                    courses = game_state.get_courses()
                    
                    if courses:
                        logger.info(f"Successfully reloaded {len(courses)} courses from database")
                    else:
                        logger.warning("Course manager reinitialization failed, using fallback")
                        courses = get_fallback_courses()
                else:
                    logger.warning("Database seeding incomplete, using fallback courses")
                    courses = get_fallback_courses()
                    
            except Exception as reload_error:
                logger.error(f"Failed to reload courses from database: {reload_error}")
                courses = get_fallback_courses()
        
        logger.info(f"Retrieved {len(courses)} courses: {list(courses.keys())}")
        return courses
        
    except Exception as e:
        logger.error(f"Critical error getting courses: {e}")
        logger.error(traceback.format_exc())
        
        # Always return fallback course to prevent frontend failure
        courses = get_fallback_courses()
        logger.warning("Returning fallback courses due to critical error")
        return courses

def get_fallback_courses():
    """Provide fallback course data when database/seeding fails"""
    return {
        "Emergency Course": {
            "name": "Emergency Course",
            "description": "Fallback course for system resilience",
            "holes": [
                {
                    "hole_number": i,
                    "par": 4 if i not in [4, 8, 12, 17] else 3 if i in [4, 8, 17] else 5,
                    "yards": 400 if i not in [4, 8, 12, 17] else 160 if i in [4, 8, 17] else 520,
                    "stroke_index": ((i - 1) % 18) + 1,
                    "description": f"Emergency hole {i} - Par {4 if i not in [4, 8, 12, 17] else 3 if i in [4, 8, 17] else 5}"
                }
                for i in range(1, 19)
            ],
            "total_par": 72,
            "total_yards": 6800,
            "hole_count": 18
        },
        "Wing Point Golf & Country Club": {
            "name": "Wing Point Golf & Country Club",
            "description": "Classic parkland course (fallback data)",
            "holes": [
                {"hole_number": 1, "par": 4, "yards": 420, "stroke_index": 5, "description": "Opening hole with water hazard"},
                {"hole_number": 2, "par": 4, "yards": 385, "stroke_index": 13, "description": "Straightaway par 4"},
                {"hole_number": 3, "par": 5, "yards": 580, "stroke_index": 1, "description": "Long par 5 with fairway bunkers"},
                {"hole_number": 4, "par": 3, "yards": 165, "stroke_index": 17, "description": "Short par 3 over water"},
                {"hole_number": 5, "par": 4, "yards": 445, "stroke_index": 7, "description": "Long par 4 with OB left"},
                {"hole_number": 6, "par": 4, "yards": 395, "stroke_index": 11, "description": "Slight dogleg left"},
                {"hole_number": 7, "par": 5, "yards": 520, "stroke_index": 15, "description": "Reachable par 5"},
                {"hole_number": 8, "par": 3, "yards": 185, "stroke_index": 3, "description": "Long par 3"},
                {"hole_number": 9, "par": 4, "yards": 410, "stroke_index": 9, "description": "Finishing hole front nine"},
                {"hole_number": 10, "par": 4, "yards": 455, "stroke_index": 2, "description": "Championship hole"},
                {"hole_number": 11, "par": 5, "yards": 545, "stroke_index": 16, "description": "Three-shot par 5"},
                {"hole_number": 12, "par": 3, "yards": 175, "stroke_index": 8, "description": "Elevated tee"},
                {"hole_number": 13, "par": 4, "yards": 375, "stroke_index": 14, "description": "Short par 4"},
                {"hole_number": 14, "par": 4, "yards": 435, "stroke_index": 4, "description": "Narrow fairway"},
                {"hole_number": 15, "par": 5, "yards": 565, "stroke_index": 18, "description": "Longest hole"},
                {"hole_number": 16, "par": 4, "yards": 425, "stroke_index": 10, "description": "Risk/reward hole"},
                {"hole_number": 17, "par": 3, "yards": 155, "stroke_index": 12, "description": "Island green"},
                {"hole_number": 18, "par": 4, "yards": 415, "stroke_index": 6, "description": "Dramatic finishing hole"}
            ],
            "total_par": 72,
            "total_yards": 7050,
            "hole_count": 18
        }
    }

@app.get("/courses/{course_id}")
def get_course_by_id(course_id: int):
    """Get a specific course by ID (index in courses list)"""
    try:
        courses = game_state.get_courses()
        if not courses:
            raise HTTPException(status_code=404, detail="No courses available")
        
        # Convert courses dict to list and get by index
        course_list = list(courses.values())
        if course_id >= len(course_list) or course_id < 0:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Return the course at the specified index
        course = course_list[course_id]
        return course
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting course by ID {course_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get course: {str(e)}")

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
async def ghin_lookup(
    last_name: str = Query(..., description="Golfer's last name"),
    first_name: str = Query(None, description="Golfer's first name (optional)"),
    page: int = Query(1),
    per_page: int = Query(10),
    db: Session = Depends(database.get_db)
):
    """Look up golfers by name using GHIN API"""
    try:
        from .services.ghin_service import GHINService
        
        # Get GHIN credentials from environment
        email = os.getenv("GHIN_API_USER")
        password = os.getenv("GHIN_API_PASS")
        static_token = os.getenv("GHIN_API_STATIC_TOKEN", "ghincom")
        
        if not email or not password:
            raise HTTPException(status_code=500, detail="GHIN credentials not configured in environment variables.")
        
        ghin_service = GHINService(db)
        if not await ghin_service.initialize():
            raise HTTPException(status_code=500, detail="GHIN service not available. Check credentials and logs.")

        search_results = await ghin_service.search_golfers(last_name, first_name, page, per_page)
        return search_results
            
    except httpx.HTTPStatusError as e:
        logger.error(f"GHIN API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"GHIN API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Error in GHIN lookup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to lookup golfer: {str(e)}")
    
@app.post("/ghin/sync-player-handicap/{player_id}", response_model=Dict[str, Any])
async def sync_player_ghin_handicap(
    player_id: int = Path(..., description="The ID of the player to sync"),
    db: Session = Depends(database.get_db)
):
    """Sync a specific player's handicap from GHIN."""
    from .services.ghin_service import GHINService
    
    logger.info(f"Attempting to sync GHIN handicap for player ID: {player_id}")
    ghin_service = GHINService(db)
    if not await ghin_service.initialize():
        raise HTTPException(status_code=500, detail="GHIN service not available. Check credentials and logs.")

    synced_data = await ghin_service.sync_player_handicap(player_id)
    
    if synced_data:
        logger.info(f"Successfully synced handicap for player {player_id}")
        return {"status": "success", "message": "Handicap synced successfully", "data": synced_data}
    else:
        logger.error(f"Failed to sync handicap for player {player_id}")
        raise HTTPException(status_code=500, detail=f"Failed to sync handicap for player {player_id}. Check if player has a GHIN ID and logs for details.")
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
    global wgp_simulation
    try:
        # Use new simulation system if available, otherwise fall back to legacy
        if wgp_simulation:
            logger.info("Returning state from wgp_simulation")
            return wgp_simulation.get_game_state()
        else:
            logger.info("Returning state from legacy game_state")
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

def _get_current_captain_id() -> Optional[str]:
    """Best-effort lookup for the active captain id across legacy and unified state."""
    try:
        simulation_state = wgp_simulation.get_game_state()
        if isinstance(simulation_state, dict):
            captain = simulation_state.get("captain_id") or simulation_state.get("captain")
            if captain:
                return captain
    except Exception:
        # If the simulation hasn't been initialized yet, fall back to legacy state
        pass

    try:
        legacy_state = game_state.get_state()
        if isinstance(legacy_state, dict):
            return legacy_state.get("captain_id")
    except Exception:
        pass

    return None


LEGACY_TO_UNIFIED_ACTIONS = {
    "next_hole": ("ADVANCE_HOLE", lambda payload: {}),
    "request_partner": ("REQUEST_PARTNERSHIP", lambda payload: payload or {}),
    "accept_partner": ("RESPOND_PARTNERSHIP", lambda payload: {"accepted": True}),
    "decline_partner": ("RESPOND_PARTNERSHIP", lambda payload: {"accepted": False}),
    "go_solo": ("DECLARE_SOLO", lambda payload: {}),
    "offer_double": (
        "OFFER_DOUBLE",
        lambda payload: {
            "player_id": payload.get("player_id")
            or payload.get("captain_id")
            or payload.get("offering_player_id")
            or payload.get("offering_team_id")
            or _get_current_captain_id(),
        },
    ),
    "accept_double": ("ACCEPT_DOUBLE", lambda payload: {"accepted": True}),
    "decline_double": ("ACCEPT_DOUBLE", lambda payload: {"accepted": False}),
    "concede_putt": ("CONCEDE_PUTT", lambda payload: payload or {}),
    "INITIALIZE_GAME": ("INITIALIZE_GAME", lambda payload: payload or {}),
}

UNIFIED_ACTION_TYPES = {
    "INITIALIZE_GAME",
    "PLAY_SHOT",
    "REQUEST_PARTNERSHIP",
    "RESPOND_PARTNERSHIP",
    "DECLARE_SOLO",
    "OFFER_DOUBLE",
    "ACCEPT_DOUBLE",
    "CONCEDE_PUTT",
    "ADVANCE_HOLE",
    "OFFER_BIG_DICK",
    "ACCEPT_BIG_DICK",
    "AARDVARK_JOIN_REQUEST",
    "AARDVARK_TOSS",
    "AARDVARK_GO_SOLO",
    "PING_PONG_AARDVARK",
    "INVOKE_JOES_SPECIAL",
    "GET_POST_HOLE_ANALYSIS",
    "ENTER_HOLE_SCORES",
    "GET_ADVANCED_ANALYTICS",
}


@app.post("/game/action")
async def legacy_game_action(action: Dict[str, Any]):
    """Legacy game action endpoint that delegates to unified handlers when available."""
    try:
        # Handle both "action" and "action_type" field names for compatibility
        action_type = action.get("action") or action.get("action_type")
        if not action_type:
            raise HTTPException(status_code=400, detail="Action type required (use 'action' or 'action_type' field)")

        payload = action.get("payload") or action.get("data") or {}

        # Determine if this action should be routed through the unified handler stack
        normalized_action_type = None
        payload_transform = None

        if action_type in LEGACY_TO_UNIFIED_ACTIONS:
            normalized_action_type, payload_transform = LEGACY_TO_UNIFIED_ACTIONS[action_type]
        else:
            upper_action = action_type.upper()
            if upper_action in UNIFIED_ACTION_TYPES:
                normalized_action_type = upper_action
                payload_transform = lambda incoming_payload: incoming_payload or {}

        if normalized_action_type:
            normalized_payload = payload_transform(payload) if payload_transform else (payload or {})

            # Route through the unified action endpoint to ensure consistent behaviour
            action_request = ActionRequest(action_type=normalized_action_type, payload=normalized_payload)
            response = await unified_action("legacy", action_request)
            return response

        # Fallback to legacy game_state dispatch for actions not yet migrated
        result = game_state.dispatch_action(action_type, payload)
        updated_state = game_state.get_state()

        return {
            "status": "success",
            "message": result,
            "game_state": updated_state,
        }
    except HTTPException:
        raise
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
    """Handle game initialization with robust error handling and fallbacks"""
    try:
        players = payload.get("players", [])
        course_name = payload.get("course_name", "Wing Point Golf & Country Club")
        
        # Validate player count (support 4, 5, 6 players)
        if len(players) not in [4, 5, 6]:
            raise HTTPException(status_code=400, detail="4, 5, or 6 players required.")
        
        # Ensure all players have required fields with smart defaults
        for i, player in enumerate(players):
            if "name" not in player:
                player["name"] = f"Player {i+1}"
                logger.warning(f"Player {i+1} missing name, using default")
            
            if "handicap" not in player:
                player["handicap"] = 18.0  # Default handicap
                logger.warning(f"Player {player['name']} missing handicap, using default 18.0")
            
            # Ensure handicap is numeric
            try:
                player["handicap"] = float(player["handicap"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid handicap for {player['name']}, using 18.0")
                player["handicap"] = 18.0
            
            # Add missing fields if not present
            if "id" not in player:
                player["id"] = f"p{i+1}"
            if "strength" not in player:
                # Default strength based on handicap (lower handicap = higher strength)
                player["strength"] = max(1, 10 - int(player["handicap"]))
        
        # Verify course exists, use fallback if needed
        try:
            available_courses = game_state.get_courses()
            if course_name not in available_courses:
                logger.warning(f"Requested course '{course_name}' not available, using fallback")
                # Use first available course or fallback
                if available_courses:
                    course_name = list(available_courses.keys())[0]
                    logger.info(f"Using available course: {course_name}")
                else:
                    logger.error("No courses available, using emergency fallback")
                    course_name = "Emergency Course"
                    # Ensure fallback courses are available
                    fallback_courses = get_fallback_courses()
                    game_state.course_manager.course_data = fallback_courses
        except Exception as course_error:
            logger.error(f"Course verification failed: {course_error}")
            course_name = "Emergency Course"
            fallback_courses = get_fallback_courses()
            game_state.course_manager.course_data = fallback_courses
        
        # Initialize game state with players (with error handling)
        try:
            game_state.setup_players(players, course_name)
            logger.info(f"Game state initialized successfully with {len(players)} players")
        except Exception as game_state_error:
            logger.error(f"Game state setup failed: {game_state_error}")
            # Try with minimal setup
            try:
                game_state.reset()
                logger.warning("Fell back to basic game state reset")
            except Exception as reset_error:
                logger.error(f"Even game state reset failed: {reset_error}")
                # Continue with current state
        
        # Initialize WGP simulation with robust error handling
        try:
            # Create WGPPlayer objects
            wgp_players = []
            for player in players:
                try:
                    wgp_players.append(WGPPlayer(
                        id=player["id"],
                        name=player["name"],
                        handicap=player["handicap"]
                    ))
                except Exception as player_creation_error:
                    logger.error(f"Failed to create WGPPlayer for {player['name']}: {player_creation_error}")
                    # Create with minimal data
                    wgp_players.append(WGPPlayer(
                        id=player.get("id", f"p{len(wgp_players)+1}"),
                        name=player.get("name", f"Player {len(wgp_players)+1}"),
                        handicap=18.0
                    ))
            
            if len(wgp_players) != len(players):
                logger.warning(f"Only created {len(wgp_players)} WGP players from {len(players)} input players")
            
            # Initialize the simulation with these players and course manager
            try:
                wgp_simulation.__init__(player_count=len(wgp_players), players=wgp_players, course_manager=game_state.course_manager)
                logger.info("WGP simulation initialized successfully with course data")
            except Exception as sim_init_error:
                logger.error(f"WGP simulation initialization failed: {sim_init_error}")
                # Try without course manager
                try:
                    wgp_simulation.__init__(player_count=len(wgp_players), players=wgp_players)
                    logger.warning("Initialized without course manager")
                except:
                    # Try with basic initialization
                    wgp_simulation.__init__(player_count=len(wgp_players))
                    logger.warning("Fell back to basic simulation initialization")
            
            # Set computer players (all except first) with error handling
            try:
                computer_player_ids = [p["id"] for p in players[1:]]
                wgp_simulation.set_computer_players(computer_player_ids)
                logger.info(f"Set {len(computer_player_ids)} computer players")
            except Exception as computer_setup_error:
                logger.error(f"Failed to set computer players: {computer_setup_error}")
                # Continue without computer player setup
            
            # Initialize the first hole with error handling
            try:
                wgp_simulation._initialize_hole(1)
                logger.info("First hole initialized")
            except Exception as hole_init_error:
                logger.error(f"Failed to initialize first hole: {hole_init_error}")
                # Continue - hole might be initialized differently
            
            # Enable shot progression and timeline tracking
            try:
                wgp_simulation.enable_shot_progression()
                logger.info("Shot progression enabled")
            except Exception as progression_error:
                logger.warning(f"Failed to enable shot progression: {progression_error}")
                # Non-critical, continue
            
            # Add initial timeline event
            try:
                if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
                    wgp_simulation.hole_progression.add_timeline_event(
                        event_type="game_start",
                        description=f"Game started with {len(players)} players on {course_name}",
                        details={"players": players, "course": course_name}
                    )
                    logger.info("Initial timeline event added")
            except Exception as timeline_error:
                logger.warning(f"Failed to add timeline event: {timeline_error}")
                # Non-critical, continue
            
        except Exception as simulation_error:
            logger.error(f"Critical simulation setup error: {simulation_error}")
            # Create minimal fallback simulation
            try:
                wgp_simulation.__init__(player_count=len(players))
                logger.warning("Created minimal fallback simulation")
            except Exception as fallback_error:
                logger.error(f"Even fallback simulation failed: {fallback_error}")
                # This is critical - raise error
                raise HTTPException(status_code=500, detail="Failed to initialize simulation engine")
        
        # Get initial game state (with error handling)
        try:
            current_state = wgp_simulation.get_game_state()
            if not current_state:
                logger.warning("Empty game state returned, creating minimal state")
                current_state = {
                    "active": True,
                    "current_hole": 1,
                    "players": players,
                    "course": course_name
                }
        except Exception as state_error:
            logger.error(f"Failed to get game state: {state_error}")
            # Create minimal state
            current_state = {
                "active": True,
                "current_hole": 1,
                "players": players,
                "course": course_name,
                "error": "Partial initialization - some features may be limited"
            }
        
        success_message = f"Game initialized with {len(players)} players on {course_name}"
        if any("error" in str(current_state).lower() for _ in [1]):  # Check if there were issues
            success_message += " (some advanced features may be limited)"
        
        return ActionResponse(
            game_state=current_state,
            log_message=success_message,
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
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Critical error initializing game: {e}")
        logger.error(traceback.format_exc())
        
        # Create minimal emergency response
        emergency_state = {
            "active": False,
            "error": "Game initialization failed",
            "fallback": True,
            "message": "Please try again or contact support"
        }
        
        return ActionResponse(
            game_state=emergency_state,
            log_message=f"Game initialization failed: {str(e)}",
            available_actions=[
                {"action_type": "RETRY_INITIALIZATION", "prompt": "Try Again"}
            ],
            timeline_event={
                "id": "init_error",
                "timestamp": datetime.now().isoformat(),
                "type": "initialization_error",
                "description": "Game initialization failed",
                "details": {"error": str(e)}
            }
        )

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
            # Teams not formed yet - check if we should offer partnership decisions
            captain_id = hole_state.teams.captain
            captain_name = wgp_simulation._get_player_name(captain_id)
            
            # Real Wolf-Goat-Pig timing: Partnership decision comes AFTER shots are hit
            # Count how many tee shots have been completed
            tee_shots_completed = sum(1 for player_id, ball in hole_state.ball_positions.items() 
                                    if ball and ball.shot_count >= 1)
            
            # Partnership decision point: After captain and at least one other player have hit
            if tee_shots_completed >= 2:
                # Get available partners based on timing rules  
                available_partners = []
                for player in wgp_simulation.players:
                    if player.id != captain_id and hole_state.can_request_partnership(captain_id, player.id):
                        # Only show players who have already hit their tee shot
                        if player.id in hole_state.ball_positions and hole_state.ball_positions[player.id]:
                            partner_ball = hole_state.ball_positions[player.id]
                            available_partners.append({
                                "id": player.id,
                                "name": player.name,
                                "handicap": player.handicap,
                                "tee_shot_distance": partner_ball.distance_to_pin,
                                "tee_shot_quality": getattr(partner_ball, 'last_shot_quality', 'unknown')
                            })
                
                if available_partners:
                    # Add partnership actions for captain with context about their shots
                    for partner in available_partners:
                        tee_context = f"{partner['name']} hit to {partner['tee_shot_distance']:.0f} yards"
                        available_actions.append({
                            "action_type": "REQUEST_PARTNERSHIP",
                            "prompt": f"Partner with {partner['name']}?",
                            "payload": {"target_player_name": partner['name']},
                            "player_turn": captain_name,
                            "context": f"🏌️ {tee_context}. Form partnership with {partner['name']} (handicap {partner['handicap']})?"
                        })
                    
                    # Add solo option with context
                available_actions.append({
                    "action_type": "DECLARE_SOLO", 
                    "prompt": "Go solo (1v3)",
                    "player_turn": captain_name,
                    "context": "Play alone against all three opponents. High risk, high reward!"
                })
            else:
                # Need more tee shots or partnership deadline passed
                if tee_shots_completed < 2:
                    remaining_players = [p.name for p in wgp_simulation.players 
                                       if p.id not in hole_state.ball_positions or not hole_state.ball_positions[p.id]]
                    available_actions.append({
                        "action_type": "TAKE_SHOT",
                        "prompt": f"Continue tee shots",
                        "context": f"Need more tee shots for partnership decisions. Waiting on: {', '.join(remaining_players) if remaining_players else 'all set'}"
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
            
            # Check for betting opportunities during hole play (doubles/flushes)
            if not hole_state.wagering_closed and hole_state.teams.type in ["partners", "solo"]:
                # Get the recent shot context for betting decisions
                recent_shots = []
                for player_id, ball in hole_state.ball_positions.items():
                    if ball and ball.shot_count > 0:
                        player_name = wgp_simulation._get_player_name(player_id)
                        recent_shots.append(f"{player_name}: {ball.distance_to_pin:.0f}yd ({ball.shot_count} shots)")
                
                # Check if there's a compelling reason to double (great shot, bad position, etc.)
                should_offer_betting = False
                betting_context = []
                
                # Look for recent excellent or terrible shots that create betting opportunities
                if shot_response and "shot_result" in shot_response:
                    last_shot = shot_response["shot_result"]
                    player_name = wgp_simulation._get_player_name(last_shot["player_id"])
                    
                    if last_shot["shot_quality"] == "excellent" and last_shot["distance_to_pin"] < 50:
                        should_offer_betting = True
                        betting_context.append(f"🎯 {player_name} hit an excellent shot to {last_shot['distance_to_pin']:.0f} yards!")
                    elif last_shot["shot_quality"] == "terrible" and last_shot["shot_number"] <= 3:
                        should_offer_betting = True  
                        betting_context.append(f"😬 {player_name} struggling after terrible shot")
                
                # Only offer doubles if there are strategic opportunities and not already doubled
                if should_offer_betting and not hole_state.betting.doubled:
                    # Find players who can offer doubles (not past line of scrimmage)
                    for player in wgp_simulation.players:
                        if hole_state.can_offer_double(player.id):
                            # Create compelling betting context based on recent action
                            current_positions = ", ".join(recent_shots[:3])  # Show top 3 positions
                            full_context = " ".join(betting_context)
                            
                            context = (f"🎲 Double from {hole_state.betting.current_wager} to {hole_state.betting.current_wager * 2} quarters? "
                                     f"{full_context} Current positions: {current_positions}")
                            
                            available_actions.append({
                                "action_type": "OFFER_DOUBLE",
                                "prompt": f"{player.name}: Offer double?",
                                "payload": {"player_id": player.id},
                                "player_turn": player.name,
                                "context": context
                            })
                
                # Also offer flush opportunities if wager has been doubled
                elif hole_state.betting.doubled and not hole_state.betting.redoubled and should_offer_betting:
                    # Flush = double it back
                    for player in wgp_simulation.players:
                        if hole_state.can_offer_double(player.id):
                            current_positions = ", ".join(recent_shots[:3])
                            full_context = " ".join(betting_context)
                            
                            context = (f"💥 Flush! Double back from {hole_state.betting.current_wager} to {hole_state.betting.current_wager * 2} quarters? "
                                     f"{full_context} Positions: {current_positions}")
                            
                            available_actions.append({
                                "action_type": "OFFER_FLUSH", 
                                "prompt": f"{player.name}: Offer flush?",
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


# Real-Time Betting Odds Endpoints
class OddsCalculationRequest(BaseModel):
    """Request model for odds calculation"""
    players: List[Dict[str, Any]] = Field(..., description="Current player states")
    hole_state: Dict[str, Any] = Field(..., description="Current hole state")
    use_monte_carlo: bool = Field(default=False, description="Use Monte Carlo simulation for higher accuracy")
    simulation_params: Optional[Dict[str, Any]] = Field(default=None, description="Monte Carlo simulation parameters")


class BettingScenarioResponse(BaseModel):
    """Response model for betting scenarios"""
    scenario_type: str
    win_probability: float
    expected_value: float
    risk_level: str
    confidence_interval: Tuple[float, float]
    recommendation: str
    reasoning: str
    payout_matrix: Dict[str, float]


class OddsCalculationResponse(BaseModel):
    """Response model for odds calculation"""
    timestamp: float
    calculation_time_ms: float
    player_probabilities: Dict[str, Dict[str, Any]]
    team_probabilities: Dict[str, float]
    betting_scenarios: List[Dict[str, Any]]
    optimal_strategy: str
    risk_assessment: Dict[str, Any]
    educational_insights: List[str]
    confidence_level: float
    monte_carlo_used: bool = False
    simulation_details: Optional[Dict[str, Any]] = None


@app.post("/wgp/calculate-odds", response_model=OddsCalculationResponse)
async def calculate_real_time_odds(request: OddsCalculationRequest):
    """
    Calculate real-time betting odds and probabilities.
    Provides comprehensive analysis for strategic decision making.
    """
    try:
        from .services.odds_calculator import (
            OddsCalculator, 
            create_player_state_from_game_data,
            create_hole_state_from_game_data
        )
        from .services.monte_carlo import run_monte_carlo_simulation, SimulationParams
        
        start_time = time.time()
        
        # Convert request data to internal objects
        player_states = [create_player_state_from_game_data(p) for p in request.players]
        hole_state = create_hole_state_from_game_data(request.hole_state)
        
        # Initialize odds calculator
        calculator = OddsCalculator()
        
        # Determine if we should use Monte Carlo
        use_mc = request.use_monte_carlo
        if not use_mc:
            # Auto-enable Monte Carlo for complex scenarios
            complex_scenario = (
                len(player_states) > 4 or
                hole_state.teams.value != "pending" or
                any(p.distance_to_pin > 200 for p in player_states)
            )
            use_mc = complex_scenario
        
        simulation_details = None
        if use_mc:
            # Run Monte Carlo simulation
            mc_params = SimulationParams()
            if request.simulation_params:
                mc_params.num_simulations = request.simulation_params.get("num_simulations", 5000)
                mc_params.max_simulation_time_ms = request.simulation_params.get("max_time_ms", 25.0)
            
            simulation_result = run_monte_carlo_simulation(player_states, hole_state, 
                                                         mc_params.num_simulations, 
                                                         mc_params.max_simulation_time_ms)
            
            simulation_details = {
                "num_simulations_run": simulation_result.num_simulations_run,
                "simulation_time_ms": simulation_result.simulation_time_ms,
                "convergence_achieved": simulation_result.convergence_achieved,
                "confidence_intervals": simulation_result.confidence_intervals
            }
            
            # Enhance calculator with Monte Carlo results
            # This would integrate MC results into the main calculation
        
        # Calculate comprehensive odds
        odds_result = calculator.calculate_real_time_odds(
            player_states, 
            hole_state,
            game_context={"monte_carlo_result": simulation_details if use_mc else None}
        )
        
        # Convert betting scenarios to response format
        betting_scenarios = []
        for scenario in odds_result.betting_scenarios:
            betting_scenarios.append({
                "scenario_type": scenario.scenario_type,
                "win_probability": scenario.win_probability,
                "expected_value": scenario.expected_value,
                "risk_level": scenario.risk_level,
                "confidence_interval": scenario.confidence_interval,
                "recommendation": scenario.recommendation,
                "reasoning": scenario.reasoning,
                "payout_matrix": scenario.payout_matrix
            })
        
        total_time = (time.time() - start_time) * 1000
        
        return OddsCalculationResponse(
            timestamp=odds_result.timestamp,
            calculation_time_ms=total_time,
            player_probabilities=odds_result.player_probabilities,
            team_probabilities=odds_result.team_probabilities,
            betting_scenarios=betting_scenarios,
            optimal_strategy=odds_result.optimal_strategy,
            risk_assessment=odds_result.risk_assessment,
            educational_insights=odds_result.educational_insights,
            confidence_level=odds_result.confidence_level,
            monte_carlo_used=use_mc,
            simulation_details=simulation_details
        )
        
    except Exception as e:
        logger.error(f"Error calculating odds: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to calculate odds: {str(e)}")


@app.get("/wgp/betting-opportunities")
async def get_current_betting_opportunities():
    """
    Get current betting opportunities based on game state.
    Lightweight endpoint for real-time updates.
    """
    try:
        # Get current game state
        current_state = wgp_simulation.get_game_state()
        
        # Quick opportunity assessment
        opportunities = []
        
        # Check if game is active
        if not current_state.get("active", False):
            return {"opportunities": [], "message": "No active game"}
        
        current_hole = current_state.get("current_hole", 1)
        hole_state = wgp_simulation.hole_states.get(current_hole)
        
        if hole_state:
            # Check for doubling opportunities
            if not hole_state.betting.doubled and hole_state.teams.type != "pending":
                opportunities.append({
                    "type": "offer_double",
                    "description": f"Double the wager from {hole_state.betting.current_wager} to {hole_state.betting.current_wager * 2} quarters",
                    "current_wager": hole_state.betting.current_wager,
                    "potential_wager": hole_state.betting.current_wager * 2,
                    "risk_level": "medium",
                    "timing": "optimal" if not hole_state.wagering_closed else "limited"
                })
            
            # Check for partnership opportunities
            if hole_state.teams.type == "pending":
                captain_id = hole_state.teams.captain
                captain_name = wgp_simulation._get_player_name(captain_id)
                
                available_partners = []
                for player in wgp_simulation.players:
                    if player.id != captain_id and hole_state.can_request_partnership(captain_id, player.id):
                        available_partners.append({
                            "id": player.id,
                            "name": player.name,
                            "handicap": player.handicap
                        })
                
                if available_partners:
                    opportunities.append({
                        "type": "partnership_decision",
                        "description": f"{captain_name} must choose a partner or go solo",
                        "captain": captain_name,
                        "available_partners": available_partners,
                        "solo_multiplier": 2,
                        "deadline_approaching": len(available_partners) < len(wgp_simulation.players) - 1
                    })
        
        return {
            "opportunities": opportunities,
            "hole_number": current_hole,
            "timestamp": datetime.now().isoformat(),
            "game_active": current_state.get("active", False)
        }
        
    except Exception as e:
        logger.error(f"Error getting betting opportunities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get betting opportunities: {str(e)}")


@app.post("/wgp/quick-odds")
async def calculate_quick_odds(players_data: List[Dict[str, Any]] = Body(...)):
    """
    Quick odds calculation for immediate feedback.
    Optimized for sub-50ms response time.
    """
    try:
        from .services.odds_calculator import OddsCalculator, PlayerState, HoleState, TeamConfiguration
        
        start_time = time.time()
        
        # Simple validation
        if len(players_data) < 2:
            raise HTTPException(status_code=400, detail="At least 2 players required")
        
        # Create simplified player states
        players = []
        for i, p_data in enumerate(players_data):
            player = PlayerState(
                id=p_data.get("id", f"p{i}"),
                name=p_data.get("name", f"Player {i+1}"),
                handicap=float(p_data.get("handicap", 18)),
                distance_to_pin=float(p_data.get("distance_to_pin", 150)),
                lie_type=p_data.get("lie_type", "fairway")
            )
            players.append(player)
        
        # Create basic hole state
        hole = HoleState(
            hole_number=1,
            par=4,
            teams=TeamConfiguration.PENDING
        )
        
        # Quick calculation
        calculator = OddsCalculator()
        
        # Calculate win probabilities only
        quick_probs = {}
        for player in players:
            win_prob = calculator._calculate_player_win_vs_field(player, players, hole)
            quick_probs[player.id] = {
                "name": player.name,
                "win_probability": win_prob,
                "handicap": player.handicap,
                "distance": player.distance_to_pin
            }
        
        calculation_time = (time.time() - start_time) * 1000
        
        return {
            "probabilities": quick_probs,
            "calculation_time_ms": calculation_time,
            "method": "quick_analytical",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error in quick odds calculation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate quick odds: {str(e)}")


@app.get("/wgp/odds-history/{game_id}")
async def get_odds_history(game_id: str, hole_number: Optional[int] = None):
    """
    Get historical odds data for analysis and trends.
    """
    try:
        # This would typically query a database for historical odds
        # For now, return mock data structure
        
        history_data = {
            "game_id": game_id,
            "holes": {},
            "trends": {
                "volatility_by_hole": {},
                "betting_patterns": {},
                "accuracy_metrics": {}
            }
        }
        
        # If specific hole requested
        if hole_number:
            history_data["holes"][str(hole_number)] = {
                "initial_odds": {},
                "final_odds": {},
                "betting_actions": [],
                "outcome": {}
            }
        
        return history_data
        
    except Exception as e:
        logger.error(f"Error getting odds history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get odds history: {str(e)}")


# Player Profile Management Endpoints
@app.post("/players", response_model=schemas.PlayerProfileResponse)
def create_player_profile(profile: schemas.PlayerProfileCreate):
    """Create a new player profile."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        result = player_service.create_player_profile(profile)
        
        logger.info(f"Created player profile: {result.name}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error creating player profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating player profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create player profile: {str(e)}")
    finally:
        db.close()

@app.get("/players", response_model=List[schemas.PlayerProfileResponse])
def get_all_player_profiles(active_only: bool = Query(True, description="Return only active profiles")):
    """Get all player profiles."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        profiles = player_service.get_all_player_profiles(active_only=active_only)
        
        logger.info(f"Retrieved {len(profiles)} player profiles")
        return profiles
        
    except Exception as e:
        logger.error(f"Error getting player profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player profiles: {str(e)}")
    finally:
        db.close()

@app.get("/players/{player_id}", response_model=schemas.PlayerProfileResponse)
def get_player_profile(player_id: int):
    """Get a specific player profile."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        profile = player_service.get_player_profile(player_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player profile {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player profile: {str(e)}")
    finally:
        db.close()

@app.put("/players/{player_id}", response_model=schemas.PlayerProfileResponse)
def update_player_profile(player_id: int, profile_update: schemas.PlayerProfileUpdate):
    """Update a player profile."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        updated_profile = player_service.update_player_profile(player_id, profile_update)
        
        if not updated_profile:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
        logger.info(f"Updated player profile {player_id}")
        return updated_profile
        
    except ValueError as e:
        logger.error(f"Validation error updating player profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating player profile {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update player profile: {str(e)}")
    finally:
        db.close()

@app.delete("/players/{player_id}")
def delete_player_profile(player_id: int):
    """Delete (deactivate) a player profile."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        success = player_service.delete_player_profile(player_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
        logger.info(f"Deleted player profile {player_id}")
        return {"message": f"Player {player_id} has been deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting player profile {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete player profile: {str(e)}")
    finally:
        db.close()

@app.get("/players/name/{player_name}", response_model=schemas.PlayerProfileResponse)
def get_player_profile_by_name(player_name: str):
    """Get a player profile by name."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        profile = player_service.get_player_profile_by_name(player_name)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player profile by name {player_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player profile: {str(e)}")
    finally:
        db.close()

# Player Statistics Endpoints
@app.get("/players/{player_id}/statistics", response_model=schemas.PlayerStatisticsResponse)
def get_player_statistics(player_id: int):
    """Get player statistics."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        stats = player_service.get_player_statistics(player_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail=f"Statistics for player {player_id} not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player statistics {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player statistics: {str(e)}")
    finally:
        db.close()

@app.get("/players/{player_id}/analytics", response_model=schemas.PlayerPerformanceAnalytics)
def get_player_analytics(player_id: int):
    """Get comprehensive player performance analytics."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        analytics = player_service.get_player_performance_analytics(player_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail=f"Analytics for player {player_id} not found")
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player analytics {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player analytics: {str(e)}")
    finally:
        db.close()

@app.get("/players/{player_id}/profile-with-stats", response_model=schemas.PlayerProfileWithStats)
def get_player_profile_with_stats(player_id: int):
    """Get player profile combined with statistics and achievements."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        
        # Get profile
        profile = player_service.get_player_profile(player_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
        # Get statistics
        stats = player_service.get_player_statistics(player_id)
        if not stats:
            # Create empty stats if none exist
            stats = schemas.PlayerStatisticsResponse(
                id=0, player_id=player_id, games_played=0, games_won=0,
                total_earnings=0.0, holes_played=0, holes_won=0,
                avg_earnings_per_hole=0.0, betting_success_rate=0.0,
                successful_bets=0, total_bets=0, partnership_success_rate=0.0,
                partnerships_formed=0, partnerships_won=0, solo_attempts=0,
                solo_wins=0, favorite_game_mode="wolf_goat_pig", preferred_player_count=4,
                best_hole_performance=[], worst_hole_performance=[],
                performance_trends=[], last_updated=datetime.now().isoformat()
            )
        
        # Get recent achievements (would need to implement this query)
        recent_achievements = []  # Placeholder
        
        return schemas.PlayerProfileWithStats(
            profile=profile,
            statistics=stats,
            recent_achievements=recent_achievements
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player profile with stats {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player profile with stats: {str(e)}")
    finally:
        db.close()

# Leaderboard and Comparative Analytics
@app.get("/leaderboard", response_model=List[schemas.LeaderboardEntry])
def get_leaderboard(
    limit: int = Query(100, ge=1, le=100),  # Default to 100 to show all players
    sort: str = Query("desc", regex="^(asc|desc)$")  # Add sort parameter
):
    """Get the player leaderboard."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        leaderboard = player_service.get_leaderboard(limit=limit)
        
        # Sort by total_earnings based on sort parameter
        if sort == "asc":
            leaderboard.sort(key=lambda x: x.total_earnings or 0)
        else:
            leaderboard.sort(key=lambda x: x.total_earnings or 0, reverse=True)
        
        # Re-rank after sorting
        for i, entry in enumerate(leaderboard, 1):
            entry.rank = i
        
        return leaderboard
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")
    finally:
        db.close()

@app.get("/leaderboard/{metric}")
def get_leaderboard_by_metric(
    metric: str, 
    limit: int = Query(10, ge=1, le=100)
):
    """Get leaderboard sorted by specific metric."""
    try:
        db = database.SessionLocal()
        from .services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        leaderboard = stats_service.get_comparative_leaderboard(metric=metric, limit=limit)
        
        return {
            "metric": metric,
            "leaderboard": leaderboard,
            "total_players": len(leaderboard)
        }
        
    except Exception as e:
        logger.error(f"Error getting leaderboard by metric {metric}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")
    finally:
        db.close()

@app.get("/analytics/game-stats")
def get_game_stats():
    """Get game statistics analytics"""
    try:
        db = database.SessionLocal()
        
        # Get basic game statistics
        total_games = db.query(models.GameRecord).count() if hasattr(models, 'GameRecord') else 0
        total_simulations = db.query(models.SimulationResult).count()
        
        # Get course usage
        courses = game_state.get_courses()
        course_names = list(courses.keys()) if courses else []
        
        return {
            "total_games": total_games,
            "total_simulations": total_simulations,
            "available_courses": len(course_names),
            "course_names": course_names,
            "game_modes": ["4-man", "5-man", "6-man"],
            "betting_types": ["Wolf", "Goat", "Pig", "Aardvark"],
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting game stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get game stats: {str(e)}")
    finally:
        db.close()

@app.get("/analytics/player-performance") 
def get_player_performance():
    """Get player performance analytics"""
    try:
        db = database.SessionLocal()
        
        # Get basic player statistics
        total_players = db.query(models.PlayerProfile).filter(models.PlayerProfile.is_active == 1).count()
        active_players = total_players  # For now, assume all active players are active
        
        # Get recent signups
        recent_signups = db.query(models.DailySignup).filter(
            models.DailySignup.status != "cancelled"
        ).count()
        
        return {
            "total_players": total_players,
            "active_players": active_players,
            "recent_signups": recent_signups,
            "average_handicap": 15.5,  # Placeholder calculation
            "performance_metrics": {
                "games_played": 0,
                "average_score": 0,
                "best_round": 0,
                "worst_round": 0
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting player performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player performance: {str(e)}")
    finally:
        db.close()

@app.get("/leaderboard/ghin-enhanced")
async def get_ghin_enhanced_leaderboard(
    limit: int = Query(100, ge=1, le=100)
):
    """Get leaderboard enhanced with GHIN handicap data."""
    try:
        db = database.SessionLocal()
        from .services.ghin_service import GHINService
        
        ghin_service = GHINService(db)
        
        # Try to initialize GHIN service for fresh data, but continue with stored data if unavailable
        try:
            await ghin_service.initialize()
        except Exception as e:
            logger.warning(f"GHIN service unavailable, using stored handicap data: {e}")
        
        # Always get enhanced leaderboard with stored GHIN data (even if service is offline)
        enhanced_leaderboard = ghin_service.get_leaderboard_with_ghin_data(limit=limit)
        
        return enhanced_leaderboard
        
    except Exception as e:
        logger.error(f"Error getting GHIN enhanced leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get GHIN enhanced leaderboard: {str(e)}")
    finally:
        db.close()

@app.post("/ghin/sync-handicaps")
async def sync_ghin_handicaps():
    """Sync handicaps for all players with GHIN IDs."""
    try:
        db = database.SessionLocal()
        from .services.ghin_service import GHINService
        
        ghin_service = GHINService(db)
        
        # Initialize and check if available
        await ghin_service.initialize()
        if not ghin_service.is_available():
            raise HTTPException(status_code=503, detail="GHIN service not available. Check configuration.")
        
        # Sync all player handicaps
        sync_results = await ghin_service.sync_all_players_handicaps()
        
        return {
            "message": "GHIN handicap sync completed",
            "results": sync_results
        }
        
    except Exception as e:
        logger.error(f"Error syncing GHIN handicaps: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync GHIN handicaps: {str(e)}")
    finally:
        db.close()

# Advanced Analytics Endpoints
@app.get("/players/{player_id}/advanced-metrics")
def get_player_advanced_metrics(player_id: int):
    """Get advanced performance metrics for a player."""
    try:
        db = database.SessionLocal()
        from .services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        metrics = stats_service.get_advanced_player_metrics(player_id)
        
        return {
            "player_id": player_id,
            "metrics": metrics,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting advanced metrics for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get advanced metrics: {str(e)}")
    finally:
        db.close()

@app.get("/players/{player_id}/trends")
def get_player_trends(
    player_id: int, 
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze")
):
    """Get performance trends for a player."""
    try:
        db = database.SessionLocal()
        from .services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        trends = stats_service.get_performance_trends(player_id, days=days)
        
        return {
            "player_id": player_id,
            "period_days": days,
            "trends": trends,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trends for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player trends: {str(e)}")
    finally:
        db.close()

@app.get("/players/{player_id}/insights")
def get_player_insights(player_id: int):
    """Get personalized insights and recommendations for a player."""
    try:
        db = database.SessionLocal()
        from .services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        insights = stats_service.get_player_insights(player_id)
        
        return {
            "player_id": player_id,
            "insights": [insight.__dict__ for insight in insights],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting insights for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player insights: {str(e)}")
    finally:
        db.close()

@app.get("/players/{player_id}/skill-rating")
def get_player_skill_rating(player_id: int):
    """Get skill rating for a player."""
    try:
        db = database.SessionLocal()
        from .services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        rating = stats_service.calculate_skill_rating(player_id)
        
        return {
            "player_id": player_id,
            "skill_rating": rating,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting skill rating for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get skill rating: {str(e)}")
    finally:
        db.close()

# Game Result Recording
@app.post("/game-results")
def record_game_result(game_result: schemas.GamePlayerResultCreate):
    """Record a game result for a player."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        
        player_service = PlayerService(db)
        success = player_service.record_game_result(game_result)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to record game result")
        
        # Check for achievements
        achievements = player_service.check_and_award_achievements(
            game_result.player_profile_id, game_result
        )
        
        logger.info(f"Recorded game result for player {game_result.player_profile_id}")
        
        return {
            "message": "Game result recorded successfully",
            "achievements_earned": achievements
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording game result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record game result: {str(e)}")
    finally:
        db.close()

# Analytics Overview
@app.get("/analytics/overview")
def get_analytics_overview():
    """Get overall analytics overview."""
    try:
        db = database.SessionLocal()
        from .services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        
        # Get game mode analytics
        game_mode_analytics = stats_service.get_game_mode_analytics()
        
        # Get basic statistics
        total_players = db.query(models.PlayerProfile).filter(models.PlayerProfile.is_active == 1).count()
        total_games = db.query(models.GameRecord).count()
        active_players = db.query(models.PlayerProfile).filter(
            and_(models.PlayerProfile.is_active == 1, models.PlayerProfile.last_played.isnot(None))
        ).count()
        
        return {
            "total_players": total_players,
            "active_players": active_players,
            "total_games": total_games,
            "game_mode_analytics": game_mode_analytics,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics overview: {str(e)}")
    finally:
        db.close()

# Sheet Integration Endpoints
@app.post("/sheet-integration/analyze-structure")
def analyze_sheet_structure(sheet_headers: List[str]):
    """Analyze Google Sheet headers and create column mappings."""
    try:
        db = database.SessionLocal()
        from .services.sheet_integration_service import SheetIntegrationService
        
        sheet_service = SheetIntegrationService(db)
        mappings = sheet_service.create_column_mappings(sheet_headers)
        
        return {
            "headers_analyzed": len(sheet_headers),
            "mappings_created": len(mappings),
            "column_mappings": [
                {
                    "sheet_column": mapping.sheet_column,
                    "db_field": mapping.db_field,
                    "data_type": mapping.data_type,
                    "transformation": mapping.transformation
                }
                for mapping in mappings
            ],
            "analyzed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing sheet structure: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze sheet structure: {str(e)}")
    finally:
        db.close()

@app.post("/sheet-integration/create-leaderboard")
def create_leaderboard_from_sheet(sheet_data: List[Dict[str, Any]]):
    """Create a leaderboard from Google Sheet data without persisting to database."""
    try:
        db = database.SessionLocal()
        from .services.sheet_integration_service import SheetIntegrationService
        
        if not sheet_data:
            raise HTTPException(status_code=400, detail="Sheet data is required")
        
        # Extract headers from first row
        headers = list(sheet_data[0].keys())
        
        sheet_service = SheetIntegrationService(db)
        mappings = sheet_service.create_column_mappings(headers)
        leaderboard = sheet_service.create_leaderboard_from_sheet_data(sheet_data, mappings)
        
        return {
            "leaderboard": leaderboard,
            "total_players": len(leaderboard),
            "columns_mapped": len(mappings),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating leaderboard from sheet: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create leaderboard: {str(e)}")
    finally:
        db.close()

@app.post("/sheet-integration/sync-data")
def sync_sheet_data(sheet_data: List[Dict[str, Any]]):
    """Sync Google Sheet data to database (creates/updates player profiles and statistics)."""
    try:
        db = database.SessionLocal()
        from .services.sheet_integration_service import SheetIntegrationService
        
        if not sheet_data:
            raise HTTPException(status_code=400, detail="Sheet data is required")
        
        # Extract headers from first row
        headers = list(sheet_data[0].keys())
        
        sheet_service = SheetIntegrationService(db)
        mappings = sheet_service.create_column_mappings(headers)
        results = sheet_service.sync_sheet_data_to_database(sheet_data, mappings)
        
        return {
            "sync_results": results,
            "synced_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error syncing sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync sheet data: {str(e)}")
    finally:
        db.close()

@app.get("/sheet-integration/export-current-data")
def export_current_data_for_sheet(sheet_headers: List[str] = Query(...)):
    """Export current database data in Google Sheet format for comparison."""
    try:
        db = database.SessionLocal()
        from .services.sheet_integration_service import SheetIntegrationService
        
        sheet_service = SheetIntegrationService(db)
        mappings = sheet_service.create_column_mappings(sheet_headers)
        exported_data = sheet_service.export_current_data_to_sheet_format(mappings)
        
        return {
            "exported_data": exported_data,
            "total_players": len(exported_data),
            "columns": sheet_headers,
            "exported_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting current data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export current data: {str(e)}")
    finally:
        db.close()

@app.post("/sheet-integration/sync-wgp-sheet")
async def sync_wgp_sheet_data(request: Dict[str, str]):
    """Sync Wolf Goat Pig specific sheet data format."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        from collections import defaultdict
        import httpx
        
        csv_url = request.get("csv_url")
        if not csv_url:
            raise HTTPException(status_code=400, detail="CSV URL is required")
        
        # Fetch the CSV data (follow redirects for Google Sheets export URLs)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(csv_url, timeout=30)
            response.raise_for_status()
        csv_text = response.text
        
        # Parse CSV
        lines = csv_text.strip().split('\n')
        if not lines:
            raise HTTPException(status_code=400, detail="Empty sheet data")
        
        # Find the actual header row (looking for "Member" column)
        header_line_index = -1
        headers = []
        
        for i, line in enumerate(lines):
            temp_headers = [h.strip().strip('"') for h in line.split(',')]
            # Check if this line contains the actual column headers
            if any('member' in h.lower() for h in temp_headers if h) and \
               any('quarters' in h.lower() for h in temp_headers if h):
                header_line_index = i
                headers = temp_headers
                logger.info(f"Found headers at row {i + 1}: {headers}")
                break
        
        if header_line_index == -1:
            # Fallback: assume headers are in the first non-empty row with multiple values
            for i, line in enumerate(lines):
                temp_headers = [h.strip().strip('"') for h in line.split(',')]
                if len([h for h in temp_headers if h]) >= 3:  # At least 3 non-empty columns
                    header_line_index = i
                    headers = temp_headers
                    logger.info(f"Using row {i + 1} as headers (fallback): {headers}")
                    break
        
        if not headers:
            raise HTTPException(status_code=400, detail="Could not find valid headers in sheet")
        
        # Create header index mapping for flexible column handling
        header_map = {header.lower(): idx for idx, header in enumerate(headers) if header}
        
        # Process each row based on detected columns
        player_stats = {}
        
        # Start processing from the row after headers
        for line in lines[header_line_index + 1:]:
            if line.strip():
                values = [v.strip().strip('"') for v in line.split(',')]
                
                # Skip empty rows or rows with too few values
                if len(values) < 2 or not any(v for v in values[:5]):  # Check first 5 columns
                    continue
                
                # Extract player name (try different column names)
                player_name = None
                for name_key in ['member', 'player', 'name', 'golfer']:
                    if name_key in header_map and header_map[name_key] < len(values):
                        player_name = values[header_map[name_key]]
                        break
                
                # Skip if no player name, or if it's a header/summary row
                if not player_name or player_name.lower() in ['member', 'player', 'name', '', 'total', 'average', 'grand total']:
                    logger.info(f"Skipping non-player row: {player_name}")
                    continue
                
                # Stop if we hit summary sections (like "Most Rounds Played")
                if any(keyword in player_name.lower() for keyword in ['most rounds', 'top 5', 'best score', 'worst score', 'group size']):
                    logger.info(f"Stopping at summary section: {player_name}")
                    break
                
                # Initialize player stats if not exists
                if player_name not in player_stats:
                    player_stats[player_name] = {
                        "quarters": 0,
                        "average": 0,
                        "rounds": 0,
                        "qb": 0,
                        "games_won": 0,
                        "total_earnings": 0
                    }
                
                # Map the sheet columns to our data model
                # Score column (total earnings - can be negative)
                score_value = None
                for score_key in ['score', 'sum score', 'total score', 'quarters']:
                    if score_key in header_map and header_map[score_key] < len(values):
                        score_value = values[header_map[score_key]]
                        break
                
                if score_value and score_value != '':
                    try:
                        # Handle negative values (e.g., "-155")
                        score_int = int(float(score_value))  # Handle decimal values too
                        # Accumulate total earnings across multiple games
                        player_stats[player_name]["quarters"] += score_int
                        player_stats[player_name]["total_earnings"] += float(score_int)
                        logger.debug(f"Added {score_value} to {player_name}, total now: {player_stats[player_name]['total_earnings']}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing score for {player_name}: {e}")
                        pass
                
                # Average column
                if 'average' in header_map and header_map['average'] < len(values):
                    try:
                        avg_value = values[header_map['average']]
                        if avg_value and avg_value != '':
                            player_stats[player_name]["average"] = float(avg_value)
                            logger.debug(f"Set {player_name} average to {avg_value}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing average for {player_name}: {e}")
                        pass
                
                # Count rounds/games played (increment for each row)
                player_stats[player_name]["rounds"] += 1
                logger.debug(f"Incremented {player_name} rounds to {player_stats[player_name]['rounds']}")
                
                # Check if they won this game (positive score)
                if score_value and score_value != '':
                    try:
                        if float(score_value) > 0:
                            player_stats[player_name]["games_won"] += 1
                    except (ValueError, TypeError):
                        pass
                
                # QB column
                if 'qb' in header_map and header_map['qb'] < len(values):
                    try:
                        qb_value = values[header_map['qb']]
                        if qb_value and qb_value != '':
                            player_stats[player_name]["qb"] = int(qb_value)
                            logger.debug(f"Set {player_name} QB to {qb_value}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing QB for {player_name}: {e}")
                        pass
                
                # Log successful player data extraction
                if player_stats[player_name]["quarters"] != 0 or player_stats[player_name]["rounds"] > 0:
                    logger.info(f"Extracted data for {player_name}: {player_stats[player_name]}")
        
        # Calculate averages for all players after processing all rows
        for player_name, stats in player_stats.items():
            if stats["rounds"] > 0:
                stats["average"] = stats["total_earnings"] / stats["rounds"]
                logger.debug(f"Calculated average for {player_name}: {stats['average']}")
        
        # Create/update players in database
        player_service = PlayerService(db)
        sync_results = {
            "players_processed": 0,
            "players_created": 0,
            "players_updated": 0,
            "errors": []
        }
        
        # Track GHIN data for response payload
        ghin_data_collection = {}
        
        for player_name, stats in player_stats.items():
            try:
                # Check if player exists
                existing_player = db.query(models.PlayerProfile).filter(
                    models.PlayerProfile.name == player_name
                ).first()
                
                if not existing_player:
                    # Create new player
                    player_data = schemas.PlayerProfileCreate(
                        name=player_name,
                        handicap=10.0,  # Default handicap
                        email=f"{player_name.lower().replace(' ', '.')}@wgp.com"
                    )
                    new_player = player_service.create_player_profile(player_data)
                    sync_results["players_created"] += 1
                    player_id = new_player.id
                else:
                    player_id = existing_player.id
                    sync_results["players_updated"] += 1
                
                # Update or create statistics record
                player_stats_record = db.query(models.PlayerStatistics).filter(
                    models.PlayerStatistics.player_id == player_id
                ).first()
                
                if not player_stats_record:
                    # Create new statistics record
                    player_stats_record = models.PlayerStatistics(player_id=player_id)
                    db.add(player_stats_record)
                
                # Update statistics with sheet data
                player_stats_record.games_played = stats.get("rounds", 0)
                player_stats_record.total_earnings = stats.get("total_earnings", 0)
                
                # Calculate win percentage based on average earnings per game
                if stats.get("rounds", 0) > 0 and stats.get("average", 0) > 0:
                    # If average is positive, estimate wins based on that
                    # Assuming positive average means winning more often
                    estimated_win_rate = min(100, max(0, (stats.get("average", 0) + 50) / 100 * 50))
                    player_stats_record.win_percentage = estimated_win_rate
                    player_stats_record.games_won = int(stats.get("rounds", 0) * estimated_win_rate / 100)
                else:
                    player_stats_record.win_percentage = 0
                    player_stats_record.games_won = 0
                
                # Store additional metrics
                player_stats_record.avg_earnings_per_game = stats.get("average", 0)
                
                # Update timestamp
                player_stats_record.last_updated = datetime.now().isoformat()
                
                # Try to fetch GHIN data if player has GHIN ID
                ghin_data = None
                if existing_player and existing_player.ghin_id:
                    try:
                        from .services.ghin_service import GHINService
                        ghin_service = GHINService(db)
                        
                        # Check if GHIN service is available
                        if await ghin_service.initialize():
                            ghin_data = await ghin_service.sync_player_handicap(player_id)
                            if ghin_data:
                                # Update handicap from GHIN
                                existing_player.handicap = ghin_data.get('handicap_index', existing_player.handicap)
                                logger.info(f"Updated GHIN data for {player_name}: handicap={ghin_data.get('handicap_index')}")
                        else:
                            # Fall back to stored GHIN data
                            ghin_data = ghin_service.get_player_ghin_data(player_id)
                            if ghin_data:
                                logger.info(f"Using stored GHIN data for {player_name}")
                    except Exception as ghin_error:
                        logger.warning(f"Failed to fetch GHIN data for {player_name}: {ghin_error}")
                
                # Store GHIN data for response payload
                if ghin_data:
                    ghin_data_collection[player_name] = {
                        "ghin_id": ghin_data.get("ghin_id"),
                        "current_handicap": ghin_data.get("current_handicap"),
                        "recent_scores": ghin_data.get("recent_scores", [])[:5],  # Last 5 scores
                        "last_updated": ghin_data.get("last_updated")
                    }
                
                db.commit()
                
                sync_results["players_processed"] += 1
                
            except Exception as e:
                sync_results["errors"].append(f"Error processing {player_name}: {str(e)}")
                continue
        
        # Log summary of synced data
        logger.info(f"Synced {len(player_stats)} players from sheet")
        logger.info(f"Sync results: {sync_results}")
        
        # Return detailed sync information including the data that was synced
        return {
            "sync_results": sync_results,
            "player_count": len(player_stats),
            "synced_at": datetime.now().isoformat(),
            "headers_found": headers,
            "players_synced": list(player_stats.keys()),
            "sample_data": {name: stats for name, stats in list(player_stats.items())[:3]},  # First 3 players as sample
            "ghin_data": ghin_data_collection,  # GHIN scores and handicap data
            "ghin_players_count": len(ghin_data_collection)
        }
        
    except httpx.RequestError as e:
        logger.error(f"Error fetching Google Sheet: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch sheet: {str(e)}")
    except Exception as e:
        logger.error(f"Error syncing WGP sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync data: {str(e)}")
    finally:
        db.close()

# Admin endpoints for email configuration
@app.get("/admin/email-config")
def get_email_config(x_admin_email: str = Header(None)):
    """Get current email configuration (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Return current config (without password)
    return {
        "config": {
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": os.getenv("SMTP_PORT", "587"),
            "smtp_username": os.getenv("SMTP_USER", ""),
            "from_email": os.getenv("FROM_EMAIL", ""),
            "from_name": os.getenv("FROM_NAME", "Wolf Goat Pig Admin"),
            # Don't return password
            "smtp_password": "••••••••" if os.getenv("SMTP_PASSWORD") else ""
        }
    }

@app.post("/admin/email-config")
def update_email_config(config: Dict[str, Any], x_admin_email: str = Header(None)):
    """Update email configuration (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Update environment variables (in memory for this session)
        if config.get("smtp_host"):
            os.environ["SMTP_HOST"] = config["smtp_host"]
        if config.get("smtp_port"):
            os.environ["SMTP_PORT"] = str(config["smtp_port"])
        if config.get("smtp_username"):
            os.environ["SMTP_USER"] = config["smtp_username"]
        if config.get("smtp_password") and not config["smtp_password"].startswith("•"):
            os.environ["SMTP_PASSWORD"] = config["smtp_password"]
        if config.get("from_email"):
            os.environ["FROM_EMAIL"] = config["from_email"]
        if config.get("from_name"):
            os.environ["FROM_NAME"] = config["from_name"]
        
        # Reinitialize email service with new config
        global email_service_instance
        email_service_instance = None  # Reset to force reinitialization
        
        return {"status": "success", "message": "Email configuration updated"}
    except Exception as e:
        logger.error(f"Error updating email config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/test-email")
async def test_admin_email(request: Dict[str, Any], x_admin_email: str = Header(None)):
    """Send a test email with provided configuration (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        test_email = request.get("test_email")
        config = request.get("config", {})
        
        if not test_email:
            raise HTTPException(status_code=400, detail="Test email address required")
        
        # Temporarily apply config if provided
        if config:
            # Save current values
            old_config = {
                "SMTP_HOST": os.getenv("SMTP_HOST"),
                "SMTP_PORT": os.getenv("SMTP_PORT"),
                "SMTP_USER": os.getenv("SMTP_USER"),
                "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
                "FROM_EMAIL": os.getenv("FROM_EMAIL"),
                "FROM_NAME": os.getenv("FROM_NAME")
            }
            
            # Apply test config
            if config.get("smtp_host"):
                os.environ["SMTP_HOST"] = config["smtp_host"]
            if config.get("smtp_port"):
                os.environ["SMTP_PORT"] = str(config["smtp_port"])
            if config.get("smtp_username"):
                os.environ["SMTP_USER"] = config["smtp_username"]
            if config.get("smtp_password") and not config["smtp_password"].startswith("•"):
                os.environ["SMTP_PASSWORD"] = config["smtp_password"]
            if config.get("from_email"):
                os.environ["FROM_EMAIL"] = config["from_email"]
            if config.get("from_name"):
                os.environ["FROM_NAME"] = config["from_name"]
        
        # Create new email service with test config
        from .services.email_service import EmailService
        test_service = EmailService()
        
        if not test_service.is_configured:
            raise HTTPException(
                status_code=400,
                detail="Email service not configured. Please provide SMTP settings."
            )
        
        # Send test email
        success = test_service.send_test_email(
            to_email=test_email,
            admin_name=x_admin_email
        )
        
        # Restore original config if we changed it
        if config and 'old_config' in locals():
            for key, value in old_config.items():
                if value is not None:
                    os.environ[key] = value
                elif key in os.environ:
                    del os.environ[key]
        
        if success:
            return {"status": "success", "message": f"Test email sent to {test_email}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# OAuth2 Email endpoints
@app.get("/admin/oauth2-status")
def get_oauth2_status(x_admin_email: str = Header(None)):
    """Get OAuth2 configuration status (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        oauth2_service = get_oauth2_email_service()
        status = oauth2_service.get_configuration_status()
        return {"status": status}
    except Exception as e:
        logger.error(f"Error getting OAuth2 status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/oauth2-authorize")
def start_oauth2_authorization(request: Dict[str, Any], x_admin_email: str = Header(None)):
    """Start OAuth2 authorization flow (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        oauth2_service = get_oauth2_email_service()
        
        # Set from_email and from_name if provided
        if request.get("from_email"):
            oauth2_service.from_email = request["from_email"]
            os.environ["FROM_EMAIL"] = request["from_email"]
        if request.get("from_name"):
            oauth2_service.from_name = request["from_name"]
            os.environ["FROM_NAME"] = request["from_name"]
        
        # Let the service auto-detect the correct redirect URI
        # The redirect URI should point to the backend API, not the frontend
        auth_url = oauth2_service.get_auth_url()
        
        return {"auth_url": auth_url, "message": "Visit the auth_url to complete authorization"}
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=400,
            detail="Gmail credentials file not found. Please upload your Gmail API credentials file first."
        )
    except Exception as e:
        logger.error(f"Error starting OAuth2 authorization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/oauth2-callback")
def handle_oauth2_callback(code: str = Query(...), state: str = Query(None)):
    """Handle OAuth2 callback from Google"""
    try:
        oauth2_service = get_oauth2_email_service()
        success = oauth2_service.handle_oauth_callback(code)
        
        if success:
            # Return HTML page that will close the window and notify the parent
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth2 Authorization Complete</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                        text-align: center;
                        max-width: 400px;
                    }
                    h1 {
                        color: #4CAF50;
                        margin-bottom: 20px;
                    }
                    p {
                        color: #666;
                        margin-bottom: 20px;
                    }
                    .spinner {
                        border: 3px solid #f3f3f3;
                        border-top: 3px solid #4CAF50;
                        border-radius: 50%;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Authorization Successful!</h1>
                    <p>OAuth2 authorization has been completed successfully.</p>
                    <div class="spinner"></div>
                    <p>This window will close automatically...</p>
                </div>
                <script>
                    // Notify parent window if it exists
                    if (window.opener) {
                        window.opener.postMessage({ type: 'oauth2-success' }, '*');
                    }
                    // Close window after 2 seconds
                    setTimeout(() => {
                        window.close();
                    }, 2000);
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=200)
        else:
            # Return error HTML page
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth2 Authorization Failed</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                        text-align: center;
                        max-width: 400px;
                    }
                    h1 {
                        color: #f44336;
                        margin-bottom: 20px;
                    }
                    p {
                        color: #666;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Authorization Failed</h1>
                    <p>Failed to complete OAuth2 authorization.</p>
                    <p>Please close this window and try again.</p>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=400)
            
    except Exception as e:
        logger.error(f"Error handling OAuth2 callback: {e}")
        # Return error HTML page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OAuth2 Error</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                    text-align: center;
                    max-width: 400px;
                }}
                h1 {{
                    color: #f44336;
                    margin-bottom: 20px;
                }}
                p {{
                    color: #666;
                    margin-bottom: 10px;
                }}
                .error {{
                    background: #ffebee;
                    color: #c62828;
                    padding: 10px;
                    border-radius: 5px;
                    margin-top: 20px;
                    font-family: monospace;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ OAuth2 Error</h1>
                <p>An error occurred during OAuth2 authorization.</p>
                <div class="error">{str(e)}</div>
                <p>Please close this window and try again.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=500)

@app.post("/admin/oauth2-test-email")
async def test_oauth2_email(request: Dict[str, Any], x_admin_email: str = Header(None)):
    """Send test email using OAuth2 (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        test_email = request.get("test_email")
        if not test_email:
            raise HTTPException(status_code=400, detail="Test email address required")
        
        oauth2_service = get_oauth2_email_service()
        
        if not oauth2_service.is_configured:
            raise HTTPException(
                status_code=400,
                detail="OAuth2 email service not configured. Please complete OAuth2 authorization first."
            )
        
        success = oauth2_service.send_test_email(test_email, x_admin_email)
        
        if success:
            return {"status": "success", "message": f"Test email sent to {test_email} using OAuth2"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending OAuth2 test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/upload-credentials")
async def upload_gmail_credentials(file: UploadFile = File(...), x_admin_email: str = Header(None)):
    """Upload Gmail API credentials file (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be a JSON file")
        
        # Read and validate JSON content
        content = await file.read()
        credentials_data = json.loads(content)
        
        # Validate it's a Google OAuth2 credentials file
        if 'installed' not in credentials_data and 'web' not in credentials_data:
            raise HTTPException(
                status_code=400,
                detail="Invalid credentials file format. Please ensure it's a Google OAuth2 credentials file."
            )
        
        # Save credentials file
        oauth2_service = get_oauth2_email_service()
        with open(oauth2_service.credentials_path, 'w') as f:
            json.dump(credentials_data, f)
        
        return {"status": "success", "message": "Gmail credentials file uploaded successfully"}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading credentials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sheet-integration/fetch-google-sheet")
async def fetch_google_sheet(request: Dict[str, str]):
    """Fetch data from a Google Sheets CSV URL."""
    try:
        import httpx
        csv_url = request.get("csv_url")
        if not csv_url:
            raise HTTPException(status_code=400, detail="CSV URL is required")
        
        # Fetch the CSV data from Google Sheets (follow redirects)
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(csv_url, timeout=30)
            response.raise_for_status()
        
        csv_text = response.text
        
        # Parse CSV data
        lines = csv_text.strip().split('\n')
        if not lines:
            raise HTTPException(status_code=400, detail="Empty sheet data")
        
        headers = [h.strip().strip('"') for h in lines[0].split(',')]
        data = []
        
        for line in lines[1:]:
            if line.strip():
                values = [v.strip().strip('"') for v in line.split(',')]
                row = {}
                for i, header in enumerate(headers):
                    row[header] = values[i] if i < len(values) else ''
                data.append(row)
        
        return {
            "headers": headers,
            "data": data,
            "total_rows": len(data),
            "fetched_at": datetime.now().isoformat()
        }
        
    except httpx.RequestError as e:
        logger.error(f"Error fetching Google Sheet: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch sheet: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing Google Sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process sheet data: {str(e)}")

@app.post("/sheet-integration/compare-data")
def compare_sheet_with_database(sheet_data: List[Dict[str, Any]]):
    """Compare Google Sheet data with current database data."""
    try:
        db = database.SessionLocal()
        from .services.sheet_integration_service import SheetIntegrationService
        
        if not sheet_data:
            raise HTTPException(status_code=400, detail="Sheet data is required")
        
        # Extract headers from first row
        headers = list(sheet_data[0].keys())
        
        sheet_service = SheetIntegrationService(db)
        mappings = sheet_service.create_column_mappings(headers)
        
        # Get current database data in sheet format
        current_data = sheet_service.export_current_data_to_sheet_format(mappings)
        
        # Generate comparison report
        comparison_report = sheet_service.generate_sheet_comparison_report(
            current_data, sheet_data, mappings
        )
        
        return {
            "comparison_report": comparison_report,
            "compared_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error comparing sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare data: {str(e)}")
    finally:
        db.close()

# ============================================================================
# SIMULATION API ENDPOINTS
# ============================================================================

# Request/Response models for simulation endpoints
class SimulationSetupRequest(BaseModel):
    """Request model for simulation setup"""
    players: List[Dict[str, Any]]
    course_id: Optional[int] = None
    computer_players: Optional[List[str]] = []
    personalities: Optional[List[str]] = []
    game_options: Optional[Dict[str, Any]] = {}

class SimulationPlayShotRequest(BaseModel):
    """Request model for playing next shot"""
    decision: Optional[Dict[str, Any]] = {}

class SimulationPlayHoleRequest(BaseModel):
    """Request model for hole simulation decision"""
    decision: Dict[str, Any]

class BettingDecisionRequest(BaseModel):
    """Request model for betting decisions"""
    decision: Dict[str, Any]


def _get_current_hole_state():
    """Safely fetch the current hole state from the active simulation."""
    if not wgp_simulation:
        return None
    return wgp_simulation.hole_states.get(wgp_simulation.current_hole)


def _get_default_player_id(preferred_role: str = "captain") -> Optional[str]:
    """
    Provide a sensible default player identifier for legacy API calls that
    don't explicitly include a player context.
    """
    hole_state = _get_current_hole_state()
    if hole_state and getattr(hole_state, "teams", None):
        if preferred_role == "captain" and getattr(hole_state.teams, "captain", None):
            return hole_state.teams.captain
        if preferred_role == "solo" and getattr(hole_state.teams, "solo_player", None):
            return hole_state.teams.solo_player

    if wgp_simulation and getattr(wgp_simulation, "players", None):
        for player in wgp_simulation.players:
            if player.id == "human":
                return player.id
        return wgp_simulation.players[0].id if wgp_simulation.players else None
    return None


def _get_opposing_team_id(reference_player_id: Optional[str] = None) -> str:
    """
    Determine the opposing team identifier for double responses.
    Falls back to generic label when team structure is not yet established.
    """
    hole_state = _get_current_hole_state()
    if not hole_state or not getattr(hole_state, "teams", None):
        return "opponents"

    if hole_state.teams.type == "partners":
        team1 = set(hole_state.teams.team1 or [])
        team2 = set(hole_state.teams.team2 or [])

        if reference_player_id and reference_player_id in team1:
            return "team2"
        if reference_player_id and reference_player_id in team2:
            return "team1"
        return "team2" if team1 else "opponents"

    return "opponents"


def _get_pending_partnership_request() -> Dict[str, Any]:
    """Return any pending partnership request details from the current hole."""
    hole_state = _get_current_hole_state()
    if hole_state and getattr(hole_state, "teams", None):
        return hole_state.teams.pending_request or {}
    return {}


def _normalize_probabilities(probabilities: Dict[str, float]) -> Dict[str, float]:
    """Normalize probability buckets so they sum to ~1.0 and clamp negatives."""
    safe_probs = {k: max(0.0, float(v)) for k, v in probabilities.items()}
    total = sum(safe_probs.values())
    if total <= 0:
        bucket_count = len(safe_probs)
        if bucket_count == 0:
            return {}
        equal_share = 1.0 / bucket_count
        return {k: equal_share for k in safe_probs}
    return {k: v / total for k, v in safe_probs.items()}


def _compute_shot_probabilities(
    player_stats: Optional[Dict[str, Any]] = None,
    hole_info: Optional[Dict[str, Any]] = None,
    lie_type: Optional[str] = None
) -> Dict[str, float]:
    """Generate a balanced shot probability distribution based on context."""
    player_stats = player_stats or {}
    hole_info = hole_info or {}
    lie_type = (lie_type or hole_info.get("lie_type") or "").lower()

    base_distribution = {
        "excellent": 0.18,
        "good": 0.32,
        "average": 0.30,
        "poor": 0.15,
        "disaster": 0.05,
    }

    handicap = float(player_stats.get("handicap", 18) or 18)
    skill_delta = max(min((18 - handicap) / 40.0, 0.2), -0.2)
    base_distribution["excellent"] += skill_delta
    base_distribution["good"] += skill_delta * 0.5
    base_distribution["poor"] -= abs(skill_delta) * 0.4
    base_distribution["disaster"] = max(0.02, base_distribution["disaster"] - skill_delta * 0.3)

    difficulty = str(hole_info.get("difficulty", "medium")).lower()
    if difficulty in {"hard", "very hard", "difficult"}:
        base_distribution["excellent"] *= 0.75
        base_distribution["good"] *= 0.85
        base_distribution["poor"] *= 1.2
        base_distribution["disaster"] *= 1.3
    elif difficulty in {"easy", "very easy"}:
        base_distribution["excellent"] *= 1.15
        base_distribution["good"] *= 1.05
        base_distribution["poor"] *= 0.85
        base_distribution["disaster"] *= 0.75

    distance = hole_info.get("distance") or hole_info.get("distance_to_pin")
    if isinstance(distance, (int, float)):
        if distance < 100:
            base_distribution["excellent"] *= 1.1
            base_distribution["good"] *= 1.05
            base_distribution["poor"] *= 0.9
        elif distance > 200:
            base_distribution["excellent"] *= 0.85
            base_distribution["good"] *= 0.9
            base_distribution["poor"] *= 1.1
            base_distribution["disaster"] *= 1.15

    if lie_type in {"tee"}:
        base_distribution["excellent"] *= 1.2
        base_distribution["good"] *= 1.1
        base_distribution["poor"] *= 0.8
        base_distribution["disaster"] *= 0.6
    elif lie_type in {"rough", "deep_rough"}:
        base_distribution["excellent"] *= 0.7
        base_distribution["good"] *= 0.8
        base_distribution["poor"] *= 1.2
        base_distribution["disaster"] *= 1.3
    elif lie_type in {"bunker"}:
        base_distribution["excellent"] *= 0.6
        base_distribution["good"] *= 0.75
        base_distribution["poor"] *= 1.25
        base_distribution["disaster"] *= 1.4
    elif lie_type in {"green"}:
        base_distribution["excellent"] *= 1.4
        base_distribution["good"] *= 1.15
        base_distribution["poor"] *= 0.6
        base_distribution["disaster"] *= 0.4

    return _normalize_probabilities(base_distribution)

@app.post("/simulation/setup")
def setup_simulation(request: Dict[str, Any]):
    """Initialize a new simulation with specified players and configuration"""
    global wgp_simulation
    
    try:
        logger.info("Setting up new simulation...")
        
        # Handle both old and new request formats
        if 'human_player' in request and 'computer_players' in request:
            # Frontend format: { human_player, computer_players, course_name }
            human_player = request['human_player']
            computer_players = request['computer_players']
            course_name = request.get('course_name')
            
            # Combine into players list
            all_players = [human_player] + computer_players
        elif 'players' in request:
            # Backend format: { players, course_id, ... }
            all_players = request['players']
            course_name = request.get('course_name')
        else:
            raise HTTPException(status_code=400, detail="Missing player data")
        
        # Validate players
        if not all_players or len(all_players) < 4:
            raise HTTPException(status_code=400, detail="At least 4 players required")
        
        if len(all_players) > 6:
            raise HTTPException(status_code=400, detail="Maximum 6 players allowed")
        
        # Create WGPPlayer objects
        wgp_players = []
        for i, player_data in enumerate(all_players):
            wgp_player = WGPPlayer(
                id=player_data.get("id", f"player_{i+1}"),
                name=player_data.get("name", f"Player {i+1}"),
                handicap=float(player_data.get("handicap", 10))
            )
            wgp_players.append(wgp_player)
        
        # Initialize simulation with players
        wgp_simulation = WolfGoatPigSimulation(
            player_count=len(wgp_players),
            players=wgp_players
        )
        
        # Enhance with timeline tracking
        wgp_simulation = enhance_simulation_with_timeline(wgp_simulation)
        
        # Set computer players if specified
        if 'computer_players' in request and request['computer_players']:
            comp_players = request['computer_players']
            personalities = request.get('personalities', ["balanced"] * len(comp_players))
            wgp_simulation.set_computer_players(comp_players, personalities)
        
        # Load course if specified
        course_id = request.get('course_id')
        course_lookup_candidates = []
        if course_name:
            course_lookup_candidates.append(str(course_name))
        if course_id is not None:
            course_lookup_candidates.append(str(course_id))

        if course_lookup_candidates:
            selected_course_name = None
            try:
                courses = game_state.get_courses()
                if isinstance(courses, dict):
                    for candidate in course_lookup_candidates:
                        if candidate in courses:
                            selected_course_name = candidate
                            break
                        # Allow matching by case-insensitive name
                        for existing_name in courses.keys():
                            if existing_name.lower() == candidate.lower():
                                selected_course_name = existing_name
                                break
                        if selected_course_name:
                            break
                if selected_course_name:
                    logger.info(f"Using course: {selected_course_name}")
                    try:
                        game_state.course_manager.load_course(selected_course_name)
                    except Exception as load_error:
                        logger.warning(f"Failed to load course '{selected_course_name}': {load_error}")
                else:
                    logger.warning(f"Course not found: {course_lookup_candidates[0]}")
            except Exception as course_error:
                logger.warning(f"Could not load course {course_lookup_candidates[0]}: {course_error}")
        
        # Initialize hole 1
        wgp_simulation._initialize_hole(1)
        wgp_simulation.enable_shot_progression()
        
        # Get initial game state
        game_state_data = wgp_simulation.get_game_state()
        
        logger.info("Simulation setup completed successfully")
        
        return {
            "status": "ok",
            "message": "Simulation initialized successfully",
            "game_state": game_state_data,
            "players": [
                {
                    "id": p.id,
                    "name": p.name, 
                    "handicap": p.handicap,
                    "points": p.points
                } for p in wgp_simulation.players
            ],
            "current_hole": wgp_simulation.current_hole,
            "next_shot_available": True,  # After setup, first shot is always available
            "feedback": ["🎮 Game started! You're on the first tee."]
        }
        
    except Exception as e:
        logger.error(f"Simulation setup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to setup simulation: {str(e)}")

@app.post("/simulation/play-next-shot")
def play_next_shot(request: SimulationPlayShotRequest = None):
    """Simulate the next shot in the current hole"""
    global wgp_simulation
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized. Call /simulation/setup first.")
        
        # Get next player to shoot
        next_player = wgp_simulation._get_next_shot_player()
        if not next_player:
            raise HTTPException(status_code=400, detail="No player available to shoot")
        
        # Simulate the shot
        shot_response = wgp_simulation.simulate_shot(next_player)
        
        # Get updated game state
        updated_state = wgp_simulation.get_game_state()
        
        # Get next shot player info
        next_shot_player = wgp_simulation._get_next_shot_player()
        next_player_name = wgp_simulation._get_player_name(next_shot_player) if next_shot_player else None
        
        # Check if there's another shot available
        hole_complete = updated_state.get("hole_complete", False)
        next_shot_available = not hole_complete and next_shot_player is not None
        
        # Build readable feedback messages from shot data
        feedback = []
        if shot_response:
            # Extract shot data
            shot_data = shot_response.get('shot_result', {})
            player_id = shot_data.get('player_id', 'player')
            
            # Get player display name
            player_name = 'Player'
            for player in wgp_simulation.players:
                if player.id == player_id:
                    player_name = player.name
                    break
            
            # Extract shot details
            distance_to_pin = shot_data.get('distance_to_pin', 0)
            shot_quality = shot_data.get('shot_quality', 'unknown')
            shot_number = shot_data.get('shot_number', 1)
            lie_type = shot_data.get('lie_type', 'unknown')
            
            # Create readable feedback
            feedback.append(f"🏌️ {player_name} hits {shot_quality} shot from {lie_type} - {round(distance_to_pin)}yd to pin")
            
            # Add shot assessment
            if shot_quality == 'excellent':
                feedback.append(f"🎯 Great shot! {player_name} is in excellent position")
            elif shot_quality == 'poor':
                feedback.append(f"😬 Tough break for {player_name}, recovery shot needed")
        
        return {
            "status": "ok",
            "success": True,
            "shot_result": shot_response,
            "game_state": updated_state,
            "next_player": next_player_name,
            "hole_complete": hole_complete,
            "next_shot_available": next_shot_available,
            "feedback": feedback
        }
        
    except Exception as e:
        logger.error(f"Play next shot failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to play next shot: {str(e)}")

@app.post("/simulation/play-hole")
def simulate_hole(request: Dict[str, Any] = Body(default_factory=dict)):
    """Process in-hole decisions or simulate an entire hole when no action supplied"""
    global wgp_simulation
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized. Call /simulation/setup first.")
        
        payload = request or {}
        if isinstance(payload.get("decision"), dict):
            payload = {**payload, **payload["decision"]}
        
        action = payload.get("action")
        if not action:
            if payload.get("accept_partnership") is True:
                action = "accept_partnership"
            elif payload.get("accept_partnership") is False:
                action = "decline_partnership"
            elif payload.get("accept_double") is True:
                action = "accept_double"
            elif payload.get("decline_double") is True:
                action = "decline_double"
            elif payload.get("offer_double"):
                action = "offer_double"
        
        interaction_needed = None
        result: Dict[str, Any] = {}
        
        if action:
            hole_state = _get_current_hole_state()
            captain_id = payload.get("captain_id") or payload.get("player_id") or _get_default_player_id()
            
            if action == "request_partner":
                partner_id = payload.get("partner_id") or payload.get("requested_partner")
                if not partner_id:
                    raise HTTPException(status_code=400, detail="Partner ID required for partnership request")
                if not captain_id:
                    raise HTTPException(status_code=400, detail="Captain ID required for partnership request")
                
                result = wgp_simulation.request_partner(captain_id, partner_id)
                interaction_needed = {
                    "type": "partnership_response",
                    "requested_partner": partner_id,
                    "captain_id": captain_id
                }
            
            elif action in ("accept_partnership", "decline_partnership"):
                pending_request = _get_pending_partnership_request()
                partner_id = payload.get("partner_id") or pending_request.get("requested")
                if not partner_id:
                    raise HTTPException(status_code=400, detail="No pending partnership request to resolve")
                accept = action == "accept_partnership"
                result = wgp_simulation.respond_to_partnership(partner_id, accept)
            
            elif action in ("go_solo", "captain_go_solo"):
                if not captain_id:
                    raise HTTPException(status_code=400, detail="Captain ID required for solo decision")
                result = wgp_simulation.captain_go_solo(captain_id)
            
            elif action == "offer_double":
                if not captain_id:
                    raise HTTPException(status_code=400, detail="Player ID required to offer double")
                result = wgp_simulation.offer_double(captain_id)
                interaction_needed = {
                    "type": "double_response",
                    "offering_player": captain_id
                }
            
            elif action in ("accept_double", "decline_double"):
                offer_history = []
                if hole_state and getattr(hole_state, "betting", None):
                    offer_history = hole_state.betting.doubles_history or []
                offering_player = None
                if offer_history:
                    offering_player = offer_history[-1].get("offering_player")
                offering_player = offering_player or payload.get("offering_player")
                
                responding_team = payload.get("team_id") or _get_opposing_team_id(offering_player or captain_id)
                accept = action == "accept_double"
                result = wgp_simulation.respond_to_double(responding_team, accept)
            
            else:
                result = {"status": "unsupported_action", "message": f"Action '{action}' not recognized"}
        
        else:
            hole_results = []
            max_shots = 20  # Safety limit
            shot_count = 0
            
            while shot_count < max_shots:
                next_player = wgp_simulation._get_next_shot_player()
                if not next_player:
                    break
                    
                shot_response = wgp_simulation.simulate_shot(next_player)
                hole_results.append(shot_response)
                shot_count += 1
                
                game_state_data = wgp_simulation.get_game_state()
                if game_state_data.get("hole_complete", False):
                    break
            
            updated_state = wgp_simulation.get_game_state()
            return {
                "success": True,
                "hole_results": hole_results,
                "game_state": updated_state,
                "shots_played": shot_count
            }
        
        updated_state = wgp_simulation.get_game_state()
        if interaction_needed is None:
            pending_request = _get_pending_partnership_request()
            if pending_request:
                interaction_needed = {
                    "type": "partnership_response",
                    "requested_partner": pending_request.get("requested"),
                    "captain_id": pending_request.get("captain")
                }
        
        return {
            "success": True,
            "result": result,
            "game_state": updated_state,
            "interaction_needed": interaction_needed,
            "hole_complete": updated_state.get("hole_complete", False)
        }
        
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Hole simulation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to simulate hole: {str(e)}")


if ENABLE_TEST_ENDPOINTS:

    @app.post("/simulation/test/seed-state")
    def seed_simulation_state(payload: SimulationSeedRequest, x_admin_email: Optional[str] = Header(None)):
        """Testing-only helper for seeding the current simulation state.

        Allows BDD and backend tests to manipulate the in-memory simulation using
        the public HTTP API instead of reaching into the global simulation object.
        """

        global wgp_simulation

        require_admin(x_admin_email)

        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized. Call /simulation/setup first.")

        if payload.current_hole is not None:
            if payload.current_hole not in wgp_simulation.hole_states:
                try:
                    wgp_simulation._initialize_hole(payload.current_hole)
                except Exception as exc:  # pragma: no cover - defensive fallback
                    raise HTTPException(status_code=500, detail=f"Failed to initialise hole {payload.current_hole}: {exc}") from exc
            wgp_simulation.current_hole = payload.current_hole

        hole_state = _get_current_hole_state()
        if not hole_state:
            raise HTTPException(status_code=400, detail="No active hole to seed")

        player_ids = {player.id for player in wgp_simulation.players}

        # Seed ball positions
        if payload.ball_positions:
            if payload.ball_positions_replace:
                hole_state.ball_positions.clear()

            if payload.clear_balls_in_hole:
                hole_state.balls_in_hole = []

            for seed in payload.ball_positions:
                if seed.player_id not in player_ids:
                    raise HTTPException(status_code=422, detail=f"Unknown player id '{seed.player_id}'")

                ball = BallPosition(
                    player_id=seed.player_id,
                    distance_to_pin=seed.distance_to_pin,
                    lie_type=seed.lie_type,
                    shot_count=seed.shot_count,
                    penalty_strokes=seed.penalty_strokes,
                )
                ball.holed = seed.holed
                ball.conceded = seed.conceded

                hole_state.ball_positions[seed.player_id] = ball

                if seed.holed:
                    if seed.player_id not in hole_state.balls_in_hole:
                        hole_state.balls_in_hole.append(seed.player_id)
                elif seed.player_id in hole_state.balls_in_hole:
                    hole_state.balls_in_hole.remove(seed.player_id)

        # Update ordering metadata
        if payload.line_of_scrimmage is not None:
            if payload.line_of_scrimmage and payload.line_of_scrimmage not in player_ids:
                raise HTTPException(status_code=422, detail=f"Unknown line of scrimmage player '{payload.line_of_scrimmage}'")
            hole_state.line_of_scrimmage = payload.line_of_scrimmage
            if payload.betting is None:
                hole_state.betting.line_of_scrimmage = payload.line_of_scrimmage

        if payload.current_order_of_play is not None:
            unknown = [pid for pid in payload.current_order_of_play if pid not in player_ids]
            if unknown:
                raise HTTPException(status_code=422, detail=f"Unknown players in order of play: {', '.join(unknown)}")
            hole_state.current_order_of_play = payload.current_order_of_play

        if payload.shot_order is not None:
            unknown = [pid for pid in payload.shot_order if pid not in player_ids]
            if unknown:
                raise HTTPException(status_code=422, detail=f"Unknown players in shot order: {', '.join(unknown)}")
            hole_state.hitting_order = payload.shot_order

        if payload.next_player_to_hit is not None:
            if payload.next_player_to_hit and payload.next_player_to_hit not in player_ids:
                raise HTTPException(status_code=422, detail=f"Unknown next player '{payload.next_player_to_hit}'")
            hole_state.next_player_to_hit = payload.next_player_to_hit

        if payload.wagering_closed is not None:
            hole_state.wagering_closed = payload.wagering_closed

        if payload.betting:
            betting = hole_state.betting
            updates = payload.betting.dict(exclude_unset=True)
            line_of_scrimmage = updates.pop("line_of_scrimmage", None)
            if line_of_scrimmage is not None:
                if line_of_scrimmage and line_of_scrimmage not in player_ids:
                    raise HTTPException(status_code=422, detail=f"Unknown line of scrimmage player '{line_of_scrimmage}'")
                hole_state.line_of_scrimmage = line_of_scrimmage
                betting.line_of_scrimmage = line_of_scrimmage

            for key, value in updates.items():
                setattr(betting, key, value)

        if payload.team_formation:
            formation_data = payload.team_formation
            hole_state.teams = TeamFormation(
                type=formation_data.get("type", hole_state.teams.type),
                captain=formation_data.get("captain", hole_state.teams.captain),
                second_captain=formation_data.get("second_captain", hole_state.teams.second_captain),
                team1=formation_data.get("team1", hole_state.teams.team1),
                team2=formation_data.get("team2", hole_state.teams.team2),
                team3=formation_data.get("team3", hole_state.teams.team3),
                solo_player=formation_data.get("solo_player", hole_state.teams.solo_player),
                opponents=formation_data.get("opponents", hole_state.teams.opponents),
                pending_request=formation_data.get("pending_request", hole_state.teams.pending_request),
            )

        if payload.reset_doubles_history:
            hole_state.betting.doubles_history = []

        return {
            "status": "seeded",
            "game_state": wgp_simulation.get_game_state(),
        }


@app.get("/simulation/state")
def get_simulation_state(x_admin_email: Optional[str] = Header(None)):
    """Return the current simulation state for diagnostics and testing."""
    global wgp_simulation

    if not ENABLE_TEST_ENDPOINTS:
        raise HTTPException(status_code=404, detail="Not found")

    require_admin(x_admin_email)

    if not wgp_simulation:
        raise HTTPException(status_code=404, detail="Simulation not initialized")

    try:
        return wgp_simulation.get_game_state()
    except Exception as exc:  # pragma: no cover
        logger.error(f"Failed to fetch simulation state: {exc}")
        raise HTTPException(status_code=500, detail="Failed to fetch simulation state")

@app.get("/simulation/available-personalities")
def get_available_personalities():
    """Get list of available AI personality types"""
    try:
        personalities = [
            {
                "id": "aggressive",
                "name": "Aggressive",
                "description": "Takes risks, goes for bold shots and betting decisions"
            },
            {
                "id": "conservative", 
                "name": "Conservative",
                "description": "Plays it safe, avoids risky bets and shots"
            },
            {
                "id": "balanced",
                "name": "Balanced",
                "description": "Balanced approach to risk and reward"
            },
            {
                "id": "strategic",
                "name": "Strategic", 
                "description": "Focuses on long-term game positioning"
            },
            {
                "id": "maverick",
                "name": "Maverick",
                "description": "Unpredictable playing style, keeps opponents guessing"
            }
        ]
        
        return {
            "status": "ok",
            "success": True,
            "personalities": personalities
        }
        
    except Exception as e:
        logger.error(f"Failed to get personalities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get personalities: {str(e)}")

# Legacy endpoints for frontend compatibility - return direct arrays
@app.get("/personalities")
def get_personalities_legacy():
    """Legacy endpoint for personalities - returns direct array for frontend compatibility"""
    try:
        personalities = [
            {"id": "aggressive", "name": "Aggressive"},
            {"id": "conservative", "name": "Conservative"},
            {"id": "balanced", "name": "Balanced"},
            {"id": "strategic", "name": "Strategic"},
            {"id": "maverick", "name": "Maverick"}
        ]
        return personalities
    except Exception as e:
        logger.error(f"Failed to get personalities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get personalities: {str(e)}")

@app.get("/suggested_opponents") 
def get_suggested_opponents_legacy():
    """Legacy endpoint for suggested opponents - returns direct array for frontend compatibility"""
    try:
        # Return array of individual players, not grouped opponents
        opponents = [
            {"name": "Clive", "handicap": "8", "personality": "aggressive"},
            {"name": "Gary", "handicap": "12", "personality": "conservative"}, 
            {"name": "Bernard", "handicap": "15", "personality": "strategic"},
            {"name": "Alex", "handicap": "5", "personality": "balanced"},
            {"name": "Sam", "handicap": "18", "personality": "maverick"},
            {"name": "Jordan", "handicap": "22", "personality": "conservative"},
            {"name": "Ace", "handicap": "3", "personality": "aggressive"},
            {"name": "Blade", "handicap": "6", "personality": "aggressive"},
            {"name": "Chase", "handicap": "9", "personality": "strategic"}
        ]
        return opponents
    except Exception as e:
        logger.error(f"Failed to get suggested opponents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggested opponents: {str(e)}")

@app.get("/simulation/suggested-opponents")
def get_suggested_opponents():
    """Get list of suggested AI opponent configurations"""
    try:
        opponents = [
            {
                "id": "classic_quartet",
                "name": "Classic Quartet",
                "description": "Traditional Wolf Goat Pig characters",
                "players": [
                    {"name": "Clive", "handicap": 8, "personality": "aggressive"},
                    {"name": "Gary", "handicap": 12, "personality": "conservative"},
                    {"name": "Bernard", "handicap": 15, "personality": "strategic"}
                ]
            },
            {
                "id": "mixed_bag",
                "name": "Mixed Bag",
                "description": "Diverse skill levels and personalities",
                "players": [
                    {"name": "Alex", "handicap": 5, "personality": "balanced"},
                    {"name": "Sam", "handicap": 18, "personality": "maverick"},
                    {"name": "Jordan", "handicap": 22, "personality": "conservative"}
                ]
            },
            {
                "id": "high_rollers",
                "name": "High Rollers", 
                "description": "Aggressive betting and low handicaps",
                "players": [
                    {"name": "Ace", "handicap": 3, "personality": "aggressive"},
                    {"name": "Blade", "handicap": 6, "personality": "aggressive"},
                    {"name": "Chase", "handicap": 9, "personality": "strategic"}
                ]
            }
        ]
        
        return {
            "status": "ok",
            "success": True,
            "opponents": opponents
        }
        
    except Exception as e:
        logger.error(f"Failed to get suggested opponents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get suggested opponents: {str(e)}")

@app.get("/simulation/shot-probabilities")  
def get_shot_probabilities():
    """Get current shot outcome probabilities for the active player"""
    global wgp_simulation
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized")
        
        # Get next player to shoot
        next_player = wgp_simulation._get_next_shot_player()
        if not next_player:
            return {"success": True, "probabilities": {}}
        
        # Get current hole state
        hole_state = _get_current_hole_state()
        if not hole_state:
            return {"success": True, "probabilities": {}}
        
        # Get player's current ball position
        ball_position = hole_state.get_player_ball_position(next_player)
        
        player_obj = next((p for p in wgp_simulation.players if p.id == next_player), None)
        hole_info = {
            "difficulty": getattr(hole_state, "hole_difficulty", "medium"),
            "par": getattr(hole_state, "hole_par", 4),
            "distance": getattr(ball_position, "distance_to_pin", None)
        }
        probabilities = _compute_shot_probabilities(
            player_stats={"handicap": getattr(player_obj, "handicap", 18)} if player_obj else None,
            hole_info=hole_info,
            lie_type=getattr(ball_position, "lie_type", None)
        )

        return {
            "success": True,
            "probabilities": probabilities,
            "player_id": next_player,
            "ball_position": {
                "lie_type": ball_position.lie_type if ball_position else "unknown",
                "distance_to_pin": ball_position.distance_to_pin if ball_position else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get shot probabilities: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get shot probabilities: {str(e)}")


@app.post("/simulation/shot-probabilities")
def calculate_shot_probabilities(payload: Dict[str, Any]):
    """Calculate shot probabilities for arbitrary scenarios (used by tests/tools)"""
    try:
        player_stats = payload.get("player_stats") or {}
        hole_info = payload.get("hole_info") or {}
        lie_type = payload.get("lie_type")
        
        probabilities = _compute_shot_probabilities(player_stats, hole_info, lie_type)
        insights = []
        if player_stats.get("handicap") is not None:
            handicap = float(player_stats["handicap"])
            if handicap <= 10:
                insights.append("Low handicap boosts excellent shot odds.")
            elif handicap >= 20:
                insights.append("Higher handicap reduces premium shot outcomes.")
        
        difficulty = str(hole_info.get("difficulty", "")).lower()
        if difficulty in {"hard", "very hard", "difficult"}:
            insights.append("Difficult hole increases chance of poor or disaster outcomes.")
        elif difficulty in {"easy", "very easy"}:
            insights.append("Easier hole improves strong shot percentages.")
        
        return {
            "success": True,
            "probabilities": probabilities,
            "insights": insights
        }
    except Exception as exc:
        logger.error(f"Shot probability calculation failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate shot probabilities: {str(exc)}")

@app.post("/simulation/betting-decision")
def make_betting_decision(request: Dict[str, Any]):
    """Process a betting decision in the simulation with poker-style actions"""
    global wgp_simulation
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized")
        
        # Handle both old format and new format
        decision = request['decision'] if isinstance(request, dict) and 'decision' in request else request
        
        action = decision.get("action")
        decision_type = decision.get("type") or decision.get("decision_type")
        if action and not decision_type:
            legacy_action_map = {
                "request_partner": "partnership_request",
                "accept_partnership": "partnership_response",
                "decline_partnership": "partnership_response",
                "offer_double": "double_offer",
                "accept_double": "double_response",
                "decline_double": "double_response",
                "go_solo": "go_solo",
            }
            decision_type = legacy_action_map.get(action, action)
        
        player_id = decision.get("player_id") or decision.get("captain_id") or _get_default_player_id()
        
        result = {"success": False, "message": "Unknown decision type"}
        interaction_needed = None
        
        # Process different types of betting decisions
        if decision_type == "partnership_request":
            partner_id = decision.get("partner_id")
            if not partner_id:
                partner_id = decision.get("requested_partner")
            if partner_id:
                if not player_id:
                    raise HTTPException(status_code=400, detail="Captain player_id required for partnership request")
                result = wgp_simulation.request_partner(player_id, partner_id)
                interaction_needed = {
                    "type": "partnership_response",
                    "requested_partner": partner_id,
                    "captain_id": player_id
                }
                
        elif decision_type == "partnership_response":
            partner_id = decision.get("partner_id") or decision.get("requested_partner")
            if not partner_id:
                pending = _get_pending_partnership_request()
                partner_id = pending.get("requested")
            if not partner_id:
                raise HTTPException(status_code=400, detail="No pending partnership request to resolve")
            accept = decision.get("accept", decision.get("accept_partnership", action == "accept_partnership"))
            result = wgp_simulation.respond_to_partnership(partner_id, bool(accept))
            
        elif decision_type == "double_offer":
            if not player_id:
                raise HTTPException(status_code=400, detail="player_id required to offer a double")
            result = wgp_simulation.offer_double(player_id)
            interaction_needed = {
                "type": "double_response",
                "offering_player": player_id
            }
            
        elif decision_type == "double_response":
            accept = decision.get("accept", decision.get("accept_double", action == "accept_double"))
            hole_state = _get_current_hole_state()
            offer_history = []
            if hole_state and getattr(hole_state, "betting", None):
                offer_history = hole_state.betting.doubles_history or []
            offering_player = decision.get("offering_player")
            if not offering_player and offer_history:
                offering_player = offer_history[-1].get("offering_player")
            responding_team = decision.get("team_id") or _get_opposing_team_id(offering_player or player_id)
            result = wgp_simulation.respond_to_double(responding_team, bool(accept))
            
        elif decision_type == "go_solo":
            if not player_id:
                raise HTTPException(status_code=400, detail="player_id required for go_solo decision")
            result = wgp_simulation.captain_go_solo(player_id)
            
        # Get updated game state
        updated_state = wgp_simulation.get_game_state()
        
        return {
            "success": True,
            "decision_result": result,
            "game_state": updated_state,
            "interaction_needed": interaction_needed
        }
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Betting decision failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process betting decision: {str(e)}")

@app.post("/simulation/next-hole")
def advance_simulation_hole():
    """Advance to the next hole in the simulation"""
    global wgp_simulation

    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized")

        # Check if current hole is complete
        current_hole_state = wgp_simulation.hole_states.get(wgp_simulation.current_hole)
        if current_hole_state and not current_hole_state.hole_complete:
            raise HTTPException(
                status_code=400,
                detail=f"Current hole {wgp_simulation.current_hole} is not complete yet"
            )

        # Advance to next hole (this handles both hole advancement and game completion)
        result = wgp_simulation.advance_to_next_hole()

        # Get updated game state
        game_state = wgp_simulation.get_game_state()

        # Prepare feedback messages
        feedback = []
        if result.get("status") == "game_finished":
            # Game is complete
            winners = result.get("winner_names", [])
            if len(winners) == 1:
                feedback.append(f"🏆 Round Complete! {winners[0]} wins the round!")
            else:
                feedback.append(f"🏆 Round Complete! Tie between {', '.join(winners)}!")
            feedback.append(f"Final scores: {result.get('final_scores', {})}")
        else:
            # Moved to next hole
            feedback.append(f"⛳ Advancing to Hole {result.get('current_hole', wgp_simulation.current_hole)}")
            hole_info = game_state.get("hole_info", {})
            if hole_info:
                feedback.append(
                    f"Hole {hole_info.get('number')}: Par {hole_info.get('par')}, {hole_info.get('distance', 0)} yards"
                )

        return {
            "status": "ok",
            "result": result,
            "game_state": game_state,
            "feedback": feedback,
            "next_shot_available": result.get("status") != "game_finished",
            "game_finished": result.get("status") == "game_finished"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to advance hole: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to advance to next hole: {str(e)}")

@app.get("/simulation/post-hole-analytics/{hole_number}")
def get_post_hole_analytics(hole_number: int):
    """Get comprehensive post-hole analytics for learning and improvement"""
    global wgp_simulation, post_hole_analyzer
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized")
        
        # Get hole state
        hole_state = wgp_simulation.hole_states.get(hole_number)
        if not hole_state:
            raise HTTPException(status_code=404, detail=f"Hole {hole_number} not found")
        
        # Check if hole is complete
        if not hole_state.hole_complete:
            raise HTTPException(status_code=400, detail=f"Hole {hole_number} is not complete yet")
        
        # Get game state and timeline events
        game_state = wgp_simulation.get_game_state()
        timeline_events = []
        if hasattr(wgp_simulation, 'hole_progression') and wgp_simulation.hole_progression:
            timeline_events = wgp_simulation.hole_progression.timeline_events
        
        # Generate analytics
        analytics = post_hole_analyzer.analyze_hole(hole_state, game_state, timeline_events)
        
        # Convert to dict for JSON response
        analytics_dict = {
            "hole_number": analytics.hole_number,
            "hole_par": analytics.hole_par,
            "hole_yardage": analytics.hole_yardage,
            "winner": analytics.winner,
            "quarters_exchanged": analytics.quarters_exchanged,
            "final_scores": analytics.final_scores,
            "decision_points": [
                {
                    "decision_type": dp.decision_type,
                    "player_id": dp.player_id,
                    "timestamp": dp.timestamp,
                    "options_available": dp.options_available,
                    "decision_made": dp.decision_made,
                    "outcome": dp.outcome,
                    "quarters_impact": dp.quarters_impact,
                    "quality": dp.quality.value,
                    "explanation": dp.explanation
                }
                for dp in analytics.decision_points
            ],
            "partnership_analysis": {
                "partnership_formed": analytics.partnership_analysis.partnership_formed,
                "captain_id": analytics.partnership_analysis.captain_id,
                "partner_id": analytics.partnership_analysis.partner_id,
                "timing": analytics.partnership_analysis.timing,
                "success": analytics.partnership_analysis.success,
                "chemistry_rating": analytics.partnership_analysis.chemistry_rating,
                "alternative_partners": analytics.partnership_analysis.alternative_partners,
                "optimal_choice": analytics.partnership_analysis.optimal_choice,
                "explanation": analytics.partnership_analysis.explanation
            } if analytics.partnership_analysis else None,
            "betting_analysis": {
                "doubles_offered": analytics.betting_analysis.doubles_offered,
                "doubles_accepted": analytics.betting_analysis.doubles_accepted,
                "doubles_declined": analytics.betting_analysis.doubles_declined,
                "duncan_used": analytics.betting_analysis.duncan_used,
                "timing_quality": analytics.betting_analysis.timing_quality,
                "aggressive_rating": analytics.betting_analysis.aggressive_rating,
                "missed_opportunities": analytics.betting_analysis.missed_opportunities,
                "costly_mistakes": analytics.betting_analysis.costly_mistakes,
                "net_quarter_impact": analytics.betting_analysis.net_quarter_impact
            },
            "shot_analysis": {
                "total_shots": analytics.shot_analysis.total_shots,
                "shot_quality_distribution": analytics.shot_analysis.shot_quality_distribution,
                "clutch_shots": analytics.shot_analysis.clutch_shots,
                "worst_shot": analytics.shot_analysis.worst_shot,
                "best_shot": analytics.shot_analysis.best_shot,
                "pressure_performance": analytics.shot_analysis.pressure_performance
            },
            "key_moments": [
                {
                    "description": km.description,
                    "impact": km.impact,
                    "quarters_swing": km.quarters_swing,
                    "player_involved": km.player_involved,
                    "timestamp": km.timestamp
                }
                for km in analytics.key_moments
            ],
            "biggest_mistake": analytics.biggest_mistake,
            "best_decision": analytics.best_decision,
            "learning_points": analytics.learning_points,
            "overall_performance": analytics.overall_performance,
            "decision_making_score": analytics.decision_making_score,
            "risk_management_score": analytics.risk_management_score,
            "ai_comparison": analytics.ai_comparison,
            "historical_comparison": analytics.historical_comparison,
            "tips_for_improvement": analytics.tips_for_improvement,
            "similar_scenarios_to_practice": analytics.similar_scenarios_to_practice
        }
        
        return analytics_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating post-hole analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/simulation/turn-based-state")
def get_turn_based_state():
    """Get structured turn-based game state for Wolf Goat Pig"""
    global wgp_simulation
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized")
        
        current_hole = wgp_simulation.current_hole
        hole_state = wgp_simulation.hole_states.get(current_hole)
        
        if not hole_state:
            return {"success": False, "message": "No active hole"}
        
        # Determine current game phase
        phase = "setup"
        if hole_state.teams.type == "pending":
            phase = "captain_selection"
        elif hole_state.teams.pending_request:
            phase = "partnership_decision"
        elif hole_state.teams.type in ["partners", "solo"]:
            phase = "match_play"
        
        # Get captain information
        captain_id = hole_state.teams.captain
        captain_player = None
        if captain_id:
            captain_player = next((p for p in wgp_simulation.players if p.id == captain_id), None)
        
        # Get rotation order for this hole
        rotation_order = getattr(hole_state, 'rotation_order', [p.id for p in wgp_simulation.players])
        
        # Get shots played
        shots_played = []
        for player_id, position in hole_state.ball_positions.items():
            shots_played.append({
                "player_id": player_id,
                "shot_number": position.shot_count,
                "distance_to_pin": position.distance_to_pin,
                "lie_type": position.lie_type,
                "holed": position.holed
            })
        
        # Determine whose turn it is for decisions or shots
        current_turn = None
        furthest_player = None
        
        if phase == "match_play":
            # Find furthest from hole for shot order
            max_distance = -1
            for player_id, pos in hole_state.ball_positions.items():
                if not pos.holed and pos.distance_to_pin > max_distance:
                    max_distance = pos.distance_to_pin
                    furthest_player = next((p for p in wgp_simulation.players if p.id == player_id), None)
            current_turn = furthest_player.id if furthest_player else None
        
        # Get pending decision info
        pending_decision = None
        if hole_state.teams.pending_request:
            pending_decision = {
                "type": "partnership_request",
                "from_player": hole_state.teams.pending_request.get("requestor"),
                "to_player": hole_state.teams.pending_request.get("requested"),
                "message": f"Partnership requested by {wgp_simulation._get_player_name(hole_state.teams.pending_request.get('requestor'))}"
            }
        
        # Check for betting opportunities
        betting_opportunities = []
        if phase == "match_play" and not hole_state.betting.doubled:
            # Check Line of Scrimmage rule
            line_of_scrimmage_player = furthest_player.id if furthest_player else None
            betting_opportunities.append({
                "type": "double_offer",
                "available": True,
                "line_of_scrimmage": line_of_scrimmage_player,
                "current_wager": hole_state.betting.current_wager,
                "potential_wager": hole_state.betting.current_wager * 2
            })
        
        # Get team formations
        teams_display = []
        if hole_state.teams.type == "partners":
            team1_names = [wgp_simulation._get_player_name(pid) for pid in hole_state.teams.team1]
            team2_names = [wgp_simulation._get_player_name(pid) for pid in hole_state.teams.team2]
            teams_display.append({
                "type": "partnership",
                "description": f"{' & '.join(team1_names)} vs {' & '.join(team2_names)}"
            })
        elif hole_state.teams.type == "solo":
            solo_name = wgp_simulation._get_player_name(hole_state.teams.solo_player)
            opponent_names = [wgp_simulation._get_player_name(pid) for pid in hole_state.teams.opponents]
            teams_display.append({
                "type": "solo",
                "description": f"{solo_name} (Solo) vs {', '.join(opponent_names)}"
            })
        
        return {
            "success": True,
            "turn_based_state": {
                "current_hole": current_hole,
                "phase": phase,
                "current_turn": current_turn,
                "captain_id": captain_id,
                "captain_name": captain_player.name if captain_player else None,
                "rotation_order": rotation_order,
                "teams": teams_display,
                "betting": {
                    "current_wager": hole_state.betting.current_wager,
                    "base_wager": hole_state.betting.base_wager,
                    "doubled": hole_state.betting.doubled,
                    "in_hole": any(pos.holed for pos in hole_state.ball_positions.values())
                },
                "pending_decision": pending_decision,
                "betting_opportunities": betting_opportunities,
                "shots_played": shots_played,
                "ball_positions": [
                    {
                        "player_id": player_id,
                        "player_name": wgp_simulation._get_player_name(player_id),
                        "distance_to_pin": pos.distance_to_pin,
                        "lie_type": pos.lie_type,
                        "shot_count": pos.shot_count,
                        "holed": pos.holed
                    } for player_id, pos in hole_state.ball_positions.items()
                ],
                "furthest_from_hole": {
                    "player_id": furthest_player.id if furthest_player else None,
                    "player_name": furthest_player.name if furthest_player else None,
                    "distance": max_distance if furthest_player else None
                } if furthest_player else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get turn-based state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get turn-based state: {str(e)}")

@app.get("/simulation/timeline")
def get_simulation_timeline(limit: int = 20):
    """Get timeline events in reverse chronological order"""
    global wgp_simulation
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized")
        
        # Get timeline events from the simulation
        if hasattr(wgp_simulation, 'timeline_manager'):
            events = wgp_simulation.timeline_manager.get_recent_events(limit)
        else:
            # Fallback to hole progression events
            events = []
            if wgp_simulation.hole_progression:
                events = wgp_simulation.hole_progression.get_timeline_events()[:limit]
        
        return {
            "success": True,
            "events": events,
            "total_events": len(events)
        }
        
    except Exception as e:
        logger.error(f"Failed to get timeline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get timeline: {str(e)}")

@app.get("/simulation/poker-state")
def get_poker_betting_state():
    """Get current betting state in poker terms"""
    global wgp_simulation
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized")
        
        # Get poker-style betting state using correct hole state structure
        current_hole = wgp_simulation.current_hole
        hole_state = wgp_simulation.hole_states.get(current_hole)
        
        if not hole_state:
            raise HTTPException(status_code=400, detail="No active hole state")
        
        # Format poker betting state manually
        betting = hole_state.betting
        pot_size = betting.current_wager * len(wgp_simulation.players)
        if betting.doubled:
            pot_size *= 2
        
        # Determine betting phase
        phase = "pre-flop"  # Before tee shots
        shots_taken = sum(1 for shot in hole_state.shots_completed.values() if shot)
        if shots_taken >= len(wgp_simulation.players):
            phase = "flop"  # After tee shots
        if hole_state.current_shot_number > len(wgp_simulation.players) * 2:
            phase = "turn"  # Mid-hole
        if any(hole_state.balls_in_hole):
            phase = "river"  # Near completion
        
        poker_state = {
            "pot_size": pot_size,
            "base_bet": betting.base_wager,
            "current_bet": betting.current_wager,
            "betting_phase": phase,
            "doubled": betting.doubled,
            "players_in": len(wgp_simulation.players),
            "wagering_closed": hole_state.wagering_closed
        }
        
        # Get available betting options for current player
        current_player_id = hole_state.next_player_to_hit or "human"
        betting_options = []  # Simplified for now
        
        return {
            "success": True,
            "pot_size": poker_state["pot_size"],
            "base_bet": poker_state["base_bet"],
            "current_bet": poker_state["current_bet"],
            "betting_phase": poker_state["betting_phase"],
            "doubled": poker_state["doubled"],
            "players_in": poker_state["players_in"],
            "wagering_closed": poker_state["wagering_closed"],
            "betting_options": betting_options,
            "current_player": current_player_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get poker state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get poker state: {str(e)}")

# Daily Sign-up System Endpoints

@app.get("/signups/weekly", response_model=schemas.WeeklySignupView)
def get_weekly_signups(week_start: str = Query(description="YYYY-MM-DD format for Monday of the week")):
    """Get sign-ups for a rolling 7-day period starting from specified Monday."""
    try:
        db = database.SessionLocal()
        from datetime import datetime, timedelta
        
        # Parse the week start date
        start_date = datetime.strptime(week_start, '%Y-%m-%d')
        
        # Get all 7 days
        daily_summaries = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            signups = db.query(models.DailySignup).filter(
                models.DailySignup.date == date_str,
                models.DailySignup.status != "cancelled"
            ).all()
            
            daily_summaries.append(schemas.DailySignupSummary(
                date=date_str,
                signups=[schemas.DailySignupResponse.from_orm(signup) for signup in signups],
                total_count=len(signups)
            ))
        
        return schemas.WeeklySignupView(
            week_start=week_start,
            daily_summaries=daily_summaries
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting weekly signups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get weekly signups: {str(e)}")
    finally:
        db.close()

@app.get("/signups")
def get_signups(limit: int = Query(50, description="Maximum number of signups to return")):
    """Get recent signups with basic information"""
    try:
        db = database.SessionLocal()
        
        # Get recent signups
        signups = db.query(models.DailySignup).filter(
            models.DailySignup.status != "cancelled"
        ).order_by(models.DailySignup.created_at.desc()).limit(limit).all()
        
        return {
            "signups": [
                {
                    "id": signup.id,
                    "date": signup.date,
                    "player_name": signup.player_name,
                    "player_profile_id": signup.player_profile_id,
                    "status": signup.status,
                    "signup_time": signup.signup_time,
                    "preferred_start_time": signup.preferred_start_time,
                    "notes": signup.notes,
                    "created_at": signup.created_at if signup.created_at else None
                }
                for signup in signups
            ],
            "total": len(signups)
        }
        
    except Exception as e:
        logger.error(f"Error getting signups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get signups: {str(e)}")
    finally:
        db.close()

@app.post("/signups", response_model=schemas.DailySignupResponse)
def create_signup(signup: schemas.DailySignupCreate):
    """Create a daily sign-up for a player."""
    try:
        db = database.SessionLocal()
        
        # Check if player already signed up for this date
        existing = db.query(models.DailySignup).filter(
            models.DailySignup.date == signup.date,
            models.DailySignup.player_profile_id == signup.player_profile_id,
            models.DailySignup.status != "cancelled"
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Player already signed up for this date")
        
        # Create new signup
        db_signup = models.DailySignup(
            date=signup.date,
            player_profile_id=signup.player_profile_id,
            player_name=signup.player_name,
            signup_time=datetime.now().isoformat(),
            preferred_start_time=signup.preferred_start_time,
            notes=signup.notes,
            status="signed_up",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        db.add(db_signup)
        db.commit()
        db.refresh(db_signup)

        logger.info(f"Created signup for player {signup.player_name} on {signup.date}")

        # Mirror the signup to the legacy CGI sheet when configured.
        try:
            legacy_service = get_legacy_signup_service()
            legacy_service.sync_signup_created(db_signup)
        except Exception:
            logger.exception(
                "Legacy signup sync failed for create id=%s", db_signup.id
            )

        return schemas.DailySignupResponse.from_orm(db_signup)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating signup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create signup: {str(e)}")
    finally:
        db.close()

@app.put("/signups/{signup_id}", response_model=schemas.DailySignupResponse)
def update_signup(signup_id: int, signup_update: schemas.DailySignupUpdate):
    """Update a daily sign-up."""
    try:
        db = database.SessionLocal()
        
        db_signup = db.query(models.DailySignup).filter(models.DailySignup.id == signup_id).first()
        if not db_signup:
            raise HTTPException(status_code=404, detail="Sign-up not found")
        
        # Update fields
        if signup_update.preferred_start_time is not None:
            db_signup.preferred_start_time = signup_update.preferred_start_time
        if signup_update.notes is not None:
            db_signup.notes = signup_update.notes
        if signup_update.status is not None:
            db_signup.status = signup_update.status
            
        db_signup.updated_at = datetime.now().isoformat()
        
        db.commit()
        db.refresh(db_signup)

        logger.info(f"Updated signup {signup_id}")

        try:
            legacy_service = get_legacy_signup_service()
            legacy_service.sync_signup_updated(db_signup)
        except Exception:
            logger.exception(
                "Legacy signup sync failed for update id=%s", db_signup.id
            )

        return schemas.DailySignupResponse.from_orm(db_signup)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating signup {signup_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update signup: {str(e)}")
    finally:
        db.close()

@app.delete("/signups/{signup_id}")
def cancel_signup(signup_id: int):
    """Cancel a daily sign-up."""
    try:
        db = database.SessionLocal()
        
        db_signup = db.query(models.DailySignup).filter(models.DailySignup.id == signup_id).first()
        if not db_signup:
            raise HTTPException(status_code=404, detail="Sign-up not found")
        
        db_signup.status = "cancelled"
        db_signup.updated_at = datetime.now().isoformat()
        
        db.commit()

        logger.info(f"Cancelled signup {signup_id}")

        try:
            legacy_service = get_legacy_signup_service()
            legacy_service.sync_signup_cancelled(db_signup)
        except Exception:
            logger.exception(
                "Legacy signup sync failed for cancel id=%s", db_signup.id
            )

        return {"message": "Sign-up cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling signup {signup_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel signup: {str(e)}")
    finally:
        db.close()

# Daily Message Board Endpoints

@app.get("/messages/daily", response_model=List[schemas.DailyMessageResponse])
def get_daily_messages(date: str = Query(description="YYYY-MM-DD format")):
    """Get all messages for a specific date."""
    try:
        db = database.SessionLocal()
        
        messages = db.query(models.DailyMessage).filter(
            models.DailyMessage.date == date,
            models.DailyMessage.is_active == 1
        ).order_by(models.DailyMessage.message_time).all()
        
        return [schemas.DailyMessageResponse.from_orm(message) for message in messages]
        
    except Exception as e:
        logger.error(f"Error getting messages for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")
    finally:
        db.close()

@app.get("/signups/weekly-with-messages", response_model=schemas.WeeklySignupWithMessagesView)
def get_weekly_signups_with_messages(week_start: str = Query(description="YYYY-MM-DD format for Monday of the week")):
    """Get sign-ups and messages for a rolling 7-day period starting from specified Monday."""
    try:
        db = database.SessionLocal()
        from datetime import datetime, timedelta
        
        # Parse the week start date
        start_date = datetime.strptime(week_start, '%Y-%m-%d')
        
        # Get all 7 days
        daily_summaries = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Get signups
            signups = db.query(models.DailySignup).filter(
                models.DailySignup.date == date_str,
                models.DailySignup.status != "cancelled"
            ).all()
            
            # Get messages
            messages = db.query(models.DailyMessage).filter(
                models.DailyMessage.date == date_str,
                models.DailyMessage.is_active == 1
            ).order_by(models.DailyMessage.message_time).all()
            
            daily_summaries.append(schemas.DailySignupWithMessages(
                date=date_str,
                signups=[schemas.DailySignupResponse.from_orm(signup) for signup in signups],
                total_count=len(signups),
                messages=[schemas.DailyMessageResponse.from_orm(message) for message in messages],
                message_count=len(messages)
            ))
        
        return schemas.WeeklySignupWithMessagesView(
            week_start=week_start,
            daily_summaries=daily_summaries
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting weekly data with messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get weekly data: {str(e)}")
    finally:
        db.close()

@app.post("/messages", response_model=schemas.DailyMessageResponse)
def create_message(message: schemas.DailyMessageCreate):
    """Create a new daily message."""
    try:
        db = database.SessionLocal()
        from datetime import datetime
        
        # Create new message
        db_message = models.DailyMessage(
            date=message.date,
            player_profile_id=message.player_profile_id or 1,  # Default player if not provided
            player_name=message.player_name or "Anonymous",
            message=message.message,
            message_time=datetime.now().isoformat(),
            is_active=1,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        logger.info(f"Created message {db_message.id} for date {message.date}")
        return schemas.DailyMessageResponse.from_orm(db_message)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")
    finally:
        db.close()

@app.put("/messages/{message_id}", response_model=schemas.DailyMessageResponse)
def update_message(message_id: int, message_update: schemas.DailyMessageUpdate):
    """Update an existing message."""
    try:
        db = database.SessionLocal()
        from datetime import datetime
        
        db_message = db.query(models.DailyMessage).filter(models.DailyMessage.id == message_id).first()
        if not db_message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if message_update.message is not None:
            db_message.message = message_update.message
            db_message.updated_at = datetime.now().isoformat()
        
        db.commit()
        db.refresh(db_message)
        
        logger.info(f"Updated message {message_id}")
        return schemas.DailyMessageResponse.from_orm(db_message)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update message: {str(e)}")
    finally:
        db.close()

@app.delete("/messages/{message_id}")
def delete_message(message_id: int):
    """Delete (deactivate) a message."""
    try:
        db = database.SessionLocal()
        from datetime import datetime
        
        db_message = db.query(models.DailyMessage).filter(models.DailyMessage.id == message_id).first()
        if not db_message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        db_message.is_active = 0
        db_message.updated_at = datetime.now().isoformat()
        
        db.commit()
        
        logger.info(f"Deleted message {message_id}")
        return {"message": "Message deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting message {message_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")
    finally:
        db.close()

# Player Availability Endpoints

@app.get("/players/me/availability", response_model=List[schemas.PlayerAvailabilityResponse])
async def get_my_availability(current_user: models.PlayerProfile = Depends(get_current_user)):
    """Get current user's weekly availability."""
    try:
        db = database.SessionLocal()
        
        availability = db.query(models.PlayerAvailability).filter(
            models.PlayerAvailability.player_profile_id == current_user.id
        ).all()
        
        return [schemas.PlayerAvailabilityResponse.from_orm(a) for a in availability]
        
    except Exception as e:
        logger.error(f"Error getting availability for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")
    finally:
        db.close()

@app.post("/players/me/availability", response_model=schemas.PlayerAvailabilityResponse)
async def set_my_availability(
    availability: schemas.PlayerAvailabilityCreate,
    current_user: models.PlayerProfile = Depends(get_current_user)
):
    """Set or update current user's availability for a specific day."""
    try:
        db = database.SessionLocal()
        
        # Override the player_profile_id with the current user's ID
        availability.player_profile_id = current_user.id
        
        # Check if availability already exists for this day
        existing = db.query(models.PlayerAvailability).filter(
            models.PlayerAvailability.player_profile_id == current_user.id,
            models.PlayerAvailability.day_of_week == availability.day_of_week
        ).first()
        
        if existing:
            # Update existing
            existing.available_from_time = availability.available_from_time
            existing.available_to_time = availability.available_to_time
            existing.is_available = availability.is_available
            existing.notes = availability.notes
            existing.updated_at = datetime.now().isoformat()
            
            db.commit()
            db.refresh(existing)
            
            logger.info(f"Updated availability for user {current_user.id}, day {availability.day_of_week}")
            return schemas.PlayerAvailabilityResponse.from_orm(existing)
        else:
            # Create new
            db_availability = models.PlayerAvailability(
                player_profile_id=current_user.id,
                day_of_week=availability.day_of_week,
                available_from_time=availability.available_from_time,
                available_to_time=availability.available_to_time,
                is_available=availability.is_available,
                notes=availability.notes,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            db.add(db_availability)
            db.commit()
            db.refresh(db_availability)
            
            logger.info(f"Created availability for user {current_user.id}, day {availability.day_of_week}")
            return schemas.PlayerAvailabilityResponse.from_orm(db_availability)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting availability for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set availability: {str(e)}")
    finally:
        db.close()

@app.get("/players/{player_id}/availability", response_model=List[schemas.PlayerAvailabilityResponse])
def get_player_availability(player_id: int):
    """Get a player's weekly availability."""
    try:
        db = database.SessionLocal()
        
        availability = db.query(models.PlayerAvailability).filter(
            models.PlayerAvailability.player_profile_id == player_id
        ).order_by(models.PlayerAvailability.day_of_week).all()
        
        return [schemas.PlayerAvailabilityResponse.from_orm(avail) for avail in availability]
        
    except Exception as e:
        logger.error(f"Error getting availability for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")
    finally:
        db.close()

@app.get("/players/availability/all", response_model=List[Dict])
def get_all_players_availability():
    """Get all players' weekly availability with their names."""
    try:
        db = database.SessionLocal()
        
        # Get all players with their availability
        players_with_availability = db.query(models.PlayerProfile).all()
        
        result = []
        for player in players_with_availability:
            player_data = {
                "player_id": player.id,
                "player_name": player.name,
                "email": player.email,
                "availability": []
            }
            
            # Get this player's availability
            availability = db.query(models.PlayerAvailability).filter(
                models.PlayerAvailability.player_profile_id == player.id
            ).all()
            
            for avail in availability:
                player_data["availability"].append({
                    "day_of_week": avail.day_of_week,
                    "is_available": avail.is_available,
                    "available_from_time": avail.available_from_time,
                    "available_to_time": avail.available_to_time,
                    "notes": avail.notes
                })
            
            result.append(player_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting all players availability: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")
    finally:
        db.close()

@app.post("/players/{player_id}/availability", response_model=schemas.PlayerAvailabilityResponse)
def set_player_availability(player_id: int, availability: schemas.PlayerAvailabilityCreate):
    """Set or update a player's availability for a specific day."""
    try:
        db = database.SessionLocal()
        
        # Check if availability already exists for this day
        existing = db.query(models.PlayerAvailability).filter(
            models.PlayerAvailability.player_profile_id == player_id,
            models.PlayerAvailability.day_of_week == availability.day_of_week
        ).first()
        
        if existing:
            # Update existing
            existing.available_from_time = availability.available_from_time
            existing.available_to_time = availability.available_to_time
            existing.is_available = availability.is_available
            existing.notes = availability.notes
            existing.updated_at = datetime.now().isoformat()
            
            db.commit()
            db.refresh(existing)
            
            logger.info(f"Updated availability for player {player_id}, day {availability.day_of_week}")
            return schemas.PlayerAvailabilityResponse.from_orm(existing)
        else:
            # Create new
            db_availability = models.PlayerAvailability(
                player_profile_id=player_id,
                day_of_week=availability.day_of_week,
                available_from_time=availability.available_from_time,
                available_to_time=availability.available_to_time,
                is_available=availability.is_available,
                notes=availability.notes,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            db.add(db_availability)
            db.commit()
            db.refresh(db_availability)
            
            logger.info(f"Created availability for player {player_id}, day {availability.day_of_week}")
            return schemas.PlayerAvailabilityResponse.from_orm(db_availability)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting availability for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set availability: {str(e)}")
    finally:
        db.close()

# Team Formation Helpers & Endpoints


def _get_active_signups_for_date(db: Session, date: str) -> List[models.DailySignup]:
    """Fetch non-cancelled signups for the requested date."""
    return db.query(models.DailySignup).filter(
        models.DailySignup.date == date,
        models.DailySignup.status != "cancelled"
    ).all()


def _build_player_payload(
    signups: List[models.DailySignup],
    *,
    include_handicap: bool = False,
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """Convert signup records into the player dictionaries used by formation services."""
    if include_handicap and db is None:
        raise ValueError("Database session is required when include_handicap=True")

    players: List[Dict[str, Any]] = []
    handicap_lookup: Dict[int, float] = {}

    if include_handicap:
        profile_ids = [s.player_profile_id for s in signups if s.player_profile_id is not None]
        if profile_ids:
            profiles = db.query(models.PlayerProfile).filter(
                models.PlayerProfile.id.in_(profile_ids)
            ).all()
            handicap_lookup = {profile.id: profile.handicap for profile in profiles}

    for signup in signups:
        player_data: Dict[str, Any] = {
            "id": signup.id,
            "player_profile_id": signup.player_profile_id,
            "player_name": signup.player_name,
            "preferred_start_time": signup.preferred_start_time,
            "notes": signup.notes,
            "signup_time": signup.signup_time
        }

        if include_handicap:
            player_data["handicap"] = handicap_lookup.get(signup.player_profile_id, 18.0)

        players.append(player_data)

    return players


@app.post("/signups/{date}/team-formation/random")
def generate_random_teams_for_date(
    date: str = Path(description="Date in YYYY-MM-DD format"),
    seed: Optional[int] = Query(None, description="Random seed for reproducible results"),
    max_teams: Optional[int] = Query(None, description="Maximum number of teams to create")
):
    """Generate random 4-player teams from players signed up for a specific date."""
    try:
        db = database.SessionLocal()

        # Get all signups for the specified date
        signups = _get_active_signups_for_date(db, date)
        
        if len(signups) < 4:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough players signed up for {date}. Need at least 4 players, found {len(signups)}"
            )
        
        # Convert signups to player dictionaries
        players = _build_player_payload(signups)
        
        # Generate random teams
        teams = TeamFormationService.generate_random_teams(
            players=players,
            seed=seed,
            max_teams=max_teams
        )
        
        # Create summary
        summary = TeamFormationService.create_team_summary(teams)
        summary["date"] = date
        summary["total_signups"] = len(signups)
        
        # Validate results
        validation = TeamFormationService.validate_team_formation(teams)
        
        logger.info(f"Generated {len(teams)} random teams for date {date}")
        
        return {
            "summary": summary,
            "teams": teams,
            "validation": validation,
            "remaining_players": len(signups) % 4
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating random teams for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate teams: {str(e)}")
    finally:
        db.close()

@app.post("/signups/{date}/team-formation/balanced")
def generate_balanced_teams_for_date(
    date: str = Path(description="Date in YYYY-MM-DD format"),
    seed: Optional[int] = Query(None, description="Random seed for reproducible results")
):
    """Generate skill-balanced 4-player teams from players signed up for a specific date."""
    try:
        db = database.SessionLocal()

        # Get all signups for the specified date
        signups = _get_active_signups_for_date(db, date)
        
        if len(signups) < 4:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough players signed up for {date}. Need at least 4 players, found {len(signups)}"
            )
        
        # Get player profiles with handicap information
        players = _build_player_payload(signups, include_handicap=True, db=db)
        
        # Generate balanced teams
        teams = TeamFormationService.generate_balanced_teams(
            players=players,
            skill_key="handicap",
            seed=seed
        )
        
        # Create summary
        summary = TeamFormationService.create_team_summary(teams)
        summary["date"] = date
        summary["total_signups"] = len(signups)
        
        # Validate results
        validation = TeamFormationService.validate_team_formation(teams)
        
        logger.info(f"Generated {len(teams)} balanced teams for date {date}")
        
        return {
            "summary": summary,
            "teams": teams,
            "validation": validation,
            "remaining_players": len(signups) % 4
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating balanced teams for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate balanced teams: {str(e)}")
    finally:
        db.close()

@app.post("/signups/{date}/team-formation/rotations")
def generate_team_rotations_for_date(
    date: str = Path(description="Date in YYYY-MM-DD format"),
    num_rotations: int = Query(3, description="Number of different team rotations to create"),
    seed: Optional[int] = Query(None, description="Random seed for reproducible results")
):
    """Generate multiple team rotation options for variety throughout the day."""
    try:
        db = database.SessionLocal()

        # Get all signups for the specified date
        signups = _get_active_signups_for_date(db, date)
        
        if len(signups) < 4:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough players signed up for {date}. Need at least 4 players, found {len(signups)}"
            )
        
        # Convert signups to player dictionaries
        players = _build_player_payload(signups)
        
        # Generate team rotations
        rotations = TeamFormationService.create_team_pairings_with_rotations(
            players=players,
            num_rotations=num_rotations,
            seed=seed
        )
        
        logger.info(f"Generated {len(rotations)} team rotations for date {date}")
        
        return {
            "date": date,
            "total_signups": len(signups),
            "num_rotations": len(rotations),
            "rotations": rotations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating team rotations for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate rotations: {str(e)}")
    finally:
        db.close()


@app.post("/signups/{date}/sunday-game/pairings")
def generate_sunday_game_pairings(
    date: str = Path(description="Date in YYYY-MM-DD format"),
    num_rotations: int = Query(3, description="Number of Sunday pairing options to generate"),
    seed: Optional[int] = Query(None, description="Override random seed for reproducible results")
):
    """Generate randomized Sunday game pairings with optional deterministic seeding."""
    try:
        db = database.SessionLocal()

        signups = _get_active_signups_for_date(db, date)

        if len(signups) < 4:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough players signed up for {date}. Need at least 4 players, found {len(signups)}"
            )

        players = _build_player_payload(signups)

        pairing_result = generate_sunday_pairings(
            players,
            num_rotations=num_rotations,
            seed=seed
        )

        return {
            "date": date,
            "total_signups": len(signups),
            "player_count": pairing_result["player_count"],
            "pairing_sets_available": pairing_result["total_rotations"],
            "selected_rotation": pairing_result["selected_rotation"],
            "rotations": pairing_result["rotations"],
            "random_seed": pairing_result["random_seed"],
            "remaining_players": pairing_result["remaining_players"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Sunday game pairings for {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Sunday pairings: {str(e)}")
    finally:
        db.close()

@app.get("/signups/{date}/players")
def get_players_for_date(date: str = Path(description="Date in YYYY-MM-DD format")):
    """Get all players signed up for a specific date."""
    try:
        db = database.SessionLocal()
        
        # Get all signups for the specified date
        signups = db.query(models.DailySignup).filter(
            models.DailySignup.date == date,
            models.DailySignup.status != "cancelled"
        ).all()
        
        players = []
        for signup in signups:
            # Get player profile for additional info
            player_profile = db.query(models.PlayerProfile).filter(
                models.PlayerProfile.id == signup.player_profile_id
            ).first()
            
            player_data = {
                "signup_id": signup.id,
                "player_profile_id": signup.player_profile_id,
                "player_name": signup.player_name,
                "preferred_start_time": signup.preferred_start_time,
                "notes": signup.notes,
                "signup_time": signup.signup_time,
                "handicap": player_profile.handicap if player_profile else None,
                "email": player_profile.email if player_profile else None
            }
            players.append(player_data)
        
        return {
            "date": date,
            "total_players": len(players),
            "players": players,
            "can_form_teams": len(players) >= 4,
            "max_complete_teams": len(players) // 4,
            "remaining_players": len(players) % 4
        }
        
    except Exception as e:
        logger.error(f"Error getting players for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get players: {str(e)}")
    finally:
        db.close()

# Email Preferences Endpoints

@app.get("/players/{player_id}/email-preferences", response_model=schemas.EmailPreferencesResponse)
def get_email_preferences(player_id: int):
    """Get a player's email preferences."""
    try:
        db = database.SessionLocal()
        
        preferences = db.query(models.EmailPreferences).filter(
            models.EmailPreferences.player_profile_id == player_id
        ).first()
        
        if not preferences:
            # Create default preferences
            preferences = models.EmailPreferences(
                player_profile_id=player_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
            
        return schemas.EmailPreferencesResponse.from_orm(preferences)
        
    except Exception as e:
        logger.error(f"Error getting email preferences for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get email preferences: {str(e)}")
    finally:
        db.close()

@app.put("/players/{player_id}/email-preferences", response_model=schemas.EmailPreferencesResponse)
def update_email_preferences(player_id: int, preferences_update: schemas.EmailPreferencesUpdate):
    """Update a player's email preferences."""
    try:
        db = database.SessionLocal()
        
        preferences = db.query(models.EmailPreferences).filter(
            models.EmailPreferences.player_profile_id == player_id
        ).first()
        
        if not preferences:
            raise HTTPException(status_code=404, detail="Email preferences not found")
        
        # Update fields
        if preferences_update.daily_signups_enabled is not None:
            preferences.daily_signups_enabled = preferences_update.daily_signups_enabled
        if preferences_update.signup_confirmations_enabled is not None:
            preferences.signup_confirmations_enabled = preferences_update.signup_confirmations_enabled
        if preferences_update.signup_reminders_enabled is not None:
            preferences.signup_reminders_enabled = preferences_update.signup_reminders_enabled
        if preferences_update.game_invitations_enabled is not None:
            preferences.game_invitations_enabled = preferences_update.game_invitations_enabled
        if preferences_update.weekly_summary_enabled is not None:
            preferences.weekly_summary_enabled = preferences_update.weekly_summary_enabled
        if preferences_update.email_frequency is not None:
            preferences.email_frequency = preferences_update.email_frequency
        if preferences_update.preferred_notification_time is not None:
            preferences.preferred_notification_time = preferences_update.preferred_notification_time
            
        preferences.updated_at = datetime.now().isoformat()
        
        db.commit()
        db.refresh(preferences)
        
        logger.info(f"Updated email preferences for player {player_id}")
        return schemas.EmailPreferencesResponse.from_orm(preferences)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating email preferences for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update email preferences: {str(e)}")
    finally:
        db.close()

# =============================================================================
# AUTHENTICATED EMAIL PREFERENCE ENDPOINTS  
# =============================================================================

@app.get("/players/me/email-preferences", response_model=schemas.EmailPreferencesResponse)
async def get_my_email_preferences(current_user: models.PlayerProfile = Depends(get_current_user)):
    """Get current user's email preferences"""
    db = database.SessionLocal()
    try:
        # Try to find existing preferences
        prefs = db.query(models.EmailPreferences).filter(
            models.EmailPreferences.player_profile_id == current_user.id
        ).first()
        
        if not prefs:
            # Create default preferences
            prefs = models.EmailPreferences(
                player_profile_id=current_user.id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        
        return schemas.EmailPreferencesResponse(
            id=prefs.id,
            player_profile_id=prefs.player_profile_id,
            daily_signups_enabled=bool(prefs.daily_signups_enabled),
            signup_confirmations_enabled=bool(prefs.signup_confirmations_enabled),
            signup_reminders_enabled=bool(prefs.signup_reminders_enabled),
            game_invitations_enabled=bool(prefs.game_invitations_enabled),
            weekly_summary_enabled=bool(prefs.weekly_summary_enabled),
            email_frequency=prefs.email_frequency,
            preferred_notification_time=prefs.preferred_notification_time
        )
    except Exception as e:
        logger.error(f"Error getting email preferences for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get email preferences: {str(e)}")
    finally:
        db.close()

@app.put("/players/me/email-preferences", response_model=schemas.EmailPreferencesResponse)
async def update_my_email_preferences(
    preferences_update: schemas.EmailPreferencesUpdate,
    current_user: models.PlayerProfile = Depends(get_current_user)
):
    """Update current user's email preferences"""
    db = database.SessionLocal()
    try:
        # Find or create preferences
        prefs = db.query(models.EmailPreferences).filter(
            models.EmailPreferences.player_profile_id == current_user.id
        ).first()
        
        if not prefs:
            prefs = models.EmailPreferences(
                player_profile_id=current_user.id,
                created_at=datetime.now().isoformat()
            )
            db.add(prefs)
        
        # Update preferences
        update_data = preferences_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(prefs, field):
                # Convert bool to int for SQLite
                if isinstance(value, bool):
                    value = 1 if value else 0
                setattr(prefs, field, value)
        
        prefs.updated_at = datetime.now().isoformat()
        db.commit()
        db.refresh(prefs)
        
        logger.info(f"Updated email preferences for user {current_user.id}")
        
        return schemas.EmailPreferencesResponse(
            id=prefs.id,
            player_profile_id=prefs.player_profile_id,
            daily_signups_enabled=bool(prefs.daily_signups_enabled),
            signup_confirmations_enabled=bool(prefs.signup_confirmations_enabled),
            signup_reminders_enabled=bool(prefs.signup_reminders_enabled),
            game_invitations_enabled=bool(prefs.game_invitations_enabled),
            weekly_summary_enabled=bool(prefs.weekly_summary_enabled),
            email_frequency=prefs.email_frequency,
            preferred_notification_time=prefs.preferred_notification_time
        )
    except Exception as e:
        logger.error(f"Error updating email preferences for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update email preferences: {str(e)}")
    finally:
        db.close()

# =============================================================================
# EMAIL ENDPOINTS
# =============================================================================

@app.post("/email/send-test")
async def send_test_email(email_data: dict):
    """Send a test email to verify email service configuration"""
    try:
        email_service = get_email_service()
        
        if not email_service.is_configured:
            raise HTTPException(
                status_code=503, 
                detail="Email service not configured. Please set SMTP_USER, SMTP_PASSWORD, and SMTP_HOST environment variables."
            )
        
        to_email = email_data.get('to_email')
        if not to_email:
            raise HTTPException(status_code=400, detail="to_email is required")
            
        success = email_service.send_signup_confirmation(
            to_email=to_email,
            player_name=email_data.get('player_name', 'Test Player'),
            signup_date=email_data.get('signup_date', 'Tomorrow')
        )
        
        if success:
            return {"message": "Test email sent successfully", "to_email": to_email}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

@app.get("/email/status")
async def get_email_service_status():
    """Check if email service is properly configured"""
    try:
        email_service = get_email_service()
        
        return {
            "configured": email_service.is_configured,
            "smtp_host": email_service.smtp_config.get('host', 'Not set'),
            "smtp_port": email_service.smtp_config.get('port', 'Not set'),
            "from_email": email_service.from_email or 'Not set',
            "from_name": email_service.from_name or 'Not set',
            "missing_config": [
                key for key in ['SMTP_USER', 'SMTP_PASSWORD', 'SMTP_HOST'] 
                if not os.getenv(key)
            ]
        }
        
    except Exception as e:
        logger.error(f"Error checking email service status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check email status: {str(e)}")

@app.post("/email/signup-confirmation")
async def send_signup_confirmation_email(email_data: dict):
    """Send signup confirmation email"""
    try:
        email_service = get_email_service()
        
        if not email_service.is_configured:
            raise HTTPException(status_code=503, detail="Email service not configured")
        
        required_fields = ['to_email', 'player_name', 'signup_date']
        missing_fields = [field for field in required_fields if not email_data.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        success = email_service.send_signup_confirmation(
            to_email=email_data['to_email'],
            player_name=email_data['player_name'],
            signup_date=email_data['signup_date']
        )
        
        if success:
            return {"message": "Signup confirmation email sent", "to_email": email_data['to_email']}
        else:
            raise HTTPException(status_code=500, detail="Failed to send signup confirmation email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending signup confirmation email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.post("/email/daily-reminder")
async def send_daily_reminder_email(email_data: dict):
    """Send daily signup reminder email"""
    try:
        email_service = get_email_service()
        
        if not email_service.is_configured:
            raise HTTPException(status_code=503, detail="Email service not configured")
        
        required_fields = ['to_email', 'player_name']
        missing_fields = [field for field in required_fields if not email_data.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        success = email_service.send_daily_signup_reminder(
            to_email=email_data['to_email'],
            player_name=email_data['player_name'],
            available_dates=email_data.get('available_dates', [])
        )
        
        if success:
            return {"message": "Daily reminder email sent", "to_email": email_data['to_email']}
        else:
            raise HTTPException(status_code=500, detail="Failed to send daily reminder email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending daily reminder email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.post("/email/weekly-summary")
async def send_weekly_summary_email(email_data: dict):
    """Send weekly summary email"""
    try:
        email_service = get_email_service()
        
        if not email_service.is_configured:
            raise HTTPException(status_code=503, detail="Email service not configured")
        
        required_fields = ['to_email', 'player_name']
        missing_fields = [field for field in required_fields if not email_data.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        success = email_service.send_weekly_summary(
            to_email=email_data['to_email'],
            player_name=email_data['player_name'],
            summary_data=email_data.get('summary_data', {})
        )
        
        if success:
            return {"message": "Weekly summary email sent", "to_email": email_data['to_email']}
        else:
            raise HTTPException(status_code=500, detail="Failed to send weekly summary email")
            
    except HTTPException:
        raise

@app.post("/email/initialize-scheduler")
async def initialize_email_scheduler():
    """Initialize the email scheduler on demand"""
    global email_scheduler
    
    try:
        # Check if already initialized
        if email_scheduler is not None:
            return {
                "status": "already_initialized",
                "message": "Email scheduler is already running"
            }
        
        # Import and initialize the scheduler
        from .services.email_scheduler import email_scheduler as scheduler_instance
        email_scheduler = scheduler_instance
        email_scheduler.start()
        
        logger.info("📧 Email scheduler initialized on demand")
        
        return {
            "status": "success",
            "message": "Email scheduler initialized successfully",
            "scheduled_jobs": ["daily_reminders", "weekly_summaries"]
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize email scheduler: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to initialize email scheduler: {str(e)}"
        )

@app.get("/email/scheduler-status")
async def get_email_scheduler_status():
    """Get the status of the email scheduler"""
    global email_scheduler
    
    return {
        "initialized": email_scheduler is not None,
        "running": email_scheduler is not None and hasattr(email_scheduler, '_started') and email_scheduler._started,
        "message": "Scheduler running" if email_scheduler else "Scheduler not initialized. Call /email/initialize-scheduler to start."
    }

# Static file serving for React frontend (must be at end after all API routes)
from pathlib import Path

# Get the path to the built React app
STATIC_DIR = Path(__file__).parent.parent.parent / "frontend" / "build"

# =============================================================================
# MATCHMAKING ENDPOINTS
# =============================================================================

@app.get("/matchmaking/suggestions")
def get_match_suggestions(
    min_overlap_hours: float = 2.0,
    preferred_days: Optional[str] = None
):
    """
    Get matchmaking suggestions based on player availability.
    
    Args:
        min_overlap_hours: Minimum hours of overlap required (default 2)
        preferred_days: Comma-separated list of preferred days (0=Monday, 6=Sunday)
    """
    try:
        from .services.matchmaking_service import MatchmakingService
        
        db = database.SessionLocal()
        
        # Get all players' availability (reuse existing endpoint logic)
        players_with_availability = db.query(models.PlayerProfile).all()
        
        all_players_data = []
        for player in players_with_availability:
            player_data = {
                "player_id": player.id,
                "player_name": player.name,
                "email": player.email,
                "availability": []
            }
            
            availability = db.query(models.PlayerAvailability).filter(
                models.PlayerAvailability.player_profile_id == player.id
            ).all()
            
            for avail in availability:
                player_data["availability"].append({
                    "day_of_week": avail.day_of_week,
                    "is_available": avail.is_available,
                    "available_from_time": avail.available_from_time,
                    "available_to_time": avail.available_to_time,
                    "notes": avail.notes
                })
            
            all_players_data.append(player_data)
        
        # Parse preferred days if provided
        preferred_days_list = None
        if preferred_days:
            preferred_days_list = [int(d.strip()) for d in preferred_days.split(",")]
        
        # Find matches
        matches = MatchmakingService.find_matches(
            all_players_data,
            min_overlap_hours=min_overlap_hours,
            preferred_days=preferred_days_list
        )
        
        # Get recent match history to filter out recently matched players
        recent_matches = db.query(models.MatchSuggestion).filter(
            models.MatchSuggestion.created_at >= (datetime.now() - timedelta(days=7)).isoformat()
        ).all()
        
        # Convert to format expected by filter function
        recent_match_history = []
        for match in recent_matches:
            match_players = db.query(models.MatchPlayer).filter(
                models.MatchPlayer.match_suggestion_id == match.id
            ).all()
            
            recent_match_history.append({
                "created_at": match.created_at,
                "players": [{"player_id": mp.player_profile_id} for mp in match_players]
            })
        
        # Filter out recently matched players
        filtered_matches = MatchmakingService.filter_recent_matches(
            matches, recent_match_history, days_between_matches=3
        )
        
        return {
            "total_matches_found": len(matches),
            "filtered_matches": len(filtered_matches),
            "matches": filtered_matches[:10]  # Return top 10 matches
        }
        
    except Exception as e:
        logger.error(f"Error finding match suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find matches: {str(e)}")
    finally:
        db.close()

@app.post("/matchmaking/create-and-notify")
async def create_and_notify_matches():
    """
    Run the full matchmaking process: find matches and send notifications.
    This endpoint can be called by a scheduler or manually.
    """
    try:
        # First, find matches
        matches_response = get_match_suggestions(min_overlap_hours=2.0)
        
        if not matches_response["matches"]:
            return {
                "message": "No suitable matches found",
                "matches_checked": matches_response["total_matches_found"]
            }
        
        db = database.SessionLocal()
        email_service = get_email_service()
        
        # Save the top matches to database
        saved_matches = []
        notifications_sent = []
        
        for match_data in matches_response["matches"][:5]:  # Save top 5 matches
            try:
                # Create match suggestion
                match = models.MatchSuggestion(
                    day_of_week=match_data["day_of_week"],
                    overlap_start=match_data["overlap_start"],
                    overlap_end=match_data["overlap_end"],
                    suggested_tee_time=match_data["suggested_tee_time"],
                    match_quality_score=match_data["match_quality"],
                    status="pending",
                    created_at=datetime.now().isoformat(),
                    expires_at=(datetime.now() + timedelta(days=7)).isoformat()
                )
                db.add(match)
                db.commit()
                db.refresh(match)
                
                # Add players to match
                for player in match_data["players"]:
                    match_player = models.MatchPlayer(
                        match_suggestion_id=match.id,
                        player_profile_id=player["player_id"],
                        player_name=player["player_name"],
                        player_email=player["email"],
                        created_at=datetime.now().isoformat()
                    )
                    db.add(match_player)
                
                db.commit()
                saved_matches.append(match.id)
                
                # Send notification email
                from .services.matchmaking_service import MatchmakingService
                notification = MatchmakingService.create_match_notification(match_data)
                
                # Send email to all players
                try:
                    for recipient in notification['recipients']:
                        await email_service.send_email(
                            to_email=recipient,
                            subject=notification['subject'],
                            body=notification['body']
                        )
                    
                    # Mark as sent
                    match.notification_sent = True
                    match.notification_sent_at = datetime.now().isoformat()
                    db.commit()
                    
                    notifications_sent.append({
                        "match_id": match.id,
                        "players": [p["player_name"] for p in match_data["players"]],
                        "status": "sent"
                    })
                    
                    logger.info(f"Sent match notification for match {match.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to send notification for match {match.id}: {e}")
                    notifications_sent.append({
                        "match_id": match.id,
                        "players": [p["player_name"] for p in match_data["players"]],
                        "status": "failed",
                        "error": str(e)
                    })
                    
            except Exception as e:
                logger.error(f"Error creating match: {e}")
                continue
        
        return {
            "matches_found": matches_response["total_matches_found"],
            "matches_created": len(saved_matches),
            "notifications_sent": len([n for n in notifications_sent if n["status"] == "sent"]),
            "notifications_failed": len([n for n in notifications_sent if n["status"] == "failed"]),
            "match_ids": saved_matches,
            "details": notifications_sent
        }
        
    except Exception as e:
        logger.error(f"Error in create and notify matches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create and notify matches: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

@app.get("/test-deployment")
async def test_deployment(x_admin_email: Optional[str] = Header(None)):
    """Test that new deployments are working."""
    require_admin(x_admin_email)
    return {"message": "Deployment is working", "timestamp": datetime.now().isoformat()}

if ENABLE_TEST_ENDPOINTS:

    @app.get("/debug/paths")
    async def debug_paths(x_admin_email: Optional[str] = Header(None)):
        """Debug endpoint to check file paths."""
        require_admin(x_admin_email)
        current_file = Path(__file__).resolve()
        static_dir = STATIC_DIR.resolve()
        index_file = static_dir / "index.html"

        return {
            "current_file": str(current_file),
            "static_dir": str(static_dir),
            "static_dir_exists": static_dir.exists(),
            "index_file": str(index_file),
            "index_file_exists": index_file.exists(),
            "static_dir_contents": list(static_dir.iterdir()) if static_dir.exists() else []
        }

# Mount static files if build directory exists
static_assets_dir = STATIC_DIR / "static"

if STATIC_DIR.exists() and static_assets_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_assets_dir)), name="static")
else:
    logger.warning(
        "Frontend static assets not found. Expected %s", static_assets_dir
    )


@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """Serve the built frontend when available, otherwise render a helpful status page."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    frontend_url = (
        os.getenv("PUBLIC_FRONTEND_URL")
        or os.getenv("FRONTEND_BASE_URL")
        or "https://wolf-goat-pig.vercel.app"
    )

    docs_link = ""
    if app.docs_url:
        docs_link = f'<li><a href="{app.docs_url}">Interactive API docs</a></li>'

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Wolf Goat Pig API</title>
        <style>
          body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: #0f172a;
            color: #e2e8f0;
          }}
          .card {{
            background: rgba(15, 23, 42, 0.9);
            border-radius: 16px;
            padding: 32px;
            max-width: 520px;
            box-shadow: 0 20px 45px rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(148, 163, 184, 0.2);
          }}
          h1 {{
            margin-top: 0;
            font-size: 1.75rem;
            letter-spacing: 0.02em;
          }}
          p {{
            line-height: 1.55;
            margin-bottom: 1.25rem;
            color: #cbd5f5;
          }}
          ul {{
            padding-left: 1.2rem;
            margin: 0 0 1.25rem 0;
          }}
          a {{
            color: #38bdf8;
            text-decoration: none;
            font-weight: 600;
          }}
          a:hover {{
            text-decoration: underline;
          }}
          .meta {{
            font-size: 0.85rem;
            color: #94a3b8;
          }}
        </style>
      </head>
      <body>
        <main class="card">
          <h1>Wolf Goat Pig API</h1>
          <p>
            The backend is running and healthy. The interactive frontend lives on our
            Vercel deployment — you can reach it here:
          </p>
          <ul>
            <li><a href="{frontend_url}" target="_blank" rel="noopener">Open the production app</a></li>
            {docs_link}
          </ul>
          <p class="meta">Last checked: {datetime.utcnow().isoformat()}Z</p>
        </main>
      </body>
    </html>
    """

    return HTMLResponse(content=html, status_code=200)
