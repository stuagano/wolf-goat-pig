"""
Courses Router

Course management and import functionality, including course CRUD operations,
course import from external sources, and course preview functionality.
"""

from fastapi import APIRouter, HTTPException, Path, UploadFile, File
from typing import Dict, List, Any
from datetime import datetime
import logging
import json
import traceback

from ..database import SessionLocal
from ..state.course_manager import CourseManager
from ..course_import import import_course_by_name, import_course_from_json
from .. import schemas, models

logger = logging.getLogger("app.routers.courses")

router = APIRouter(
    prefix="/courses",
    tags=["courses"]
)

# Initialize course manager
course_manager = CourseManager()


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
            "description": "Classic parkland course on Bainbridge Island, WA (Est. 1903)",
            "holes": [
                {"hole_number": 1, "par": 5, "yards": 476, "stroke_index": 5, "description": "Opening Drive - gentle starting hole, slight dogleg right"},
                {"hole_number": 2, "par": 3, "yards": 175, "stroke_index": 13, "description": "Short Iron - downhill par 3 with bunkers"},
                {"hole_number": 3, "par": 4, "yards": 401, "stroke_index": 1, "description": "The Challenge - handicap 1, tough dogleg left"},
                {"hole_number": 4, "par": 3, "yards": 133, "stroke_index": 17, "description": "Precision - short but tricky par 3"},
                {"hole_number": 5, "par": 5, "yards": 498, "stroke_index": 7, "description": "The Long One - reachable par 5"},
                {"hole_number": 6, "par": 4, "yards": 351, "stroke_index": 11, "description": "Mid Iron - strategic placement required"},
                {"hole_number": 7, "par": 4, "yards": 316, "stroke_index": 15, "description": "Risk Reward - short par 4"},
                {"hole_number": 8, "par": 4, "yards": 294, "stroke_index": 3, "description": "The Turn - another short par 4"},
                {"hole_number": 9, "par": 4, "yards": 340, "stroke_index": 9, "description": "Home Bound - tough finishing hole for front nine"},
                {"hole_number": 10, "par": 3, "yards": 239, "stroke_index": 2, "description": "Back Nine Starter - long par 3"},
                {"hole_number": 11, "par": 4, "yards": 401, "stroke_index": 16, "description": "The Beast - second toughest hole"},
                {"hole_number": 12, "par": 3, "yards": 204, "stroke_index": 8, "description": "Over Water - beautiful par 3"},
                {"hole_number": 13, "par": 4, "yards": 310, "stroke_index": 14, "description": "Breathing Room - easiest hole"},
                {"hole_number": 14, "par": 4, "yards": 317, "stroke_index": 4, "description": "Deceptive - looks easy but plays tough"},
                {"hole_number": 15, "par": 4, "yards": 396, "stroke_index": 18, "description": "The Stretch - start of tough finish"},
                {"hole_number": 16, "par": 4, "yards": 358, "stroke_index": 10, "description": "Penultimate - tough as you near finish"},
                {"hole_number": 17, "par": 5, "yards": 490, "stroke_index": 12, "description": "The Penultimate - par 5 start of Hoepfinger"},
                {"hole_number": 18, "par": 4, "yards": 394, "stroke_index": 6, "description": "The Finale - strong finishing par 4"}
            ],
            "total_par": 71,
            "total_yards": 6093,
            "hole_count": 18
        }
    }


# Course Management Endpoints

@router.get("")
def get_courses():
    """Get all available courses with robust fallback handling"""
    try:
        courses = course_manager.get_courses()

        # Ensure we always return at least one default course
        if not courses:
            logger.warning("No courses found in game state, attempting to reload from database")

            # Try to reload from database
            try:
                from ..seed_data import get_seeding_status
                seeding_status = get_seeding_status()

                if seeding_status["status"] == "success":
                    # Reinitialize course manager
                    course_manager.__init__()
                    courses = course_manager.get_courses()

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


@router.get("/{course_id}")
def get_course_by_id(course_id: int):
    """Get a specific course by ID (index in courses list)"""
    try:
        courses = course_manager.get_courses()
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


@router.post("", response_model=dict)
def add_course(course: schemas.CourseCreate):
    """Add a new course - persists to database with Hole records"""
    db = SessionLocal()
    try:
        course_dict = course.dict()

        # Check if course already exists
        existing_course = db.query(models.Course).filter(models.Course.name == course.name).first()
        if existing_course:
            raise HTTPException(status_code=400, detail=f"Course '{course.name}' already exists")

        # Calculate course statistics
        holes = course_dict.get("holes", [])
        total_par = sum(h.get("par", 0) for h in holes)
        total_yards = sum(h.get("yards", 0) for h in holes)

        # Create database record
        now = datetime.utcnow().isoformat()
        db_course = models.Course(
            name=course.name,
            description=course_dict.get("description", ""),
            total_par=total_par,
            total_yards=total_yards,
            holes_data=holes,  # Keep for backward compatibility
            created_at=now,
            updated_at=now
        )

        db.add(db_course)
        db.flush()  # Flush to get the course ID

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

        # Also add to in-memory course manager for current session
        course_manager.add_course(course.name, holes)

        logger.info(f"Created course '{course.name}' with {len(holes)} holes in database (ID: {db_course.id})")

        return {
            "status": "success",
            "message": f"Course '{course.name}' added successfully",
            "data": {
                "id": db_course.id,
                "name": db_course.name,
                "total_par": total_par,
                "total_yards": total_yards,
                "hole_count": len(holes)
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add course: {str(e)}")
    finally:
        db.close()


@router.put("/{course_name}")
def update_course(course_name: str, course_update: schemas.CourseUpdate):
    """Update an existing course - persists to database and updates Hole records"""
    db = SessionLocal()
    try:
        # Find the course in database
        db_course = db.query(models.Course).filter(models.Course.name == course_name).first()
        if not db_course:
            raise HTTPException(status_code=404, detail=f"Course '{course_name}' not found")

        # Get update data
        update_dict = course_update.dict(exclude_unset=True)

        # Update fields
        if "name" in update_dict:
            db_course.name = update_dict["name"]
        if "description" in update_dict:
            db_course.description = update_dict["description"]
        if "holes" in update_dict:
            holes = update_dict["holes"]
            db_course.holes_data = holes  # Keep for backward compatibility
            # Recalculate statistics
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

        db_course.updated_at = datetime.utcnow().isoformat()

        db.commit()
        db.refresh(db_course)

        # Update in-memory course manager
        if "holes" in update_dict:
            course_manager.update_course(course_name, update_dict["holes"])

        logger.info(f"Updated course '{course_name}' and its holes in database (ID: {db_course.id})")

        return {
            "status": "success",
            "message": f"Course '{course_name}' updated successfully",
            "data": {
                "id": db_course.id,
                "name": db_course.name,
                "total_par": db_course.total_par,
                "total_yards": db_course.total_yards
            }
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update course: {str(e)}")
    finally:
        db.close()


@router.delete("/{course_name}")
def delete_course(course_name: str = Path(...)):
    """Delete a course - removes from database"""
    db = SessionLocal()
    try:
        # Find the course in database
        db_course = db.query(models.Course).filter(models.Course.name == course_name).first()
        if not db_course:
            raise HTTPException(status_code=404, detail=f"Course '{course_name}' not found")

        # Delete from database
        db.delete(db_course)
        db.commit()

        # Also remove from in-memory course manager
        course_manager.delete_course(course_name)

        logger.info(f"Deleted course '{course_name}' from database")

        return {
            "status": "success",
            "message": f"Course '{course_name}' deleted successfully"
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete course: {str(e)}")
    finally:
        db.close()


# Course Import Endpoints

@router.post("/import/search")
async def import_course_by_search(request: schemas.CourseImportRequest):
    """Search and import a course by name"""
    try:
        result = await import_course_by_name(request.course_name, request.state, request.city)
        return result
    except Exception as e:
        logger.error(f"Error importing course by search: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import course: {str(e)}")


@router.post("/import/file")
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


@router.get("/import/sources")
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


@router.post("/import/preview")
async def preview_course_import(request: schemas.CourseImportRequest):
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
