from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

DEFAULT_COURSES = {
    "Wing Point": [
        {"hole_number": 1, "stroke_index": 5, "par": 5, "yards": 476, "description": "Par 5 opening hole. Long, straight, reachable in two for long hitters."},
        {"hole_number": 2, "stroke_index": 15, "par": 3, "yards": 175, "description": "Short par 3. Watch for wind and tricky green."},
        {"hole_number": 3, "stroke_index": 1, "par": 4, "yards": 401, "description": "Difficult par 4. Long and demanding with a tough approach."},
        {"hole_number": 4, "stroke_index": 17, "par": 3, "yards": 133, "description": "Shortest hole on the course. Precision required."},
        {"hole_number": 5, "stroke_index": 7, "par": 5, "yards": 498, "description": "Par 5 with risk/reward second shot. Birdie opportunity."},
        {"hole_number": 6, "stroke_index": 11, "par": 4, "yards": 351, "description": "Dogleg par 4. Position off the tee is key."},
        {"hole_number": 7, "stroke_index": 9, "par": 4, "yards": 316, "description": "Short par 4. Play for position, not distance."},
        {"hole_number": 8, "stroke_index": 13, "par": 4, "yards": 294, "description": "Drivable par 4 for long hitters. Risk/reward."},
        {"hole_number": 9, "stroke_index": 3, "par": 4, "yards": 340, "description": "Tough finishing hole on the front. Demanding approach."},
        {"hole_number": 10, "stroke_index": 16, "par": 3, "yards": 239, "description": "Long par 3. Club selection is crucial."},
        {"hole_number": 11, "stroke_index": 2, "par": 4, "yards": 401, "description": "Strong par 4. Demands accuracy off the tee."},
        {"hole_number": 12, "stroke_index": 14, "par": 3, "yards": 204, "description": "Mid-length par 3. Green is well protected."},
        {"hole_number": 13, "stroke_index": 8, "par": 4, "yards": 310, "description": "Short par 4. Good birdie chance."},
        {"hole_number": 14, "stroke_index": 10, "par": 4, "yards": 317, "description": "Dogleg par 4. Play to the corner for best angle."},
        {"hole_number": 15, "stroke_index": 18, "par": 4, "yards": 396, "description": "Easiest hole on the course. Play aggressively."},
        {"hole_number": 16, "stroke_index": 4, "par": 4, "yards": 358, "description": "Challenging par 4. Demanding approach shot."},
        {"hole_number": 17, "stroke_index": 12, "par": 5, "yards": 490, "description": "Par 5. Reachable in two for long hitters."},
        {"hole_number": 18, "stroke_index": 6, "par": 4, "yards": 394, "description": "Strong finishing hole. Demanding tee shot and approach."}
    ],
    "Championship Links": [
        {"hole_number": 1, "stroke_index": 7, "par": 4, "yards": 450, "description": "Opening hole with wide fairway but challenging approach to elevated green."},
        {"hole_number": 2, "stroke_index": 15, "par": 3, "yards": 185, "description": "Long par 3 with deep bunkers and wind factor."},
        {"hole_number": 3, "stroke_index": 1, "par": 5, "yards": 620, "description": "Monster par 5 requiring three solid shots. Water hazard on the right."},
        {"hole_number": 4, "stroke_index": 3, "par": 4, "yards": 485, "description": "Long par 4 with narrow fairway and difficult green complex."},
        {"hole_number": 5, "stroke_index": 11, "par": 4, "yards": 420, "description": "Dogleg left with strategic bunkering. Position is key."},
        {"hole_number": 6, "stroke_index": 17, "par": 5, "yards": 580, "description": "Reachable par 5 with risk/reward second shot over water."},
        {"hole_number": 7, "stroke_index": 5, "par": 4, "yards": 465, "description": "Long par 4 with out of bounds left and water right."},
        {"hole_number": 8, "stroke_index": 13, "par": 3, "yards": 195, "description": "Elevated tee with wind factor. Green slopes severely."},
        {"hole_number": 9, "stroke_index": 9, "par": 4, "yards": 440, "description": "Finishing hole with water hazard and dramatic green setting."},
        {"hole_number": 10, "stroke_index": 2, "par": 4, "yards": 470, "description": "Challenging par 4 with narrow landing area and difficult approach."},
        {"hole_number": 11, "stroke_index": 16, "par": 5, "yards": 600, "description": "Long par 5 requiring three solid shots. Strategic layup area."},
        {"hole_number": 12, "stroke_index": 14, "par": 3, "yards": 175, "description": "Short par 3 with island green. Wind and pressure factor."},
        {"hole_number": 13, "stroke_index": 18, "par": 4, "yards": 400, "description": "Short par 4, drivable for long hitters. Risk/reward hole."},
        {"hole_number": 14, "stroke_index": 4, "par": 4, "yards": 480, "description": "Long par 4 with narrow fairway and challenging green."},
        {"hole_number": 15, "stroke_index": 12, "par": 5, "yards": 590, "description": "Three-shot par 5 with water hazard crossing the fairway."},
        {"hole_number": 16, "stroke_index": 8, "par": 4, "yards": 460, "description": "Dogleg right with water hazard. Demanding tee shot and approach."},
        {"hole_number": 17, "stroke_index": 10, "par": 3, "yards": 165, "description": "Short par 3 with deep bunkers and wind factor."},
        {"hole_number": 18, "stroke_index": 6, "par": 4, "yards": 655, "description": "Epic finishing hole with water hazard and dramatic green setting."}
    ],
    "Executive Course": [
        {"hole_number": 1, "stroke_index": 9, "par": 4, "yards": 320, "description": "Short opening hole with wide fairway. Good for building confidence."},
        {"hole_number": 2, "stroke_index": 17, "par": 3, "yards": 140, "description": "Short par 3 with large green. Good for practicing irons."},
        {"hole_number": 3, "stroke_index": 5, "par": 4, "yards": 350, "description": "Straightaway par 4 with minimal hazards. Fairway is generous."},
        {"hole_number": 4, "stroke_index": 15, "par": 4, "yards": 155, "description": "Elevated tee with wind factor. Green slopes from back to front."},
        {"hole_number": 5, "stroke_index": 3, "par": 4, "yards": 365, "description": "Slight dogleg with bunkers protecting the green."},
        {"hole_number": 6, "stroke_index": 11, "par": 5, "yards": 480, "description": "Short par 5 reachable in two. Good for practicing long approach shots."},
        {"hole_number": 7, "stroke_index": 7, "par": 4, "yards": 340, "description": "Straight par 4 with water hazard on the right."},
        {"hole_number": 8, "stroke_index": 13, "par": 3, "yards": 150, "description": "Short par 3 with bunkers around the green."},
        {"hole_number": 9, "stroke_index": 1, "par": 4, "yards": 355, "description": "Finishing hole with elevated green. Approach shot requires extra club."},
        {"hole_number": 10, "stroke_index": 8, "par": 4, "yards": 330, "description": "Short par 4 with wide fairway. Good scoring opportunity."},
        {"hole_number": 11, "stroke_index": 16, "par": 4, "yards": 145, "description": "Short par 4 with large green. Wind can be a factor."},
        {"hole_number": 12, "stroke_index": 4, "par": 4, "yards": 360, "description": "Straightaway par 4 with bunkers protecting the green."},
        {"hole_number": 13, "stroke_index": 14, "par": 4, "yards": 160, "description": "Elevated tee with wind factor. Green slopes from back to front."},
        {"hole_number": 14, "stroke_index": 2, "par": 4, "yards": 375, "description": "Longest par 4 on the course. Requires solid tee shot and approach."},
        {"hole_number": 15, "stroke_index": 12, "par": 5, "yards": 490, "description": "Short par 5 reachable in two. Water hazard on the right."},
        {"hole_number": 16, "stroke_index": 6, "par": 4, "yards": 345, "description": "Dogleg left with strategic bunkering. Position is key."},
        {"hole_number": 17, "stroke_index": 18, "par": 4, "yards": 135, "description": "Shortest hole on the course. Good for practicing short irons."},
        {"hole_number": 18, "stroke_index": 10, "par": 4, "yards": 350, "description": "Finishing hole with water hazard and dramatic green setting."}
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