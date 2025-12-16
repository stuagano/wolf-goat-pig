import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initialize test database tables before running tests."""
    # Import all models to register them with SQLAlchemy
    from app import models  # noqa: F401
    from app.database import Base, engine

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Seed essential data like courses
    try:
        from app.seed_courses import seed_courses
        seed_courses()
    except Exception:
        pass  # Ignore if already seeded or any issues

    yield

    # Cleanup after all tests (optional - drop tables)
    # Base.metadata.drop_all(bind=engine)
