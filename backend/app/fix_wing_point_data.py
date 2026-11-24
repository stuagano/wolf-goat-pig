"""
Fix Wing Point Golf & Country Club course data if it exists with incorrect values.

Par is rewritten only when hole 1 is still the old par 4. Stroke indexes are
synced on every call: seed skips an existing Wing Point course, so a par-only
guard would leave the old BlueGolf handicaps in place.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Course
from .utils.time import utc_now

logger = logging.getLogger(__name__)

WING_POINT_COURSE_NAME = "Wing Point Golf & Country Club"

# Correct Wing Point data from wing_point_course_data.py (white tees)
CORRECT_WING_POINT_DATA: list[dict[str, Any]] = [
    {
        "hole_number": 1,
        "par": 5,
        "yards": 429,
        "stroke_index": 5,
        "description": "Opening Drive - gentle starting hole, slight dogleg right",
    },
    {
        "hole_number": 2,
        "par": 3,
        "yards": 158,
        "stroke_index": 15,
        "description": "Short Iron - downhill par 3 with bunkers guarding the green",
    },
    {
        "hole_number": 3,
        "par": 4,
        "yards": 310,
        "stroke_index": 1,
        "description": "The Challenge - handicap 1, tough dogleg left requiring precision",
    },
    {
        "hole_number": 4,
        "par": 3,
        "yards": 112,
        "stroke_index": 17,
        "description": "Precision - short but tricky par 3",
    },
    {
        "hole_number": 5,
        "par": 5,
        "yards": 440,
        "stroke_index": 9,
        "description": "The Long One - reachable par 5 for longer hitters",
    },
    {
        "hole_number": 6,
        "par": 4,
        "yards": 327,
        "stroke_index": 7,
        "description": "Mid Iron - strategic placement required off the tee",
    },
    {
        "hole_number": 7,
        "par": 4,
        "yards": 291,
        "stroke_index": 13,
        "description": "Risk Reward - short par 4 with risk-reward options",
    },
    {
        "hole_number": 8,
        "par": 4,
        "yards": 280,
        "stroke_index": 11,
        "description": "The Turn - another short par 4 before the turn",
    },
    {
        "hole_number": 9,
        "par": 4,
        "yards": 316,
        "stroke_index": 3,
        "description": "Home Bound - tough finishing hole for the front nine",
    },
    {
        "hole_number": 10,
        "par": 3,
        "yards": 200,
        "stroke_index": 16,
        "description": "Back Nine Starter - long par 3 to start the back nine",
    },
    {
        "hole_number": 11,
        "par": 4,
        "yards": 353,
        "stroke_index": 2,
        "description": "The Beast - second toughest hole on the course",
    },
    {
        "hole_number": 12,
        "par": 3,
        "yards": 168,
        "stroke_index": 14,
        "description": "Over Water - beautiful par 3 with water in play",
    },
    {
        "hole_number": 13,
        "par": 4,
        "yards": 272,
        "stroke_index": 18,
        "description": "Breathing Room - easiest hole on the course",
    },
    {
        "hole_number": 14,
        "par": 4,
        "yards": 303,
        "stroke_index": 10,
        "description": "Deceptive - looks easy but plays tough",
    },
    {
        "hole_number": 15,
        "par": 4,
        "yards": 356,
        "stroke_index": 8,
        "description": "The Stretch - start of the tough finishing stretch",
    },
    {
        "hole_number": 16,
        "par": 4,
        "yards": 344,
        "stroke_index": 4,
        "description": "Penultimate - tough hole as you near the finish",
    },
    {
        "hole_number": 17,
        "par": 5,
        "yards": 455,
        "stroke_index": 12,
        "description": "The Penultimate - par 5 start of Hoepfinger phase",
    },
    {
        "hole_number": 18,
        "par": 4,
        "yards": 372,
        "stroke_index": 6,
        "description": "The Finale - strong finishing par 4",
    },
]


def mens_stroke_index_by_hole() -> dict[int, int]:
    """Official men's stroke index keyed by hole number (1-18)."""
    return {hole["hole_number"]: hole["stroke_index"] for hole in CORRECT_WING_POINT_DATA}


def sync_wing_point_stroke_indexes(db: Session) -> int:
    """Set existing Wing Point ``Hole.handicap`` rows to the official men's stroke index.

    ``Hole.handicap`` is the men's stroke index used for stroke allocation.
    The model has no women's handicap column; women's indexes stay in
    ``wing_point_course_data`` and are not written here.

    Returns how many holes changed. A second call finds the official values
    already stored and returns 0. Missing holes are left missing, and other
    courses are not touched.
    """
    wing_point = db.query(Course).filter_by(name=WING_POINT_COURSE_NAME).first()
    if wing_point is None:
        logger.info("Wing Point course not found - stroke index sync skipped")
        return 0

    official = mens_stroke_index_by_hole()
    changed = 0
    for hole in wing_point.holes:
        target = official.get(hole.hole_number)
        if target is None or hole.handicap == target:
            continue
        logger.info("Wing Point hole %s handicap %s -> %s", hole.hole_number, hole.handicap, target)
        hole.handicap = target
        changed += 1

    if changed:
        wing_point.updated_at = utc_now().isoformat()
        db.commit()
        logger.info("Updated %s Wing Point hole handicap(s) to the official men's stroke index", changed)
    else:
        logger.info("Wing Point hole handicaps already match the official men's stroke index")
    return changed


def fix_wing_point_course():
    """Fix a stale Wing Point par, then sync stroke indexes even when par is already right."""
    db = SessionLocal()
    try:
        wing_point = db.query(Course).filter_by(name=WING_POINT_COURSE_NAME).first()

        if not wing_point:
            logger.info("Wing Point course not found in database - will be seeded correctly on next seed")
            return False

        hole_1 = wing_point.get_hole(1)

        if hole_1 is None:
            logger.warning("Wing Point course has no holes - skipping fix")
            return False

        par_fixed = False
        if hole_1.par == 4:  # Wrong value, need to fix
            logger.warning(f"Wing Point hole 1 has incorrect par {hole_1.par}, updating to correct values...")

            correct_total_par = sum(h["par"] for h in CORRECT_WING_POINT_DATA)
            correct_total_yards = sum(h["yards"] for h in CORRECT_WING_POINT_DATA)

            wing_point.total_par = correct_total_par
            wing_point.total_yards = correct_total_yards
            wing_point.course_rating = 71.1  # Black tees (men)
            wing_point.slope_rating = 130
            wing_point.updated_at = utc_now().isoformat()

            for hole_data in CORRECT_WING_POINT_DATA:
                hole = wing_point.get_hole(hole_data["hole_number"])
                if hole:
                    hole.par = hole_data["par"]
                    hole.yards = hole_data["yards"]
                    hole.handicap = hole_data["stroke_index"]
                    hole.description = hole_data["description"]

            db.commit()
            logger.info(
                f"Wing Point course updated successfully! Hole 1 par is now {CORRECT_WING_POINT_DATA[0]['par']}"
            )
            par_fixed = True
        else:
            logger.info(f"Wing Point par is already correct (hole 1 par = {hole_1.par})")

        # Par may already be 5 while handicaps are still the old BlueGolf card.
        handicaps_changed = sync_wing_point_stroke_indexes(db)
        return par_fixed or handicaps_changed > 0

    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing Wing Point course: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fix_wing_point_course()
