"""
Wing Point Golf & Country Club
Official Course Data
Est. 1903
"""

from typing import Any, Dict

WING_POINT_COURSE_DATA: Dict[str, Any] = {
    "name": "Wing Point Golf & Country Club",
    "established": 1903,
    "location": "Bainbridge Island, WA",
    "tees": {
        "black": {
            "rating": 70.3,
            "slope": 124,
            "total_yards": 6093
        },
        "white": {
            "rating": 67.4,
            "slope": 120,
            "total_yards": 5486
        },
        "red": {
            "rating": 71.3,
            "slope": 122,
            "total_yards": 5117
        },
        "gold": {
            "rating": 68.4,
            "slope": 114,
            "total_yards": 4699
        }
    },
    "holes": [
        {
            "hole_number": 1,
            "par": 5,
            "handicap_men": 5,
            "handicap_women": 1,
            "yards": {
                "black": 476,
                "white": 429,
                "red": 400,
                "gold": 339
            },
            "name": "Opening Drive",
            "description": "A gentle starting hole, slight dogleg right"
        },
        {
            "hole_number": 2,
            "par": 3,
            "handicap_men": 15,
            "handicap_women": 17,
            "yards": {
                "black": 175,
                "white": 158,
                "red": 103,
                "gold": 96
            },
            "name": "Short Iron",
            "description": "Downhill par 3 with bunkers guarding the green"
        },
        {
            "hole_number": 3,
            "par": 4,
            "handicap_men": 1,
            "handicap_women": 7,
            "yards": {
                "black": 401,
                "white": 310,
                "red": 310,
                "gold": 299
            },
            "name": "The Challenge",
            "description": "Handicap 1 - tough dogleg left requiring precision"
        },
        {
            "hole_number": 4,
            "par": 3,
            "handicap_men": 17,
            "handicap_women": 15,
            "yards": {
                "black": 133,
                "white": 112,
                "red": 103,
                "gold": 92
            },
            "name": "Precision",
            "description": "Short but tricky par 3"
        },
        {
            "hole_number": 5,
            "par": 5,
            "handicap_men": 7,
            "handicap_women": 9,
            "yards": {
                "black": 498,
                "white": 440,
                "red": 415,
                "gold": 372
            },
            "name": "The Long One",
            "description": "Reachable par 5 for longer hitters"
        },
        {
            "hole_number": 6,
            "par": 4,
            "handicap_men": 9,
            "handicap_women": 13,
            "yards": {
                "black": 351,
                "white": 327,
                "red": 290,
                "gold": 278
            },
            "name": "Mid Iron",
            "description": "Strategic placement required off the tee"
        },
        {
            "hole_number": 7,
            "par": 4,
            "handicap_men": 13,
            "handicap_women": 11,
            "yards": {
                "black": 316,
                "white": 291,
                "red": 282,
                "gold": 256
            },
            "name": "Risk Reward",
            "description": "Short par 4 with risk-reward options"
        },
        {
            "hole_number": 8,
            "par": 4,
            "handicap_men": 11,
            "handicap_women": 5,
            "yards": {
                "black": 294,
                "white": 280,
                "red": 255,
                "gold": 194
            },
            "name": "The Turn",
            "description": "Another short par 4 before the turn"
        },
        {
            "hole_number": 9,
            "par": 4,
            "handicap_men": 3,
            "handicap_women": 3,
            "yards": {
                "black": 340,
                "white": 316,
                "red": 292,
                "gold": 282
            },
            "name": "Home Bound",
            "description": "Tough finishing hole for the front nine"
        },
        {
            "hole_number": 10,
            "par": 3,
            "handicap_men": 16,
            "handicap_women": 16,
            "yards": {
                "black": 239,
                "white": 200,
                "red": 165,
                "gold": 156
            },
            "name": "Back Nine Starter",
            "description": "Long par 3 to start the back nine"
        },
        {
            "hole_number": 11,
            "par": 4,  # Note: Par 4/5 depending on tee box (typically Par 4 for men's white tees)
            "par_variation": {
                "default": 4,
                "championship": 5,
                "note": "Par 4/5 depending on tee box used"
            },
            "handicap_men": 2,
            "handicap_women": 10,
            "yards": {
                "black": 401,
                "white": 353,
                "red": 401,
                "gold": 349
            },
            "name": "The Beast",
            "description": "Second toughest hole on the course - Par 4/5 depending on tees"
        },
        {
            "hole_number": 12,
            "par": 3,
            "handicap_men": 14,
            "handicap_women": 12,
            "yards": {
                "black": 204,
                "white": 168,
                "red": 153,
                "gold": 135
            },
            "name": "Over Water",
            "description": "Beautiful par 3 with water in play"
        },
        {
            "hole_number": 13,
            "par": 4,
            "handicap_men": 18,
            "handicap_women": 18,
            "yards": {
                "black": 310,
                "white": 272,
                "red": 236,
                "gold": 211
            },
            "name": "Breathing Room",
            "description": "Easiest hole on the course - make your birdie here"
        },
        {
            "hole_number": 14,
            "par": 4,
            "handicap_men": 8,
            "handicap_women": 2,
            "yards": {
                "black": 317,
                "white": 303,
                "red": 303,
                "gold": 295
            },
            "name": "Deceptive",
            "description": "Looks easy but plays tough"
        },
        {
            "hole_number": 15,
            "par": 4,
            "handicap_men": 10,
            "handicap_women": 6,
            "yards": {
                "black": 396,
                "white": 356,
                "red": 349,
                "gold": 296
            },
            "name": "The Stretch",
            "description": "Start of the tough finishing stretch"
        },
        {
            "hole_number": 16,
            "par": 4,
            "handicap_men": 4,
            "handicap_women": 8,
            "yards": {
                "black": 358,
                "white": 344,
                "red": 301,
                "gold": 298
            },
            "name": "Penultimate",
            "description": "Tough hole as you near the finish"
        },
        {
            "hole_number": 17,
            "par": 5,
            "handicap_men": 12,
            "handicap_women": 4,
            "yards": {
                "black": 490,
                "white": 455,
                "red": 447,
                "gold": 447
            },
            "name": "The Penultimate",
            "description": "Par 5 start of Hoepfinger phase"
        },
        {
            "hole_number": 18,
            "par": 4,
            "handicap_men": 6,
            "handicap_women": 14,
            "yards": {
                "black": 394,
                "white": 372,
                "red": 312,
                "gold": 306
            },
            "name": "The Finale",
            "description": "Strong finishing par 4 - Big Dick opportunity"
        }
    ],
    "total_par": 71,  # 36 front, 35 back (72 if hole 11 played as Par 5)
    "course_rules": {
        "out_of_bounds": "Marked by white stakes on holes 10 and 15",
        "lateral_hazards": "Red stakes throughout",
        "relief_areas": "Free relief from flowerbeds and memorials",
        "sprinkler_heads": "Relief may be taken from sprinkler heads on or within two club lengths of green"
    },
    "local_rules": [
        "The road is out of bounds on holes 10, 14, and 15",
        "On holes 10 and 15, any ball that crosses the out of bounds road and comes to rest on another part of the golf course is considered out of bounds",
        "Free relief from flowerbeds and memorials",
        "Relief may be taken from sprinkler heads that lie on or within two club lengths of the green when your ball is within two club lengths of that sprinkler head"
    ],
    "wgp_specific": {
        "vinnie_variation_start": 13,  # Holes 13-16
        "hoepfinger_start": 17,  # Holes 17-18 in 4-man game
        "easiest_hole": 13,  # Handicap 18 - good for strategic decisions
        "toughest_hole": 3,  # Handicap 1 - be careful here
        "signature_holes": [2, 10, 12, 18],  # Par 3s and finishing hole
        "risk_reward_holes": [5, 7, 13, 18]  # Good for betting decisions
    }
}

def get_hole_data(hole_number: int, tee_box: str = "white") -> dict:
    """Get data for a specific hole"""
    if hole_number < 1 or hole_number > 18:
        raise ValueError(f"Invalid hole number: {hole_number}")
    
    hole = WING_POINT_COURSE_DATA["holes"][hole_number - 1]
    return {
        "number": hole["hole_number"],
        "par": hole["par"],
        "yards": hole["yards"].get(tee_box, hole["yards"]["white"]),
        "handicap": hole["handicap_men"],
        "name": hole["name"],
        "description": hole["description"]
    }

def get_nine_hole_par(front: bool = True) -> int:
    """Get par for front or back nine"""
    holes = WING_POINT_COURSE_DATA["holes"]
    if front:
        return sum(h["par"] for h in holes[:9])
    else:
        return sum(h["par"] for h in holes[9:])

def get_total_yards(tee_box: str = "white") -> int:
    """Get total yardage for a tee box"""
    return sum(h["yards"].get(tee_box, h["yards"]["white"]) 
               for h in WING_POINT_COURSE_DATA["holes"])

def is_vinnie_variation_hole(hole_number: int) -> bool:
    """Check if hole is in Vinnie's Variation range (13-16)"""
    return 13 <= hole_number <= 16

def is_hoepfinger_hole(hole_number: int, game_type: str = "4_man") -> bool:
    """Check if hole is in Hoepfinger phase"""
    if game_type == "4_man":
        return hole_number >= 17
    elif game_type == "5_man":
        return hole_number >= 16
    elif game_type == "6_man":
        return hole_number >= 13
    return False

def get_strategic_value(hole_number: int) -> str:
    """Get strategic betting advice for a hole"""
    hole = WING_POINT_COURSE_DATA["holes"][hole_number - 1]
    
    if hole_number in WING_POINT_COURSE_DATA["wgp_specific"]["risk_reward_holes"]:
        return "HIGH_RISK_REWARD"
    elif hole["handicap_men"] <= 4:
        return "PLAY_SAFE"
    elif hole["handicap_men"] >= 15:
        return "ATTACK"
    else:
        return "STANDARD"