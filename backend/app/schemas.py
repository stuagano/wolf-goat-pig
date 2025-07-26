from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime

class Rule(BaseModel):
    id: int
    title: str
    description: str

    class Config:
        from_attributes = True

class HoleInfo(BaseModel):
    hole_number: int
    par: int
    yards: int
    handicap: int  # Stroke index (1-18)
    description: Optional[str] = None
    tee_box: str = "regular"

    @field_validator('par')
    @classmethod
    def validate_par(cls, v):
        if not 3 <= v <= 6:
            raise ValueError('Par must be between 3 and 6')
        return v

    @field_validator('handicap')
    @classmethod
    def validate_handicap(cls, v):
        if not 1 <= v <= 18:
            raise ValueError('Handicap must be between 1 and 18')
        return v

    @field_validator('yards')
    @classmethod
    def validate_yards(cls, v):
        if v < 100:
            raise ValueError('Yards must be at least 100')
        if v > 700:
            raise ValueError('Yards cannot exceed 700')
        return v

class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    holes: List[HoleInfo]

    @field_validator('holes')
    @classmethod
    def validate_holes(cls, v):
        if len(v) != 18:
            raise ValueError('Course must have exactly 18 holes')
        
        # Check for unique handicaps
        handicaps = [hole.handicap for hole in v]
        if len(set(handicaps)) != 18:
            raise ValueError('All handicaps must be unique (1-18)')
        
        # Check for unique hole numbers
        hole_numbers = [hole.hole_number for hole in v]
        if sorted(hole_numbers) != list(range(1, 19)):
            raise ValueError('Hole numbers must be 1-18 and unique')
        
        # Validate total par
        total_par = sum(hole.par for hole in v)
        if not 70 <= total_par <= 74:
            raise ValueError('Total par must be between 70 and 74')
        
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Course name must be at least 3 characters')
        return v.strip()

class CourseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    total_par: int
    total_yards: int
    course_rating: Optional[float]
    slope_rating: Optional[float]
    holes: List[HoleInfo]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    holes: Optional[List[HoleInfo]] = None

    @field_validator('holes')
    @classmethod
    def validate_holes_update(cls, v):
        if v is not None:
            # Same validation as CourseCreate
            if len(v) != 18:
                raise ValueError('Course must have exactly 18 holes')
            
            handicaps = [hole.handicap for hole in v]
            if len(set(handicaps)) != 18:
                raise ValueError('All handicaps must be unique (1-18)')
            
            hole_numbers = [hole.hole_number for hole in v]
            if sorted(hole_numbers) != list(range(1, 19)):
                raise ValueError('Hole numbers must be 1-18 and unique')
            
            total_par = sum(hole.par for hole in v)
            if not 70 <= total_par <= 74:
                raise ValueError('Total par must be between 70 and 74')
        
        return v

class CourseList(BaseModel):
    courses: List[CourseResponse]

class CourseStats(BaseModel):
    total_par: int
    total_yards: int
    par_3_count: int
    par_4_count: int
    par_5_count: int
    average_yards_per_hole: float
    longest_hole: HoleInfo
    shortest_hole: HoleInfo
    difficulty_rating: float

class CourseComparison(BaseModel):
    course1: CourseResponse
    course2: CourseResponse
    stats1: CourseStats
    stats2: CourseStats
    difficulty_difference: float
    yard_difference: int

class SimulationCourseData(BaseModel):
    course_name: str
    holes: List[HoleInfo]
    difficulty_factors: List[float]  # Per-hole difficulty multipliers
    distance_factors: List[float]    # Per-hole distance impact factors 