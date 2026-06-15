from pydantic import BaseModel, ConfigDict, field_validator


class HoleInfo(BaseModel):
    hole_number: int
    par: int
    yards: int
    handicap: int  # Stroke index (1-18)
    description: str | None = None
    tee_box: str = "regular"

    @field_validator("par")
    @classmethod
    def validate_par(cls, v):
        if not 3 <= v <= 6:
            raise ValueError("Par must be between 3 and 6")
        return v

    @field_validator("handicap")
    @classmethod
    def validate_handicap(cls, v):
        if not 1 <= v <= 18:
            raise ValueError("Handicap must be between 1 and 18")
        return v

    @field_validator("yards")
    @classmethod
    def validate_yards(cls, v):
        if v < 100:
            raise ValueError("Yards must be at least 100")
        if v > 700:
            raise ValueError("Yards cannot exceed 700")
        return v


class CourseCreate(BaseModel):
    name: str
    description: str | None = None
    holes: list[HoleInfo]

    @field_validator("holes")
    @classmethod
    def validate_holes(cls, v):
        if len(v) != 18:
            raise ValueError("Course must have exactly 18 holes")

        # Check for unique handicaps
        handicaps = [hole.handicap for hole in v]
        if len(set(handicaps)) != 18:
            raise ValueError("All handicaps must be unique (1-18)")

        # Check for unique hole numbers
        hole_numbers = [hole.hole_number for hole in v]
        if sorted(hole_numbers) != list(range(1, 19)):
            raise ValueError("Hole numbers must be 1-18 and unique")

        # Validate total par
        total_par = sum(hole.par for hole in v)
        if not 70 <= total_par <= 74:
            raise ValueError("Total par must be between 70 and 74")

        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError("Course name must be at least 3 characters")
        return v.strip()


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    total_par: int
    total_yards: int
    course_rating: float | None
    slope_rating: float | None
    holes: list[HoleInfo]
    created_at: str
    updated_at: str


class CourseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    holes: list[HoleInfo] | None = None

    @field_validator("holes")
    @classmethod
    def validate_holes_update(cls, v):
        # An update may be a PARTIAL subset of holes (the router merges them and
        # preserves the rest), so we validate only what a partial payload can see:
        # at least one hole, no more than 18, with in-range, unique hole numbers.
        # The full-course invariants (exactly 18 holes, all handicaps unique 1-18,
        # total par 70-74) belong to CourseCreate, which sees the whole course.
        if v is not None:
            if not v:
                raise ValueError("holes update must include at least one hole")
            if len(v) > 18:
                raise ValueError("Course cannot have more than 18 holes")

            hole_numbers = [hole.hole_number for hole in v]
            if not all(1 <= n <= 18 for n in hole_numbers):
                raise ValueError("Hole numbers must be between 1 and 18")
            if len(set(hole_numbers)) != len(hole_numbers):
                raise ValueError("Hole numbers must be unique")

        return v


class CourseList(BaseModel):
    courses: list[CourseResponse]


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


class CourseImportRequest(BaseModel):
    course_name: str
    state: str | None = None
    city: str | None = None
