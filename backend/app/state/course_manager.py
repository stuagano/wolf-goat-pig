import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from ..database import SessionLocal
from ..models import Course, Hole

logger = logging.getLogger(__name__)

@dataclass
class CourseManager:
    """Manages golf course data by interacting directly with the database."""

    selected_course_name: Optional[str] = None
    selected_course_id: Optional[int] = None

    # In-memory cache for the currently selected course
    _course_cache: Dict[int, Course] = field(default_factory=dict)

    def load_course(self, course_name: str) -> bool:
        """Loads a course from the database and caches it."""
        db: Session = SessionLocal()
        try:
            course = db.query(Course).options(joinedload(Course.holes)).filter(Course.name == course_name).first()
            if course:
                course_id = int(course.id)
                self._course_cache[course_id] = course
                self.selected_course_name = str(course.name)
                self.selected_course_id = int(course.id)
                logger.info(f"Successfully loaded and cached course: {course_name}")
                return True
            logger.warning(f"Course '{course_name}' not found in the database.")
            return False
        finally:
            db.close()

    def get_selected_course(self) -> Optional[Course]:
        """Returns the currently selected course from the cache."""
        if self.selected_course_id is None:
            return None
        return self._course_cache.get(self.selected_course_id)

    def refresh_course(self, course_id: int) -> bool:
        """Reloads a course from the database to refresh the cache."""
        db: Session = SessionLocal()
        try:
            course = db.query(Course).options(joinedload(Course.holes)).get(course_id)
            if course:
                cached_course_id = int(course.id)
                self._course_cache[cached_course_id] = course
                logger.info(f"Refreshed course '{course.name}' from database.")
                return True
            return False
        finally:
            db.close()

    def get_courses(self) -> Dict[str, Dict[str, Any]]:
        """Returns a dict of all courses from the database, keyed by course name."""
        db: Session = SessionLocal()
        try:
            courses = db.query(Course).all()
            return {
                c.name: {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "total_par": c.total_par,
                    "total_yards": c.total_yards,
                    "rating": c.course_rating,
                    "slope": c.slope_rating,
                }
                for c in courses
            }
        finally:
            db.close()

    def get_course_details(self, course_name: str) -> Optional[Dict[str, Any]]:
        """Returns detailed information for a specific course, including all holes."""
        db: Session = SessionLocal()
        try:
            course = db.query(Course).options(joinedload(Course.holes)).filter(Course.name == course_name).first()
            if not course:
                return None

            return {
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "total_par": course.total_par,
                "total_yards": course.total_yards,
                "rating": course.course_rating,
                "slope": course.slope_rating,
                "holes": [
                    {
                        "hole_number": h.hole_number,
                        "par": h.par,
                        "yards": h.yards,
                        "handicap": h.handicap,
                        "description": h.description,
                    }
                    for h in sorted(course.holes, key=lambda x: x.hole_number)
                ],
            }
        finally:
            db.close()

    def create_course(self, course_data: Dict[str, Any]) -> Course:
        """Creates a new course and its holes in the database."""
        db: Session = SessionLocal()
        try:
            new_course = Course(
                name=course_data['name'],
                description=course_data.get('description'),
                total_par=course_data['total_par'],
                total_yards=course_data['total_yards'],
                course_rating=course_data.get('course_rating'),
                slope_rating=course_data.get('slope_rating'),
            )
            db.add(new_course)
            db.flush()  # To get the new_course.id

            holes_data = course_data.get('holes_data', [])
            for hole_data in holes_data:
                # Map stroke_index to handicap if present (different naming conventions)
                mapped_hole_data = hole_data.copy()
                if 'stroke_index' in mapped_hole_data:
                    mapped_hole_data['handicap'] = mapped_hole_data.pop('stroke_index')
                new_hole = Hole(
                    course_id=new_course.id,
                    **mapped_hole_data
                )
                db.add(new_hole)

            db.commit()
            db.refresh(new_course)
            logger.info(f"Created new course: {new_course.name}")
            return new_course
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating course: {e}")
            raise
        finally:
            db.close()

    def get_hole_pars(self) -> List[int]:
        """Gets the pars for the currently selected course."""
        course = self.get_selected_course()
        if not course:
            return []
        return [h.par for h in sorted(course.holes, key=lambda x: x.hole_number)]

    def get_hole_handicaps(self) -> List[int]:
        """Gets the handicaps for the currently selected course."""
        course = self.get_selected_course()
        if not course:
            return []
        return [h.handicap for h in sorted(course.holes, key=lambda x: x.hole_number)]

# Singleton instance of the CourseManager
_course_manager_instance = None

def get_course_manager() -> CourseManager:
    """Provides a singleton instance of the CourseManager."""
    global _course_manager_instance
    if _course_manager_instance is None:
        _course_manager_instance = CourseManager()
        # Load a default course on first initialization
        courses = _course_manager_instance.get_courses()
        if courses:
            first_course_name = next(iter(courses.keys()))
            _course_manager_instance.load_course(first_course_name)
    return _course_manager_instance
