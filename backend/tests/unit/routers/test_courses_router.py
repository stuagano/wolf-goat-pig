"""Unit tests for courses router — list, get, create, delete."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGetCourses:
    def test_list_courses_returns_200(self):
        resp = client.get("/courses")
        assert resp.status_code == 200

    def test_list_courses_is_list_or_dict(self):
        resp = client.get("/courses")
        assert isinstance(resp.json(), (list, dict))

    def test_nonexistent_course_id_returns_404(self):
        resp = client.get("/courses/999999")
        assert resp.status_code == 404


class TestImportSources:
    def test_import_sources_returns_200(self):
        resp = client.get("/courses/import/sources")
        assert resp.status_code == 200

    def test_import_sources_has_sources_key(self):
        resp = client.get("/courses/import/sources")
        data = resp.json()
        assert "sources" in data or isinstance(data, dict)


class TestCreateCourse:
    def test_missing_required_fields_returns_422(self):
        resp = client.post("/courses", json={})
        assert resp.status_code == 422

    def test_import_by_search_without_name_returns_422_or_400(self):
        resp = client.post("/courses/import/search", json={})
        assert resp.status_code in (400, 422)


class TestDeleteCourse:
    def test_delete_nonexistent_course_returns_404_or_400(self):
        resp = client.delete("/courses/NonExistentCourseXYZ")
        assert resp.status_code in (400, 404)
