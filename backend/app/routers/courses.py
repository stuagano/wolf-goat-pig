"""
Courses Router (Refactored)

Course management and import functionality, including course CRUD operations,
course import from external sources, and course preview functionality.

Uses new utility patterns:
- @handle_api_errors decorator for consistent error handling
- Dependency injection for database sessions
"""

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, cast

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..course_import import import_course_by_name, import_course_from_json
from ..database import get_db
from ..state.course_manager import CourseManager
from ..utils.api_helpers import handle_api_errors, ApiResponse

logger = logging.getLogger("app.routers.courses")

router = APIRouter(
    prefix="/courses",
    tags=["courses"]
)

# Initialize course manager
course_manager = CourseManager()


def get_fallback_courses() -> Dict[str, Any]:
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
                    "handicap": ((i - 1) % 18) + 1,
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
            "description": "Classic parkland course on Bainbridge Island, WA (Est. 1903)",
            "holes": [
                {"hole_number": 1, "par": 5, "yards": 476, "handicap": 5, "description": "Opening Drive - gentle starting hole, slight dogleg right"},
                {"hole_number": 2, "par": 3, "yards": 175, "handicap": 13, "description": "Short Iron - downhill par 3 with bunkers"},
                {"hole_number": 3, "par": 4, "yards": 401, "handicap": 1, "description": "The Challenge - handicap 1, tough dogleg left"},
                {"hole_number": 4, "par": 3, "yards": 133, "handicap": 17, "description": "Precision - short but tricky par 3"},
                {"hole_number": 5, "par": 5, "yards": 498, "handicap": 7, "description": "The Long One - reachable par 5"},
                {"hole_number": 6, "par": 4, "yards": 351, "handicap": 11, "description": "Mid Iron - strategic placement required"},
                {"hole_number": 7, "par": 4, "yards": 316, "handicap": 15, "description": "Risk Reward - short par 4"},
                {"hole_number": 8, "par": 4, "yards": 294, "handicap": 3, "description": "The Turn - another short par 4"},
                {"hole_number": 9, "par": 4, "yards": 340, "handicap": 9, "description": "Home Bound - tough finishing hole for front nine"},
                {"hole_number": 10, "par": 3, "yards": 239, "handicap": 2, "description": "Back Nine Starter - long par 3"},
                {"hole_number": 11, "par": 4, "yards": 401, "handicap": 16, "description": "The Beast - second toughest hole"},
                {"hole_number": 12, "par": 3, "yards": 204, "handicap": 8, "description": "Over Water - beautiful par 3"},
                {"hole_number": 13, "par": 4, "yards": 310, "handicap": 14, "description": "Breathing Room - easiest hole"},
                {"hole_number": 14, "par": 4, "yards": 317, "handicap": 4, "description": "Deceptive - looks easy but plays tough"},
                {"hole_number": 15, "par": 4, "yards": 396, "handicap": 18, "description": "The Stretch - start of tough finish"},
                {"hole_number": 16, "par": 4, "yards": 358, "handicap": 10, "description": "Penultimate - tough as you near finish"},
                {"hole_number": 17, "par": 5, "yards": 490, "handicap": 12, "description": "The Penultimate - par 5 start of Hoepfinger"},
                {"hole_number": 18, "par": 4, "yards": 394, "handicap": 6, "description": "The Finale - strong finishing par 4"}
            ],
            "total_par": 71,
            "total_yards": 6093,
            "hole_count": 18
        }
    }


# ============================================================================
# Course Management Endpoints
# ============================================================================

@router.get("")
def get_courses() -> Any:
    """Get all available courses with robust fallback handling.

    Returns course data WITH holes information for each course.
    """
    global course_manager
    try:
        # First get the list of course names
        courses_summary: Any = course_manager.get_courses()

        # Ensure we always return at least one default course
        if not courses_summary:
            logger.warning("No courses found in game state, attempting to reload from database")

            try:
                from ..seed_data import get_seeding_status
                seeding_status = get_seeding_status()

                if seeding_status["status"] == "success":
                    # Reinitialize by creating a new instance
                    course_manager = CourseManager()
                    courses_summary = course_manager.get_courses()

                    if courses_summary:
                        logger.info(f"Successfully reloaded {len(courses_summary)} courses from database")
                    else:
                        logger.warning("Course manager reinitialization failed, using fallback")
                        return get_fallback_courses()
                else:
                    logger.warning("Database seeding incomplete, using fallback courses")
                    return get_fallback_courses()

            except Exception as reload_error:
                logger.error(f"Failed to reload courses from database: {reload_error}")
                return get_fallback_courses()

        # Now get detailed course data (with holes) for each course
        if isinstance(courses_summary, dict):
            courses_with_holes: Dict[str, Any] = {}
            for course_name in courses_summary.keys():
                course_details = course_manager.get_course_details(course_name)
                if course_details:
                    courses_with_holes[course_name] = course_details
                else:
                    # Fall back to summary data if details not available
                    courses_with_holes[course_name] = courses_summary[course_name]

            logger.info(f"Retrieved {len(courses_with_holes)} courses with holes data: {list(courses_with_holes.keys())}")
            return courses_with_holes

        return courses_summary

    except Exception as e:
        logger.error(f"Critical error getting courses: {e}")
        logger.error(traceback.format_exc())
        courses = get_fallback_courses()
        logger.warning("Returning fallback courses due to critical error")
        return courses


@router.get("/{course_id}")
@handle_api_errors(operation_name="get course by ID")
def get_course_by_id(course_id: int) -> Dict[str, Any]:
    """Get a specific course by ID (index in courses list)"""
    courses: Any = course_manager.get_courses()
    if not courses:
        raise HTTPException(status_code=404, detail="No courses available")

    if isinstance(courses, dict):
        course_list = list(courses.values())
        if course_id >= len(course_list) or course_id < 0:
            raise HTTPException(status_code=404, detail="Course not found")
        return cast(Dict[str, Any], course_list[course_id])
    else:
        raise HTTPException(status_code=500, detail="Invalid courses data structure")


@router.post("", response_model=dict)
@handle_api_errors(operation_name="add course")
def add_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Add a new course - persists to database with Hole records"""
    course_dict = course.dict()

    # Check if course already exists
    existing_course = db.query(models.Course).filter(models.Course.name == course.name).first()
    if existing_course:
        raise ValueError(f"Course '{course.name}' already exists")

    # Calculate course statistics
    holes = course_dict.get("holes", [])
    total_par = sum(h.get("par", 0) for h in holes)
    total_yards = sum(h.get("yards", 0) for h in holes)

    # Create database record
    now = datetime.now(timezone.utc).isoformat()
    db_course = models.Course(
        name=course.name,
        description=course_dict.get("description", ""),
        total_par=total_par,
        total_yards=total_yards,
        holes_data=holes,
        created_at=now,
        updated_at=now
    )

    db.add(db_course)
    db.flush()

    # Create Hole records for each hole
    for hole_data in holes:
        db_hole = models.Hole(
            course_id=db_course.id,
            hole_number=hole_data.get("hole_number"),
            par=hole_data.get("par"),
            yards=hole_data.get("yards"),
            handicap=hole_data.get("handicap"),
            description=hole_data.get("description"),
            tee_box=hole_data.get("tee_box", "regular")
        )
        db.add(db_hole)

    db.commit()
    db.refresh(db_course)

    # Also add to in-memory course manager
    course_manager.add_course(course.name, holes)  # type: ignore

    logger.info(f"Created course '{course.name}' with {len(holes)} holes (ID: {db_course.id})")

    return ApiResponse.success(
        data={
            "id": db_course.id,
            "name": db_course.name,
            "total_par": total_par,
            "total_yards": total_yards,
            "hole_count": len(holes)
        },
        message=f"Course '{course.name}' added successfully"
    )


@router.put("/{course_name}")
@handle_api_errors(operation_name="update course")
def update_course(
    course_name: str,
    course_update: schemas.CourseUpdate,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update an existing course - persists to database and updates Hole records"""
    db_course = db.query(models.Course).filter(models.Course.name == course_name).first()
    if not db_course:
        raise HTTPException(status_code=404, detail=f"Course '{course_name}' not found")

    update_dict = course_update.dict(exclude_unset=True)

    if "name" in update_dict:
        db_course.name = update_dict["name"]
    if "description" in update_dict:
        db_course.description = update_dict["description"]
    if "holes" in update_dict:
        holes = update_dict["holes"]
        db_course.holes_data = holes
        db_course.total_par = sum(h.get("par", 0) for h in holes)
        db_course.total_yards = sum(h.get("yards", 0) for h in holes)

        # Update Hole records - delete existing and create new ones
        db.query(models.Hole).filter(models.Hole.course_id == db_course.id).delete()
        for hole_data in holes:
            db_hole = models.Hole(
                course_id=db_course.id,
                hole_number=hole_data.get("hole_number"),
                par=hole_data.get("par"),
                yards=hole_data.get("yards"),
                handicap=hole_data.get("handicap"),
                description=hole_data.get("description"),
                tee_box=hole_data.get("tee_box", "regular")
            )
            db.add(db_hole)

    db_course.updated_at = datetime.now(timezone.utc).isoformat()

    db.commit()
    db.refresh(db_course)

    # Update in-memory course manager
    if "holes" in update_dict:
        course_manager.update_course(course_name, update_dict["holes"])  # type: ignore

    logger.info(f"Updated course '{course_name}' (ID: {db_course.id})")

    return ApiResponse.success(
        data={
            "id": db_course.id,
            "name": db_course.name,
            "total_par": db_course.total_par,
            "total_yards": db_course.total_yards
        },
        message=f"Course '{course_name}' updated successfully"
    )


@router.delete("/{course_name}")
@handle_api_errors(operation_name="delete course")
def delete_course(
    course_name: str = Path(...),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Delete a course - removes from database"""
    db_course = db.query(models.Course).filter(models.Course.name == course_name).first()
    if not db_course:
        raise HTTPException(status_code=404, detail=f"Course '{course_name}' not found")

    db.delete(db_course)
    db.commit()

    # Also remove from in-memory course manager
    course_manager.delete_course(course_name)  # type: ignore

    logger.info(f"Deleted course '{course_name}' from database")

    return ApiResponse.success(message=f"Course '{course_name}' deleted successfully")


# ============================================================================
# Course Import Endpoints
# ============================================================================

@router.post("/import/search")
@handle_api_errors(operation_name="import course by search")
async def import_course_by_search(request: schemas.CourseImportRequest) -> Dict[str, Any]:
    """Search and import a course by name"""
    result = await import_course_by_name(request.course_name, request.state, request.city)
    return cast(Dict[str, Any], result if result else {})


@router.post("/import/file")
@handle_api_errors(operation_name="import course from file")
async def import_course_from_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Import a course from uploaded JSON file"""
    filename = file.filename or ""
    if not filename.endswith('.json'):
        raise ValueError("File must be a JSON file")

    content = await file.read()
    course_data = json.loads(content.decode('utf-8'))

    result = await import_course_from_json(course_data)
    return cast(Dict[str, Any], result if result else {})


@router.get("/import/sources")
@handle_api_errors(operation_name="get import sources")
def get_import_sources() -> Dict[str, Any]:
    """Get available course import sources"""
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


@router.post("/import/preview")
@handle_api_errors(operation_name="preview course import")
async def preview_course_import(request: schemas.CourseImportRequest) -> Dict[str, Any]:
    """Preview course data before importing"""
    return {
        "course_name": request.course_name,
        "preview_data": {
            "holes": 18,
            "par": 72,
            "rating": 72.5,
            "slope": 135,
            "sample_holes": [
                {"hole": 1, "par": 4, "yards": 400, "handicap": 7},
                {"hole": 2, "par": 3, "yards": 175, "handicap": 15}
            ]
        }
    }
