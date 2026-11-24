"""Official Wing Point stroke indexes, and the update that writes them onto existing rows.

Men's and women's indexes are the club scorecard (holes 1-18). The old BlueGolf
card had men's 5/6 and 14/15 swapped. ``Hole.handicap`` stores the men's index;
the model has no women's column, so the startup update writes men's values only.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.fix_wing_point_data as fix
import app.migrations_runner as mr
from app.data.wing_point_course_data import WING_POINT_COURSE_DATA
from app.database import Base
from app.models import Course, Hole
from app.seed_courses import DEFAULT_COURSES

OFFICIAL_MEN = [5, 15, 1, 17, 9, 7, 13, 11, 3, 16, 2, 14, 18, 10, 8, 4, 12, 6]
OFFICIAL_WOMEN = [1, 17, 7, 15, 9, 5, 11, 13, 3, 16, 10, 12, 18, 8, 6, 2, 4, 14]
# Previous BlueGolf card: men's holes 5/6 (7↔9) and 14/15 (8↔10) swapped.
STALE_MEN = [5, 15, 1, 17, 7, 9, 13, 11, 3, 16, 2, 14, 18, 8, 10, 4, 12, 6]

WING_POINT = "Wing Point Golf & Country Club"
MIGRATION = "update_wing_point_stroke_index_postgres.sql"


def _indexes(holes: list, key: str) -> list[int]:
    ordered = sorted(holes, key=lambda hole: hole["hole_number"])
    return [hole[key] for hole in ordered]


def test_course_data_matches_the_official_scorecard():
    holes = WING_POINT_COURSE_DATA["holes"]
    assert _indexes(holes, "handicap_men") == OFFICIAL_MEN
    assert _indexes(holes, "handicap_women") == OFFICIAL_WOMEN
    assert sorted(OFFICIAL_MEN) == list(range(1, 19))
    assert sorted(OFFICIAL_WOMEN) == list(range(1, 19))


def test_seed_and_fix_lists_match_the_mens_scorecard():
    seeded = next(course for course in DEFAULT_COURSES if course["name"] == WING_POINT)
    assert _indexes(seeded["holes_data"], "stroke_index") == OFFICIAL_MEN
    assert _indexes(fix.CORRECT_WING_POINT_DATA, "stroke_index") == OFFICIAL_MEN


def test_hole_model_stores_one_handicap_column():
    columns = {column.name for column in Hole.__table__.columns}
    assert "handicap" in columns
    assert "handicap_women" not in columns


def _engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


def _add_course(db, name: str, handicaps: list[int], hole_one_par: int = 5) -> Course:
    course = Course(name=name, total_par=71, total_yards=1000, created_at="t", updated_at="t")
    db.add(course)
    db.flush()
    for number, handicap in enumerate(handicaps, start=1):
        db.add(
            Hole(
                course_id=course.id,
                hole_number=number,
                par=hole_one_par if number == 1 else 4,
                yards=300 + number,
                handicap=handicap,
                description=f"hole {number}",
                tee_box="white",
            )
        )
    db.commit()
    return course


def _handicaps(db, name: str) -> list[int]:
    course = db.query(Course).filter_by(name=name).one()
    return [course.get_hole(number).handicap for number in range(1, 19)]


def test_sync_rewrites_stale_handicaps_and_is_idempotent():
    engine = _engine()
    Session = sessionmaker(bind=engine)
    db = Session()
    wing = _add_course(db, WING_POINT, STALE_MEN)
    _add_course(db, "Championship Links", list(range(1, 19)))
    yards_before = wing.get_hole(5).yards
    par_before = wing.get_hole(1).par

    changed = fix.sync_wing_point_stroke_indexes(db)
    assert changed == 4

    db.expire_all()
    assert _handicaps(db, WING_POINT) == OFFICIAL_MEN
    assert wing.get_hole(1).par == par_before
    assert wing.get_hole(5).yards == yards_before
    assert _handicaps(db, "Championship Links") == list(range(1, 19))

    assert fix.sync_wing_point_stroke_indexes(db) == 0
    assert _handicaps(db, WING_POINT) == OFFICIAL_MEN
    db.close()


def test_sync_with_no_wing_point_course_changes_nothing():
    engine = _engine()
    Session = sessionmaker(bind=engine)
    db = Session()
    assert fix.sync_wing_point_stroke_indexes(db) == 0
    db.close()


def test_fix_updates_handicaps_when_par_is_already_correct(monkeypatch):
    engine = _engine()
    Session = sessionmaker(bind=engine)
    db = Session()
    _add_course(db, WING_POINT, STALE_MEN, hole_one_par=5)
    db.close()
    monkeypatch.setattr(fix, "SessionLocal", Session)

    assert fix.fix_wing_point_course() is True
    assert fix.fix_wing_point_course() is False

    db = Session()
    course = db.query(Course).filter_by(name=WING_POINT).one()
    assert course.get_hole(1).par == 5
    assert course.get_hole(5).yards == 305
    assert _handicaps(db, WING_POINT) == OFFICIAL_MEN
    db.close()


def test_fix_still_repairs_stale_par_and_then_is_idempotent(monkeypatch):
    engine = _engine()
    Session = sessionmaker(bind=engine)
    db = Session()
    _add_course(db, WING_POINT, STALE_MEN, hole_one_par=4)
    db.close()
    monkeypatch.setattr(fix, "SessionLocal", Session)

    assert fix.fix_wing_point_course() is True
    assert fix.fix_wing_point_course() is False

    db = Session()
    course = db.query(Course).filter_by(name=WING_POINT).one()
    assert course.get_hole(1).par == 5
    assert course.get_hole(5).yards == 440
    assert _handicaps(db, WING_POINT) == OFFICIAL_MEN
    db.close()


def test_sql_migration_encodes_the_official_mens_index():
    sql = (mr.MIGRATIONS_DIR / MIGRATION).read_text()
    for hole_number, stroke_index in enumerate(OFFICIAL_MEN, start=1):
        assert f"WHEN {hole_number} THEN {stroke_index}" in sql
    assert "Wing Point Golf & Country Club" in sql


def test_sql_migration_applies_once_and_is_idempotent(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'mig.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    _add_course(db, WING_POINT, STALE_MEN)
    _add_course(db, "Championship Links", list(range(1, 19)))
    db.close()

    (tmp_path / MIGRATION).write_text((mr.MIGRATIONS_DIR / MIGRATION).read_text())
    monkeypatch.setattr(mr, "MIGRATIONS_DIR", tmp_path)
    engine.dialect.name = "postgresql"

    first = mr.run_sql_migrations(engine)
    assert first["applied"] == [MIGRATION]
    assert first["failed"] == []

    second = mr.run_sql_migrations(engine)
    assert second["applied"] == []
    assert second["failed"] == []

    db = Session()
    assert _handicaps(db, WING_POINT) == OFFICIAL_MEN
    assert _handicaps(db, "Championship Links") == list(range(1, 19))
    # Running the statement again writes the same men's indexes.
    with engine.begin() as conn:
        conn.execute(text((tmp_path / MIGRATION).read_text()))
    assert _handicaps(db, WING_POINT) == OFFICIAL_MEN
    db.close()
