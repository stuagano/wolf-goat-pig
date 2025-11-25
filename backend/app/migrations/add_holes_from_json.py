"""
Migration script to populate Hole table from existing holes_data JSON in courses.

This script reads the holes_data JSON field from existing Course records
and creates individual Hole records for each hole.
"""

import logging

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Course, Hole

logger = logging.getLogger(__name__)


def migrate_holes_from_json(db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Migrate hole data from JSON to individual Hole records.

    This function:
    1. Reads all courses from the database
    2. For each course, checks if Hole records already exist
    3. If not, creates Hole records from the holes_data JSON field

    Args:
        db: Database session (optional, will create one if not provided)
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        courses = db.query(Course).all()
        logger.info(f"Found {len(courses)} courses to process")

        courses_migrated = 0
        holes_created = 0

        for course in courses:
            # Check if this course already has Hole records
            existing_holes = db.query(Hole).filter(Hole.course_id == course.id).count()

            if existing_holes > 0:
                logger.info(f"Course '{course.name}' already has {existing_holes} holes, skipping")
                continue

            # Get holes data from JSON
            holes_data = course.holes_data
            if not holes_data:
                logger.warning(f"Course '{course.name}' has no holes_data, skipping")
                continue

            # Create Hole records
            for hole_data in holes_data:
                hole = Hole(
                    course_id=course.id,
                    hole_number=hole_data.get("hole_number"),
                    par=hole_data.get("par"),
                    yards=hole_data.get("yards"),
                    handicap=hole_data.get("handicap"),
                    description=hole_data.get("description"),
                    tee_box=hole_data.get("tee_box", "regular")
                )
                db.add(hole)
                holes_created += 1

            courses_migrated += 1
            logger.info(f"Migrated {len(holes_data)} holes for course '{course.name}'")

        db.commit()
        logger.info(f"Migration complete: {courses_migrated} courses, {holes_created} holes created")

        return {
            "status": "success",
            "courses_migrated": courses_migrated,
            "holes_created": holes_created
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Migration failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = migrate_holes_from_json()
    print(f"Migration result: {result}")
