-- Migration: Add holes to existing courses
-- This migration seeds hole data for courses that were created without holes

-- Note: This is a one-time fix for courses that were seeded without hole data.
-- The actual seeding should be done via Python to use the DEFAULT_COURSES data.
-- This SQL migration serves as documentation of the issue.

-- To fix production, run the following Python code on the Render console or via API:
/*
from app.database import SessionLocal
from app.models import Course, Hole
from app.seed_courses import DEFAULT_COURSES

db = SessionLocal()
try:
    for course_data in DEFAULT_COURSES:
        course_name = course_data['name']
        existing_course = db.query(Course).filter_by(name=course_name).first()

        if not existing_course:
            print(f'Course {course_name} not found, skipping...')
            continue

        existing_holes = db.query(Hole).filter(Hole.course_id == existing_course.id).count()
        if existing_holes > 0:
            print(f'Course {course_name} already has {existing_holes} holes, skipping...')
            continue

        holes_data = course_data.get('holes_data', [])
        for hole_detail in holes_data:
            hole = Hole(
                course_id=existing_course.id,
                hole_number=hole_detail['hole_number'],
                par=hole_detail['par'],
                yards=hole_detail['yards'],
                handicap=hole_detail['stroke_index'],
                description=hole_detail.get('description'),
                tee_box=hole_detail.get('tee_box', 'white')
            )
            db.add(hole)

        print(f'Added {len(holes_data)} holes to {course_name}')

    db.commit()
    print('Done!')

finally:
    db.close()
*/
