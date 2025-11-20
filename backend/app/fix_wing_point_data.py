"""
Fix Wing Point Golf & Country Club course data if it exists with incorrect par values.
This script checks if Wing Point exists in the database and updates it if the par values are wrong.
"""
from database import SessionLocal
from models import Course
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Correct Wing Point data from wing_point_course_data.py (white tees)
CORRECT_WING_POINT_DATA = [
    {"hole_number": 1, "par": 5, "yards": 429, "stroke_index": 5, "description": "Opening Drive - gentle starting hole, slight dogleg right"},
    {"hole_number": 2, "par": 3, "yards": 158, "stroke_index": 15, "description": "Short Iron - downhill par 3 with bunkers guarding the green"},
    {"hole_number": 3, "par": 4, "yards": 310, "stroke_index": 1, "description": "The Challenge - handicap 1, tough dogleg left requiring precision"},
    {"hole_number": 4, "par": 3, "yards": 112, "stroke_index": 17, "description": "Precision - short but tricky par 3"},
    {"hole_number": 5, "par": 5, "yards": 440, "stroke_index": 7, "description": "The Long One - reachable par 5 for longer hitters"},
    {"hole_number": 6, "par": 4, "yards": 327, "stroke_index": 9, "description": "Mid Iron - strategic placement required off the tee"},
    {"hole_number": 7, "par": 4, "yards": 291, "stroke_index": 13, "description": "Risk Reward - short par 4 with risk-reward options"},
    {"hole_number": 8, "par": 4, "yards": 280, "stroke_index": 11, "description": "The Turn - another short par 4 before the turn"},
    {"hole_number": 9, "par": 4, "yards": 316, "stroke_index": 3, "description": "Home Bound - tough finishing hole for the front nine"},
    {"hole_number": 10, "par": 3, "yards": 200, "stroke_index": 16, "description": "Back Nine Starter - long par 3 to start the back nine"},
    {"hole_number": 11, "par": 4, "yards": 353, "stroke_index": 2, "description": "The Beast - second toughest hole on the course"},
    {"hole_number": 12, "par": 3, "yards": 168, "stroke_index": 14, "description": "Over Water - beautiful par 3 with water in play"},
    {"hole_number": 13, "par": 4, "yards": 272, "stroke_index": 18, "description": "Breathing Room - easiest hole on the course"},
    {"hole_number": 14, "par": 4, "yards": 303, "stroke_index": 8, "description": "Deceptive - looks easy but plays tough"},
    {"hole_number": 15, "par": 4, "yards": 356, "stroke_index": 10, "description": "The Stretch - start of the tough finishing stretch"},
    {"hole_number": 16, "par": 4, "yards": 344, "stroke_index": 4, "description": "Penultimate - tough hole as you near the finish"},
    {"hole_number": 17, "par": 5, "yards": 455, "stroke_index": 12, "description": "The Penultimate - par 5 start of Hoepfinger phase"},
    {"hole_number": 18, "par": 4, "yards": 372, "stroke_index": 6, "description": "The Finale - strong finishing par 4"}
]

def fix_wing_point_course():
    """Fix Wing Point course data if it exists with wrong par values."""
    db = SessionLocal()
    try:
        # Find Wing Point course
        wing_point = db.query(Course).filter_by(name="Wing Point Golf & Country Club").first()

        if not wing_point:
            logger.info("Wing Point course not found in database - will be seeded correctly on next seed")
            return False

        # Check if hole 1 has wrong par value (should be 5, not 4)
        if wing_point.holes_data and len(wing_point.holes_data) > 0:
            hole_1_par = wing_point.holes_data[0].get("par", 0)

            if hole_1_par == 4:  # Wrong value, need to fix
                logger.warning(f"Wing Point hole 1 has incorrect par {hole_1_par}, updating to correct values...")

                # Calculate correct totals
                correct_total_par = sum(h["par"] for h in CORRECT_WING_POINT_DATA)
                correct_total_yards = sum(h["yards"] for h in CORRECT_WING_POINT_DATA)

                # Update the course
                wing_point.holes_data = CORRECT_WING_POINT_DATA
                wing_point.total_par = correct_total_par
                wing_point.total_yards = correct_total_yards
                wing_point.course_rating = 67.4
                wing_point.slope_rating = 120
                wing_point.updated_at = datetime.now().isoformat()

                db.commit()
                logger.info(f"✅ Wing Point course updated successfully! Hole 1 par is now {CORRECT_WING_POINT_DATA[0]['par']}")
                return True
            else:
                logger.info(f"Wing Point course data is already correct (hole 1 par = {hole_1_par})")
                return False
        else:
            logger.warning("Wing Point course has no holes data")
            return False

    except Exception as e:
        db.rollback()
        logger.error(f"Error fixing Wing Point course: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fix_wing_point_course()
