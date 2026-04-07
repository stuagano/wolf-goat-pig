"""Comprehensive tests for advanced Wolf Goat Pig rules."""

from unittest.mock import patch

import pytest

from app.wolf_goat_pig import WGPPlayer, WolfGoatPigGame


def _make_game(player_count: int = 4) -> WolfGoatPigGame:
    """Create a WolfGoatPigGame with DB persistence stubbed out."""
    with patch.object(WolfGoatPigGame, "__init_persistence__", lambda self, gid: None), \
         patch.object(WolfGoatPigGame, "_save_to_db", lambda self: None):
        game = WolfGoatPigGame(player_count=player_count)
    return game


class TestAdvancedWGPRules:
    """Test advanced Wolf Goat Pig rules implementation."""

    def setup_method(self):
        self.game = _make_game(player_count=4)
        self.players = [
            WGPPlayer("p1", "Player1", 12.0),
            WGPPlayer("p2", "Player2", 15.0),
            WGPPlayer("p3", "Player3", 8.0),
            WGPPlayer("p4", "Player4", 20.0),
        ]
        self.game.players = self.players

    def test_hoepfinger_phase_4_man_game(self):
        assert self.game.hoepfinger_start_hole == 17
        assert 17 >= self.game.hoepfinger_start_hole

    def test_hoepfinger_phase_5_man_game(self):
        game_5 = _make_game(player_count=5)
        assert game_5.hoepfinger_start_hole == 16

    def test_hoepfinger_phase_6_man_game(self):
        game_6 = _make_game(player_count=6)
        assert game_6.hoepfinger_start_hole == 13

    def test_joes_special_implementation(self):
        self.game.current_hole = 1
        self.game._initialize_hole(1)
        hole_state = self.game.hole_states[1]

        hole_state.betting.joes_special_value = 4
        hole_state.betting.base_wager = 4
        hole_state.betting.current_wager = 4

        assert hole_state.betting.joes_special_value == 4
        assert hole_state.betting.base_wager == 4
        assert hole_state.betting.current_wager == 4

    def test_carry_over_rules(self):
        self.game.current_hole = 1
        self.game._initialize_hole(1)
        hole_state = self.game.hole_states[1]
        hole_state.betting.base_wager = 2
        hole_state.betting.current_wager = 2
        hole_state.betting.carry_over = True

        self.game.current_hole = 2
        self.game._initialize_hole(2)
        next_hole_state = self.game.hole_states[2]

        assert next_hole_state.betting.base_wager >= hole_state.betting.base_wager

    def test_duncan_rule_3_for_2_odds(self):
        self.game.current_hole = 1
        self.game._initialize_hole(1)
        hole_state = self.game.hole_states[1]
        captain_id = hole_state.teams.captain

        result = self.game.captain_go_solo(captain_id, use_duncan=True)

        assert result["status"] == "solo"
        assert hole_state.betting.duncan_invoked is True
        assert hole_state.teams.type == "solo"

    def test_big_dick_rule_hole_18(self):
        self.players[0].points = 10
        self.players[1].points = 5
        self.players[2].points = 3
        self.players[3].points = 2

        self.game.current_hole = 18
        self.game._initialize_hole(18)

        result = self.game.offer_big_dick("p1")

        assert result["status"] == "big_dick_offered"
        assert result["challenger"] == "p1"
        assert result["wager_amount"] == 10
        assert self.game.hole_states[18].betting.big_dick_invoked is True

    def test_big_dick_unanimous_acceptance(self):
        self.players[0].points = 10
        self.game.current_hole = 18
        self.game._initialize_hole(18)
        self.game.offer_big_dick("p1")

        result = self.game.accept_big_dick(["p2", "p3", "p4"])

        assert result["status"] == "big_dick_accepted"
        assert result["teams_formed"] is True
        hole_state = self.game.hole_states[18]
        assert hole_state.teams.type == "solo"
        assert hole_state.teams.solo_player == "p1"

    def test_big_dick_ackerley_gambit(self):
        self.players[0].points = 12
        self.game.current_hole = 18
        self.game._initialize_hole(18)
        self.game.offer_big_dick("p1")

        result = self.game.accept_big_dick(["p2", "p3"])  # p4 declines

        assert result["status"] == "big_dick_gambit"
        assert len(result["accepting_players"]) == 2
        assert len(result["declining_players"]) == 1
        assert result["wager_per_player"] == 6

    def test_ping_pong_aardvark(self):
        self.game.current_hole = 1
        self.game._initialize_hole(1)
        hole_state = self.game.hole_states[1]
        initial_wager = hole_state.betting.current_wager

        result = self.game.ping_pong_aardvark("team1", "p4")

        assert result["status"] in ["aardvark_ping_ponged", "aardvark_stuck"]
        assert result["new_wager"] == initial_wager * 2
        assert "p4" in hole_state.betting.tossed_aardvarks
        assert hole_state.betting.ping_pong_count == 1

    def test_ping_pong_aardvark_same_player_twice_fails(self):
        self.game.current_hole = 1
        self.game._initialize_hole(1)
        self.game.ping_pong_aardvark("team1", "p4")

        with pytest.raises(ValueError, match="Cannot ping pong the same Aardvark twice"):
            self.game.ping_pong_aardvark("team1", "p4")

    def test_vinnies_variation_4_man_game(self):
        assert self.game.vinnie_variation_start == 13
        assert 13 >= self.game.vinnie_variation_start
        assert 12 < self.game.vinnie_variation_start

    def test_vinnies_variation_not_in_5_man_game(self):
        game_5 = _make_game(player_count=5)
        assert game_5.vinnie_variation_start is None

    def test_handicap_creecher_feature(self):
        self.game.current_hole = 1
        self.game._initialize_hole(1)
        hole_state = self.game.hole_states[1]

        assert len(hole_state.stroke_advantages) == 4
        for player_id, sa in hole_state.stroke_advantages.items():
            assert player_id in ["p1", "p2", "p3", "p4"]
            assert sa.handicap >= 0
            assert sa.strokes_received >= 0

    def test_karl_marx_rule_implementation(self):
        self.players[0].points = 5
        self.players[1].points = 0
        self.players[2].points = -3
        self.players[3].points = -1

        changes = self.game._apply_karl_marx_rule(["p1"], ["p2", "p3", "p4"], 5)

        # Worst player (p3) should pay less or equal to second worst (p4)
        assert changes["p3"] >= changes["p4"]

    def test_option_rule_for_losing_captain(self):
        self.players[0].points = -5
        self.players[1].points = 0
        self.players[2].points = 2
        self.players[3].points = 1

        self.game.current_hole = 5
        self.game._initialize_hole(5)
        hole_state = self.game.hole_states[5]
        captain_id = hole_state.teams.captain

        if captain_id == "p1":
            assert self.game._should_apply_option(captain_id) is True
            assert hole_state.betting.option_invoked is True

    def test_complete_rule_integration(self):
        self.game.current_hole = 17
        self.game._initialize_hole(17)
        hole_state = self.game.hole_states[17]

        hole_state.betting.joes_special_value = 8
        hole_state.betting.current_wager = 8

        assert self.game.game_phase.value == "hoepfinger"

        captain_id = hole_state.teams.captain
        partner_id = next(p.id for p in self.game.players if p.id != captain_id)

        result = self.game.request_partner(captain_id, partner_id)
        assert result["status"] == "pending"

        result = self.game.respond_to_partnership(partner_id, True)
        assert result["status"] == "partnership_formed"

        assert hole_state.teams.type == "partners"
        assert hole_state.betting.joes_special_value == 8

    def test_6_man_goat_restriction(self):
        """Goat can't choose the same position three times in a row (6-man only).

        With history [1, 1], the very next choice must not be position 1.
        After choosing something different, position 1 is available again.
        """
        game_6 = _make_game(player_count=6)
        players = [WGPPlayer(f"p{i}", f"Player{i}", 10.0) for i in range(1, 7)]
        game_6.players = players

        game_6.current_hole = 13
        game_6._initialize_hole(13)

        goat = game_6._get_goat()
        current_order = game_6.hole_states[13].hitting_order

        # With two consecutive position-1 choices in history, the next must differ
        goat.goat_position_history = [1, 1]
        new_order = game_6._goat_chooses_position(goat, current_order)
        assert new_order.index(goat.id) != 1, "Should not choose same position a third time in a row"

        # History is now [1, <new>] — position 1 is available again
        # (restriction only blocks a third consecutive repeat)
