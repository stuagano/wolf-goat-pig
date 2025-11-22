"""
Health Check Router

System health monitoring endpoints.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import logging
import os

from .. import database, models
from ..wolf_goat_pig import WolfGoatPigGame
from ..state.course_manager import CourseManager

logger = logging.getLogger("app.routers.health")

# Initialize CourseManager instance for health checks
course_manager = CourseManager()

router = APIRouter(
    tags=["health"]
)


@router.get("/health")
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
            courses = course_manager.get_courses()
            course_count = len(courses) if courses else 0

            if course_count >= 1:
                health_status["components"]["courses"] = {
                    "status": "healthy",
                    "message": f"{course_count} courses available",
                    "courses": [c["name"] for c in courses] if courses else []
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
            # Check if we can instantiate the game engine
            game = WolfGoatPigGame(player_count=4)
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


        # 7. Import seeding status check
        try:
            from ..seed_data import get_seeding_status
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


@router.get("/healthz")
def health_check_render_alias():
    """Simplified health endpoint for Render monitoring."""
    try:
        # Reuse the comprehensive health check; Render only needs 200/503.
        health_check()
        return {"status": "ok"}
    except HTTPException as exc:
        # Mirror original status code to keep behaviour consistent.
        raise exc


@router.get("/ready")
def readiness_check():
    """
    Lightweight readiness probe for Render/K8s.
    Only checks if the app is running, not comprehensive system health.
    Use /health for detailed health checks.
    """
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat()
    }
