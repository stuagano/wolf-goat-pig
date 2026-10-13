"""Index -> course handicap off the course's rating, slope and par."""

import pytest

from app.utils.handicap_resolve import to_course_handicap

# Wing Point Black tees (men), par from the 18 holes.
WING_POINT = {"rating": 71.1, "slope": 130, "holes": [{"par": 4}] * 17 + [{"par": 3}]}


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        (11.8, 14),  # 11.8 x 130/113 + 0.1 = 13.68
        (0.0, 0),
        (20.0, 23),  # 23.11
        (4.3, 5),  # 5.05
        (-1.5, -2),  # plus handicap: -1.63
    ],
)
def test_converts_index_with_course_rating_slope_and_par(index, expected):
    assert to_course_handicap(index, WING_POINT) == expected


def test_rounds_half_up_like_the_usga_not_bankers():
    # 12.5 must become 13 (Python's round() gives 12).
    course = {"rating": 72.0, "slope": 113, "holes": [{"par": 4}] * 18}
    assert to_course_handicap(12.5, course) == 13


@pytest.mark.parametrize(
    "course",
    [None, {}, {"rating": None, "slope": 130, "holes": WING_POINT["holes"]}, {"rating": 71.1, "slope": None}],
)
def test_without_rating_or_slope_the_index_is_used_as_is(course):
    assert to_course_handicap(11.8, course) == 11.8


def test_par_falls_back_to_total_par_when_holes_are_missing():
    assert to_course_handicap(11.8, {"rating": 71.1, "slope": 130, "total_par": 71}) == 14
