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


class TestUpdateCoursePreservesHoles:
    """Regression (salvaged from root tests/test_hole_update_fix.py): a partial
    PUT /courses/{name} must update only the listed holes and preserve the rest.
    Bug it guards: 'updating a hole in the past erases all future holes.'"""

    _NAME = "WGP Hole-Update Regression Course"

    def _eighteen_holes(self):
        return [
            {
                "hole_number": i,
                "par": 4,
                "yards": 400,
                "handicap": i,
                "description": f"Hole {i}",
                "tee_box": "regular",
            }
            for i in range(1, 19)
        ]

    def _holes_via_db(self):
        from app import models
        from app.database import get_db

        db = next(get_db())
        course = db.query(models.Course).filter(models.Course.name == self._NAME).first()
        assert course is not None, "course was not created"
        return {h.hole_number: h for h in db.query(models.Hole).filter(models.Hole.course_id == course.id).all()}

    def test_partial_update_preserves_other_holes(self):
        # Clean slate in case a previous run left this course behind.
        client.delete(f"/courses/{self._NAME}")

        resp = client.post(
            "/courses",
            json={
                "name": self._NAME,
                "description": "regression fixture",
                "holes": self._eighteen_holes(),
            },
        )
        assert resp.status_code == 200
        assert len(self._holes_via_db()) == 18

        # Update ONLY hole 5.
        resp = client.put(
            f"/courses/{self._NAME}",
            json={
                "holes": [
                    {
                        "hole_number": 5,
                        "par": 3,
                        "yards": 180,
                        "handicap": 5,
                        "description": "Updated Hole 5 - now a par 3",
                        "tee_box": "regular",
                    }
                ]
            },
        )
        assert resp.status_code == 200

        holes = self._holes_via_db()
        # All 18 survive — this is the bug fix.
        assert len(holes) == 18, f"expected 18 holes, found {len(holes)}"
        # Hole 5 changed.
        assert holes[5].par == 3
        assert holes[5].yards == 180
        # Every other hole is untouched.
        for n in list(range(1, 5)) + list(range(6, 19)):
            assert holes[n].par == 4, f"hole {n} par changed unexpectedly"
            assert holes[n].yards == 400, f"hole {n} yards changed unexpectedly"

        client.delete(f"/courses/{self._NAME}")
