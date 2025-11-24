"""
Comprehensive tests for the Creecher Feature (half-stroke handicapping).

The Creecher Feature is a Wolf-Goat-Pig house rule that provides more granular
handicapping through the use of half strokes.

Official Rules:
1. Players with net handicap <= 6: Play all their handicap holes at half strokes.
2. Players with net handicap > 6 and <= 18: Play their easiest 6 handicap holes
   at half strokes, and the rest at full strokes.
3. Players with net handicap > 18:
   - Play holes 13-18 at half stroke (easiest 6 of base 18).
   - Play holes 1-12 at full stroke.
   - Receive an additional 1/2 stroke on two holes for every 1 stroke > 18.
     (These extra half strokes wrap around starting from the hardest holes).

IMPORTANT: In match play, strokes are calculated relative to the lowest handicap
player. Use calculate_net_handicaps() first to get relative handicaps, then pass
those to calculate_strokes_received_with_creecher().
"""

import pytest
from app.validators import HandicapValidator, HandicapValidationError


class TestNetHandicapCalculation:
    """Test calculation of net handicaps relative to lowest player."""

    def test_net_handicaps_basic(self):
        """Test basic net handicap calculation."""
        player_handicaps = {
            "player1": 5.0,
            "player2": 10.0,
            "player3": 15.0,
            "player4": 20.0
        }

        net_handicaps = HandicapValidator.calculate_net_handicaps(player_handicaps)

        assert net_handicaps["player1"] == 0.0  # Lowest gets 0
        assert net_handicaps["player2"] == 5.0  # 10 - 5
        assert net_handicaps["player3"] == 10.0  # 15 - 5
        assert net_handicaps["player4"] == 15.0  # 20 - 5

    def test_net_handicaps_with_equal_lowest(self):
        """Test when multiple players have the same lowest handicap."""
        player_handicaps = {
            "player1": 10.0,
            "player2": 10.0,
            "player3": 15.0
        }

        net_handicaps = HandicapValidator.calculate_net_handicaps(player_handicaps)

        assert net_handicaps["player1"] == 0.0
        assert net_handicaps["player2"] == 0.0
        assert net_handicaps["player3"] == 5.0

    def test_net_handicaps_all_equal(self):
        """Test when all players have the same handicap."""
        player_handicaps = {
            "player1": 15.0,
            "player2": 15.0,
            "player3": 15.0
        }

        net_handicaps = HandicapValidator.calculate_net_handicaps(player_handicaps)

        assert net_handicaps["player1"] == 0.0
        assert net_handicaps["player2"] == 0.0
        assert net_handicaps["player3"] == 0.0

    def test_net_handicaps_with_fractional(self):
        """Test net handicap calculation with fractional handicaps."""
        player_handicaps = {
            "player1": 5.5,
            "player2": 10.5,
            "player3": 15.5
        }

        net_handicaps = HandicapValidator.calculate_net_handicaps(player_handicaps)

        assert net_handicaps["player1"] == 0.0
        assert net_handicaps["player2"] == 5.0  # 10.5 - 5.5
        assert net_handicaps["player3"] == 10.0  # 15.5 - 5.5

    def test_net_handicaps_empty_dict(self):
        """Test with empty player dictionary."""
        net_handicaps = HandicapValidator.calculate_net_handicaps({})
        assert net_handicaps == {}


class TestCreecherFeatureLowHandicaps:
    """Test Creecher Feature for handicaps <= 6."""

    def test_handicap_6_all_half_strokes(self):
        """Test that handicap 6 gets all half strokes."""
        # H=6: Holes 1-6 get 0.5.
        for hole in range(1, 7):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(6.0, hole)
            assert strokes == 0.5, f"Hole {hole} should get 0.5 strokes"
        
        for hole in range(7, 19):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(6.0, hole)
            assert strokes == 0.0

    def test_handicap_4_all_half_strokes(self):
        """Test that handicap 4 gets all half strokes."""
        # H=4: Holes 1-4 get 0.5.
        for hole in range(1, 5):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(4.0, hole)
            assert strokes == 0.5
        
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(4.0, 5)
        assert strokes == 0.0


class TestCreecherFeatureMidHandicaps:
    """Test Creecher Feature for handicaps > 6 and <= 18."""

    def test_handicap_10_split_strokes(self):
        """Test handicap 10 (Example 2 from rules)."""
        # H=10:
        # Allocated: 1-10.
        # Easiest 6 (5-10) get 0.5.
        # Hardest 4 (1-4) get 1.0.
        
        # Hardest 4
        for hole in range(1, 5):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.0, hole)
            assert strokes == 1.0, f"Hole {hole} should get 1.0"
            
        # Easiest 6
        for hole in range(5, 11):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.0, hole)
            assert strokes == 0.5, f"Hole {hole} should get 0.5"
            
        # Unallocated
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.0, 11)
        assert strokes == 0.0

    def test_handicap_18_base_allocation(self):
        """Test handicap 18 (Example 1 base)."""
        # H=18:
        # Allocated: 1-18.
        # Easiest 6 (13-18) get 0.5.
        # Hardest 12 (1-12) get 1.0.
        
        for hole in range(1, 13):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(18.0, hole)
            assert strokes == 1.0
            
        for hole in range(13, 19):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(18.0, hole)
            assert strokes == 0.5

    def test_handicap_7_transition(self):
        """Test handicap 7 (just above 6)."""
        # H=7:
        # Allocated: 1-7.
        # Easiest 6 (2-7) get 0.5.
        # Hardest 1 (1) gets 1.0.
        
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(7.0, 1)
        assert strokes == 1.0
        
        for hole in range(2, 8):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(7.0, hole)
            assert strokes == 0.5


class TestCreecherFeatureHighHandicaps:
    """Test Creecher Feature for handicaps > 18."""

    def test_handicap_20_extra_strokes(self):
        """Test handicap 20 (2 extra strokes)."""
        # H=20 (2 extra):
        # Base: 1-12 (1.0), 13-18 (0.5).
        # Extra: 2 * 2 = 4 half strokes.
        # Distributed to 1, 2, 3, 4.
        # Result:
        # 1-4: 1.0 + 0.5 = 1.5.
        # 5-12: 1.0.
        # 13-18: 0.5.
        
        for hole in range(1, 5):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(20.0, hole)
            assert strokes == 1.5
            
        for hole in range(5, 13):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(20.0, hole)
            assert strokes == 1.0
            
        for hole in range(13, 19):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(20.0, hole)
            assert strokes == 0.5

    def test_handicap_30_high_extras(self):
        """Test handicap 30 (12 extra strokes)."""
        # H=30 (12 extra):
        # Base: 1-12 (1.0), 13-18 (0.5).
        # Extra: 12 * 2 = 24 half strokes.
        # Pass 1 (18 halves): All holes get +0.5.
        # Pass 2 (6 halves): Holes 1-6 get +0.5.
        
        # Result:
        # 1-6: 1.0 (Base) + 0.5 (P1) + 0.5 (P2) = 2.0.
        # 7-12: 1.0 (Base) + 0.5 (P1) = 1.5.
        # 13-18: 0.5 (Base) + 0.5 (P1) = 1.0.
        
        for hole in range(1, 7):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(30.0, hole)
            assert strokes == 2.0
            
        for hole in range(7, 13):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(30.0, hole)
            assert strokes == 1.5
            
        for hole in range(13, 19):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(30.0, hole)
            assert strokes == 1.0


class TestFractionalHandicaps:
    """Test fractional handicap handling."""

    def test_handicap_10_5(self):
        """Test 10.5 handicap."""
        # H=10.5:
        # Full 10: 1-4 (1.0), 5-10 (0.5).
        # Fractional: 0.5 on next hole (11).
        
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.5, 11)
        assert strokes == 0.5
        
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.5, 10)
        assert strokes == 0.5  # From base 10 allocation

    def test_handicap_19_5(self):
        """Test 19.5 handicap."""
        # H=19.5:
        # Full 19 (1 extra):
        # Base 18.
        # Extra 1 -> 2 halves (Holes 1, 2).
        # Fractional: Next hole in sequence -> Hole 3.
        
        # Hole 1: 1.0 + 0.5 = 1.5
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(19.5, 1)
        assert strokes == 1.5
        
        # Hole 2: 1.0 + 0.5 = 1.5
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(19.5, 2)
        assert strokes == 1.5
        
        # Hole 3: 1.0 (Base) + 0.5 (Fractional) = 1.5
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(19.5, 3)
        assert strokes == 1.5
        
        # Hole 4: 1.0 (Base)
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(19.5, 4)
        assert strokes == 1.0


class TestNetScoreCalculation:
    """Test net score calculation with half strokes."""

    def test_net_score_with_half_stroke(self):
        """Test that net scores correctly handle half strokes."""
        net = HandicapValidator.calculate_net_score(5, 0.5)
        assert net == 4.5

    def test_net_score_with_full_stroke(self):
        """Test that net scores work with full strokes."""
        net = HandicapValidator.calculate_net_score(5, 1.0)
        assert net == 4.0


class TestValidation:
    """Test validation and error handling."""

    def test_invalid_handicap_raises_error(self):
        """Test that invalid handicaps raise errors."""
        with pytest.raises(HandicapValidationError):
            HandicapValidator.calculate_strokes_received_with_creecher(-1.0, 10)

    def test_invalid_stroke_index_raises_error(self):
        """Test that invalid stroke indexes raise errors."""
        with pytest.raises(HandicapValidationError):
            HandicapValidator.calculate_strokes_received_with_creecher(10.5, 19)


    def test_high_handicapper_on_easiest_hole(self):
        """Test high handicapper gets proper strokes on easiest hole."""
        # 25 handicap on easiest hole (stroke index 18)
        # Base: 13-18 get 0.5.
        # Extra: 25-18 = 7 strokes -> 14 half strokes.
        # Distributed to holes 1-14.
        # Hole 18 does NOT get an extra half stroke.
        # So it stays at 0.5.
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(25.0, 18)
        assert strokes == 0.5
