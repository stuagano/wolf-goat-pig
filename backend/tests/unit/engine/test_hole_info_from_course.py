"""Hole par/yardage/stroke index must come from the course, never from random defaults.

Regression: CourseManager had no get_hole_info(), so hole setup fell through to
HoleState.set_hole_info() with no arguments — which randomizes par and picks a
random stroke index. Handicap strokes for the hole were therefore unrelated to
the course being played, and disagreed with the scorecard's stroke allocation.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.domain.game_types import Player
from app.state.course_manager import CourseManager
from app.wolf_goat_pig import WolfGoatPigGame

# hole_number, par, yards, stroke index (Wing Point front nine)
COURSE_HOLES = [
    (1, 5, 429, 5),
    (2, 3, 158, 15),
    (3, 4, 310, 1),
]

PLAYERS = [
    Player(id="p1", name="Mark", handicap=11.0),
    Player(id="p2", name="Hart", handicap=9.0),
    Player(id="p3", name="Stuart", handicap=15.0),
    Player(id="p4", name="Rainer", handicap=18.0),
]


def make_course_manager() -> CourseManager:
    """A CourseManager with a course in its cache, no database required."""
    holes = [
        SimpleNamespace(hole_number=n, par=par, yards=yards, handicap=si, description="")
        for n, par, yards, si in COURSE_HOLES
    ]
    manager = CourseManager()
    manager.selected_course_name = "Test Course"
    manager.selected_course_id = 1
    manager._course_cache[1] = SimpleNamespace(id=1, name="Test Course", holes=holes)
    return manager


class TestGetHoleInfo:
    def test_returns_course_values_for_the_hole(self):
        info = make_course_manager().get_hole_info(1)

        assert info["par"] == 5
        assert info["yards"] == 429
        assert info["stroke_index"] == 5

    def test_handicap_column_is_exposed_as_stroke_index(self):
        info = make_course_manager().get_hole_info(3)

        assert info["stroke_index"] == 1
        assert info["handicap"] == 1

    def test_unknown_hole_raises(self):
        with pytest.raises(KeyError):
            make_course_manager().get_hole_info(17)

    def test_no_course_loaded_raises(self):
        with pytest.raises(KeyError):
            CourseManager().get_hole_info(1)


class TestHoleSetupUsesCourseData:
    def _make_game(self) -> WolfGoatPigGame:
        with (
            patch.object(WolfGoatPigGame, "__init_persistence__", lambda self, gid: None),
            patch.object(WolfGoatPigGame, "_save_to_db", lambda self: None),
        ):
            return WolfGoatPigGame(player_count=4, players=list(PLAYERS), course_manager=make_course_manager())

    def test_hole_state_matches_the_course(self):
        hole_state = self._make_game().hole_states[1]

        assert hole_state.hole_par == 5
        assert hole_state.hole_yardage == 429
        assert hole_state.stroke_index == 5

    def test_stroke_index_is_stable_across_games(self):
        indexes = {self._make_game().hole_states[1].stroke_index for _ in range(5)}

        assert indexes == {5}

    def test_strokes_received_use_the_course_stroke_index(self):
        advantages = self._make_game().hole_states[1].stroke_advantages

        # Hole 1 is stroke index 5. Net handicaps are 2 / 0 / 7 / 10, so only the
        # two highest handicaps reach index 5, and both at a Creecher half stroke.
        assert advantages["p1"].strokes_received == 0.0
        assert advantages["p2"].strokes_received == 0.0
        assert advantages["p3"].strokes_received == 0.5
        assert advantages["p4"].strokes_received == 0.5
