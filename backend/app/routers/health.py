"""
Health Check Router (Refactored)

System health monitoring endpoints.

Uses new utility patterns:
- @handle_api_errors decorator for consistent error handling
- with_db_session context manager for database access
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, cast

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from .. import database, models
from ..state.course_manager import CourseManager
from ..utils.api_helpers import handle_api_errors, managed_session
from ..wolf_goat_pig import WolfGoatPigGame

logger = logging.getLogger("app.routers.health")

# Initialize CourseManager instance for health checks
course_manager = CourseManager()

router = APIRouter(
    tags=["health"]
)


def _check_database(health_status: Dict[str, Any]) -> bool:
    """Check database connectivity"""
    try:
        with managed_session() as db:
            db.execute(text("SELECT 1"))
            health_status["components"]["database"] = {
                "status": "healthy",
                "message": "Database connection successful"
            }
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        return False


def _check_courses(health_status: Dict[str, Any], is_initial_deployment: bool) -> bool:
    """Check course data availability"""
    try:
        courses = course_manager.get_courses()
        course_count = len(courses) if courses else 0

        if course_count >= 1:
            health_status["components"]["courses"] = {
                "status": "healthy",
                "message": f"{course_count} courses available",
                "courses": list(courses.keys()) if courses else []
            }
            return True
        else:
            health_status["components"]["courses"] = {
                "status": "warning" if is_initial_deployment else "unhealthy",
                "message": "No courses available (may be initializing)"
            }
            return is_initial_deployment
    except Exception as e:
        logger.error(f"Course availability check failed: {e}")
        health_status["components"]["courses"] = {
            "status": "warning" if is_initial_deployment else "unhealthy",
            "message": f"Course check failed: {str(e)}"
        }
        return is_initial_deployment


def _check_rules(health_status: Dict[str, Any]) -> bool:
    """Check rules availability"""
    try:
        with managed_session() as db:
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
            return True
    except Exception as e:
        logger.error(f"Rules availability check failed: {e}")
        health_status["components"]["rules"] = {
            "status": "warning",
            "message": f"Rules check error: {str(e)}"
        }
        return True  # Rules check doesn't fail health


def _check_ai_players(health_status: Dict[str, Any], is_initial_deployment: bool) -> bool:
    """Check AI players availability"""
    try:
        with managed_session() as db:
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
                return True
            elif ai_player_count >= 1:
                health_status["components"]["ai_players"] = {
                    "status": "warning",
                    "message": f"Only {ai_player_count} AI players available, need at least 4 for full game"
                }
                return True
            else:
                health_status["components"]["ai_players"] = {
                    "status": "warning",
                    "message": "No AI players available (may be initializing)"
                }
                return is_initial_deployment
    except Exception as e:
        logger.error(f"AI players availability check failed: {e}")
        health_status["components"]["ai_players"] = {
            "status": "warning",
            "message": f"AI players check failed: {str(e)}"
        }
        return True


def _check_simulation(health_status: Dict[str, Any], is_initial_deployment: bool) -> bool:
    """Check simulation engine initialization"""
    try:
        # Check if we can instantiate the game engine
        _game = WolfGoatPigGame(player_count=4)
        health_status["components"]["simulation"] = {
            "status": "healthy",
            "message": "Simulation engine operational"
        }
        return True
    except Exception as e:
        logger.error(f"Simulation initialization test failed: {e}")
        health_status["components"]["simulation"] = {
            "status": "warning" if is_initial_deployment else "unhealthy",
            "message": f"Simulation test failed: {str(e)}"
        }
        return is_initial_deployment


def _check_data_seeding(health_status: Dict[str, Any]) -> bool:
    """Check data seeding status"""
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
    return True  # Seeding check doesn't fail health


@router.get("/health")
@handle_api_errors(operation_name="health check")
def health_check() -> Dict[str, Any]:
    """Comprehensive health check endpoint verifying all critical systems"""
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "version": "1.0.0",
        "components": {}
    }

    # During initial deployment, be more lenient with health checks
    is_initial_deployment = os.getenv("ENVIRONMENT") == "production"

    # Run all health checks
    checks = [
        _check_database(health_status),
        _check_courses(health_status, is_initial_deployment),
        _check_rules(health_status),
        _check_ai_players(health_status, is_initial_deployment),
        _check_simulation(health_status, is_initial_deployment),
        _check_data_seeding(health_status),
    ]

    overall_healthy = all(checks)

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


@router.post("/admin/seed-course-holes")
@handle_api_errors(operation_name="seed course holes")
def seed_course_holes() -> Dict[str, Any]:
    """
    Admin endpoint to seed holes for courses that are missing them.

    This is a one-time fix for courses that were seeded without hole data.
    It adds holes to existing courses using the DEFAULT_COURSES data.
    """
    from ..seed_courses import DEFAULT_COURSES

    results: Dict[str, Any] = {
        "status": "success",
        "courses_updated": [],
        "courses_skipped": [],
        "errors": []
    }

    try:
        with managed_session() as db:
            for course_data in DEFAULT_COURSES:
                course_name = course_data['name']
                try:
                    existing_course = db.query(models.Course).filter_by(name=course_name).first()

                    if not existing_course:
                        results["courses_skipped"].append({
                            "name": course_name,
                            "reason": "Course not found in database"
                        })
                        continue

                    # Check if holes already exist
                    existing_holes = db.query(models.Hole).filter(
                        models.Hole.course_id == existing_course.id
                    ).count()

                    if existing_holes > 0:
                        results["courses_skipped"].append({
                            "name": course_name,
                            "reason": f"Already has {existing_holes} holes"
                        })
                        continue

                    # Add holes
                    holes_data = cast(List[Dict[str, Any]], course_data.get('holes_data', []))
                    for hole_detail in holes_data:
                        hole = models.Hole(
                            course_id=existing_course.id,
                            hole_number=hole_detail['hole_number'],
                            par=hole_detail['par'],
                            yards=hole_detail['yards'],
                            handicap=hole_detail['stroke_index'],
                            description=hole_detail.get('description'),
                            tee_box=hole_detail.get('tee_box', 'white')
                        )
                        db.add(hole)

                    results["courses_updated"].append({
                        "name": course_name,
                        "holes_added": len(holes_data)
                    })
                    logger.info(f"Added {len(holes_data)} holes to {course_name}")

                except Exception as e:
                    results["errors"].append({
                        "course": course_name,
                        "error": str(e)
                    })
                    logger.error(f"Error seeding holes for {course_name}: {e}")

            db.commit()

        if results["errors"]:
            results["status"] = "partial"

        return results

    except Exception as e:
        logger.error(f"Failed to seed course holes: {e}")
        results["status"] = "error"
        results["message"] = str(e)
        return results
