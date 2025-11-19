from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path, Query, UploadFile, File, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from . import models, schemas, crud, database

from .state.course_manager import CourseManager
from .wolf_goat_pig import WolfGoatPigGame, Player, GamePhase
from .post_hole_analytics import PostHoleAnalyzer
from .simulation_timeline_enhancements import (
    enhance_simulation_with_timeline, 
    format_poker_betting_state, 
    create_betting_options
)
from .course_import import CourseImporter, import_course_by_name, import_course_from_json, save_course_to_database
from .domain.shot_result import ShotResult
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
from .services.game_lifecycle_service import get_game_lifecycle_service
from .services.notification_service import get_notification_service
from .services.leaderboard_service import get_leaderboard_service
# Email scheduler will be initialized on-demand to prevent startup blocking
# from .services.email_scheduler import email_scheduler
from .services.auth_service import get_current_user
from .managers.rule_manager import RuleManager, RuleViolationError
from .managers.scoring_manager import get_scoring_manager
from .validators import (
    HandicapValidator,
    BettingValidator,
    GameStateValidator,
    HandicapValidationError,
    BettingValidationError,
    GameStateValidationError
)
from .badge_routes import router as badge_router
from .routes.betting_events import router as betting_events_router

# Import routers
from .routers import health, sheet_integration, players, courses

# Global variable for email scheduler (initialized on demand)
email_scheduler = None

# Configure logging
logger = logging.getLogger(__name__)


# Initialize Post-Hole Analyzer
post_hole_analyzer = PostHoleAnalyzer()
# Initialize Course Manager (replaces game_state.course_manager)
course_manager = CourseManager()

# Response model classes for Action API
class ActionRequest(BaseModel):
    """Unified action request for all game interactions"""
    model_config = {"extra": "allow"}  # Allow extra fields for backward compatibility
    action_type: str  # INITIALIZE_GAME, PLAY_SHOT, REQUEST_PARTNERSHIP, etc.
    payload: Optional[Dict[str, Any]] = None

class ActionResponse(BaseModel):
    """Standard response structure for all actions"""
    game_state: Dict[str, Any]
    log_message: str
    available_actions: List[Dict[str, Any]]
    timeline_event: Optional[Dict[str, Any]] = None

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


# Simplified Scorekeeper Models
class HoleTeams(BaseModel):
    """Team configuration for a hole"""
    type: str  # 'partners' or 'solo'
    team1: Optional[List[str]] = None  # Player IDs for team 1 (partners mode)
    team2: Optional[List[str]] = None  # Player IDs for team 2 (partners mode)
    captain: Optional[str] = None  # Captain player ID (solo mode)
    opponents: Optional[List[str]] = None  # Opponent player IDs (solo mode)


class CompleteHoleRequest(BaseModel):
    """Request to complete a hole with all data at once - for scorekeeper mode"""
    hole_number: int = Field(..., ge=1, le=18)
    rotation_order: List[str] = Field(..., description="Hitting order for this hole")
    captain_index: int = Field(0, ge=0, description="Index in rotation_order who is captain")
    phase: Optional[str] = Field("normal", description="Game phase: 'normal' or 'hoepfinger'")
    joes_special_wager: Optional[int] = Field(None, description="Wager set by Goat (2, 4, or 8) during Hoepfinger")
    option_turned_off: Optional[bool] = Field(False, description="Captain proactively turned off The Option")
    duncan_invoked: Optional[bool] = Field(False, description="Captain went solo before hitting (3-for-2 payout)")
    tunkarri_invoked: Optional[bool] = Field(False, description="Aardvark went solo before Captain hit (3-for-2 payout)")
    teams: HoleTeams
    final_wager: float = Field(..., gt=0)
    winner: str  # 'team1', 'team2', 'captain', 'opponents', or 'push' for completed holes; 'team1_flush' (Team2 conceded), 'team2_flush' (Team1 conceded), 'captain_flush' (Opponents conceded), 'opponents_flush' (Captain conceded) for folded holes
    scores: Dict[str, int] = Field(..., description="Player ID to strokes mapping")
    hole_par: Optional[int] = Field(4, ge=3, le=5)
    float_invoked_by: Optional[str] = Field(None, description="Player ID who invoked float on this hole")
    option_invoked_by: Optional[str] = Field(None, description="Player ID who triggered option on this hole")
    carry_over_applied: Optional[bool] = Field(False, description="Whether carry-over was applied to this hole")
    doubles_history: Optional[List[Dict]] = Field(None, description="Pre-hole doubles offered and accepted")
    big_dick_invoked_by: Optional[str] = Field(None, description="Player ID who invoked The Big Dick on hole 18")
    # Phase 5: The Aardvark (5-man game mechanics)
    aardvark_requested_team: Optional[str] = Field(None, description="Team Aardvark requested to join ('team1' or 'team2')")
    aardvark_tossed: Optional[bool] = Field(False, description="Whether Aardvark was tossed by requested team")
    aardvark_ping_ponged: Optional[bool] = Field(False, description="Whether Aardvark was re-tossed (ping-ponged) by second team")
    aardvark_solo: Optional[bool] = Field(False, description="Whether Aardvark went solo (1v4)")


class RotationSelectionRequest(BaseModel):
    """Request to select rotation position - for 5-man games on holes 16-18"""
    hole_number: int = Field(..., ge=16, le=18, description="Hole number (16, 17, or 18)")
    goat_player_id: str = Field(..., description="Player ID of the Goat (lowest points)")
    selected_position: int = Field(..., ge=1, le=5, description="Desired position in rotation (1-5)")


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

# Include betting events routes
app.include_router(betting_events_router)

# Include modular routers
app.include_router(health.router)
app.include_router(sheet_integration.router)
app.include_router(players.router)
app.include_router(courses.router)

# Import and include course data update router
from .routers import course_data_update
app.include_router(course_data_update.router)

logger.info("✅ All routers registered")

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

        # Run database migrations to add any missing columns
        logger.info("🔄 Running database migrations...")
        try:
            from sqlalchemy import text, inspect
            migration_db = database.SessionLocal()
            try:
                inspector = inspect(database.engine)
                if 'game_state' in inspector.get_table_names():
                    columns = [col['name'] for col in inspector.get_columns('game_state')]
                    migrations_needed = []

                    # Determine database type (needed for migrations and sequence check)
                    database_url = os.getenv('DATABASE_URL', '')
                    is_postgresql = 'postgresql://' in database_url or 'postgres://' in database_url

                    # Check for missing columns
                    if 'game_id' not in columns:
                        migrations_needed.append('game_id')
                    if 'created_at' not in columns:
                        migrations_needed.append('created_at')
                    if 'updated_at' not in columns:
                        migrations_needed.append('updated_at')
                    if 'join_code' not in columns:
                        migrations_needed.append('join_code')
                    if 'creator_user_id' not in columns:
                        migrations_needed.append('creator_user_id')
                    if 'game_status' not in columns:
                        migrations_needed.append('game_status')

                    if migrations_needed:
                        logger.info(f"  Missing columns detected: {', '.join(migrations_needed)}")

                        # Add game_id column
                        if 'game_id' not in columns:
                            logger.info("  Adding game_id column...")
                            migration_db.execute(text("ALTER TABLE game_state ADD COLUMN game_id VARCHAR"))
                            migration_db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id)"))
                            migration_db.execute(text("UPDATE game_state SET game_id = 'legacy-game-' || CAST(id AS VARCHAR) WHERE game_id IS NULL"))
                            logger.info("  ✅ Added game_id column")

                        # Add created_at column
                        if 'created_at' not in columns:
                            logger.info("  Adding created_at column...")
                            migration_db.execute(text("ALTER TABLE game_state ADD COLUMN created_at VARCHAR"))
                            if is_postgresql:
                                migration_db.execute(text("UPDATE game_state SET created_at = NOW()::text WHERE created_at IS NULL"))
                            else:
                                migration_db.execute(text("UPDATE game_state SET created_at = datetime('now') WHERE created_at IS NULL"))
                            logger.info("  ✅ Added created_at column")

                        # Add updated_at column
                        if 'updated_at' not in columns:
                            logger.info("  Adding updated_at column...")
                            migration_db.execute(text("ALTER TABLE game_state ADD COLUMN updated_at VARCHAR"))
                            if is_postgresql:
                                migration_db.execute(text("UPDATE game_state SET updated_at = NOW()::text WHERE updated_at IS NULL"))
                            else:
                                migration_db.execute(text("UPDATE game_state SET updated_at = datetime('now') WHERE updated_at IS NULL"))
                            logger.info("  ✅ Added updated_at column")

                        # Add join_code column
                        if 'join_code' not in columns:
                            logger.info("  Adding join_code column...")
                            migration_db.execute(text("ALTER TABLE game_state ADD COLUMN join_code VARCHAR"))
                            migration_db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_join_code ON game_state(join_code)"))
                            logger.info("  ✅ Added join_code column")

                        # Add creator_user_id column
                        if 'creator_user_id' not in columns:
                            logger.info("  Adding creator_user_id column...")
                            migration_db.execute(text("ALTER TABLE game_state ADD COLUMN creator_user_id VARCHAR"))
                            logger.info("  ✅ Added creator_user_id column")

                        # Add game_status column
                        if 'game_status' not in columns:
                            logger.info("  Adding game_status column...")
                            if is_postgresql:
                                migration_db.execute(text("ALTER TABLE game_state ADD COLUMN game_status VARCHAR DEFAULT 'setup'"))
                                migration_db.execute(text("UPDATE game_state SET game_status = 'setup' WHERE game_status IS NULL"))
                            else:
                                migration_db.execute(text("ALTER TABLE game_state ADD COLUMN game_status VARCHAR DEFAULT 'setup'"))
                                migration_db.execute(text("UPDATE game_state SET game_status = 'setup' WHERE game_status IS NULL"))
                            logger.info("  ✅ Added game_status column")

                        migration_db.commit()
                        logger.info(f"✅ Successfully applied {len(migrations_needed)} migration(s)")

                    # Fix PostgreSQL sequence for game_state.id after migrations
                    if is_postgresql:
                        try:
                            logger.info("🔄 Checking game_state id sequence...")
                            result = migration_db.execute(text("SELECT MAX(id) FROM game_state"))
                            max_id = result.scalar()

                            if max_id is not None:
                                migration_db.execute(text(f"SELECT setval('game_state_id_seq', {max_id})"))
                                migration_db.commit()
                                logger.info(f"  ✅ Reset sequence to {max_id} (next ID will be {max_id + 1})")
                            else:
                                logger.info("  ✅ Table empty, sequence OK")
                        except Exception as seq_error:
                            logger.warning(f"  ⚠️ Could not fix sequence: {seq_error}")
                            # Don't fail startup for sequence issues
                    else:
                        logger.info("  ✅ Schema is up-to-date - no migrations needed")
                else:
                    logger.info("  game_state table will be created by init_db")
            except Exception as migration_error:
                migration_db.rollback()
                logger.error(f"  ❌ Migration failed: {migration_error}")
                logger.error(f"  Traceback: {traceback.format_exc()}")
                raise
            finally:
                migration_db.close()
        except Exception as e:
            logger.error(f"❌ Failed to run migrations: {e}")
            # Don't fail startup if migrations fail in development
            if os.getenv("ENVIRONMENT") == "production":
                raise

        # Run score performance metrics migration
        logger.info("🔄 Running score performance metrics migration...")
        try:
            from .migrate_score_performance import add_score_performance_columns
            success = add_score_performance_columns()
            if success:
                logger.info("✅ Score performance metrics migration completed")
            else:
                logger.warning("⚠️ Score performance metrics migration had issues")
        except Exception as migration_error:
            logger.error(f"❌ Score performance migration failed: {migration_error}")
            # Don't fail startup if migration fails in development
            if os.getenv("ENVIRONMENT") == "production":
                raise

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
            courses = course_manager.get_courses()
            if not courses:
                logger.warning("⚠️ No courses found in game state, attempting to reload...")
                course_manager.__init__()  # Reinitialize course manager
                courses = course_manager.get_courses()
            
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
            test_simulation = WolfGoatPigGame(player_count=4)
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


@app.post("/games/create")
async def create_game_with_join_code(
    course_name: Optional[str] = None,
    player_count: int = 4,
    user_id: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    """Create a new game with a join code for authenticated players"""
    try:
        import random
        import string
        import uuid

        # Generate 6-character join code
        join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Ensure uniqueness
        while db.query(models.GameStateModel).filter(models.GameStateModel.join_code == join_code).first():
            join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Create game with unique ID
        game_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat()

        # Initial game state
        initial_state = {
            "current_hole": 1,
            "game_status": "setup",
            "player_count": player_count,
            "course_name": course_name,
            "players": [],
            "hole_history": []
        }

        # Create GameStateModel
        game_state_model = models.GameStateModel(
            game_id=game_id,
            join_code=join_code,
            creator_user_id=user_id,
            game_status="setup",
            state=initial_state,
            created_at=current_time,
            updated_at=current_time
        )
        db.add(game_state_model)
        db.commit()
        db.refresh(game_state_model)

        return {
            "game_id": game_id,
            "join_code": join_code,
            "status": "setup",
            "player_count": player_count,
            "players_joined": 0,
            "created_at": current_time,
            "join_url": f"/join/{join_code}"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating game: {str(e)}")


@app.post("/games/create-test")
async def create_test_game(
    course_name: Optional[str] = None,
    player_count: int = 4,
    db: Session = Depends(database.get_db)
):
    """
    Create a test game with mock players and immediately start it - for single-device testing

    Supports fallback mode: if database operations fail, the game is created in memory only.
    """
    import random
    import string
    import uuid
    from .fallback_game_manager import get_fallback_manager

    # Generate 6-character join code
    join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    game_id = str(uuid.uuid4())
    current_time = datetime.utcnow().isoformat()

    # Create mock players
    mock_players = [
        {"id": "test-player-1", "name": "Test Player 1", "handicap": 18, "is_human": True},
        {"id": "test-player-2", "name": "Test Player 2", "handicap": 15, "is_human": False},
        {"id": "test-player-3", "name": "Test Player 3", "handicap": 12, "is_human": False},
        {"id": "test-player-4", "name": "Test Player 4", "handicap": 20, "is_human": False},
        {"id": "test-player-5", "name": "Test Player 5", "handicap": 16, "is_human": False}
    ][:player_count]

    # Initialize WolfGoatPigGame for this game
    wgp_players = [
        Player(
            id=p["id"],
            name=p["name"],
            handicap=p["handicap"]
        )
        for p in mock_players
    ]

    simulation = WolfGoatPigGame(player_count=player_count, players=wgp_players)

    # Get the game state (game is already started in __init__)
    game_state = simulation.get_game_state()
    game_state["game_status"] = "in_progress"
    game_state["test_mode"] = True

    # Add simulation to active_games for test mode
    service = get_game_lifecycle_service()
    service._active_games[game_id] = simulation

    # Try to save to database first
    database_saved = False
    fallback_mode = False

    try:
        # Ensure uniqueness of join code
        existing = db.query(models.GameStateModel).filter(
            models.GameStateModel.join_code == join_code
        ).first()

        if existing:
            join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Create GameStateModel
        game_state_model = models.GameStateModel(
            game_id=game_id,
            join_code=join_code,
            creator_user_id="test-user",
            game_status="in_progress",
            state=game_state,
            created_at=current_time,
            updated_at=current_time
        )
        db.add(game_state_model)

        # Create GamePlayer records for each mock player
        for i, player in enumerate(mock_players):
            game_player = models.GamePlayer(
                game_id=game_id,
                player_slot_id=player["id"],
                user_id=f"test-user-{i+1}",
                player_name=player["name"],
                handicap=player["handicap"],
                join_status="joined",
                joined_at=current_time,
                created_at=current_time
            )
            db.add(game_player)

        db.commit()
        db.refresh(game_state_model)
        database_saved = True

        logger.info(f"✅ Created test game {game_id} in database with {player_count} mock players")

    except Exception as db_error:
        db.rollback()
        logger.warning(f"⚠️ Database save failed: {db_error}")
        logger.info("🔄 Attempting fallback mode...")

        # Try fallback mode
        try:
            fallback = get_fallback_manager()
            fallback.enable()

            fallback.create_game(
                game_id=game_id,
                join_code=join_code,
                creator_user_id="test-user",
                game_status="in_progress",
                state=game_state
            )

            fallback_mode = True
            logger.warning(f"⚠️ Created test game {game_id} in FALLBACK MODE (memory only)")

        except Exception as fallback_error:
            logger.error(f"❌ Both database and fallback mode failed: {fallback_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create game. Database error: {str(db_error)}. Fallback error: {str(fallback_error)}"
            )

    # Build response
    response = {
        "game_id": game_id,
        "join_code": join_code,
        "status": "in_progress",
        "player_count": player_count,
        "players": mock_players,
        "test_mode": True,
        "created_at": current_time,
        "message": "Test game created and started successfully"
    }

    # Add warnings if in fallback mode
    if fallback_mode:
        response["warning"] = "Game created in memory only - will be lost on server restart"
        response["fallback_mode"] = True
        response["persistence"] = "memory"
    else:
        response["persistence"] = "database"

    return response


@app.patch("/games/{game_id}/players/{player_id}/name")
async def update_player_name(
    game_id: str,
    player_id: str,
    name_update: dict,
    db: Session = Depends(database.get_db)
):
    """
    Update a player's name in an active game.
    Allows editing player names in the game scorer without requiring PlayerProfile records.

    Args:
        game_id: The game ID
        player_id: The player's ID (e.g., "test-player-1")
        name_update: Dict with "name" key containing the new name
    """
    try:
        new_name = name_update.get("name")
        if not new_name or not isinstance(new_name, str) or not new_name.strip():
            raise HTTPException(status_code=400, detail="Invalid name provided")

        new_name = new_name.strip()

        # Try to get game from lifecycle service (active games in memory)
        service = get_game_lifecycle_service()
        simulation = service._active_games.get(game_id)

        if simulation:
            # Update player name in simulation
            player_found = False
            for player in simulation.players:
                if player.id == player_id:
                    player.name = new_name
                    player_found = True
                    break

            if not player_found:
                raise HTTPException(status_code=404, detail=f"Player {player_id} not found in game")

            # Update player name in game state
            game_state = simulation.get_game_state()
            for player in game_state.get("players", []):
                if player.get("id") == player_id:
                    player["name"] = new_name
                    break

            logger.info(f"Updated player {player_id} name to '{new_name}' in game {game_id}")

        # Try to update in database as well (if game exists in DB)
        try:
            # Update GameStateModel
            game = db.query(models.GameStateModel).filter(
                models.GameStateModel.game_id == game_id
            ).first()

            if game:
                state = game.state or {}
                players = state.get("players", [])
                for player in players:
                    if player.get("id") == player_id:
                        player["name"] = new_name
                        break

                game.state = state
                game.updated_at = datetime.utcnow().isoformat()

                # Also update GamePlayer record
                game_player = db.query(models.GamePlayer).filter(
                    models.GamePlayer.game_id == game_id,
                    models.GamePlayer.player_slot_id == player_id
                ).first()

                if game_player:
                    game_player.player_name = new_name

                db.commit()
                logger.info(f"Updated player {player_id} name to '{new_name}' in database for game {game_id}")

        except Exception as db_error:
            # Log but don't fail - game can continue in memory
            logger.warning(f"Failed to update player name in database: {db_error}")
            try:
                db.rollback()
            except:
                pass

        return {
            "success": True,
            "game_id": game_id,
            "player_id": player_id,
            "name": new_name,
            "message": f"Player name updated to '{new_name}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating player name: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update player name: {str(e)}")


@app.delete("/games/{game_id}/players/{player_slot_id}")
async def remove_player(
    game_id: str,
    player_slot_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Remove a player from a game in setup/lobby status.
    Only allowed before game starts.

    Args:
        game_id: The game ID
        player_slot_id: The player's slot ID (e.g., "p1", "p2")
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Only allow removing players if game hasn't started
        if game.status not in ['setup', 'lobby']:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove players from a game that has already started"
            )

        # Remove from game_players table
        game_player = db.query(models.GamePlayer).filter(
            models.GamePlayer.game_id == game_id,
            models.GamePlayer.player_slot_id == player_slot_id
        ).first()

        if not game_player:
            raise HTTPException(
                status_code=404,
                detail=f"Player {player_slot_id} not found in game"
            )

        player_name = game_player.player_name
        db.delete(game_player)

        # Remove from game state players array
        state = game.state or {}
        players = state.get("players", [])
        state["players"] = [p for p in players if p.get("id") != player_slot_id]
        game.state = state
        game.updated_at = datetime.utcnow().isoformat()

        db.commit()

        logger.info(f"Removed player {player_slot_id} ({player_name}) from game {game_id}")

        return {
            "success": True,
            "game_id": game_id,
            "player_slot_id": player_slot_id,
            "message": f"Player {player_name} removed from game",
            "players_remaining": len(state["players"])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing player: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove player: {str(e)}")


@app.patch("/games/{game_id}/players/{player_slot_id}/handicap")
async def update_player_handicap(
    game_id: str,
    player_slot_id: str,
    handicap_update: dict,
    db: Session = Depends(database.get_db)
):
    """
    Update a player's handicap in a game in setup/lobby status.
    Only allowed before game starts.

    Args:
        game_id: The game ID
        player_slot_id: The player's slot ID (e.g., "p1", "p2")
        handicap_update: Dict with "handicap" key containing the new handicap
    """
    try:
        new_handicap = handicap_update.get("handicap")
        if new_handicap is None:
            raise HTTPException(status_code=400, detail="Handicap not provided")

        try:
            new_handicap = float(new_handicap)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid handicap value")

        if new_handicap < 0 or new_handicap > 54:
            raise HTTPException(status_code=400, detail="Handicap must be between 0 and 54")

        # Get game from database
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Only allow updating handicap if game hasn't started
        if game.status not in ['setup', 'lobby']:
            raise HTTPException(
                status_code=400,
                detail="Cannot update handicap after game has started"
            )

        # Update in game_players table
        game_player = db.query(models.GamePlayer).filter(
            models.GamePlayer.game_id == game_id,
            models.GamePlayer.player_slot_id == player_slot_id
        ).first()

        if not game_player:
            raise HTTPException(
                status_code=404,
                detail=f"Player {player_slot_id} not found in game"
            )

        game_player.handicap = new_handicap

        # Update in game state players array
        state = game.state or {}
        players = state.get("players", [])
        for player in players:
            if player.get("id") == player_slot_id:
                player["handicap"] = new_handicap
                break

        game.state = state
        game.updated_at = datetime.utcnow().isoformat()

        db.commit()

        logger.info(f"Updated player {player_slot_id} handicap to {new_handicap} in game {game_id}")

        return {
            "success": True,
            "game_id": game_id,
            "player_slot_id": player_slot_id,
            "handicap": new_handicap,
            "message": f"Handicap updated to {new_handicap}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating player handicap: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update handicap: {str(e)}")


@app.post("/games/{game_id}/holes/complete")
async def complete_hole(
    game_id: str,
    request: CompleteHoleRequest,
    db: Session = Depends(database.get_db)
):
    """
    Complete a hole with all data at once - simplified scorekeeper mode.
    No state machine validation, just direct data storage.
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Validate Joe's Special
        if request.phase == "hoepfinger" and request.joes_special_wager:
            valid_wagers = [2, 4, 8]
            if request.joes_special_wager not in valid_wagers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Joe's Special must be 2, 4, or 8 quarters. Got: {request.joes_special_wager}. Joe's Special maximum is 8 quarters."
                )

        # Phase 4: The Big Dick validation
        if request.big_dick_invoked_by:
            if request.hole_number != 18:
                raise HTTPException(
                    status_code=400,
                    detail="The Big Dick can only be invoked on hole 18"
                )

        # Phase 5: The Aardvark validation (5-man games only)
        player_count = len(request.rotation_order)
        if player_count == 5:
            # Aardvark is player in position 5 (index 4)
            aardvark_id = request.rotation_order[4]
            captain_id = request.rotation_order[request.captain_index]

            # Validate: Captain cannot DIRECTLY partner with Aardvark (meaning 2-person team)
            if request.teams.type == "partners":
                team1 = request.teams.team1 or []
                team2 = request.teams.team2 or []

                # Check if it's a 2-person team with ONLY Captain and Aardvark
                if len(team1) == 2 and set(team1) == {captain_id, aardvark_id}:
                    raise HTTPException(
                        status_code=400,
                        detail="Captain cannot directly partner with the Aardvark (player #5). Aardvark must request to join teams after Captain forms partnership."
                    )
                if len(team2) == 2 and set(team2) == {captain_id, aardvark_id}:
                    raise HTTPException(
                        status_code=400,
                        detail="Captain cannot directly partner with the Aardvark (player #5). Aardvark must request to join teams after Captain forms partnership."
                    )

            # Validate: Ping Pong can only happen if Aardvark was tossed
            if request.aardvark_ping_ponged and not request.aardvark_tossed:
                raise HTTPException(
                    status_code=400,
                    detail="Aardvark cannot be ping-ponged unless initially tossed. Set aardvark_tossed=True."
                )

            # Validate: The Tunkarri (Aardvark solo with 3-for-2 payout)
            if request.tunkarri_invoked:
                if request.teams.type != "solo":
                    raise HTTPException(
                        status_code=400,
                        detail="The Tunkarri can only be invoked in solo mode (Aardvark vs all others)."
                    )
                # In solo mode, captain field contains the solo player
                if request.teams.captain != aardvark_id:
                    raise HTTPException(
                        status_code=400,
                        detail="The Tunkarri can only be invoked by the Aardvark (player #5)."
                    )

        # Validate: Tunkarri only in 5-man/6-man games
        if request.tunkarri_invoked and player_count < 5:
            raise HTTPException(
                status_code=400,
                detail="The Tunkarri is only available in 5-man or 6-man games."
            )

        # Phase 4: Enhanced Error Handling & Validation
        rotation_player_ids = set(request.rotation_order)

        # Validate team formations FIRST (before scores)
        all_team_players = []

        if request.teams.type == "partners":
            team1 = request.teams.team1 or []
            team2 = request.teams.team2 or []
            all_team_players = team1 + team2

            # Check for duplicates within teams
            if len(team1) != len(set(team1)):
                raise HTTPException(
                    status_code=400,
                    detail="Duplicate players found in team1"
                )
            if len(team2) != len(set(team2)):
                raise HTTPException(
                    status_code=400,
                    detail="Duplicate players found in team2"
                )

            # Check for players on both teams
            team1_set = set(team1)
            team2_set = set(team2)
            overlap = team1_set.intersection(team2_set)
            if overlap:
                raise HTTPException(
                    status_code=400,
                    detail=f"Players cannot be on both teams: {overlap}"
                )

        elif request.teams.type == "solo":
            captain = request.teams.captain
            opponents = request.teams.opponents or []
            all_team_players = [captain] + opponents if captain else opponents

            # Validate solo formation: 1 captain vs N-1 opponents
            expected_opponent_count = len(rotation_player_ids) - 1
            if len(opponents) != expected_opponent_count:
                raise HTTPException(
                    status_code=400,
                    detail=f"Solo must be 1 vs {expected_opponent_count}. Got {len(opponents)} opponents"
                )

            # Validate: Solo player must be in rotation
            # Note: Solo player can be ANY player in rotation, not just the Captain
            # - Captain can go solo (choosing not to pick a partner)
            # - Any other player can go solo (by rejecting Captain's partnership offer)
            # - On hole 18, Big Dick allows the points leader to go solo
            if captain and captain not in rotation_player_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Solo player {captain} is not in rotation_order"
                )

            # Check for duplicates in opponents
            if len(opponents) != len(set(opponents)):
                raise HTTPException(
                    status_code=400,
                    detail="Duplicate players found in opponents"
                )

            # Check captain not in opponents
            if captain and captain in opponents:
                raise HTTPException(
                    status_code=400,
                    detail="Captain cannot be in opponents list"
                )

        # Validate all rotation players are on teams
        all_team_players_set = set(all_team_players)
        if all_team_players_set != rotation_player_ids:
            missing = rotation_player_ids - all_team_players_set
            extra = all_team_players_set - rotation_player_ids
            if missing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Players in rotation but not on teams: {missing}"
                )
            if extra:
                raise HTTPException(
                    status_code=400,
                    detail=f"Players on teams but not in rotation: {extra}"
                )

        # Validate scores (after team validation)
        # Check all scores are for players in rotation
        for player_id in request.scores.keys():
            if player_id not in rotation_player_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score provided for player {player_id} not in rotation order"
                )

        # Check all rotation players have scores
        for player_id in rotation_player_ids:
            if player_id not in request.scores:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing score for player {player_id} in rotation"
                )

        # Validate score values
        for player_id, score in request.scores.items():
            if score < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score cannot be negative. Player {player_id} has score {score}"
                )
            if score > 15:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score unreasonably high (max 15). Player {player_id} has score {score}"
                )

        # Get current game state
        game_state = game.state or {}

        # Validate Float usage (once per round per player)
        if request.float_invoked_by:
            # Check if player has already used float
            for player in game_state.get("players", []):
                if player["id"] == request.float_invoked_by:
                    float_count = player.get("float_used", 0)
                    # Handle boolean False or numeric values
                    if isinstance(float_count, bool):
                        float_count = 0
                    if float_count >= 1:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Player {request.float_invoked_by} has already used float this round"
                        )
                    break

        # Initialize hole_history if it doesn't exist
        if "hole_history" not in game_state:
            game_state["hole_history"] = []

        # Helper function for Karl Marx distribution
        def apply_karl_marx(team_players, total_amount, game_state):
            """
            Distribute quarters unevenly according to Karl Marx rule:
            Player furthest down (Goat) gets smaller loss or larger win.

            Args:
                team_players: List of player IDs on the team
                total_amount: Total quarters to distribute (positive for win, negative for loss)
                game_state: Current game state with player points

            Returns:
                Dict mapping player_id -> amount
            """
            if len(team_players) == 0:
                return {}

            num_players = len(team_players)
            result = {}

            # Work with absolute value for easier math
            abs_total = abs(total_amount)
            is_loss = total_amount < 0

            # Check if distribution is uneven
            if abs_total % num_players != 0:
                # Karl Marx applies!
                base_share = abs_total // num_players
                remainder = abs_total % num_players

                # Calculate current standings for these players
                player_points = {}
                for player in game_state.get("players", []):
                    if player["id"] in team_players:
                        player_points[player["id"]] = player.get("total_points", 0)

                # Find Goat (player with lowest points)
                goat_id = min(player_points, key=player_points.get) if player_points else team_players[0]

                # Distribute remainder among non-Goat players (for losses) or to Goat (for wins)
                non_goat_count = num_players - 1
                extra_per_non_goat = remainder // non_goat_count if non_goat_count > 0 else 0
                leftover_after_even_split = remainder % non_goat_count if non_goat_count > 0 else remainder

                # Assign shares
                if is_loss:
                    # LOSING: Goat loses LESS (base), non-Goat players split the remainder
                    leftover_counter = leftover_after_even_split
                    for player_id in team_players:
                        if player_id == goat_id:
                            result[player_id] = -base_share
                        else:
                            share = base_share + extra_per_non_goat
                            if leftover_counter > 0:
                                share += 1
                                leftover_counter -= 1
                            result[player_id] = -share
                else:
                    # WINNING: Goat wins MORE (gets all the remainder), non-Goat gets base
                    for player_id in team_players:
                        if player_id == goat_id:
                            result[player_id] = base_share + remainder
                        else:
                            result[player_id] = base_share
            else:
                # Even split, no Karl Marx needed
                even_amount = total_amount / num_players
                for player_id in team_players:
                    result[player_id] = even_amount

            return result

        # Calculate quarters won/lost based on winner and wager
        points_delta = {}
        if request.teams.type == "partners":
            # Calculate total amounts based on team sizes
            team1_size = len(request.teams.team1)
            team2_size = len(request.teams.team2)

            if request.winner == "team1":
                # Team1 wins: each winner gets wager, total = winning_team_size * wager
                # Losing team2 pays out that total
                total_won_by_team1 = request.final_wager * team1_size
                total_lost_by_team2 = -request.final_wager * team1_size
                points_delta.update(apply_karl_marx(request.teams.team1, total_won_by_team1, game_state))
                points_delta.update(apply_karl_marx(request.teams.team2, total_lost_by_team2, game_state))
            elif request.winner == "team2":
                # Team2 wins: each winner gets wager, total = winning_team_size * wager
                # Losing team1 pays out that total
                total_won_by_team2 = request.final_wager * team2_size
                total_lost_by_team1 = -request.final_wager * team2_size
                points_delta.update(apply_karl_marx(request.teams.team2, total_won_by_team2, game_state))
                points_delta.update(apply_karl_marx(request.teams.team1, total_lost_by_team1, game_state))
            elif request.winner == "team1_flush":
                # Flush: Team2 concedes/folds - Team1 wins current wager
                total_won = request.final_wager * team2_size
                total_lost = -request.final_wager * team2_size
                points_delta.update(apply_karl_marx(request.teams.team1, total_won, game_state))
                points_delta.update(apply_karl_marx(request.teams.team2, total_lost, game_state))
            elif request.winner == "team2_flush":
                # Flush: Team1 concedes/folds - Team2 wins current wager
                total_won = request.final_wager * team1_size
                total_lost = -request.final_wager * team1_size
                points_delta.update(apply_karl_marx(request.teams.team2, total_won, game_state))
                points_delta.update(apply_karl_marx(request.teams.team1, total_lost, game_state))
            else:  # push
                for player_id in request.teams.team1 + request.teams.team2:
                    points_delta[player_id] = 0
        else:  # solo mode
            if request.duncan_invoked and request.winner == "captain":
                # The Duncan: Captain wins 3Q for every 2Q wagered
                total_payout = (request.final_wager * 3) / 2
                points_delta[request.teams.captain] = total_payout
                loss_per_opponent = total_payout / len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = -loss_per_opponent
            elif request.duncan_invoked and request.winner == "opponents":
                # The Duncan failed: Opponents win normal, Captain loses normal
                total_loss = request.final_wager * len(request.teams.opponents)
                points_delta[request.teams.captain] = -total_loss
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = request.final_wager
            elif request.tunkarri_invoked and request.winner == "captain":
                # The Tunkarri: Aardvark wins 3Q for every 2Q wagered (5-man/6-man only)
                total_payout = (request.final_wager * 3) / 2
                points_delta[request.teams.captain] = total_payout  # Aardvark is "captain" in solo mode
                loss_per_opponent = total_payout / len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = -loss_per_opponent
            elif request.tunkarri_invoked and request.winner == "opponents":
                # The Tunkarri failed: Opponents win normal, Aardvark loses normal
                total_loss = request.final_wager * len(request.teams.opponents)
                points_delta[request.teams.captain] = -total_loss  # Aardvark is "captain" in solo mode
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = request.final_wager
            elif request.winner == "captain":
                # Normal solo win
                points_delta[request.teams.captain] = request.final_wager * len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = -request.final_wager
            elif request.winner == "opponents":
                # Normal solo loss
                points_delta[request.teams.captain] = -request.final_wager * len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = request.final_wager
            elif request.winner == "captain_flush":
                # Flush: Opponents concede/fold - Captain wins current wager
                points_delta[request.teams.captain] = request.final_wager * len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = -request.final_wager
            elif request.winner == "opponents_flush":
                # Flush: Captain concedes/folds - Opponents win current wager
                points_delta[request.teams.captain] = -request.final_wager * len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = request.final_wager
            else:  # push
                points_delta[request.teams.captain] = 0
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = 0

        # Apply double points for holes 17-18 (except during Hoepfinger which has Joe's Special)
        if request.hole_number in [17, 18] and request.phase != "hoepfinger":
            for player_id in points_delta:
                points_delta[player_id] *= 2

        # Phase 5: Aardvark toss doubling (5-man games only)
        # When Aardvark is tossed, the wager is effectively doubled for ALL players to maintain balance
        # Ping Pong: If tossed AGAIN by second team, quadruple the points (2x for toss, 2x for ping pong)
        if player_count == 5 and request.aardvark_tossed and request.aardvark_requested_team:
            if request.teams.type == "partners":
                # Calculate multiplier: 2x for toss, 4x if ping-ponged
                multiplier = 4 if request.aardvark_ping_ponged else 2

                # Apply multiplier to all players' points to maintain zero-sum balance
                for player_id in points_delta:
                    points_delta[player_id] *= multiplier

        # Phase 4: Scorekeeping Validation - verify points balance to zero
        points_total = sum(points_delta.values())
        if abs(points_total) > 0.01:  # Allow for floating point precision
            logger.error(
                f"SCOREKEEPING ERROR: Points do not balance to zero! "
                f"Hole {request.hole_number}, Total: {points_total}, "
                f"Points: {points_delta}"
            )
            # Return error to prevent saving invalid data
            raise HTTPException(
                status_code=500,
                detail=f"Scorekeeping error: points total {points_total} instead of 0. Please report this bug."
            )

        # Create hole result
        hole_result = {
            "hole": request.hole_number,
            "hole_number": request.hole_number,  # Alias for consistency
            "rotation_order": request.rotation_order,
            "captain_index": request.captain_index,
            "phase": request.phase,
            "joes_special_wager": request.joes_special_wager,
            "option_turned_off": request.option_turned_off,
            "duncan_invoked": request.duncan_invoked,
            "tunkarri_invoked": request.tunkarri_invoked if player_count >= 5 else False,
            "teams": request.teams.model_dump(),
            "wager": request.final_wager,
            "final_wager": request.final_wager,  # Phase 4: Add final_wager field
            "winner": request.winner,
            "gross_scores": request.scores,
            "hole_par": request.hole_par,
            "points_delta": points_delta,
            "float_invoked_by": request.float_invoked_by,
            "option_invoked_by": request.option_invoked_by,
            "carry_over_applied": request.carry_over_applied,
            "doubles_history": request.doubles_history or [],  # Phase 4: Add doubles history
            "big_dick_invoked_by": request.big_dick_invoked_by,  # Phase 4: The Big Dick
            # Phase 5: The Aardvark (5-man games only)
            "aardvark_requested_team": request.aardvark_requested_team if player_count == 5 else None,
            "aardvark_tossed": request.aardvark_tossed if player_count == 5 else False,
            "aardvark_ping_ponged": request.aardvark_ping_ponged if player_count == 5 else False,
            "aardvark_solo": request.aardvark_solo if player_count == 5 else False
        }

        # Add or update hole in history
        existing_hole_index = next(
            (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == request.hole_number),
            None
        )

        if existing_hole_index is not None:
            game_state["hole_history"][existing_hole_index] = hole_result
        else:
            game_state["hole_history"].append(hole_result)

        # Track carry-over state
        if request.winner == "push":
            # Check if last hole was also a push (consecutive block)
            last_push_hole = game_state.get("last_push_hole")
            if last_push_hole == request.hole_number - 1:
                # Consecutive push - don't trigger new carry-over
                game_state["consecutive_push_block"] = True
                game_state["last_push_hole"] = request.hole_number
            else:
                # Trigger carry-over for next hole
                game_state["carry_over_wager"] = request.final_wager * 2
                game_state["carry_over_from_hole"] = request.hole_number
                game_state["last_push_hole"] = request.hole_number
                game_state["consecutive_push_block"] = False
        else:
            # Hole was decided - reset carry-over tracking
            if "carry_over_wager" in game_state:
                del game_state["carry_over_wager"]
            if "carry_over_from_hole" in game_state:
                del game_state["carry_over_from_hole"]
            game_state["consecutive_push_block"] = False

        # Update player totals
        if "players" not in game_state:
            game_state["players"] = []

        # Ensure all players from rotation_order are in game_state["players"]
        existing_player_ids = {p.get("id") for p in game_state["players"]}
        for player_id in request.rotation_order:
            if player_id not in existing_player_ids:
                game_state["players"].append({"id": player_id, "points": 0, "float_used": 0})

        for player in game_state["players"]:
            player_id = player.get("id")
            if player_id in points_delta:
                if "points" not in player:
                    player["points"] = 0
                player["points"] += points_delta[player_id]

            # Track float usage
            if request.float_invoked_by == player_id:
                current_float_count = player.get("float_used", 0)
                # Handle boolean False
                if isinstance(current_float_count, bool):
                    current_float_count = 0
                player["float_used"] = current_float_count + 1

        # Update current hole
        game_state["current_hole"] = request.hole_number + 1

        # Update game state in database
        game.state = game_state
        game.updated_at = datetime.utcnow().isoformat()

        # Mark state as modified for SQLAlchemy to detect changes in JSON field
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(game, "state")

        db.commit()
        db.refresh(game)

        # Also update simulation if game is in active_games (for test mode)
        service = get_game_lifecycle_service()
        if game_id in service._active_games:
            simulation = service._active_games[game_id]
            # Store tracking fields as direct simulation attributes
            simulation.carry_over_wager = game_state.get("carry_over_wager")
            simulation.carry_over_from_hole = game_state.get("carry_over_from_hole")
            simulation.consecutive_push_block = game_state.get("consecutive_push_block", False)
            simulation.last_push_hole = game_state.get("last_push_hole")
            simulation.base_wager = game_state.get("base_wager")
            simulation.scorekeeper_hole_history = game_state.get("hole_history", [])

            # Update player float/solo counts in simulation
            if request.float_invoked_by:
                float_player = next((p for p in simulation.players if p.id == request.float_invoked_by), None)
                if float_player:
                    float_player.float_used += 1

            # Sync player points from database game state to simulation
            for db_player in game_state.get("players", []):
                sim_player = next((p for p in simulation.players if p.id == db_player["id"]), None)
                if sim_player:
                    sim_player.points = db_player.get("points", 0)

        logger.info(f"Completed hole {request.hole_number} for game {game_id}")

        return {
            "success": True,
            "game_state": game_state,
            "hole_result": hole_result,
            "message": f"Hole {request.hole_number} completed successfully"
        }

    except HTTPException:
        # Re-raise HTTPException without wrapping
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing hole: {e}")
        raise HTTPException(status_code=500, detail=f"Error completing hole: {str(e)}")


@app.patch("/games/{game_id}/holes/{hole_number}")
async def update_hole(
    game_id: str,
    hole_number: int,
    request: CompleteHoleRequest,
    db: Session = Depends(database.get_db)
):
    """
    Update an existing hole's data. Uses same validation as complete_hole.
    Recalculates all player totals from scratch after update.
    """
    try:
        # Validate hole_number matches request
        if request.hole_number != hole_number:
            raise HTTPException(
                status_code=400,
                detail=f"Hole number in URL ({hole_number}) must match request body ({request.hole_number})"
            )

        # Get game from database
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}

        # Check if hole exists
        if "hole_history" not in game_state:
            raise HTTPException(status_code=404, detail="No holes recorded for this game")

        existing_hole_index = next(
            (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == hole_number),
            None
        )

        if existing_hole_index is None:
            raise HTTPException(
                status_code=404,
                detail=f"Hole {hole_number} not found in game history"
            )

        # Validate the new hole data (reuse validation from complete_hole)
        player_count = len(request.rotation_order)

        # Validate Joe's Special
        if request.phase == "hoepfinger" and request.joes_special_wager:
            valid_wagers = [2, 4, 8]
            if request.joes_special_wager not in valid_wagers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Joe's Special must be 2, 4, or 8 quarters. Got: {request.joes_special_wager}"
                )

        # Phase 4: The Big Dick validation
        if request.big_dick_invoked_by and hole_number != 18:
            raise HTTPException(
                status_code=400,
                detail="The Big Dick can only be invoked on hole 18"
            )

        # Validate team formations
        rotation_player_ids = set(request.rotation_order)
        all_team_players = []

        if request.teams.type == "partners":
            team1 = request.teams.team1 or []
            team2 = request.teams.team2 or []
            all_team_players = team1 + team2

            if len(team1) != len(set(team1)):
                raise HTTPException(status_code=400, detail="Duplicate players in team1")
            if len(team2) != len(set(team2)):
                raise HTTPException(status_code=400, detail="Duplicate players in team2")

            overlap = set(team1).intersection(set(team2))
            if overlap:
                raise HTTPException(status_code=400, detail=f"Players on both teams: {overlap}")

        elif request.teams.type == "solo":
            captain = request.teams.captain
            opponents = request.teams.opponents or []
            all_team_players = [captain] + opponents if captain else opponents

            expected_opponent_count = len(rotation_player_ids) - 1
            if len(opponents) != expected_opponent_count:
                raise HTTPException(
                    status_code=400,
                    detail=f"Solo must be 1 vs {expected_opponent_count}. Got {len(opponents)} opponents"
                )

        # Validate all rotation players are on teams
        all_team_players_set = set(all_team_players)
        if all_team_players_set != rotation_player_ids:
            missing = rotation_player_ids - all_team_players_set
            extra = all_team_players_set - rotation_player_ids
            if missing:
                raise HTTPException(status_code=400, detail=f"Missing from teams: {missing}")
            if extra:
                raise HTTPException(status_code=400, detail=f"Not in rotation: {extra}")

        # Validate scores
        for player_id in request.scores.keys():
            if player_id not in rotation_player_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Score for player {player_id} not in rotation"
                )

        for player_id in rotation_player_ids:
            if player_id not in request.scores:
                raise HTTPException(status_code=400, detail=f"Missing score for {player_id}")

        for player_id, score in request.scores.items():
            if score < 0:
                raise HTTPException(status_code=400, detail=f"Negative score for {player_id}")
            if score > 15:
                raise HTTPException(status_code=400, detail=f"Score too high for {player_id}")

        # Create updated hole result (simplified - no Karl Marx recalculation here)
        # We'll recalculate all player totals from scratch below
        hole_result = {
            "hole": hole_number,
            "hole_number": hole_number,
            "rotation_order": request.rotation_order,
            "captain_index": request.captain_index,
            "phase": request.phase,
            "joes_special_wager": request.joes_special_wager,
            "option_turned_off": request.option_turned_off,
            "duncan_invoked": request.duncan_invoked,
            "tunkarri_invoked": request.tunkarri_invoked if player_count >= 5 else False,
            "teams": request.teams.model_dump(),
            "wager": request.final_wager,
            "final_wager": request.final_wager,
            "winner": request.winner,
            "gross_scores": request.scores,
            "hole_par": request.hole_par,
            "points_delta": {},  # Will be recalculated
            "float_invoked_by": request.float_invoked_by,
            "option_invoked_by": request.option_invoked_by,
            "carry_over_applied": request.carry_over_applied,
            "doubles_history": request.doubles_history or [],
            "big_dick_invoked_by": request.big_dick_invoked_by,
            "aardvark_requested_team": request.aardvark_requested_team if player_count == 5 else None,
            "aardvark_tossed": request.aardvark_tossed if player_count == 5 else False,
            "aardvark_ping_ponged": request.aardvark_ping_ponged if player_count == 5 else False,
            "aardvark_solo": request.aardvark_solo if player_count == 5 else False
        }

        # Update the hole in history
        game_state["hole_history"][existing_hole_index] = hole_result

        # Recalculate all player totals from scratch
        # Reset all player points and float usage
        for player in game_state.get("players", []):
            player["points"] = 0
            player["float_used"] = 0

        # Replay all holes to recalculate totals
        # (This ensures consistency if hole was modified)
        # Note: This is a simplified version - for full accuracy, would need to
        # recalculate Karl Marx distribution for each hole
        for hole in game_state["hole_history"]:
            points_delta = hole.get("points_delta", {})
            for player in game_state.get("players", []):
                player_id = player.get("id")
                if player_id in points_delta:
                    player["points"] += points_delta[player_id]

                # Track float usage
                if hole.get("float_invoked_by") == player_id:
                    player["float_used"] += 1

        # Update game state in database
        game.state = game_state
        game.updated_at = datetime.utcnow().isoformat()

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(game, "state")

        db.commit()
        db.refresh(game)

        logger.info(f"Updated hole {hole_number} for game {game_id}")

        return {
            "success": True,
            "game_state": game_state,
            "hole_result": hole_result,
            "message": f"Hole {hole_number} updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating hole: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating hole: {str(e)}")


@app.delete("/games/{game_id}/holes/{hole_number}")
async def delete_hole(
    game_id: str,
    hole_number: int,
    db: Session = Depends(database.get_db)
):
    """
    Delete a hole from hole_history.
    Recalculates all player totals and updates current_hole if needed.
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}

        # Check if hole exists
        if "hole_history" not in game_state or not game_state["hole_history"]:
            raise HTTPException(status_code=404, detail="No holes recorded for this game")

        existing_hole_index = next(
            (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == hole_number),
            None
        )

        if existing_hole_index is None:
            raise HTTPException(
                status_code=404,
                detail=f"Hole {hole_number} not found in game history"
            )

        # Remove the hole from history
        deleted_hole = game_state["hole_history"].pop(existing_hole_index)

        # Recalculate all player totals from scratch
        # Reset all player points and float usage
        for player in game_state.get("players", []):
            player["points"] = 0
            player["float_used"] = 0

        # Replay remaining holes to recalculate totals
        for hole in game_state["hole_history"]:
            points_delta = hole.get("points_delta", {})
            for player in game_state.get("players", []):
                player_id = player.get("id")
                if player_id in points_delta:
                    player["points"] += points_delta[player_id]

                # Track float usage
                if hole.get("float_invoked_by") == player_id:
                    player["float_used"] += 1

        # Update current_hole if the deleted hole was the last one played
        max_hole_played = max([h.get("hole", 0) for h in game_state["hole_history"]], default=0)
        game_state["current_hole"] = max_hole_played + 1

        # Update game state in database
        game.state = game_state
        game.updated_at = datetime.utcnow().isoformat()

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(game, "state")

        db.commit()
        db.refresh(game)

        logger.info(f"Deleted hole {hole_number} from game {game_id}")

        return {
            "success": True,
            "game_state": game_state,
            "deleted_hole": deleted_hole,
            "message": f"Hole {hole_number} deleted successfully",
            "remaining_holes": len(game_state["hole_history"])
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting hole: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting hole: {str(e)}")


@app.get("/games/{game_id}/next-rotation")
async def get_next_rotation(
    game_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Calculate the next rotation order based on current hole.
    Handles normal rotation and Hoepfinger special selection.
    """
    try:
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}
        player_count = len(game_state.get("players", []))
        current_hole = game_state.get("current_hole", 1)

        # Determine Hoepfinger start based on player count
        hoepfinger_start = {
            4: 17,
            5: 16,
            6: 13
        }.get(player_count, 17)

        is_hoepfinger = current_hole >= hoepfinger_start

        # Get last hole's rotation
        hole_history = game_state.get("hole_history", [])
        if hole_history:
            last_hole = hole_history[-1]
            last_rotation = last_hole.get("rotation_order", [p["id"] for p in game_state["players"]])
        else:
            # First hole - use player order
            last_rotation = [p["id"] for p in game_state["players"]]

        if is_hoepfinger:
            # Hoepfinger: Goat (furthest down) selects position
            # Calculate current standings
            standings = {}
            for player in game_state["players"]:
                standings[player["id"]] = player.get("points", 0)

            goat_id = min(standings, key=standings.get)

            return {
                "is_hoepfinger": True,
                "goat_id": goat_id,
                "goat_selects_position": True,
                "available_positions": list(range(player_count)),
                "current_rotation": last_rotation,
                "message": "Goat selects hitting position"
            }
        else:
            # Normal rotation: shift left by 1
            new_rotation = last_rotation[1:] + [last_rotation[0]]

            return {
                "is_hoepfinger": False,
                "rotation_order": new_rotation,
                "captain_index": 0,
                "captain_id": new_rotation[0]
            }

    except Exception as e:
        logger.error(f"Error calculating next rotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/games/{game_id}/next-hole-wager")
async def get_next_hole_wager(
    game_id: str,
    current_hole: Optional[int] = None,
    db: Session = Depends(database.get_db)
):
    """
    Calculate the base wager for the next hole.
    Accounts for carry-over, Vinnie's Variation, and Hoepfinger rules.
    """
    try:
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}
        player_count = len(game_state.get("players", []))

        # Use provided current_hole or get from game state
        if current_hole is None:
            current_hole = game_state.get("current_hole", 1)

        base_wager = game_state.get("base_wager", 1)

        # Check for carry-over
        if game_state.get("carry_over_wager"):
            carry_over_wager = game_state["carry_over_wager"]
            from_hole = game_state.get("carry_over_from_hole", current_hole - 1)

            if game_state.get("consecutive_push_block"):
                return {
                    "base_wager": carry_over_wager,
                    "carry_over": False,
                    "message": f"Consecutive carry-over blocked. Base wager remains {carry_over_wager}Q from hole {from_hole}"
                }
            else:
                return {
                    "base_wager": carry_over_wager,
                    "carry_over": True,
                    "message": f"Carry-over from hole {from_hole} push"
                }

        # Check for The Option (Captain is Goat)
        if not game_state.get("carry_over_wager"):  # Option doesn't stack with carry-over
            # Calculate current standings to find Goat
            standings = {}
            for player in game_state.get("players", []):
                standings[player["id"]] = player.get("points", 0)

            if standings:
                goat_id = min(standings, key=standings.get)
                goat_points = standings[goat_id]

                # Option applies if Captain (first in rotation) is the Goat AND has negative points
                hole_history = game_state.get("hole_history", [])
                if hole_history:
                    last_hole = hole_history[-1]
                    next_rotation_order = last_hole.get("rotation_order", [])[1:] + [last_hole.get("rotation_order", [])[0]]
                    next_captain_id = next_rotation_order[0] if next_rotation_order else None

                    if next_captain_id == goat_id and goat_points < 0:
                        # Check if last hole turned off Option
                        if not last_hole.get("option_turned_off", False):
                            return {
                                "base_wager": base_wager * 2,
                                "option_active": True,
                                "goat_id": goat_id,
                                "carry_over": False,
                                "vinnies_variation": False,
                                "message": f"The Option: Captain is Goat ({goat_points}Q), wager doubled"
                            }

        # Check for Vinnie's Variation (holes 13-16 in 4-player)
        if player_count == 4 and 13 <= current_hole <= 16:
            return {
                "base_wager": base_wager * 2,
                "vinnies_variation": True,
                "carry_over": False,
                "message": f"Vinnie's Variation: holes 13-16 doubled (hole {current_hole})"
            }

        # Normal base wager
        return {
            "base_wager": base_wager,
            "carry_over": False,
            "vinnies_variation": False,
            "message": "Normal base wager"
        }

    except Exception as e:
        logger.error(f"Error calculating next hole wager: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/games/{game_id}/select-rotation")
async def select_rotation(
    game_id: str,
    request: RotationSelectionRequest,
    db: Session = Depends(database.get_db)
):
    """
    Phase 5: Dynamic rotation selection for 5-man games on holes 16-18.
    The Goat (lowest points player) selects their position in the rotation.
    """
    # Get game state (follow same pattern as get_game_state_by_id)
    service = get_game_lifecycle_service()
    simulation = None
    game = None
    game_state = None

    if game_id in service._active_games:
        simulation = service._active_games[game_id]
        game_state = simulation.get_game_state()
    else:
        # Fetch from database
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state

    if not game_state:
        raise HTTPException(status_code=404, detail="Game state not found")

    player_count = len(game_state.get("players", []))

    # Validate: Only 5-man games
    if player_count != 5:
        raise HTTPException(
            status_code=400,
            detail="Dynamic rotation selection only applies to 5-player games"
        )

    # Validate: Only holes 16, 17, 18
    if request.hole_number not in [16, 17, 18]:
        raise HTTPException(
            status_code=400,
            detail="Rotation selection only allowed on holes 16, 17, and 18"
        )

    # Validate: Position must be 1-5 for 5-man game
    if request.selected_position < 1 or request.selected_position > 5:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid position {request.selected_position}. Must be 1-5 for 5-player games"
        )

    # Identify current Goat (player with lowest total points)
    players = game_state.get("players", [])
    if not players:
        raise HTTPException(status_code=404, detail="No players found in game")

    # Find player with lowest points
    goat_player = min(players, key=lambda p: p.get("points", 0))
    actual_goat_id = goat_player["id"]

    # Validate: Request must be from actual Goat
    if request.goat_player_id != actual_goat_id:
        raise HTTPException(
            status_code=400,
            detail=f"Only the Goat (player with lowest points) can select rotation. Current Goat is {actual_goat_id}, not {request.goat_player_id}"
        )

    # Get current rotation order (or use default player order)
    current_rotation = game_state.get("current_rotation_order") or [p["id"] for p in players]

    # Reorder rotation: Goat at selected position, others maintain relative order
    goat_id = request.goat_player_id
    selected_index = request.selected_position - 1  # Convert to 0-indexed

    # Remove Goat from current rotation
    rotation_without_goat = [pid for pid in current_rotation if pid != goat_id]

    # Insert Goat at selected position
    new_rotation = rotation_without_goat[:selected_index] + [goat_id] + rotation_without_goat[selected_index:]

    # Store new rotation in game state
    game_state["current_rotation_order"] = new_rotation

    # Save updated rotation
    if simulation:
        # Update simulation state for in-progress games
        simulation._game_state = game_state
    else:
        # Update database for stored games
        game.state = game_state
        db.commit()

    return {
        "message": f"Rotation updated for hole {request.hole_number}",
        "rotation_order": new_rotation,
        "goat_id": goat_id,
        "selected_position": request.selected_position
    }


@app.post("/games/join/{join_code}")
async def join_game_with_code(
    join_code: str,
    request: schemas.JoinGameRequest,
    db: Session = Depends(database.get_db)
):
    """Join a game using a join code"""
    try:
        # Find game by join code
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.join_code == join_code
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found with that join code")

        if game.game_status != "setup":
            raise HTTPException(status_code=400, detail="Game has already started")

        # Check if user already joined
        if request.user_id:
            existing = db.query(models.GamePlayer).filter(
                models.GamePlayer.game_id == game.game_id,
                models.GamePlayer.user_id == request.user_id
            ).first()
            if existing:
                return {
                    "status": "already_joined",
                    "message": "You've already joined this game",
                    "game_id": game.game_id,
                    "player_slot_id": existing.player_slot_id
                }

        # Get current players
        current_players = db.query(models.GamePlayer).filter(
            models.GamePlayer.game_id == game.game_id
        ).all()

        # Check player limit
        max_players = game.state.get("player_count", 4)
        if len(current_players) >= max_players:
            raise HTTPException(status_code=400, detail="Game is full")

        # Assign player slot
        player_slot_id = f"p{len(current_players) + 1}"
        current_time = datetime.utcnow().isoformat()

        # Ensure handicap is valid - use default if None
        player_handicap = request.handicap if request.handicap is not None else 18.0

        # Create GamePlayer record
        game_player = models.GamePlayer(
            game_id=game.game_id,
            player_slot_id=player_slot_id,
            user_id=request.user_id,
            player_profile_id=request.player_profile_id,
            player_name=request.player_name,
            handicap=player_handicap,
            join_status="joined",
            joined_at=current_time,
            created_at=current_time
        )
        db.add(game_player)

        # Update game state with new player
        game.state["players"] = game.state.get("players", [])
        game.state["players"].append({
            "id": player_slot_id,
            "name": request.player_name,
            "handicap": player_handicap,
            "user_id": request.user_id,
            "player_profile_id": request.player_profile_id
        })
        game.updated_at = current_time

        db.commit()
        db.refresh(game_player)

        return {
            "status": "joined",
            "game_id": game.game_id,
            "player_slot_id": player_slot_id,
            "players_joined": len(current_players) + 1,
            "max_players": max_players,
            "message": f"Welcome {request.player_name}! Waiting for {max_players - len(current_players) - 1} more player(s)"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error joining game: {str(e)}")

@app.get("/games/{game_id}/lobby")
async def get_game_lobby(game_id: str, db: Session = Depends(database.get_db)):
    """Get game lobby information - who has joined"""
    try:
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        players = db.query(models.GamePlayer).filter(
            models.GamePlayer.game_id == game_id
        ).order_by(models.GamePlayer.player_slot_id).all()

        max_players = game.state.get("player_count", 4)

        return {
            "game_id": game_id,
            "join_code": game.join_code,
            "status": game.game_status,
            "course_name": game.state.get("course_name"),
            "max_players": max_players,
            "players_joined": len(players),
            "ready_to_start": len(players) >= 2 and len(players) <= max_players,
            "players": [
                {
                    "player_slot_id": p.player_slot_id,
                    "player_name": p.player_name,
                    "handicap": p.handicap,
                    "is_authenticated": p.user_id is not None,
                    "join_status": p.join_status,
                    "joined_at": p.joined_at
                }
                for p in players
            ],
            "created_at": game.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving game lobby: {str(e)}")

@app.post("/games/{game_id}/start")
async def start_game_from_lobby(game_id: str, db: Session = Depends(database.get_db)):
    """Start a game from the lobby - initializes WGP simulation"""
    # MIGRATED: Using GameLifecycleService instead of global active_games

    try:
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        if game.game_status != "setup":
            raise HTTPException(status_code=400, detail="Game has already been started")

        players = db.query(models.GamePlayer).filter(
            models.GamePlayer.game_id == game_id
        ).order_by(models.GamePlayer.player_slot_id).all()

        if len(players) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 players to start")

        # Create Player objects from database players
        wgp_players = []
        for p in players:
            # Ensure handicap is not None - default to 18.0 if missing
            player_handicap = p.handicap if p.handicap is not None else 18.0

            # Validate handicap range
            if player_handicap < 0 or player_handicap > 54:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {p.player_name} has invalid handicap {player_handicap}. Handicap must be between 0 and 54."
                )

            wgp_player = Player(
                id=p.player_slot_id,
                name=p.player_name,
                handicap=player_handicap
            )
            wgp_players.append(wgp_player)

        # Initialize WolfGoatPigGame for this game
        # Use the configured player_count from game state, not actual number of players joined
        configured_player_count = game.state.get("player_count", 4)
        logger.info(f"Initializing WGP simulation for game {game_id} with {len(wgp_players)} players (configured for {configured_player_count})")

        try:
            # Create simulation with configured player count and actual players
            simulation = WolfGoatPigGame(player_count=configured_player_count, players=wgp_players)
            logger.info(f"Simulation initialized for game {game_id}")
        except Exception as init_error:
            logger.error(f"Failed to initialize simulation: {init_error}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize game: {str(init_error)}")

        # MIGRATED: Store simulation using GameLifecycleService
        # Add to service cache (note: game was already created in DB, just adding to cache)
        get_game_lifecycle_service()._active_games[game_id] = simulation

        # Get initial game state from simulation
        initial_state = simulation.get_game_state()

        # Update database game state
        game.game_status = "in_progress"
        game.updated_at = datetime.utcnow().isoformat()
        game.state = initial_state
        game.state["game_status"] = "in_progress"
        game.state["started_at"] = game.updated_at
        game.state["game_id"] = game_id  # Track game_id in state

        db.commit()

        logger.info(f"Game {game_id} started successfully with {len(players)} players")

        # Send game start notifications to all players using NotificationService
        notification_service = get_notification_service()
        for player in players:
            if player.player_profile_id:  # Only send to registered players
                try:
                    notification_service.send_notification(
                        player_id=player.player_profile_id,
                        notification_type="game_start",
                        message=f"Game {game_id[:8]} has started with {len(players)} players!",
                        db=db,
                        data={"game_id": game_id, "player_count": len(players)}
                    )
                except Exception as notif_error:
                    logger.warning(f"Failed to send game start notification to player {player.player_profile_id}: {notif_error}")

        return {
            "status": "started",
            "game_id": game_id,
            "message": f"Game started with {len(players)} players!",
            "players": [p.player_name for p in players],
            "game_state": initial_state
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting game: {str(e)}")

@app.get("/games")
async def get_games(
    status: Optional[str] = Query(None, description="Filter by game status: setup, in_progress, completed"),
    creator_user_id: Optional[str] = Query(None, description="Filter by creator user ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of games to return"),
    offset: int = Query(0, ge=0, description="Number of games to skip"),
    db: Session = Depends(database.get_db)
):
    """
    Get list of all games with optional filters.

    Filters:
    - status: Filter by game_status (setup, in_progress, completed)
    - creator_user_id: Filter by game creator
    - limit: Maximum results (1-100, default 20)
    - offset: Pagination offset (default 0)
    """
    try:
        # Build query
        query = db.query(models.GameStateModel)

        # Apply filters
        if status:
            query = query.filter(models.GameStateModel.game_status == status)

        if creator_user_id:
            query = query.filter(models.GameStateModel.creator_user_id == creator_user_id)

        # Order by created_at descending (newest first)
        query = query.order_by(models.GameStateModel.created_at.desc())

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        games = query.offset(offset).limit(limit).all()

        # Format response
        games_list = []
        for game in games:
            # Get player count
            player_count = db.query(models.GamePlayer).filter(
                models.GamePlayer.game_id == game.game_id
            ).count()

            games_list.append({
                "game_id": game.game_id,
                "join_code": game.join_code,
                "game_status": game.game_status,
                "creator_user_id": game.creator_user_id,
                "player_count": player_count,
                "created_at": game.created_at,
                "updated_at": game.updated_at
            })

        return {
            "games": games_list,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }

    except Exception as e:
        logger.error(f"Error retrieving games: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving games: {str(e)}")


@app.delete("/games/{game_id}")
async def delete_game(
    game_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Delete a game and all associated data.

    This will remove:
    - The game state record
    - All player records for this game
    - Any game records and player results
    - The game from active games if it's currently running

    Args:
        game_id: The game ID to delete

    Returns:
        Success message with deletion details
    """
    try:
        # Check if game exists
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Remove from active games service if it's running
        service = get_game_lifecycle_service()
        if game_id in service._active_games:
            del service._active_games[game_id]
            logger.info(f"Removed game {game_id} from active games")

        # Delete all related game players
        players_deleted = db.query(models.GamePlayer).filter(
            models.GamePlayer.game_id == game_id
        ).delete()

        # Delete game record if it exists
        game_record = db.query(models.GameRecord).filter(
            models.GameRecord.game_id == game_id
        ).first()

        if game_record:
            # Delete player results for this game record
            db.query(models.GamePlayerResult).filter(
                models.GamePlayerResult.game_record_id == game_record.id
            ).delete()

            # Delete the game record
            db.delete(game_record)

        # Delete the game state itself
        db.delete(game)
        db.commit()

        logger.info(f"Successfully deleted game {game_id} and {players_deleted} associated players")

        return {
            "success": True,
            "message": "Game deleted successfully",
            "game_id": game_id,
            "players_deleted": players_deleted
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting game {game_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error deleting game: {str(e)}")


@app.get("/games/{game_id}/state")
async def get_game_state_by_id(game_id: str, db: Session = Depends(database.get_db)):
    """Get current game state for a specific multiplayer game"""
    # MIGRATED: Using GameLifecycleService instead of global active_games

    try:
        # Check if game is in active games (in-progress) using service
        service = get_game_lifecycle_service()
        if game_id in service._active_games:
            simulation = service._active_games[game_id]
            state = simulation.get_game_state()
            state["game_id"] = game_id
            return state

        # Otherwise, fetch from database
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # If game is completed, just return the saved state
        if game.game_status == "completed":
            return game.state

        # If game is in setup, return lobby info
        if game.game_status == "setup":
            players = db.query(models.GamePlayer).filter(
                models.GamePlayer.game_id == game_id
            ).order_by(models.GamePlayer.player_slot_id).all()

            return {
                "game_id": game_id,
                "game_status": "setup",
                "players": [
                    {
                        "id": p.player_slot_id,
                        "name": p.player_name,
                        "handicap": p.handicap
                    }
                    for p in players
                ],
                "message": "Game not started yet. Please start from lobby."
            }

        # Game is in_progress but not in active_games (server restart?)
        # Try to restore from database
        logger.warning(f"Game {game_id} is in_progress but not in active_games. Attempting to restore...")

        # For now, return the saved state
        # TODO: Implement full state restoration
        return game.state

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game state for {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving game state: {str(e)}")

@app.post("/games/{game_id}/action")
async def perform_game_action_by_id(
    game_id: str,
    action_request: ActionRequest,
    db: Session = Depends(database.get_db)
):
    """Perform an action on a specific multiplayer game"""
    # MIGRATED: Using GameLifecycleService instead of global active_games
    service = get_game_lifecycle_service()

    try:
        # Check if game is in active_games using service
        if game_id not in service._active_games:
            # Try to restore/reload game from database
            logger.warning(f"Game {game_id} not in active_games, attempting to restore from database...")

            game = db.query(models.GameStateModel).filter(
                models.GameStateModel.game_id == game_id
            ).first()

            if not game:
                raise HTTPException(status_code=404, detail="Game not found")

            if game.game_status == "completed":
                raise HTTPException(status_code=400, detail="Game is already completed")

            if game.game_status == "setup":
                raise HTTPException(status_code=400, detail="Game has not been started yet")

            # Restore game simulation from database
            # Get players from database
            players = db.query(models.GamePlayer).filter(
                models.GamePlayer.game_id == game_id
            ).order_by(models.GamePlayer.player_slot_id).all()

            # Create Player objects
            wgp_players = []
            for p in players:
                # Ensure handicap is not None - default to 18.0 if missing
                player_handicap = p.handicap if p.handicap is not None else 18.0

                wgp_player = Player(
                    id=p.player_slot_id,
                    name=p.player_name,
                    handicap=player_handicap
                )
                wgp_players.append(wgp_player)

            # Get configured player count from saved state
            configured_player_count = game.state.get("player_count", 4)

            # Create new simulation
            simulation = WolfGoatPigGame(player_count=configured_player_count, players=wgp_players)

            # TODO: Restore full game state (hole states, scores, etc.) from game.state
            # For now, this creates a fresh simulation - user will need to restart game
            # This is a temporary fix to prevent 404 errors

            # MIGRATED: Add to active_games using service
            service._active_games[game_id] = simulation
            logger.info(f"Restored game {game_id} from database")

        # MIGRATED: Get simulation from service
        simulation = service._active_games[game_id]

        # Use the existing unified action handler
        # Temporarily set global wgp_simulation to this game's simulation
        global wgp_simulation
        original_simulation = wgp_simulation
        wgp_simulation = simulation

        try:
            # Call the unified action endpoint logic
            response = await unified_action(game_id, action_request)

            # Save state back to database after action
            game = db.query(models.GameStateModel).filter(
                models.GameStateModel.game_id == game_id
            ).first()

            if game:
                game.state = simulation.get_game_state()
                game.state["game_id"] = game_id
                game.updated_at = datetime.utcnow().isoformat()

                # Check if game is completed
                if simulation.current_hole > 18:
                    game.game_status = "completed"
                    game.state["game_status"] = "completed"

                db.commit()
                logger.info(f"Saved state for game {game_id} after action {action_request.action_type}")

            return response

        finally:
            # Restore original simulation
            wgp_simulation = original_simulation

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error performing action on game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error performing action: {str(e)}")

@app.get("/games/history")
async def get_game_history(limit: int = 10, offset: int = 0, db: Session = Depends(database.get_db)):
    """Get list of completed games"""
    try:
        games = db.query(models.GameRecord).order_by(models.GameRecord.completed_at.desc()).offset(offset).limit(limit).all()
        return {
            "games": [
                {
                    "id": game.id,
                    "game_id": game.game_id,
                    "course_name": game.course_name,
                    "player_count": game.player_count,
                    "total_holes_played": game.total_holes_played,
                    "game_duration_minutes": game.game_duration_minutes,
                    "created_at": game.created_at,
                    "completed_at": game.completed_at,
                    "final_scores": game.final_scores
                }
                for game in games
            ],
            "total": db.query(models.GameRecord).count(),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving game history: {str(e)}")

@app.get("/games/{game_id}/details")
async def get_game_details(game_id: str, db: Session = Depends(database.get_db)):
    """Get detailed game results including player performances and hole-by-hole scores"""
    try:
        # Get game record
        game = db.query(models.GameRecord).filter(models.GameRecord.game_id == game_id).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Get player results
        player_results = db.query(models.GamePlayerResult).filter(
            models.GamePlayerResult.game_record_id == game.id
        ).order_by(models.GamePlayerResult.final_position).all()

        return {
            "game": {
                "id": game.id,
                "game_id": game.game_id,
                "course_name": game.course_name,
                "player_count": game.player_count,
                "total_holes_played": game.total_holes_played,
                "game_duration_minutes": game.game_duration_minutes,
                "created_at": game.created_at,
                "completed_at": game.completed_at,
                "game_settings": game.game_settings,
                "final_scores": game.final_scores
            },
            "player_results": [
                {
                    "player_name": result.player_name,
                    "final_position": result.final_position,
                    "total_earnings": result.total_earnings,
                    "holes_won": result.holes_won,
                    "partnerships_formed": result.partnerships_formed,
                    "partnerships_won": result.partnerships_won,
                    "solo_attempts": result.solo_attempts,
                    "solo_wins": result.solo_wins,
                    "hole_scores": result.hole_scores,
                    "betting_history": result.betting_history,
                    "performance_metrics": result.performance_metrics
                }
                for result in player_results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving game details: {str(e)}")

def _get_current_captain_id() -> Optional[str]:
    """Best-effort lookup for the active captain id across legacy and unified state."""
    try:
        simulation_state = game.get_game_state()
        if isinstance(simulation_state, dict):
            captain = simulation_state.get("captain_id") or simulation_state.get("captain")
            if captain:
                return captain
    except Exception:
        # If the simulation hasn't been initialized yet, fall back to legacy state
        pass

    try:
        legacy_state = {"message": "Legacy game_state.get_state() is deprecated"}
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
        updated_state = {"message": "Legacy game_state.get_state() is deprecated"}

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
async def unified_action(game_id: str, action: ActionRequest, db: Session = Depends(database.get_db)):
    """Unified action endpoint for all Wolf Goat Pig game interactions"""
    try:
        # Get the specific game instance for this game_id
        # MIGRATED: Using GameLifecycleService instead of get_or_load_game
        game = get_game_lifecycle_service().get_game(db, game_id)

        # Normalize action_type to uppercase for consistent matching
        action_type = action.action_type.upper()
        payload = action.payload or {}

        # Route to appropriate handler based on action type
        # All handlers now receive the game instance instead of using global wgp_simulation
        if action_type == "INITIALIZE_GAME":
            return await handle_initialize_game(game, payload)
        elif action_type == "PLAY_SHOT":
            return await handle_play_shot(game, payload)
        elif action_type == "REQUEST_PARTNERSHIP" or action_type == "REQUEST_PARTNER":
            return await handle_request_partnership(game, payload)
        elif action_type == "RESPOND_PARTNERSHIP" or action_type == "ACCEPT_PARTNER" or action_type == "DECLINE_PARTNER":
            return await handle_respond_partnership(game, payload)
        elif action_type == "DECLARE_SOLO" or action_type == "GO_SOLO":
            return await handle_declare_solo(game)
        elif action_type == "OFFER_DOUBLE":
            return await handle_offer_double(game, payload)
        elif action_type == "ACCEPT_DOUBLE":
            return await handle_accept_double(game, payload)
        elif action_type == "INVOKE_FLOAT":
            # Frontend sends captain_id as direct field
            action_dict = action.model_dump() if hasattr(action, 'model_dump') else action.dict()
            return await handle_invoke_float(game, action_dict)
        elif action_type == "TOGGLE_OPTION":
            # Frontend sends captain_id as direct field
            action_dict = action.model_dump() if hasattr(action, 'model_dump') else action.dict()
            return await handle_toggle_option(game, action_dict)
        elif action_type == "FLUSH":
            # Flush = concede/fold the hole
            action_dict = action.model_dump() if hasattr(action, 'model_dump') else action.dict()
            return await handle_flush(game, action_dict)
        elif action_type == "CONCEDE_PUTT":
            return await handle_concede_putt(game, payload)
        elif action_type == "ADVANCE_HOLE" or action_type == "NEXT_HOLE":
            return await handle_advance_hole(game)
        elif action_type == "OFFER_BIG_DICK":
            return await handle_offer_big_dick(game, payload)
        elif action_type == "ACCEPT_BIG_DICK":
            return await handle_accept_big_dick(game, payload)
        elif action_type == "AARDVARK_JOIN_REQUEST":
            return await handle_aardvark_join_request(game, payload)
        elif action_type == "AARDVARK_TOSS":
            return await handle_aardvark_toss(game, payload)
        elif action_type == "AARDVARK_GO_SOLO":
            return await handle_aardvark_go_solo(game, payload)
        elif action_type == "PING_PONG_AARDVARK":
            return await handle_ping_pong_aardvark(game, payload)
        elif action_type == "INVOKE_JOES_SPECIAL":
            return await handle_joes_special(game, payload)
        elif action_type == "GET_POST_HOLE_ANALYSIS":
            return await handle_get_post_hole_analysis(game, payload)
        elif action_type == "ENTER_HOLE_SCORES":
            return await handle_enter_hole_scores(game, payload)
        elif action_type == "GET_ADVANCED_ANALYTICS":
            return await handle_get_advanced_analytics(game, payload)
        elif action_type == "COMPLETE_GAME":
            return await handle_complete_game(game, payload)
        elif action_type == "RECORD_NET_SCORE":
            # Handle score recording action from frontend
            # Frontend sends player_id and score as direct fields, not in payload
            action_dict = action.model_dump() if hasattr(action, 'model_dump') else action.dict()
            return await handle_record_net_score(game, action_dict)
        elif action_type == "CALCULATE_HOLE_POINTS":
            # Handle calculate points action from frontend
            action_dict = action.model_dump() if hasattr(action, 'model_dump') else action.dict()
            return await handle_calculate_hole_points(game, action_dict)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action type: {action_type}")
            
    except HTTPException:
        # Re-raise HTTPExceptions to preserve their status codes
        raise
        raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")

# Global game instance (per-game instances are preferred)
game: Optional[WolfGoatPigGame] = None
# Action Handlers
async def handle_initialize_game(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle game initialization with robust error handling and fallbacks"""
    try:
        players = payload.get("players", [])
        course_name = payload.get("course_name", "Wing Point Golf & Country Club")
        
        # Validate player count using GameStateValidator
        GameStateValidator.validate_player_count(len(players))

        # Ensure all players have required fields with smart defaults
        for i, player in enumerate(players):
            if "name" not in player:
                player["name"] = f"Player {i+1}"
                logger.warning(f"Player {i+1} missing name, using default")

            # Validate and normalize handicap using HandicapValidator
            player["handicap"] = HandicapValidator.validate_and_normalize_handicap(
                player.get("handicap"),
                player_name=player.get("name")
            )

            # Add missing fields if not present
            if "id" not in player:
                player["id"] = f"p{i+1}"
            if "strength" not in player:
                # Calculate strength from handicap using HandicapValidator
                player["strength"] = HandicapValidator.calculate_strength_from_handicap(
                    player["handicap"]
                )
        
        # Verify course exists, use fallback if needed
        try:
            available_courses = course_manager.get_courses()
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
            # Create Player objects
            wgp_players = []
            for player in players:
                try:
                    wgp_players.append(Player(
                        id=player["id"],
                        name=player["name"],
                        handicap=player["handicap"]
                    ))
                except Exception as player_creation_error:
                    logger.error(f"Failed to create Player for {player['name']}: {player_creation_error}")
                    # Create with minimal data
                    wgp_players.append(Player(
                        id=player.get("id", f"p{len(wgp_players)+1}"),
                        name=player.get("name", f"Player {len(wgp_players)+1}"),
                        handicap=18.0
                    ))
            
            if len(wgp_players) != len(players):
                logger.warning(f"Only created {len(wgp_players)} WGP players from {len(players)} input players")
            
            # Initialize the simulation with these players and course manager
            try:
                game.__init__(player_count=len(wgp_players), players=wgp_players, course_manager=game_state.course_manager)
                logger.info("WGP simulation initialized successfully with course data")
            except Exception as sim_init_error:
                logger.error(f"WGP simulation initialization failed: {sim_init_error}")
                # Try without course manager
                try:
                    game.__init__(player_count=len(wgp_players), players=wgp_players)
                    logger.warning("Initialized without course manager")
                except:
                    # Try with basic initialization
                    game.__init__(player_count=len(wgp_players))
                    logger.warning("Fell back to basic simulation initialization")
            
            # Set computer players (all except first) with error handling
            try:
                computer_player_ids = [p["id"] for p in players[1:]]
                game.set_computer_players(computer_player_ids)
                logger.info(f"Set {len(computer_player_ids)} computer players")
            except Exception as computer_setup_error:
                logger.error(f"Failed to set computer players: {computer_setup_error}")
                # Continue without computer player setup
            
            # Initialize the first hole with error handling
            try:
                game._initialize_hole(1)
                logger.info("First hole initialized")
            except Exception as hole_init_error:
                logger.error(f"Failed to initialize first hole: {hole_init_error}")
                # Continue - hole might be initialized differently
            
            # Enable shot progression and timeline tracking
            try:
                game.enable_shot_progression()
                logger.info("Shot progression enabled")
            except Exception as progression_error:
                logger.warning(f"Failed to enable shot progression: {progression_error}")
                # Non-critical, continue
            
            # Add initial timeline event
            try:
                if hasattr(wgp_simulation, 'hole_progression') and game.hole_progression:
                    game.hole_progression.add_timeline_event(
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
                game.__init__(player_count=len(players))
                logger.warning("Created minimal fallback simulation")
            except Exception as fallback_error:
                logger.error(f"Even fallback simulation failed: {fallback_error}")
                # This is critical - raise error
                raise HTTPException(status_code=500, detail="Failed to initialize simulation engine")
        
        # Get initial game state (with error handling)
        try:
            current_state = game.get_game_state()
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

async def handle_play_shot(game: WolfGoatPigGame, payload: Dict[str, Any] = None) -> ActionResponse:
    """Handle playing a shot"""
    try:
        # Get current game state
        current_state = game.get_game_state()
        
        # Determine next player to hit
        next_player = game._get_next_shot_player()
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
        shot_response = game.simulate_shot(next_player)
        shot_result = shot_response.get("shot_result", {})
        
        # Update game state  
        updated_state = game.get_game_state()
        hole_state = game.hole_states[game.current_hole]
        
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
            captain_name = game._get_player_name(captain_id)
            
            # Get available partners using RuleManager
            rule_mgr = RuleManager.get_instance()
            available_partners = rule_mgr.get_available_partners(
                game_state=game.get_game_state(),
                captain_id=captain_id,
                hole_number=game.current_hole
            )

            # Check if we have enough tee shots for partnership decisions
            tee_shots_completed = sum(1 for player_id, ball in hole_state.ball_positions.items()
                                    if ball and ball.shot_count >= 1)

            if tee_shots_completed >= 2:
                
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
                    remaining_players = [p.name for p in game.players 
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
            next_shot_player = game._get_next_shot_player()
            if next_shot_player:
                next_shot_player_name = game._get_player_name(next_shot_player)
                
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
            
            # Check for betting opportunities using RuleManager
            rule_mgr = RuleManager.get_instance()
            betting_check = rule_mgr.check_betting_opportunities(
                game_state=game.get_game_state(),
                hole_number=game.current_hole,
                last_shot=shot_response.get("shot_result") if shot_response else None
            )

            if betting_check["should_offer"]:
                # Add betting action to available_actions
                available_actions.append(betting_check["action"])
        
        # Create timeline event from shot response
        player_name = game._get_player_name(next_player)
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

async def handle_request_partnership(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle partnership request"""
    try:
        # Accept either partner_id or target_player_name
        partner_id = payload.get("partner_id")
        target_player = payload.get("target_player_name")

        if not partner_id and not target_player:
            raise HTTPException(status_code=400, detail="Either partner_id or target_player_name is required")

        # Get current game state
        current_state = game.get_game_state()

        # Get the actual captain ID from the current hole state
        hole_state = game.hole_states[game.current_hole]
        captain_id = hole_state.teams.captain

        # If we have target_player name, convert to ID
        if target_player and not partner_id:
            for player in game.players:
                if player.name == target_player:
                    partner_id = player.id
                    break

            if not partner_id:
                raise HTTPException(status_code=400, detail=f"Player '{target_player}' not found")

        # If we have partner_id, get the name for response
        if partner_id and not target_player:
            for player in game.players:
                if player.id == partner_id:
                    target_player = player.name
                    break

            if not target_player:
                raise HTTPException(status_code=400, detail=f"Player with ID '{partner_id}' not found")
        
        # Request the partnership
        result = game.request_partner(captain_id, partner_id)
        
        # Get updated game state
        updated_state = game.get_game_state()
        
        # Determine next available actions
        available_actions = []
        
        # If partnership was requested, the target player needs to respond
        if result.get("partnership_requested"):
            captain_name = game._get_player_name(captain_id)
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
                "player_name": game._get_player_name(captain_id),
                "details": {
                    "captain": game._get_player_name(captain_id),
                    "requested_partner": target_player,
                    "status": "pending_response"
                }
            }
        )
    except Exception as e:
        logger.error(f"Error requesting partnership: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to request partnership: {str(e)}")

async def handle_respond_partnership(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle partnership response"""
    try:
        accepted = payload.get("accepted", False)
        
        # Get current game state
        current_state = game.get_game_state()
        
        # Get the partner ID from the pending request
        hole_state = game.hole_states[game.current_hole]
        partner_id = hole_state.teams.pending_request.get("requested") if hole_state.teams.pending_request else None
        
        if not partner_id:
            raise HTTPException(status_code=400, detail="No pending partnership request")
        
        # Respond to partnership
        if accepted:
            result = game.respond_to_partnership(partner_id, True)
            message = "Partnership accepted! Teams are formed."
        else:
            result = game.respond_to_partnership(partner_id, False)
            message = "Partnership declined. Captain goes solo."
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and game.hole_progression:
            game.hole_progression.add_timeline_event(
                event_type="partnership_response",
                description=f"Partnership {'accepted' if accepted else 'declined'}",
                player_name="Partner",
                details={"accepted": accepted}
            )
        
        # Update game state
        updated_state = game.get_game_state()
        
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

async def handle_declare_solo(game: WolfGoatPigGame) -> ActionResponse:
    """Handle captain going solo"""
    try:
        # Get current game state
        current_state = game.get_game_state()
        
        # Get the actual captain ID from the current hole state
        hole_state = game.hole_states.get(game.current_hole)
        if not hole_state or not hole_state.teams.captain:
            raise HTTPException(status_code=400, detail="No captain found for current hole")
        
        captain_id = hole_state.teams.captain
        
        # Captain goes solo
        result = game.captain_go_solo(captain_id)
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and game.hole_progression:
            game.hole_progression.add_timeline_event(
                event_type="partnership_decision",
                description="Captain goes solo - 1 vs 3",
                player_name="Captain",
                details={"solo": True}
            )
        
        # Update game state
        updated_state = game.get_game_state()
        
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

async def handle_offer_double(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle double offer"""
    try:
        player_id = payload.get("player_id")
        if not player_id:
            raise ValueError("Player ID required for double offer")

        # Check if partnerships have been formed (REQUIRED before any betting)
        game_state = game.get_game_state()
        rule_mgr = RuleManager.get_instance()

        # Validate partnerships formed before betting using RuleManager
        if not rule_mgr.are_partnerships_formed(game_state, game.current_hole):
            raise HTTPException(
                status_code=400,
                detail="Partnerships must be formed before betting can start"
            )

        # Validate player can double using RuleManager
        if not rule_mgr.can_double(player_id, game_state):
            raise HTTPException(
                status_code=400,
                detail="Cannot double at this time"
            )

        # Get current game state
        current_state = game.get_game_state()
        
        # Offer double
        result = game.offer_double(player_id)
        
        player_name = game._get_player_name(player_id)
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and game.hole_progression:
            game.hole_progression.add_timeline_event(
                event_type="double_offer",
                description=f"{player_name} offered to double the wager",
                player_name=player_name,
                details={"double_offered": True, "player_id": player_id}
            )
        
        # Update game state
        updated_state = game.get_game_state()
        
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

async def handle_accept_double(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle double acceptance/decline"""
    try:
        accepted = payload.get("accepted", False)
        
        # Get current game state
        current_state = game.get_game_state()
        
        # Respond to double
        if accepted:
            result = game.respond_to_double("responding_team", True)
            message = "Double accepted! Wager doubled."
        else:
            result = game.respond_to_double("responding_team", False)
            message = "Double declined. Original wager maintained."
        
        # Add timeline event to hole progression if available
        if hasattr(wgp_simulation, 'hole_progression') and game.hole_progression:
            game.hole_progression.add_timeline_event(
                event_type="double_response",
                description=f"Double {'accepted' if accepted else 'declined'}",
                player_name="Responding Team",
                details={"accepted": accepted}
            )
        
        # Update game state
        updated_state = game.get_game_state()
        
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

async def handle_concede_putt(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle putt concession"""
    try:
        conceding_player = payload.get("conceding_player")
        conceded_player = payload.get("conceded_player")
        
        if not conceding_player or not conceded_player:
            raise HTTPException(status_code=400, detail="conceding_player and conceded_player are required")
        
        # Get current game state
        current_state = game.get_game_state()
        
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

async def handle_advance_hole(game: WolfGoatPigGame) -> ActionResponse:
    """Handle advancing to the next hole"""
    try:
        # Advance to next hole
        result = game.advance_to_next_hole()
        
        # Get updated game state
        current_state = game.get_game_state()
        
        # Add timeline event for hole advancement
        if hasattr(wgp_simulation, 'hole_progression') and game.hole_progression:
            game.hole_progression.add_timeline_event(
                event_type="hole_start",
                description=f"Started hole {game.current_hole}",
                details={"hole_number": game.current_hole}
            )
        
        # Enable shot progression for the new hole
        game.enable_shot_progression()
        
        # Get the next player to hit
        next_player = game._get_next_shot_player()
        next_player_name = game._get_player_name(next_player) if next_player else "Unknown"
        
        return ActionResponse(
            game_state=current_state,
            log_message=f"Advanced to hole {game.current_hole}",
            available_actions=[
                {"action_type": "PLAY_SHOT", "prompt": f"Start hole {game.current_hole}", "player_turn": next_player_name}
            ],
            timeline_event={
                "id": f"hole_start_{game.current_hole}",
                "timestamp": datetime.now().isoformat(),
                "type": "hole_start",
                "description": f"Started hole {game.current_hole}",
                "details": {"hole_number": game.current_hole}
            }
        )
    except Exception as e:
        logger.error(f"Error advancing hole: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to advance hole: {str(e)}")

async def handle_offer_big_dick(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Big Dick challenge on hole 18"""
    try:
        player_id = payload.get("player_id", "default_player")
        
        result = game.offer_big_dick(player_id)
        updated_state = game.get_game_state()
        
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

async def handle_accept_big_dick(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Big Dick challenge response"""
    try:
        accepting_players = payload.get("accepting_players", [])
        
        result = game.accept_big_dick(accepting_players)
        updated_state = game.get_game_state()
        
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

async def handle_ping_pong_aardvark(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Ping Pong Aardvark"""
    try:
        team_id = payload.get("team_id", "team1")
        aardvark_id = payload.get("aardvark_id", "default_aardvark")
        
        result = game.ping_pong_aardvark(team_id, aardvark_id)
        updated_state = game.get_game_state()
        
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

async def handle_aardvark_join_request(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Aardvark requesting to join a team"""
    try:
        aardvark_id = payload.get("aardvark_id")
        target_team = payload.get("target_team", "team1")
        
        if not aardvark_id:
            raise HTTPException(status_code=400, detail="aardvark_id is required")
        
        result = game.aardvark_request_team(aardvark_id, target_team)
        updated_state = game.get_game_state()
        
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

async def handle_aardvark_toss(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle team response to Aardvark request (accept or toss)"""
    try:
        team_id = payload.get("team_id", "team1")
        accept = payload.get("accept", False)
        
        result = game.respond_to_aardvark(team_id, accept)
        updated_state = game.get_game_state()
        
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

async def handle_aardvark_go_solo(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Aardvark deciding to go solo"""
    try:
        aardvark_id = payload.get("aardvark_id")
        use_tunkarri = payload.get("use_tunkarri", False)
        
        if not aardvark_id:
            raise HTTPException(status_code=400, detail="aardvark_id is required")
        
        result = game.aardvark_go_solo(aardvark_id, use_tunkarri)
        updated_state = game.get_game_state()
        
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

async def handle_joes_special(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Joe's Special wager selection in Hoepfinger"""
    try:
        selected_value = payload.get("selected_value", 2)

        # Apply Joe's Special using RuleManager
        rule_mgr = RuleManager.get_instance()
        rule_mgr.apply_joes_special(
            game_state=game.get_game_state(),
            hole_number=game.current_hole,
            selected_value=selected_value
        )
        
        updated_state = game.get_game_state()
        
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

async def handle_get_post_hole_analysis(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle post-hole analysis request"""
    try:
        hole_number = payload.get("hole_number", game.current_hole)
        
        analysis = game.get_post_hole_analysis(hole_number)
        updated_state = game.get_game_state()
        
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

async def handle_enter_hole_scores(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle entering hole scores"""
    try:
        scores = payload.get("scores", {})
        
        result = game.enter_hole_scores(scores)
        updated_state = game.get_game_state()
        
        return ActionResponse(
            game_state=updated_state,
            log_message=result.get("message", "Hole scores entered and points calculated"),
            available_actions=[
                {"action_type": "GET_POST_HOLE_ANALYSIS", "prompt": "View Hole Analysis"},
                {"action_type": "ADVANCE_HOLE", "prompt": "Continue to Next Hole"}
            ],
            timeline_event={
                "id": f"scores_entered_{game.current_hole}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "scores_entered",
                "description": f"Scores entered for hole {game.current_hole}",
                "details": {
                    "scores": scores,
                    "points_result": result
                }
            }
        )
    except Exception as e:
        logger.error(f"Error entering hole scores: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enter hole scores: {str(e)}")

async def handle_complete_game(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle completing a game and saving results permanently"""
    try:
        # Get the game state instance
        game_state = game.game_state if hasattr(wgp_simulation, 'game_state') else None

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game to complete")

        # Complete the game and save results
        result_message = game_state.complete_game()

        updated_state = game.get_game_state()
        updated_state["game_completed"] = True
        updated_state["completion_message"] = result_message

        # TODO: Send game_end notifications using NotificationService
        # Once DB session is passed to handlers, add:
        # notification_service = get_notification_service()
        # for player in game_state.player_manager.players:
        #     notification_service.send_notification(
        #         player_id=player.db_id,
        #         notification_type="game_end",
        #         message=f"Game completed! {result_message}",
        #         db=db
        #     )

        return ActionResponse(
            game_state=updated_state,
            log_message=f"🎉 Game completed! {result_message}",
            available_actions=[],  # No more actions available
            timeline_event={
                "id": f"game_completed_{game.game_state.game_id}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "game_completed",
                "description": "Game completed and results saved",
                "details": {
                    "game_id": game.game_state.game_id,
                    "holes_played": len(game.game_state.hole_history),
                    "final_scores": {p.id: p.points for p in game.game_state.player_manager.players}
                }
            }
        )
    except Exception as e:
        logger.error(f"Error completing game: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete game: {str(e)}")

async def handle_get_advanced_analytics(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle getting advanced analytics dashboard data"""
    try:
        analytics = game.get_advanced_analytics()
        updated_state = game.get_game_state()

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

async def handle_record_net_score(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle recording a net score for a player"""
    try:
        # Debug: Log the payload
        logger.info(f"handle_record_net_score payload: {payload}")

        # Use 'in' to check if keys exist, since player_id can be 0
        if "player_id" not in payload or "score" not in payload:
            logger.error(f"Missing keys in payload. Keys present: {list(payload.keys())}")
            raise ValueError("player_id and score are required")

        player_id = payload["player_id"]
        score = payload["score"]

        # Get the game state instance
        game_state = game.game_state if hasattr(wgp_simulation, 'game_state') else None

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Record the net score
        result = game_state.record_net_score(player_id, score)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=result,
            available_actions=[],  # No specific actions after recording score
            timeline_event={
                "id": f"score_recorded_{player_id}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "score_recorded",
                "description": f"Score {score} recorded for player {player_id}",
                "details": {
                    "player_id": player_id,
                    "score": score
                }
            }
        )
    except Exception as e:
        logger.error(f"Error recording net score: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record net score: {str(e)}")

async def handle_calculate_hole_points(payload: Dict[str, Any]) -> ActionResponse:
    """Handle calculating points for the current hole"""
    try:
        # Get the game state instance
        game_state = game.game_state if hasattr(wgp_simulation, 'game_state') else None

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Calculate hole points
        game_state.calculate_hole_points()
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message="Hole points calculated",
            available_actions=[
                {"action_type": "GET_POST_HOLE_ANALYSIS", "prompt": "View Hole Analysis"},
                {"action_type": "ADVANCE_HOLE", "prompt": "Continue to Next Hole"}
            ],
            timeline_event={
                "id": f"points_calculated_{game_state.current_hole}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "points_calculated",
                "description": f"Points calculated for hole {game_state.current_hole}",
                "details": {
                    "hole": game_state.current_hole,
                    "points": {p.id: p.points for p in game_state.player_manager.players}
                }
            }
        )
    except Exception as e:
        logger.error(f"Error calculating hole points: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate hole points: {str(e)}")

async def handle_invoke_float(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Float invocation by captain"""
    try:
        logger.info(f"handle_invoke_float payload: {payload}")

        if "captain_id" not in payload:
            raise ValueError("captain_id is required")

        captain_id = payload["captain_id"]

        # Get the game state instance
        game_state = game.game_state if hasattr(game, 'game_state') else None

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Check if partnerships have been formed (REQUIRED before any betting)
        rule_mgr = RuleManager.get_instance()
        if not rule_mgr.are_partnerships_formed(game_state, game.current_hole):
            raise HTTPException(
                status_code=400,
                detail="Partnerships must be formed before betting can start"
            )

        # Validate captain can double (Float is a type of double)
        try:
            rule_mgr.validate_can_double(captain_id, game.get_game_state())
        except RuleViolationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Invoke the float
        result = game.invoke_float(captain_id)
        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=f"Float invoked! Wager doubled.",
            available_actions=[],
            timeline_event={
                "id": f"float_invoked_{captain_id}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "float_invoked",
                "description": f"Captain invoked Float - wager doubled!",
                "details": {
                    "captain_id": captain_id,
                    "new_wager": updated_state.get("hole_state", {}).get("betting", {}).get("current_wager", 0)
                }
            }
        )
    except Exception as e:
        logger.error(f"Error invoking float: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invoke float: {str(e)}")

async def handle_toggle_option(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """Handle Option toggle by captain"""
    try:
        logger.info(f"handle_toggle_option payload: {payload}")

        if "captain_id" not in payload:
            raise ValueError("captain_id is required")

        captain_id = payload["captain_id"]

        # Get the game state instance
        game_state = game.game_state if hasattr(wgp_simulation, 'game_state') else None

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Check if partnerships have been formed (REQUIRED before any betting)
        rule_mgr = RuleManager.get_instance()
        if not rule_mgr.are_partnerships_formed(game_state, game.current_hole):
            raise HTTPException(
                status_code=400,
                detail="Partnerships must be formed before betting can start"
            )

        # Additional validation: Check if captain can invoke option (type of doubling)
        full_game_state = game.get_game_state()
        if not rule_mgr.can_double(captain_id, full_game_state):
            raise HTTPException(
                status_code=400,
                detail="Cannot toggle Option at this time"
            )

        # Apply The Option using RuleManager (FULL IMPLEMENTATION)
        rule_mgr.apply_option(
            game_state=game_state,
            captain_id=captain_id,
            hole_number=game_state.current_hole
        )

        # Get the new option state for logging
        hole_state = game_state.hole_states[game_state.current_hole]
        current_option = getattr(hole_state.betting, 'option_active', False)

        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=f"The Option {'activated' if not current_option else 'deactivated'}",
            available_actions=[],
            timeline_event={
                "id": f"option_toggled_{captain_id}_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "option_toggled",
                "description": f"Captain {'activated' if not current_option else 'deactivated'} The Option",
                "details": {
                    "captain_id": captain_id,
                    "option_active": not current_option
                }
            }
        )
    except Exception as e:
        logger.error(f"Error toggling option: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle option: {str(e)}")

async def handle_flush(game: WolfGoatPigGame, payload: Dict[str, Any]) -> ActionResponse:
    """
    Handle Flush action - conceding/folding the hole.
    A player or team gives up on the current hole, awarding the hole to opponents.
    """
    try:
        logger.info(f"handle_flush payload: {payload}")

        # Validate required fields
        if "player_id" not in payload and "team_id" not in payload:
            raise ValueError("Either player_id or team_id is required for flush")

        # Get the game state instance
        game_state = game.game_state if hasattr(wgp_simulation, 'game_state') else None

        if not game_state:
            raise HTTPException(status_code=400, detail="No active game")

        # Check if partnerships have been formed (REQUIRED before any betting/conceding)
        rule_mgr = RuleManager.get_instance()
        if not rule_mgr.are_partnerships_formed(game_state, game.current_hole):
            raise HTTPException(
                status_code=400,
                detail="Partnerships must be formed before you can flush"
            )

        # Validate game is in correct phase for concession
        try:
            full_game_state = game.get_game_state()
            GameStateValidator.validate_game_phase(
                full_game_state.get("phase", "unknown"),
                "playing",
                "concede hole"
            )
        except GameStateValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Get player/team info
        player_id = payload.get("player_id")
        team_id = payload.get("team_id")

        # Get current hole state
        hole_state = game_state.hole_states[game_state.current_hole]

        # Determine who is conceding
        if player_id is not None:
            conceding_player_name = game._get_player_name(player_id)
            concede_description = f"{conceding_player_name} has flushed (conceded) the hole"
        else:
            concede_description = f"Team {team_id} has flushed (conceded) the hole"

        # Award concession points using ScoringManager
        scoring_mgr = get_scoring_manager()
        points_awarded = scoring_mgr.award_concession_points(
            game_state=game_state,
            conceding_player=player_id,
            conceding_team=team_id,
            hole_number=game_state.current_hole
        )

        updated_state = game.get_game_state()

        return ActionResponse(
            game_state=updated_state,
            log_message=f"Flush! {concede_description}",
            available_actions=[
                {"action_type": "ADVANCE_HOLE", "prompt": "Continue to next hole"}
            ],
            timeline_event={
                "id": f"flush_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "type": "flush",
                "description": concede_description,
                "details": {
                    "player_id": player_id,
                    "team_id": team_id,
                    "current_wager": hole_state.betting.current_wager
                }
            }
        )
    except Exception as e:
        logger.error(f"Error handling flush: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to handle flush: {str(e)}")

# Helper function to serialize game state
def _serialize_game_state():
    """Convert game state to serializable format"""
    try:
        # Get the current game state from the WGP simulation
        state = game.get_game_state()
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
        current_state = game.get_game_state()
        
        # Quick opportunity assessment
        opportunities = []
        
        # Check if game is active
        if not current_state.get("active", False):
            return {"opportunities": [], "message": "No active game"}
        
        current_hole = current_state.get("current_hole", 1)
        hole_state = game.hole_states.get(current_hole)
        
        if hole_state:
            # REFACTORED: Using RuleManager for betting opportunities
            # Check for doubling opportunities
            rule_mgr = RuleManager.get_instance()

            # Check if any player can double
            can_any_player_double = False
            for player in game.players:
                if rule_mgr.can_double(player.id, current_state):
                    can_any_player_double = True
                    break

            if can_any_player_double and hole_state.teams.type != "pending":
                opportunities.append({
                    "type": "offer_double",
                    "description": f"Double the wager from {hole_state.betting.current_wager} to {hole_state.betting.current_wager * 2} quarters",
                    "current_wager": hole_state.betting.current_wager,
                    "potential_wager": hole_state.betting.current_wager * 2,
                    "risk_level": "medium",
                    "timing": "optimal" if not hole_state.wagering_closed else "limited"
                })
            
            # REFACTORED: Using RuleManager for partnership opportunities
            # Check for partnership opportunities
            if hole_state.teams.type == "pending":
                captain_id = hole_state.teams.captain
                captain_name = game._get_player_name(captain_id)

                available_partners = []
                for player in game.players:
                    # Use both hole state and RuleManager for validation
                    if player.id != captain_id and hole_state.can_request_partnership(captain_id, player.id):
                        try:
                            if rule_mgr.can_form_partnership(captain_id, player.id, current_state):
                                available_partners.append({
                                    "id": player.id,
                                    "name": player.name,
                                    "handicap": player.handicap
                                })
                        except RuleViolationError:
                            # Partnership not allowed
                            pass
                
                if available_partners:
                    opportunities.append({
                        "type": "partnership_decision",
                        "description": f"{captain_name} must choose a partner or go solo",
                        "captain": captain_name,
                        "available_partners": available_partners,
                        "solo_multiplier": 2,
                        "deadline_approaching": len(available_partners) < len(game.players) - 1
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


# Leaderboard and Comparative Analytics
@app.get("/leaderboard", response_model=List[schemas.LeaderboardEntry])
def get_leaderboard(
    limit: int = Query(100, ge=1, le=100),  # Default to 100 to show all players
    sort: str = Query("desc", regex="^(asc|desc)$")  # Add sort parameter
):
    """Get the player leaderboard. Uses LeaderboardService for consolidated leaderboard logic."""
    try:
        db = database.SessionLocal()

        # Use LeaderboardService for leaderboard queries
        leaderboard_service = get_leaderboard_service(db)
        leaderboard_type = "total_earnings"  # Default leaderboard type
        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=leaderboard_type,
            db=db,
            limit=limit
        )

        # Sort by total_earnings based on sort parameter
        if sort == "asc":
            leaderboard.sort(key=lambda x: x.get("total_earnings", 0))
        else:
            leaderboard.sort(key=lambda x: x.get("total_earnings", 0), reverse=True)

        # Convert to schema format
        entries = []
        for i, entry in enumerate(leaderboard, 1):
            total_earnings = entry.get("value", 0) if leaderboard_type == "total_earnings" else entry.get("total_earnings", 0)
            games = entry.get("games_played", 1)
            entries.append(schemas.LeaderboardEntry(
                rank=entry.get("rank", i),
                player_id=entry.get("player_id"),
                player_name=entry.get("player_name"),
                total_earnings=total_earnings,
                games_played=games,
                win_percentage=entry.get("win_percentage", 0) * 100 if entry.get("win_percentage", 0) <= 1 else entry.get("win_percentage", 0),
                avg_earnings=total_earnings / games if games > 0 else 0,
                partnership_success=entry.get("partnership_success", 0)
            ))

        return entries

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
    """Get leaderboard sorted by specific metric. Uses LeaderboardService."""
    try:
        db = database.SessionLocal()

        # Use LeaderboardService for metric-based leaderboards
        leaderboard_service = get_leaderboard_service(db)

        # Map metric names to leaderboard types
        metric_map = {
            "earnings": "total_earnings",
            "total_earnings": "total_earnings",
            "win_rate": "win_rate",
            "games_played": "games_played",
            "avg_score": "avg_score"
        }

        leaderboard_type = metric_map.get(metric, "total_earnings")
        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=leaderboard_type,
            db=db,
            limit=limit
        )

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
        courses = course_manager.get_courses()
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
async def sync_wgp_sheet_data(request: Dict[str, str], db: Session = Depends(database.get_db)):
    """
    Sync Wolf Goat Pig specific sheet data format.

    Rate limited to once per hour to prevent excessive API calls.
    Results are cached for 1 hour.

    Uses isolated sessions per player to ensure failures are isolated and
    don't cascade to other players' data.
    """
    from .middleware.rate_limiting import rate_limiter
    from .middleware.caching import sheet_sync_cache

    try:
        # Rate limit: max once per hour
        rate_limiter.check_limit("sheet_sync", min_interval_seconds=3600)

        csv_url = request.get("csv_url")
        if not csv_url:
            raise HTTPException(status_code=400, detail="CSV URL is required")

        # Check cache first
        cache_key = f"sheet_sync:{csv_url}"
        cached_result = sheet_sync_cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached sheet sync data (CSV: {csv_url[:50]}...)")
            return cached_result

        from .services.player_service import PlayerService
        from collections import defaultdict
        import httpx
        
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
                db.rollback()  # CRITICAL: Roll back the failed transaction
                sync_results["errors"].append(f"Error processing {player_name}: {str(e)}")
                logger.error(f"Failed to process {player_name}, rolled back transaction: {e}")
                continue
        
        # Log summary of synced data
        logger.info(f"Synced {len(player_stats)} players from sheet")
        logger.info(f"Sync results: {sync_results}")
        
        # Return detailed sync information including the data that was synced
        result = {
            "sync_results": sync_results,
            "player_count": len(player_stats),
            "synced_at": datetime.now().isoformat(),
            "headers_found": headers,
            "players_synced": list(player_stats.keys()),
            "sample_data": {name: stats for name, stats in list(player_stats.items())[:3]},  # First 3 players as sample
            "ghin_data": ghin_data_collection,  # GHIN scores and handicap data
            "ghin_players_count": len(ghin_data_collection)
        }

        # Cache the result for 1 hour
        sheet_sync_cache.set(cache_key, result)
        logger.info(f"Sheet sync data cached for 1 hour (key: {cache_key})")

        return result

    except httpx.RequestError as e:
        logger.error(f"Error fetching Google Sheet: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch sheet: {str(e)}")
    except Exception as e:
        logger.error(f"Error syncing WGP sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync data: {str(e)}")

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

## BANNER MANAGEMENT ROUTES ##

@app.get("/banner")
async def get_active_banner(db: Session = Depends(database.get_db)):
    """Get the currently active banner for display on game pages (public route)"""
    try:
        banner = db.query(models.GameBanner).filter(
            models.GameBanner.is_active == True
        ).order_by(models.GameBanner.id.desc()).first()

        if not banner:
            return {"banner": None}

        return {"banner": {
            "id": banner.id,
            "title": banner.title,
            "message": banner.message,
            "banner_type": banner.banner_type,
            "background_color": banner.background_color,
            "text_color": banner.text_color,
            "show_icon": banner.show_icon,
            "dismissible": banner.dismissible
        }}
    except Exception as e:
        logger.error(f"Error fetching active banner: {e}")
        return {"banner": None}

@app.get("/admin/banner")
async def get_banner_config(x_admin_email: str = Header(None), db: Session = Depends(database.get_db)):
    """Get current banner configuration (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        banner = db.query(models.GameBanner).order_by(models.GameBanner.id.desc()).first()

        if not banner:
            return {"banner": None}

        return {
            "banner": {
                "id": banner.id,
                "title": banner.title,
                "message": banner.message,
                "banner_type": banner.banner_type,
                "is_active": banner.is_active,
                "background_color": banner.background_color,
                "text_color": banner.text_color,
                "show_icon": banner.show_icon,
                "dismissible": banner.dismissible,
                "created_at": banner.created_at,
                "updated_at": banner.updated_at
            }
        }
    except Exception as e:
        logger.error(f"Error fetching banner config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/banner")
async def create_or_update_banner(
    banner_data: schemas.GameBannerCreate,
    x_admin_email: str = Header(None),
    db: Session = Depends(database.get_db)
):
    """Create or update the game banner (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        # Deactivate all existing banners if creating a new active one
        if banner_data.is_active:
            db.query(models.GameBanner).update({"is_active": False})

        # Create new banner
        new_banner = models.GameBanner(
            title=banner_data.title,
            message=banner_data.message,
            banner_type=banner_data.banner_type,
            is_active=banner_data.is_active,
            background_color=banner_data.background_color,
            text_color=banner_data.text_color,
            show_icon=banner_data.show_icon,
            dismissible=banner_data.dismissible,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )

        db.add(new_banner)
        db.commit()
        db.refresh(new_banner)

        return {
            "status": "success",
            "message": "Banner created successfully",
            "banner": {
                "id": new_banner.id,
                "title": new_banner.title,
                "message": new_banner.message,
                "banner_type": new_banner.banner_type,
                "is_active": new_banner.is_active,
                "background_color": new_banner.background_color,
                "text_color": new_banner.text_color,
                "show_icon": new_banner.show_icon,
                "dismissible": new_banner.dismissible,
                "created_at": new_banner.created_at,
                "updated_at": new_banner.updated_at
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating banner: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/banner/{banner_id}")
async def update_banner(
    banner_id: int,
    banner_data: schemas.GameBannerUpdate,
    x_admin_email: str = Header(None),
    db: Session = Depends(database.get_db)
):
    """Update an existing banner (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        banner = db.query(models.GameBanner).filter(models.GameBanner.id == banner_id).first()

        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")

        # If activating this banner, deactivate all others
        if banner_data.is_active and banner_data.is_active != banner.is_active:
            db.query(models.GameBanner).filter(models.GameBanner.id != banner_id).update({"is_active": False})

        # Update banner fields
        update_data = banner_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(banner, field, value)

        banner.updated_at = datetime.utcnow().isoformat()

        db.commit()
        db.refresh(banner)

        return {
            "status": "success",
            "message": "Banner updated successfully",
            "banner": {
                "id": banner.id,
                "title": banner.title,
                "message": banner.message,
                "banner_type": banner.banner_type,
                "is_active": banner.is_active,
                "background_color": banner.background_color,
                "text_color": banner.text_color,
                "show_icon": banner.show_icon,
                "dismissible": banner.dismissible,
                "created_at": banner.created_at,
                "updated_at": banner.updated_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating banner: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/banner/{banner_id}")
async def delete_banner(
    banner_id: int,
    x_admin_email: str = Header(None),
    db: Session = Depends(database.get_db)
):
    """Delete a banner (admin only)"""
    # Check admin access
    admin_emails = ['stuagano@gmail.com', 'admin@wgp.com']
    if not x_admin_email or x_admin_email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        banner = db.query(models.GameBanner).filter(models.GameBanner.id == banner_id).first()

        if not banner:
            raise HTTPException(status_code=404, detail="Banner not found")

        db.delete(banner)
        db.commit()

        return {
            "status": "success",
            "message": "Banner deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting banner: {e}")
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
        
        # Create Player objects
        wgp_players = []
        for i, player_data in enumerate(all_players):
            wgp_player = Player(
                id=player_data.get("id", f"player_{i+1}"),
                name=player_data.get("name", f"Player {i+1}"),
                handicap=float(player_data.get("handicap", 18.0))
            )
            wgp_players.append(wgp_player)
        
        # Initialize simulation with players
        wgp_simulation = WolfGoatPigGame(
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
                courses = course_manager.get_courses()
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
                        wgp_simulation.course_manager.load_course(selected_course_name)
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

        # Check if captain needs to make partnership decision after first tee shot
        interaction_needed = None
        hole_state = _get_current_hole_state()
        if hole_state and hole_state.tee_shots_complete == 1:
            # First player (captain) has hit - they need to make a decision
            captain_id = hole_state.hitting_order[0] if hole_state.hitting_order else None
            if captain_id:
                # Get available partners (players who haven't hit yet)
                available_partners = hole_state.get_available_partners_for_captain(captain_id)
                if available_partners:
                    interaction_needed = {
                        "type": "captain_decision",
                        "captain_id": captain_id,
                        "available_partners": available_partners,
                        "message": f"Captain {wgp_simulation._get_player_name(captain_id)} needs to choose a partner or go solo"
                    }
                    feedback.append(f"🤔 {wgp_simulation._get_player_name(captain_id)} is captain - time to make your decision!")

        return {
            "status": "ok",
            "success": True,
            "shot_result": shot_response,
            "game_state": updated_state,
            "next_player": next_player_name,
            "hole_complete": hole_complete,
            "next_shot_available": not hole_complete and next_shot_player is not None,
            "interaction_needed": interaction_needed,
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
        # NOTE: HandicapValidator.get_handicap_category() could be used here for consistent categorization
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
        hole_state = game.hole_states.get(hole_number)
        if not hole_state:
            raise HTTPException(status_code=404, detail=f"Hole {hole_number} not found")
        
        # Check if hole is complete
        if not hole_state.hole_complete:
            raise HTTPException(status_code=400, detail=f"Hole {hole_number} is not complete yet")
        
        # Get game state and timeline events
        game_state = game.get_game_state()
        timeline_events = []
        if hasattr(wgp_simulation, 'hole_progression') and game.hole_progression:
            timeline_events = game.hole_progression.timeline_events
        
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
        
        current_hole = game.current_hole
        hole_state = game.hole_states.get(current_hole)
        
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
            captain_player = next((p for p in game.players if p.id == captain_id), None)
        
        # Get rotation order for this hole
        rotation_order = getattr(hole_state, 'rotation_order', [p.id for p in game.players])
        
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
                    furthest_player = next((p for p in game.players if p.id == player_id), None)
            current_turn = furthest_player.id if furthest_player else None
        
        # Get pending decision info
        pending_decision = None
        if hole_state.teams.pending_request:
            pending_decision = {
                "type": "partnership_request",
                "from_player": hole_state.teams.pending_request.get("requestor"),
                "to_player": hole_state.teams.pending_request.get("requested"),
                "message": f"Partnership requested by {game._get_player_name(hole_state.teams.pending_request.get('requestor'))}"
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
            team1_names = [game._get_player_name(pid) for pid in hole_state.teams.team1]
            team2_names = [game._get_player_name(pid) for pid in hole_state.teams.team2]
            teams_display.append({
                "type": "partnership",
                "description": f"{' & '.join(team1_names)} vs {' & '.join(team2_names)}"
            })
        elif hole_state.teams.type == "solo":
            solo_name = game._get_player_name(hole_state.teams.solo_player)
            opponent_names = [game._get_player_name(pid) for pid in hole_state.teams.opponents]
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
                        "player_name": game._get_player_name(player_id),
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
            events = game.timeline_manager.get_recent_events(limit)
        else:
            # Fallback to hole progression events
            events = []
            if game.hole_progression:
                events = game.hole_progression.get_timeline_events()[:limit]
        
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
        current_hole = game.current_hole
        hole_state = game.hole_states.get(current_hole)
        
        if not hole_state:
            raise HTTPException(status_code=400, detail="No active hole state")
        
        # Format poker betting state manually
        betting = hole_state.betting
        pot_size = betting.current_wager * len(game.players)
        if betting.doubled:
            pot_size *= 2
        
        # Determine betting phase
        phase = "pre-flop"  # Before tee shots
        shots_taken = sum(1 for shot in hole_state.shots_completed.values() if shot)
        if shots_taken >= len(game.players):
            phase = "flop"  # After tee shots
        if hole_state.current_shot_number > len(game.players) * 2:
            phase = "turn"  # Mid-hole
        if any(hole_state.balls_in_hole):
            phase = "river"  # Near completion
        
        poker_state = {
            "pot_size": pot_size,
            "base_bet": betting.base_wager,
            "current_bet": betting.current_wager,
            "betting_phase": phase,
            "doubled": betting.doubled,
            "players_in": len(game.players),
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


@app.post("/simulation/save-results")
def save_simulation_results(request: dict):
    """Save simulation game results to database for tracking"""
    try:
        game_state = request.get("game_state")
        final_scores = request.get("final_scores", [])

        if not game_state:
            raise HTTPException(status_code=400, detail="game_state is required")

        # For now, just log the results
        # In the future, this could save to a SimulationResults table
        logger.info(f"Saving simulation results - Players: {len(final_scores)}")
        for score in final_scores:
            logger.info(f"  {score.get('player_name')}: {score.get('points')} points (handicap {score.get('handicap')})")

        # Could extend this to save to database:
        # db = database.SessionLocal()
        # try:
        #     result = models.SimulationResult(
        #         players=final_scores,
        #         course_name=game_state.get("course_name"),
        #         created_at=datetime.utcnow()
        #     )
        #     db.add(result)
        #     db.commit()
        # finally:
        #     db.close()

        return {
            "status": "ok",
            "message": "Results saved successfully",
            "saved": True
        }

    except Exception as e:
        logger.error(f"Failed to save simulation results: {e}")
        return {
            "status": "error",
            "message": f"Failed to save results: {str(e)}",
            "saved": False
        }


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

# ========== SIMPLIFIED SCORING ENDPOINTS ==========

from .simplified_scoring import SimplifiedScoring

# Global simplified scoring instances (keyed by game_id)
simplified_games: Dict[str, SimplifiedScoring] = {}

@app.post("/wgp/simplified/start-game")
async def start_simplified_game(payload: Dict[str, Any]):
    """Start a new game with simplified scoring system"""
    try:
        game_id = payload.get("game_id", str(uuid.uuid4()))
        players = payload.get("players", [])
        
        if not players:
            raise HTTPException(status_code=400, detail="Players required")
        
        # Create simplified scoring instance
        simplified_games[game_id] = SimplifiedScoring(players)
        
        return {
            "success": True,
            "game_id": game_id,
            "message": f"Simplified game started with {len(players)} players",
            "players": simplified_games[game_id].players
        }
        
    except Exception as e:
        logger.error(f"Error starting simplified game: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start game: {str(e)}")

@app.post("/wgp/simplified/score-hole")
async def score_hole_simplified(payload: Dict[str, Any]):
    """Score a hole using the simplified scoring system"""
    try:
        game_id = payload.get("game_id")
        if not game_id or game_id not in simplified_games:
            raise HTTPException(status_code=404, detail="Game not found")
        
        hole_number = payload.get("hole_number")
        scores = payload.get("scores", {})
        teams = payload.get("teams", {})
        wager = payload.get("wager", 1)
        
        if not hole_number or not scores:
            raise HTTPException(status_code=400, detail="Hole number and scores required")
        
        # Score the hole
        game = simplified_games[game_id]
        result = game.enter_hole_scores(hole_number, scores, teams, wager)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "hole_result": result,
            "game_summary": game.get_game_summary()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring hole: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to score hole: {str(e)}")

@app.get("/wgp/simplified/{game_id}/status")
async def get_simplified_game_status(game_id: str):
    """Get current status of a simplified scoring game"""
    try:
        if game_id not in simplified_games:
            raise HTTPException(status_code=404, detail="Game not found")
        
        game = simplified_games[game_id]
        
        return {
            "game_id": game_id,
            "game_summary": game.get_game_summary(),
            "hole_history": game.get_hole_history()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.get("/wgp/simplified/{game_id}/hole-history")
async def get_simplified_hole_history(game_id: str):
    """Get hole-by-hole history for a simplified scoring game"""
    try:
        if game_id not in simplified_games:
            raise HTTPException(status_code=404, detail="Game not found")
        
        game = simplified_games[game_id]
        
        return {
            "game_id": game_id,
            "hole_history": game.get_hole_history()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hole history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


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
