"""Shared router-test fixtures."""

import pytest

from app.database import SessionLocal
from app.main import app
from app.services.auth_service import get_current_user
from app.utils.admin_auth import require_admin

WING_POINT_NAME = "Wing Point Golf & Country Club"


def _override(dependency, value):
    previous = app.dependency_overrides.get(dependency)
    app.dependency_overrides[dependency] = lambda: value
    yield
    if previous is None:
        app.dependency_overrides.pop(dependency, None)
    else:
        app.dependency_overrides[dependency] = previous


@pytest.fixture
def as_admin():
    """Call admin-only routes as an admin."""
    yield from _override(require_admin, {"email": "admin@test.com"})


@pytest.fixture
def signed_in():
    """Call sign-in-required routes as a signed-in player."""
    yield from _override(get_current_user, object())


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
