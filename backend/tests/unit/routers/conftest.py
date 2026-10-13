"""Shared router-test fixtures."""

import pytest

from app.database import SessionLocal

WING_POINT_NAME = "Wing Point Golf & Country Club"


@pytest.fixture
def wing_point_blacks():
    """Pin the Wing Point row to the Black (men) tees: 71.1 / 130, par 71."""
    from app.models import Course

    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.name == WING_POINT_NAME).first()
        if course is None:
            pytest.skip("Wing Point course is not seeded in this database")
        saved = (course.course_rating, course.slope_rating)
        course.course_rating, course.slope_rating = 71.1, 130
        db.commit()
        assert sum(h.par for h in course.holes) == 71
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.name == WING_POINT_NAME).first()
        course.course_rating, course.slope_rating = saved
        db.commit()
    finally:
        db.close()
