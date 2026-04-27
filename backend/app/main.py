import json
import logging
import os
import random
import time
import traceback
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import httpx
from fastapi import (
    Body,
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Path,
    Query,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import and_, text
from sqlalchemy.orm import Session

from . import database, models, schemas
from .badge_routes import router as badge_router
from .managers.rule_manager import RuleManager, RuleViolationError
from .managers.scoring_manager import get_scoring_manager
from .managers.websocket_manager import manager as websocket_manager
from .migrations_routes import router as migrations_router
from .post_hole_analytics import PostHoleAnalyzer

# Import routers
from .routers import admin_oauth, analytics, courses, foretees, games, games_holes, games_players, health, leaderboard, matchmaking, players, sheet_integration, wgp_actions
from .routers.email_routes import initialize_email_scheduler
from .services.email_service import get_email_service
from .services.game_lifecycle_service import get_game_lifecycle_service
from .services.leaderboard_service import get_leaderboard_service
from .services.legacy_player_service import (
    get_legacy_players,
    validate_player_for_legacy,
)
from .services.legacy_signup_service import get_legacy_signup_service
from .services.notification_service import get_notification_service
# Simulation timeline enhancements removed
from .state.course_manager import CourseManager
from .validators import GameStateValidationError, GameStateValidator, HandicapValidator
from .wolf_goat_pig import Player, WolfGoatPigGame

# Configure logging
logger = logging.getLogger(__name__)

# Shared state accessors — actual state lives in state/app_state.py
from .state.app_state import (  # noqa: E402
    get_course_manager,
    get_email_scheduler,
    get_email_service_instance,
    get_post_hole_analyzer,
    set_course_manager,
    set_email_scheduler,
    set_email_service_instance,
    set_post_hole_analyzer,
)


# Import shared action models from schemas
from .schemas import ActionRequest, ActionResponse, CompleteHoleRequest, HoleTeams, ManualPointsOverride, RotationSelectionRequest  # noqa: E402


# Testing seed models moved to routers/games_players.py


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("🐺 Wolf Goat Pig API starting up...")
    logger.info(f"ENVIRONMENT: {os.getenv('ENVIRONMENT')}")

    # Initialize Post-Hole Analyzer and Course Manager (deferred from import time)
    if get_post_hole_analyzer() is None:
        set_post_hole_analyzer(PostHoleAnalyzer())
    if get_course_manager() is None:
        set_course_manager(CourseManager())

    # Initialize database
    try:
        database.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize email scheduler if enabled
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

    # Kick off an immediate legacy rounds sync on startup (non-blocking)
    try:
        import threading
        from .services.email_scheduler import email_scheduler as _sched
        t = threading.Thread(target=_sched._sync_legacy_rounds, daemon=True)
        t.start()
        logger.info("📊 Legacy rounds sync started in background")
    except Exception as e:
        logger.warning(f"Legacy rounds startup sync failed to launch: {e}")

    logger.info("🚀 Wolf Goat Pig API startup completed successfully!")

    yield  # Application runs here

    # Shutdown
    logger.info("🛑 Wolf Goat Pig API shutting down...")

    # Stop email scheduler if it was started
    try:
        _scheduler = get_email_scheduler()
        if _scheduler is not None and hasattr(_scheduler, "stop"):
            _scheduler.stop()
            logger.info("📧 Email scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop email scheduler: {e!s}")

    # Close database connections gracefully
    try:
        if database.engine:
            database.engine.dispose()
            logger.info("🗄️ Database connections closed successfully")
    except Exception as e:
        logger.error(f"Failed to close database connections: {e!s}")

    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="Wolf Goat Pig Golf Simulation API",
    description="A comprehensive golf betting simulation API with unified Action API",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
    lifespan=lifespan,
)

ENABLE_TEST_ENDPOINTS = os.getenv("ENABLE_TEST_ENDPOINTS", "false").lower() in {
    "1",
    "true",
    "yes",
}
from .utils.admin_auth import require_admin  # noqa: E402


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
    allowed_origins.extend(
        [
            "http://localhost:3000",  # Local development
            "http://localhost:3001",  # Alternative local port
            "http://localhost:3333",  # E2E test port
            "http://127.0.0.1:3000",  # Alternative localhost
            "http://127.0.0.1:3001",  # Alternative localhost
            "http://127.0.0.1:3333",  # Alternative E2E test port
        ]
    )

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
        "X-Admin-Key",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
)

# Include badge system routes
app.include_router(badge_router)

# betting_events router removed - events now sent inline with hole completion

# Include migrations management routes
app.include_router(migrations_router)

# Include spreadsheet sync routes (admin)
from .routers import spreadsheet_sync

app.include_router(spreadsheet_sync.router)

# Include unified data routes (merges all data sources)
from .routers import unified_data

app.include_router(unified_data.router)

# Include modular routers
app.include_router(health.router)
app.include_router(sheet_integration.router)
app.include_router(players.router)
app.include_router(courses.router)

# Import and include course data update router
from .routers import course_data_update

app.include_router(course_data_update.router)
app.include_router(foretees.router)
app.include_router(matchmaking.router)
from .routers import commissioner, ghin, scorecard
app.include_router(commissioner.router)
app.include_router(ghin.router)
app.include_router(scorecard.router)
app.include_router(analytics.router)
app.include_router(leaderboard.router)
from .routers import admin, betting_odds, email_routes, legacy_scoring, messages, signups, team_formation, websocket_routes
app.include_router(messages.router)
app.include_router(email_routes.router)
app.include_router(signups.router)
app.include_router(admin_oauth.router)
app.include_router(admin.router)
app.include_router(betting_odds.router)
app.include_router(team_formation.router)
app.include_router(wgp_actions.router)
app.include_router(games.router)
app.include_router(games_holes.router)
app.include_router(games_players.router)
app.include_router(legacy_scoring.router)
app.include_router(websocket_routes.router)

logger.info("✅ All routers registered")


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions and preserve their status codes"""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    # Add logging for host header during exceptions
    logger.error(f"Request Host header: {request.headers.get('host')}")
    if request.client is not None:
        logger.error(f"Request Client host: {request.client.host}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP error", "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


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
        rules = db.query(models.Rule).all()
        return rules
    except Exception as e:
        logger.error(f"Error getting rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rules")
    finally:
        db.close()



# Games routes moved to routers/games.py, routers/games_holes.py, routers/games_players.py

# WGP action engine moved to routers/wgp_actions.py + domain/wgp_handlers_*.py

# Betting odds routes moved to routers/betting_odds.py

# Sheet Integration Endpoints — moved to routers/sheet_integration.py

# OAuth2 Email endpoints — moved to routers/admin_oauth.py

# Banner and admin routes moved to routers/admin.py


# ============================================================================
# SIMULATION API ENDPOINTS
# ============================================================================


class BettingDecisionRequest(BaseModel):
    """Request model for betting decisions"""

    decision: dict[str, Any]


def _get_current_hole_state():
    """Safely fetch the current hole state from the active simulation."""
    if not wgp_simulation:  # type: ignore
        return None
    return wgp_simulation.hole_states.get(wgp_simulation.current_hole)  # type: ignore


def _get_default_player_id(preferred_role: str = "captain") -> str | None:
    """
    Provide a sensible default player identifier for legacy API calls that
    don't explicitly include a player context.
    """
    hole_state = _get_current_hole_state()
    if hole_state and getattr(hole_state, "teams", None):
        if preferred_role == "captain" and getattr(hole_state.teams, "captain", None):
            return hole_state.teams.captain  # type: ignore
        if preferred_role == "solo" and getattr(hole_state.teams, "solo_player", None):
            return hole_state.teams.solo_player  # type: ignore

    if wgp_simulation and getattr(wgp_simulation, "players", None):  # type: ignore
        for player in wgp_simulation.players:  # type: ignore
            if player.id == "human":
                return player.id  # type: ignore
        return wgp_simulation.players[0].id if wgp_simulation.players else None  # type: ignore
    return None


def _get_opposing_team_id(reference_player_id: str | None = None) -> str:
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


def _get_pending_partnership_request() -> dict[str, Any]:
    """Return any pending partnership request details from the current hole."""
    hole_state = _get_current_hole_state()
    if hole_state and getattr(hole_state, "teams", None):
        return hole_state.teams.pending_request or {}
    return {}


# Probability helpers moved to routers/betting_odds.py

# Legacy Player + Daily Sign-up endpoints moved to routers/signups.py

# Team Formation + Pairing endpoints moved to routers/team_formation.py


# Static file serving for React frontend (must be at end after all API routes)
from pathlib import Path

# Get the path to the built React app
STATIC_DIR = Path(__file__).parent.parent.parent / "frontend" / "build"

# Matchmaking endpoints — moved to routers/matchmaking.py


if ENABLE_TEST_ENDPOINTS:

    @app.get("/debug/paths")
    async def debug_paths(x_admin_email: str | None = Header(None)):  # type: ignore
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
            "static_dir_contents": (list(static_dir.iterdir()) if static_dir.exists() else []),
        }


# Mount static files if build directory exists
static_assets_dir = STATIC_DIR / "static"

if STATIC_DIR.exists() and static_assets_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_assets_dir)), name="static")
else:
    logger.warning("Frontend static assets not found. Expected %s", static_assets_dir)



@app.head("/")
async def head_root():
    """Handle HEAD requests for health checks (e.g., Render)."""
    return Response(status_code=200)


@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """Serve the built frontend when available, otherwise render a helpful status page."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    frontend_url = (
        os.getenv("PUBLIC_FRONTEND_URL") or os.getenv("FRONTEND_BASE_URL") or "https://wolf-goat-pig.vercel.app"
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
          <p class="meta">Last checked: {datetime.now(UTC).isoformat()}Z</p>
        </main>
      </body>
    </html>
    """

    return HTMLResponse(content=html, status_code=200)
