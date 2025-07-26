from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

# Default course data to avoid circular imports
DEFAULT_COURSES = {
    "Wing Point Golf & Country Club": [
        {"hole_number": 1, "par": 4, "yards": 420, "stroke_index": 5},
        {"hole_number": 2, "par": 4, "yards": 385, "stroke_index": 13},
        {"hole_number": 3, "par": 5, "yards": 580, "stroke_index": 1},
        {"hole_number": 4, "par": 3, "yards": 165, "stroke_index": 17},
        {"hole_number": 5, "par": 4, "yards": 445, "stroke_index": 7},
        {"hole_number": 6, "par": 4, "yards": 395, "stroke_index": 11},
        {"hole_number": 7, "par": 5, "yards": 520, "stroke_index": 15},
        {"hole_number": 8, "par": 3, "yards": 185, "stroke_index": 3},
        {"hole_number": 9, "par": 4, "yards": 410, "stroke_index": 9},
        {"hole_number": 10, "par": 4, "yards": 455, "stroke_index": 2},
        {"hole_number": 11, "par": 5, "yards": 545, "stroke_index": 16},
        {"hole_number": 12, "par": 3, "yards": 175, "stroke_index": 18},
        {"hole_number": 13, "par": 4, "yards": 435, "stroke_index": 4},
        {"hole_number": 14, "par": 4, "yards": 415, "stroke_index": 8},
        {"hole_number": 15, "par": 3, "yards": 155, "stroke_index": 14},
        {"hole_number": 16, "par": 4, "yards": 425, "stroke_index": 6},
        {"hole_number": 17, "par": 5, "yards": 535, "stroke_index": 12},
        {"hole_number": 18, "par": 4, "yards": 350, "stroke_index": 10}
    ]
}

@dataclass
class CourseManager:
    selected_course: Optional[str] = None
    hole_stroke_indexes: List[int] = field(default_factory=list)
    hole_pars: List[int] = field(default_factory=list)
    hole_yards: List[int] = field(default_factory=list)
    course_data: Dict[str, Any] = field(default_factory=lambda: DEFAULT_COURSES.copy())

    def load_course(self, course_name: str):
        course = self.course_data.get(course_name)
        if not course:
            raise ValueError(f"Course '{course_name}' not found.")
        self.selected_course = course_name
        self.hole_stroke_indexes = [h["stroke_index"] for h in course]
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

    def get_courses(self) -> Dict[str, Any]:
        return self.course_data

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
            # Higher difficulty for longer holes and harder stroke indexes
            yard_factor = hole["yards"] / (hole["par"] * 100)  # Normalize by par
            stroke_factor = (19 - hole["stroke_index"]) / 18  # Lower stroke index = harder
            difficulty_score += yard_factor * stroke_factor
        
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
        
        # Combine stroke index difficulty with distance
        stroke_index = course[hole_idx]["stroke_index"]
        stroke_difficulty = (19 - stroke_index) / 18  # 0-1, higher = more difficult
        
        par = course[hole_idx]["par"]
        yards = course[hole_idx]["yards"]
        # Normalize yards by par (longer than expected = harder)
        expected_yards = {3: 150, 4: 400, 5: 550}
        yard_difficulty = min(1.5, yards / expected_yards.get(par, 400))
        
        # Combine factors
        return 0.7 * stroke_difficulty + 0.3 * (yard_difficulty - 0.5)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_course": self.selected_course,
            "hole_stroke_indexes": self.hole_stroke_indexes,
            "hole_pars": self.hole_pars,
            "hole_yards": self.hole_yards,
            "course_data": self.course_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CourseManager':
        obj = cls()
        obj.selected_course = data.get("selected_course")
        obj.hole_stroke_indexes = data.get("hole_stroke_indexes", [])
        obj.hole_pars = data.get("hole_pars", [])
        obj.hole_yards = data.get("hole_yards", [])
        obj.course_data = data.get("course_data", DEFAULT_COURSES.copy())
        return obj 