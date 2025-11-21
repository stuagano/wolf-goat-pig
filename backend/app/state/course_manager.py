from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

try:
    from data.wing_point_course_data import WING_POINT_COURSE_DATA
except ImportError:
    WING_POINT_COURSE_DATA = None

# Convert Wing Point data to the expected format
def get_wing_point_holes():
    if WING_POINT_COURSE_DATA:
        return [
            {
                "hole_number": h["hole_number"],
                "handicap": h["handicap_men"],
                "par": h["par"],
                "yards": h["yards"]["white"],  # Use white tees as default
                "description": h["description"]
            }
            for h in WING_POINT_COURSE_DATA["holes"]
        ]
    else:
        # Fallback to basic data if import fails
        return [
            {"hole_number": i, "handicap": i, "par": 4, "yards": 400,
             "description": f"Hole {i}"} for i in range(1, 19)
        ]

# Default courses dictionary
DEFAULT_COURSES = {
    "Wing Point Golf & Country Club": get_wing_point_holes(),
    "Championship Links": [
        {"hole_number": 1, "handicap": 7, "par": 4, "yards": 450, "description": "Opening hole with wide fairway but challenging approach to elevated green."},
        {"hole_number": 2, "handicap": 15, "par": 3, "yards": 185, "description": "Long par 3 with deep bunkers and wind factor."},
        {"hole_number": 3, "handicap": 1, "par": 5, "yards": 620, "description": "Monster par 5 requiring three solid shots. Water hazard on the right."},
        {"hole_number": 4, "handicap": 3, "par": 4, "yards": 485, "description": "Long par 4 with narrow fairway and difficult green complex."},
        {"hole_number": 5, "handicap": 11, "par": 4, "yards": 420, "description": "Dogleg left with strategic bunkering. Position is key."},
        {"hole_number": 6, "handicap": 17, "par": 5, "yards": 580, "description": "Reachable par 5 with risk/reward second shot over water."},
        {"hole_number": 7, "handicap": 5, "par": 4, "yards": 465, "description": "Long par 4 with out of bounds left and water right."},
        {"hole_number": 8, "handicap": 13, "par": 3, "yards": 195, "description": "Elevated tee with wind factor. Green slopes severely."},
        {"hole_number": 9, "handicap": 9, "par": 4, "yards": 440, "description": "Finishing hole with water hazard and dramatic green setting."},
        {"hole_number": 10, "handicap": 2, "par": 4, "yards": 470, "description": "Challenging par 4 with narrow landing area and difficult approach."},
        {"hole_number": 11, "handicap": 16, "par": 5, "yards": 600, "description": "Long par 5 requiring three solid shots. Strategic layup area."},
        {"hole_number": 12, "handicap": 14, "par": 3, "yards": 175, "description": "Short par 3 with island green. Wind and pressure factor."},
        {"hole_number": 13, "handicap": 18, "par": 4, "yards": 400, "description": "Short par 4, drivable for long hitters. Risk/reward hole."},
        {"hole_number": 14, "handicap": 4, "par": 4, "yards": 480, "description": "Long par 4 with narrow fairway and challenging green."},
        {"hole_number": 15, "handicap": 12, "par": 5, "yards": 590, "description": "Three-shot par 5 with water hazard crossing the fairway."},
        {"hole_number": 16, "handicap": 8, "par": 4, "yards": 460, "description": "Dogleg right with water hazard. Demanding tee shot and approach."},
        {"hole_number": 17, "handicap": 10, "par": 3, "yards": 165, "description": "Short par 3 with deep bunkers and wind factor."},
        {"hole_number": 18, "handicap": 6, "par": 4, "yards": 655, "description": "Epic finishing hole with water hazard and dramatic green setting."}
    ],
    "Executive Course": [
        {"hole_number": 1, "handicap": 9, "par": 4, "yards": 320, "description": "Short opening hole with wide fairway. Good for building confidence."},
        {"hole_number": 2, "handicap": 17, "par": 3, "yards": 140, "description": "Short par 3 with large green. Good for practicing irons."},
        {"hole_number": 3, "handicap": 5, "par": 4, "yards": 350, "description": "Straightaway par 4 with minimal hazards. Fairway is generous."},
        {"hole_number": 4, "handicap": 15, "par": 4, "yards": 155, "description": "Elevated tee with wind factor. Green slopes from back to front."},
        {"hole_number": 5, "handicap": 3, "par": 4, "yards": 365, "description": "Slight dogleg with bunkers protecting the green."},
        {"hole_number": 6, "handicap": 11, "par": 5, "yards": 480, "description": "Short par 5 reachable in two. Good for practicing long approach shots."},
        {"hole_number": 7, "handicap": 7, "par": 4, "yards": 340, "description": "Straight par 4 with water hazard on the right."},
        {"hole_number": 8, "handicap": 13, "par": 3, "yards": 150, "description": "Short par 3 with bunkers around the green."},
        {"hole_number": 9, "handicap": 1, "par": 4, "yards": 355, "description": "Finishing hole with elevated green. Approach shot requires extra club."},
        {"hole_number": 10, "handicap": 8, "par": 4, "yards": 330, "description": "Short par 4 with wide fairway. Good scoring opportunity."},
        {"hole_number": 11, "handicap": 16, "par": 4, "yards": 145, "description": "Short par 4 with large green. Wind can be a factor."},
        {"hole_number": 12, "handicap": 4, "par": 4, "yards": 360, "description": "Straightaway par 4 with bunkers protecting the green."},
        {"hole_number": 13, "handicap": 14, "par": 4, "yards": 160, "description": "Elevated tee with wind factor. Green slopes from back to front."},
        {"hole_number": 14, "handicap": 2, "par": 4, "yards": 375, "description": "Longest par 4 on the course. Requires solid tee shot and approach."},
        {"hole_number": 15, "handicap": 12, "par": 5, "yards": 490, "description": "Short par 5 reachable in two. Water hazard on the right."},
        {"hole_number": 16, "handicap": 6, "par": 4, "yards": 345, "description": "Dogleg left with strategic bunkering. Position is key."},
        {"hole_number": 17, "handicap": 18, "par": 4, "yards": 135, "description": "Shortest hole on the course. Good for practicing short irons."},
        {"hole_number": 18, "handicap": 10, "par": 4, "yards": 350, "description": "Finishing hole with water hazard and dramatic green setting."}
    ]
}

@dataclass
class CourseManager:
    selected_course: Optional[str] = None
    hole_handicaps: List[int] = field(default_factory=list)
    hole_pars: List[int] = field(default_factory=list)
    hole_yards: List[int] = field(default_factory=list)
    course_data: Dict[str, Any] = field(default_factory=lambda: DEFAULT_COURSES.copy())

    def __post_init__(self):
        """Load courses from database, fallback to default courses if needed"""
        self.load_courses_from_database()
        self.ensure_default_courses()
    
    def load_courses_from_database(self):
        """Load courses from database on initialization"""
        try:
            # Avoid circular import by importing here
            from ..database import SessionLocal
            from ..models import Course

            db = SessionLocal()
            try:
                # Query all courses from database
                db_courses = db.query(Course).all()

                if db_courses:
                    logger.info(f"Loading {len(db_courses)} courses from database")
                    self.course_data = {}

                    for db_course in db_courses:
                        # Convert database Course model to in-memory format
                        self.course_data[db_course.name] = db_course.holes_data

                    logger.info(f"Loaded courses: {list(self.course_data.keys())}")
                else:
                    logger.warning("No courses found in database, will use defaults")

            except Exception as db_error:
                logger.error(f"Error loading courses from database: {db_error}")
                logger.info("Will fall back to default courses")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to connect to database for course loading: {e}")
            logger.info("Will use default courses")

    def ensure_default_courses(self):
        """Ensure at least one default course is available, adding if necessary"""
        # Check if we have any valid courses
        has_valid_courses = False
        if self.course_data:
            for course_name, holes in self.course_data.items():
                if isinstance(holes, list) and len(holes) == 18:
                    # Quick check for valid course structure
                    if all(isinstance(hole, dict) and "hole_number" in hole for hole in holes[:3]):
                        has_valid_courses = True
                        break

        if not has_valid_courses:
            # Replace with default courses or create fallback
            if DEFAULT_COURSES:
                self.course_data = DEFAULT_COURSES.copy()
            else:
                self.course_data = {
                    "Fallback Course": [
                        {"hole_number": i, "par": 4, "yards": 400, "handicap": i,
                         "description": f"Fallback hole {i}"}
                        for i in range(1, 19)
                    ]
                }

        # Auto-select first course if none selected or selected course is invalid
        if not self.selected_course or self.selected_course not in self.course_data:
            if self.course_data:
                first_course = list(self.course_data.keys())[0]
                self.load_course(first_course)

    def load_course(self, course_name: str):
        course = self.course_data.get(course_name)
        if not course:
            raise ValueError(f"Course '{course_name}' not found.")
        self.selected_course = course_name
        self.hole_handicaps = [h["handicap"] for h in course]
        self.hole_pars = [h["par"] for h in course]
        self.hole_yards = [h["yards"] for h in course]

    def get_hole_info(self, hole_number: int) -> Dict[str, Any]:
        if not self.selected_course:
            raise ValueError("No course selected.")
        course = self.course_data[self.selected_course]
        if hole_number < 1 or hole_number > len(course):
            raise IndexError("Invalid hole number.")
        return course[hole_number - 1]

    def update_hole(self, hole_number: int, hole_info: Dict[str, Any]):
        if not self.selected_course:
            raise ValueError("No course selected.")
        course = self.course_data[self.selected_course]
        if hole_number < 1 or hole_number > len(course):
            raise IndexError("Invalid hole number.")
        course[hole_number - 1] = hole_info
        self.load_course(self.selected_course)  # Refresh attributes

    def get_courses(self) -> Dict[str, Dict[str, Any]]:
        """Return courses as a dictionary with course names as keys, matching frontend expectations"""
        result = {}
        for course_name, holes in self.course_data.items():
            try:
                # Validate that holes is a list of dictionaries
                if not isinstance(holes, list):
                    continue  # Skip invalid course data
                
                # Calculate course statistics for each course
                total_par = 0
                total_yards = 0
                
                for hole in holes:
                    if isinstance(hole, dict) and "par" in hole and "yards" in hole:
                        total_par += hole["par"]
                        total_yards += hole["yards"]
                
                result[course_name] = {
                    "name": course_name,
                    "holes": holes,
                    "total_par": total_par,
                    "total_yards": total_yards,
                    "hole_count": len(holes)
                }
            except (TypeError, KeyError, AttributeError):
                # Skip malformed course data
                continue
        
        # If no valid courses found, ensure we have fallback
        if not result:
            self.ensure_default_courses()
            # Try again with the new course data, but only once to avoid recursion
            for course_name, holes in self.course_data.items():
                try:
                    if isinstance(holes, list):
                        total_par = sum(hole.get("par", 0) for hole in holes if isinstance(hole, dict))
                        total_yards = sum(hole.get("yards", 0) for hole in holes if isinstance(hole, dict))
                        result[course_name] = {
                            "name": course_name,
                            "holes": holes,
                            "total_par": total_par,
                            "total_yards": total_yards,
                            "hole_count": len(holes)
                        }
                except (TypeError, KeyError, AttributeError):
                    continue
            
        return result

    def add_course(self, course_name: str, holes: List[Dict[str, Any]]):
        self.course_data[course_name] = holes

    def delete_course(self, course_name: str):
        if course_name in self.course_data:
            del self.course_data[course_name]
            if self.selected_course == course_name:
                self.selected_course = None
                if self.course_data:
                    self.load_course(next(iter(self.course_data)))

    def update_course(self, course_name: str, holes: List[Dict[str, Any]]):
        if course_name not in self.course_data:
            raise ValueError(f"Course '{course_name}' not found.")
        self.course_data[course_name] = holes
        if self.selected_course == course_name:
            self.load_course(course_name)

    def get_course_stats(self, course_name: str) -> Dict[str, Any]:
        course = self.course_data.get(course_name)
        if not course:
            raise ValueError(f"Course '{course_name}' not found.")
        
        total_par = sum(h["par"] for h in course)
        total_yards = sum(h["yards"] for h in course)
        
        par_counts = {3: 0, 4: 0, 5: 0, 6: 0}
        for hole in course:
            par_counts[hole["par"]] += 1
        
        longest_hole = max(course, key=lambda h: h["yards"])
        shortest_hole = min(course, key=lambda h: h["yards"])
        
        # Calculate difficulty rating based on yards and par
        difficulty_score = 0
        for hole in course:
            # Higher difficulty for longer holes and harder handicaps
            yard_factor = hole["yards"] / (hole["par"] * 100)  # Normalize by par
            handicap_factor = (19 - hole["handicap"]) / 18  # Lower handicap = harder
            difficulty_score += yard_factor * handicap_factor
        
        return {
            "total_par": total_par,
            "total_yards": total_yards,
            "par_3_count": par_counts[3],
            "par_4_count": par_counts[4], 
            "par_5_count": par_counts[5],
            "par_6_count": par_counts[6],
            "average_yards_per_hole": total_yards / 18,
            "longest_hole": longest_hole,
            "shortest_hole": shortest_hole,
            "difficulty_rating": round(difficulty_score, 2)
        }

    def get_current_hole_info(self, current_hole: int) -> Dict[str, Any]:
        if not self.selected_course:
            raise ValueError("No course selected.")
        course = self.course_data[self.selected_course]
        hole_idx = current_hole - 1
        if hole_idx < 0 or hole_idx >= len(course):
            raise IndexError("Invalid hole number.")
        
        hole_info = course[hole_idx].copy()
        hole_info["hole_number"] = current_hole
        hole_info["selected_course"] = self.selected_course
        return hole_info

    def get_hole_difficulty_factor(self, hole_number: int) -> float:
        if not self.selected_course:
            raise ValueError("No course selected.")
        course = self.course_data[self.selected_course]
        hole_idx = hole_number - 1
        if hole_idx < 0 or hole_idx >= len(course):
            return 1.0

        # Combine handicap difficulty with distance
        handicap = course[hole_idx]["handicap"]
        handicap_difficulty = (19 - handicap) / 18  # 0-1, higher = more difficult

        par = course[hole_idx]["par"]
        yards = course[hole_idx]["yards"]
        # Normalize yards by par (longer than expected = harder)
        expected_yards = {3: 150, 4: 400, 5: 550}
        yard_difficulty = min(1.5, yards / expected_yards.get(par, 400))

        # Combine factors
        return 0.7 * handicap_difficulty + 0.3 * (yard_difficulty - 0.5)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_course": self.selected_course,
            "hole_handicaps": self.hole_handicaps,
            "hole_pars": self.hole_pars,
            "hole_yards": self.hole_yards,
            "course_data": self.course_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CourseManager':
        obj = cls()
        obj.selected_course = data.get("selected_course")
        obj.hole_handicaps = data.get("hole_handicaps", [])
        obj.hole_pars = data.get("hole_pars", [])
        obj.hole_yards = data.get("hole_yards", [])
        obj.course_data = data.get("course_data", DEFAULT_COURSES.copy())
        # Ensure default courses are available after deserialization
        obj.ensure_default_courses()
        return obj 