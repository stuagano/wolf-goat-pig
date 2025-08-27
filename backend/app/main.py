from fastapi import FastAPI, Depends, Body, HTTPException, Request, Path, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from . import models, schemas, crud, database

from .game_state import game_state
from .wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer
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

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
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
    allow_origins=[
        "https://wolf-goat-pig.vercel.app",  # Production frontend
        "http://localhost:3000",             # Local development
        "http://localhost:3001",             # Alternative local port
        "https://wolf-goat-pig-frontend.onrender.com"  # Alternative frontend URL
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
async def startup():
    """Enhanced startup event handler with comprehensive bootstrapping."""
    logger.info("🐺 Wolf Goat Pig API starting up...")
    logger.info(f"ENVIRONMENT: {os.getenv('ENVIRONMENT')}")
    
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
        
        logger.info("🚀 Wolf Goat Pig API startup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}")
        logger.error("⚠️ Application may not function properly")
        # Don't raise - allow app to start with limited functionality

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
                    "status": "unhealthy",
                    "message": "No courses available"
                }
                overall_healthy = False
                
        except Exception as e:
            logger.error(f"Course availability check failed: {e}")
            health_status["components"]["courses"] = {
                "status": "unhealthy",
                "message": f"Course check failed: {str(e)}"
            }
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
                ai_player_count = db.query(models.PlayerProfile).filter_by(is_ai=True, is_active=True).count()
                
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
                        "status": "unhealthy",
                        "message": "No AI players available"
                    }
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
                "status": "unhealthy",
                "message": f"Simulation test failed: {str(e)}"
            }
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
                "status": "unhealthy",
                "message": f"Game state check failed: {str(e)}"
            }
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
            
            # Initialize the simulation with these players
            try:
                wgp_simulation.__init__(player_count=len(wgp_players), players=wgp_players)
                logger.info("WGP simulation initialized successfully")
            except Exception as sim_init_error:
                logger.error(f"WGP simulation initialization failed: {sim_init_error}")
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
def sync_wgp_sheet_data(request: Dict[str, str]):
    """Sync Wolf Goat Pig specific sheet data format."""
    try:
        db = database.SessionLocal()
        from .services.player_service import PlayerService
        from collections import defaultdict
        import requests
        
        csv_url = request.get("csv_url")
        if not csv_url:
            raise HTTPException(status_code=400, detail="CSV URL is required")
        
        # Fetch the CSV data
        response = requests.get(csv_url, timeout=30)
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
                # Quarters column (total earnings in quarters - can be negative)
                if 'quarters' in header_map and header_map['quarters'] < len(values):
                    try:
                        quarters_value = values[header_map['quarters']]
                        if quarters_value and quarters_value != '':
                            # Handle negative values (e.g., "-155")
                            quarters_int = int(quarters_value)
                            player_stats[player_name]["quarters"] = quarters_int
                            player_stats[player_name]["total_earnings"] = float(quarters_int)
                            logger.debug(f"Set {player_name} quarters to {quarters_value}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing quarters for {player_name}: {e}")
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
                
                # Rounds column (games played)
                if 'rounds' in header_map and header_map['rounds'] < len(values):
                    try:
                        rounds_value = values[header_map['rounds']]
                        if rounds_value and rounds_value != '':
                            player_stats[player_name]["rounds"] = int(rounds_value)
                            logger.debug(f"Set {player_name} rounds to {rounds_value}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing rounds for {player_name}: {e}")
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
                if player_stats[player_name]["quarters"] > 0 or player_stats[player_name]["rounds"] > 0:
                    logger.info(f"Extracted data for {player_name}: {player_stats[player_name]}")
        
        # Create/update players in database
        player_service = PlayerService(db)
        sync_results = {
            "players_processed": 0,
            "players_created": 0,
            "players_updated": 0,
            "errors": []
        }
        
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
            "sample_data": {name: stats for name, stats in list(player_stats.items())[:3]}  # First 3 players as sample
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Google Sheet: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch sheet: {str(e)}")
    except Exception as e:
        logger.error(f"Error syncing WGP sheet data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync data: {str(e)}")
    finally:
        db.close()

@app.post("/sheet-integration/fetch-google-sheet")
def fetch_google_sheet(request: Dict[str, str]):
    """Fetch data from a Google Sheets CSV URL."""
    try:
        import requests
        csv_url = request.get("csv_url")
        if not csv_url:
            raise HTTPException(status_code=400, detail="CSV URL is required")
        
        # Fetch the CSV data from Google Sheets
        response = requests.get(csv_url, timeout=30)
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
        
    except requests.exceptions.RequestException as e:
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
        
        # Set computer players if specified
        if 'computer_players' in request and request['computer_players']:
            comp_players = request['computer_players']
            personalities = request.get('personalities', ["balanced"] * len(comp_players))
            wgp_simulation.set_computer_players(comp_players, personalities)
        
        # Load course if specified
        course_id = request.get('course_id') or (course_name and 1)  # Use course_name for lookup
        if course_id or course_name:
            try:
                courses = game_state.get_courses()
                if course_id:
                    selected_course = next((c for c in courses if c.id == course_id), None)
                elif course_name:
                    selected_course = next((c for c in courses if c.name == course_name), None)
                else:
                    selected_course = None
                
                if selected_course:
                    # Set course for simulation
                    logger.info(f"Using course: {selected_course.name}")
                else:
                    logger.warning(f"Course not found: {course_name or course_id}")
            except Exception as course_error:
                logger.warning(f"Could not load course {course_name or course_id}: {course_error}")
        
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
def simulate_hole(request: SimulationPlayHoleRequest):
    """Complete simulation of an entire hole with given decisions"""
    global wgp_simulation
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized. Call /simulation/setup first.")
        
        # Process the decision for hole simulation
        decision = request.decision
        
        # For now, simulate all shots for the hole
        hole_results = []
        max_shots = 20  # Safety limit
        shot_count = 0
        
        while shot_count < max_shots:
            next_player = wgp_simulation._get_next_shot_player()
            if not next_player:
                break
                
            # Simulate shot
            shot_response = wgp_simulation.simulate_shot(next_player)
            hole_results.append(shot_response)
            shot_count += 1
            
            # Check if hole is complete
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
        
    except Exception as e:
        logger.error(f"Hole simulation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to simulate hole: {str(e)}")

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
        hole_state = wgp_simulation.hole_states.get(wgp_simulation.current_hole)
        if not hole_state:
            return {"success": True, "probabilities": {}}
        
        # Get player's current ball position
        ball_position = hole_state.get_player_ball_position(next_player)
        
        # Calculate probabilities based on lie type and distance
        probabilities = {
            "excellent": 0.15,
            "good": 0.35, 
            "average": 0.30,
            "poor": 0.15,
            "disaster": 0.05
        }
        
        # Adjust based on lie type
        if ball_position:
            if ball_position.lie_type == "tee":
                probabilities.update({
                    "excellent": 0.25,
                    "good": 0.40,
                    "average": 0.25,
                    "poor": 0.08,
                    "disaster": 0.02
                })
            elif ball_position.lie_type == "rough":
                probabilities.update({
                    "excellent": 0.08,
                    "good": 0.22,
                    "average": 0.35,
                    "poor": 0.25,
                    "disaster": 0.10
                })
            elif ball_position.lie_type == "bunker":
                probabilities.update({
                    "excellent": 0.05,
                    "good": 0.15,
                    "average": 0.30,
                    "poor": 0.35,
                    "disaster": 0.15
                })
        
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

@app.post("/simulation/betting-decision")
def make_betting_decision(request: BettingDecisionRequest):
    """Process a betting decision in the simulation"""
    global wgp_simulation
    
    try:
        if not wgp_simulation:
            raise HTTPException(status_code=400, detail="Simulation not initialized")
        
        decision = request.decision
        decision_type = decision.get("type")
        player_id = decision.get("player_id")
        
        result = {"success": False, "message": "Unknown decision type"}
        
        # Process different types of betting decisions
        if decision_type == "partnership_request":
            partner_id = decision.get("partner_id")
            if partner_id:
                result = wgp_simulation.request_partner(player_id, partner_id)
                
        elif decision_type == "partnership_response":
            accept = decision.get("accept", False)
            result = wgp_simulation.respond_to_partnership(player_id, accept)
            
        elif decision_type == "double_offer":
            result = wgp_simulation.offer_double(player_id)
            
        elif decision_type == "double_response":
            accept = decision.get("accept", False)
            result = wgp_simulation.respond_to_double("responding_team", accept)
            
        elif decision_type == "go_solo":
            result = wgp_simulation.captain_go_solo(player_id)
            
        # Get updated game state
        updated_state = wgp_simulation.get_game_state()
        
        return {
            "success": True,
            "decision_result": result,
            "game_state": updated_state
        }
        
    except Exception as e:
        logger.error(f"Betting decision failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process betting decision: {str(e)}")

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

# Static file serving for React frontend (must be at end after all API routes)
from pathlib import Path

# Get the path to the built React app
STATIC_DIR = Path(__file__).parent.parent.parent / "frontend" / "build"

# Simple test endpoint  
@app.get("/test-deployment")
async def test_deployment():
    """Test that new deployments are working"""
    return {"message": "Deployment is working", "timestamp": datetime.now().isoformat()}

# Debug endpoint to check paths
@app.get("/debug/paths")
async def debug_paths():
    """Debug endpoint to check file paths"""
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
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR / "static")), name="static")
    
    # Simple root route for testing
    @app.get("/")
    async def serve_homepage():
        """Serve React app homepage"""
        index_file = STATIC_DIR / "index.html" 
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            raise HTTPException(status_code=404, detail="Frontend not built")
else:
    logger.warning("Frontend build directory not found. Frontend will not be served.")


