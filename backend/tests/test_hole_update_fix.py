"""
Test to verify that updating a single hole doesn't delete future holes.
This test verifies the fix for the bug: "When I update a hole in the past all future holes get erased"
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, Base, engine
from app import models

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_update_single_hole_preserves_future_holes(test_db):
    """Test that updating a single hole (e.g., hole 5) doesn't delete future holes (6-18)"""

    # Create a test course with 18 holes
    course_data = {
        "name": "Test Course for Hole Update",
        "description": "Test course",
        "holes": [
            {
                "hole_number": i,
                "par": 4,
                "yards": 400,
                "handicap": i,
                "description": f"Hole {i}",
                "tee_box": "regular"
            }
            for i in range(1, 19)
        ]
    }

    # Create the course
    response = client.post("/courses", json=course_data)
    assert response.status_code == 200
    print(f"Created course: {response.json()}")

    # Verify all 18 holes were created
    db = next(get_db())
    course = db.query(models.Course).filter(models.Course.name == "Test Course for Hole Update").first()
    assert course is not None
    all_holes = db.query(models.Hole).filter(models.Hole.course_id == course.id).all()
    assert len(all_holes) == 18
    print(f"Verified: Course has {len(all_holes)} holes")

    # Now update ONLY hole 5 (a hole "in the past" if we're on hole 10)
    update_data = {
        "holes": [
            {
                "hole_number": 5,
                "par": 3,  # Changed from 4 to 3
                "yards": 180,  # Changed from 400 to 180
                "handicap": 5,
                "description": "Updated Hole 5 - Now a par 3",
                "tee_box": "regular"
            }
        ]
    }

    # Update the course with just hole 5
    response = client.put("/courses/Test Course for Hole Update", json=update_data)
    assert response.status_code == 200
    print(f"Updated hole 5: {response.json()}")

    # Verify that ALL 18 holes still exist
    db = next(get_db())
    course = db.query(models.Course).filter(models.Course.name == "Test Course for Hole Update").first()
    remaining_holes = db.query(models.Hole).filter(models.Hole.course_id == course.id).all()

    print(f"\nAfter update:")
    print(f"Total holes remaining: {len(remaining_holes)}")
    print(f"Hole numbers: {sorted([h.hole_number for h in remaining_holes])}")

    # THE BUG FIX: All 18 holes should still exist
    assert len(remaining_holes) == 18, f"Expected 18 holes, but found {len(remaining_holes)}"

    # Verify hole 5 was updated
    hole_5 = db.query(models.Hole).filter(
        models.Hole.course_id == course.id,
        models.Hole.hole_number == 5
    ).first()
    assert hole_5 is not None
    assert hole_5.par == 3, f"Hole 5 par should be 3, but is {hole_5.par}"
    assert hole_5.yards == 180, f"Hole 5 yards should be 180, but is {hole_5.yards}"
    print(f"Verified: Hole 5 was updated correctly (par={hole_5.par}, yards={hole_5.yards})")

    # Verify future holes (6-18) still exist and weren't modified
    for hole_num in range(6, 19):
        hole = db.query(models.Hole).filter(
            models.Hole.course_id == course.id,
            models.Hole.hole_number == hole_num
        ).first()
        assert hole is not None, f"Hole {hole_num} was deleted! This is the bug."
        assert hole.par == 4, f"Hole {hole_num} was modified unexpectedly"
        assert hole.yards == 400, f"Hole {hole_num} was modified unexpectedly"

    print("✓ All future holes (6-18) still exist and weren't modified")

    # Verify holes 1-4 also still exist
    for hole_num in range(1, 5):
        hole = db.query(models.Hole).filter(
            models.Hole.course_id == course.id,
            models.Hole.hole_number == hole_num
        ).first()
        assert hole is not None, f"Hole {hole_num} was deleted!"

    print("✓ All past holes (1-4) still exist")

    # Cleanup
    client.delete("/courses/Test Course for Hole Update")
    print("\n✓ Test passed! The bug is fixed.")


def test_full_18_hole_update_works_correctly(test_db):
    """Test that a full 18-hole update still works correctly"""

    # Create a test course
    course_data = {
        "name": "Test Course Full Update",
        "description": "Test course",
        "holes": [
            {
                "hole_number": i,
                "par": 4,
                "yards": 400,
                "handicap": i,
                "description": f"Hole {i}",
                "tee_box": "regular"
            }
            for i in range(1, 19)
        ]
    }

    response = client.post("/courses", json=course_data)
    assert response.status_code == 200

    # Update all 18 holes
    update_data = {
        "holes": [
            {
                "hole_number": i,
                "par": 3 if i % 6 == 0 else 5 if i % 5 == 0 else 4,
                "yards": 400 + i * 10,
                "handicap": i,
                "description": f"Updated Hole {i}",
                "tee_box": "regular"
            }
            for i in range(1, 19)
        ]
    }

    response = client.put("/courses/Test Course Full Update", json=update_data)
    assert response.status_code == 200

    # Verify all holes were updated
    db = next(get_db())
    course = db.query(models.Course).filter(models.Course.name == "Test Course Full Update").first()
    holes = db.query(models.Hole).filter(models.Hole.course_id == course.id).all()

    assert len(holes) == 18
    for hole in holes:
        expected_par = 3 if hole.hole_number % 6 == 0 else 5 if hole.hole_number % 5 == 0 else 4
        assert hole.par == expected_par

    # Cleanup
    client.delete("/courses/Test Course Full Update")
    print("✓ Full 18-hole update works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
