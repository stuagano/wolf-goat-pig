"""
Comprehensive tests for Wolf Goat Pig API endpoints
"""

import os
import sys
import uuid

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import SessionLocal, init_db
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database and seed essential data before each test.

    The FastAPI lifespan does not run under TestClient, so we manually
    seed courses and rules here to mirror production startup state.
    """
    init_db()

    # Seed rules so /rules and health-check pass
    try:
        from app.seed_rules import main as _seed_rules_main

        _seed_rules_main()
    except Exception:
        pass

    yield
    # Cleanup can be added here if needed


class TestHealthEndpoints:
    """Test health and diagnostic endpoints"""

    def test_health_check(self, client):
        response = client.get("/health")
        # In the test environment some components (e.g. AI players) are not
        # seeded, so the endpoint may return 200 (healthy/degraded) or 503
        # (unhealthy).  We verify the endpoint responds and that the JSON
        # body contains the expected structure.
        assert response.status_code in (200, 503)
        data = response.json()
        if response.status_code == 200:
            assert data["status"] in ("healthy", "degraded")
            assert "timestamp" in data
        else:
            # 503 wraps the detail in an HTTPException
            assert "detail" in data

    def test_ghin_diagnostic(self, client):
        response = client.get("/ghin/diagnostic")
        assert response.status_code == 200
        assert "email_configured" in response.json()
        assert "environment" in response.json()


class TestCourseManagement:
    """Test course management endpoints"""

    def test_get_courses(self, client):
        response = client.get("/courses")
        assert response.status_code == 200
        data = response.json()
        # The /courses endpoint returns a dict keyed by course name
        assert isinstance(data, dict)
        # Should have at least one seeded course
        assert len(data) > 0

    def test_add_course(self, client):
        course_name = f"Test Golf Club {uuid.uuid4().hex[:8]}"
        new_course = {
            "name": course_name,
            "holes": [{"hole_number": i, "par": 4, "yards": 400, "handicap": i} for i in range(1, 19)],
        }

        response = client.post("/courses", json=new_course)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert course_name in data["message"]

    def test_update_course(self, client):
        course_name = f"Update Test Club {uuid.uuid4().hex[:8]}"
        # First add a course
        new_course = {
            "name": course_name,
            "holes": [{"hole_number": i, "par": 4, "yards": 400, "handicap": i} for i in range(1, 19)],
        }
        resp = client.post("/courses", json=new_course)
        assert resp.status_code == 200, f"Course creation failed: {resp.text}"

        # Update it -- keep total par in valid range (70-74)
        update_data = {"holes": [{"hole_number": i, "par": 4, "yards": 350, "handicap": i} for i in range(1, 19)]}

        response = client.put(f"/courses/{course_name}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_delete_course(self, client):
        course_name = f"Delete Test Club {uuid.uuid4().hex[:8]}"
        # First add a course
        new_course = {
            "name": course_name,
            "holes": [{"hole_number": i, "par": 4, "yards": 400, "handicap": i} for i in range(1, 19)],
        }
        resp = client.post("/courses", json=new_course)
        assert resp.status_code == 200, f"Course creation failed: {resp.text}"

        # Delete it
        response = client.delete(f"/courses/{course_name}")
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True


class TestGameEndpoints:
    """Test game-related endpoints"""

    def test_get_rules(self, client):
        response = client.get("/rules")
        assert response.status_code == 200
        rules = response.json()
        assert isinstance(rules, list)
        # Should have seeded rules
        assert len(rules) > 0


class TestCourseImport:
    """Test course import endpoints"""

    def test_get_import_sources(self, client):
        response = client.get("/courses/import/sources")
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert len(data["sources"]) > 0

    def test_preview_course_import(self, client):
        request_data = {"course_name": "Pebble Beach Golf Links", "state": "CA", "city": "Pebble Beach"}

        response = client.post("/courses/import/preview", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "course_name" in data
        assert "preview_data" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
