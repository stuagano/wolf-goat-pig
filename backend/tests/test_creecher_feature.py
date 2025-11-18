"""
Comprehensive tests for the Creecher Feature (half-stroke handicapping).

The Creecher Feature is a Wolf-Goat-Pig house rule that provides more granular
handicapping through the use of half strokes.

Rule Summary:
1. Players with fractional handicaps (e.g., 10.5) get half strokes
2. Half strokes awarded on specific holes based on stroke index
3. For handicaps >18, additional half strokes on easiest 6 holes
"""

import pytest
from app.validators import HandicapValidator, HandicapValidationError


class TestCreecherFeatureBasics:
    """Test basic half-stroke functionality."""

    def test_fractional_handicap_half_stroke(self):
        """Test that fractional handicaps award half strokes correctly."""
        # Player with 10.5 handicap
        # Should get full stroke on holes 1-10
        # Should get half stroke on hole 11
        # Should get no stroke on holes 12-18

        # Full stroke on hole 10
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.5, 10)
        assert strokes == 1.0

        # Half stroke on hole 11 (fractional part)
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.5, 11)
        assert strokes == 0.5

        # No stroke on hole 12
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.5, 12)
        assert strokes == 0.0

    def test_integer_handicap_no_half_strokes(self):
        """Test that integer handicaps don't get half strokes from fractional rule."""
        # Player with exactly 10 handicap
        # Should get full stroke on holes 1-10
        # Should get no stroke on holes 11-18

        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.0, 10)
        assert strokes == 1.0

        # No half stroke on hole 11 (no fractional part)
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.0, 11)
        assert strokes == 0.0

    def test_low_fractional_part_no_half_stroke(self):
        """Test that fractional parts <0.5 don't trigger half strokes."""
        # Player with 10.4 handicap (fractional < 0.5)

        # Full stroke on hole 10
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.4, 10)
        assert strokes == 1.0

        # NO half stroke on hole 11 (fractional 0.4 < 0.5)
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(10.4, 11)
        assert strokes == 0.0


class TestCreecherFeatureHighHandicaps:
    """Test Creecher Feature for handicaps >18."""

    def test_handicap_20_gets_creecher_half_strokes(self):
        """Test that handicap >18 gets half strokes on easiest holes."""
        # Player with 20 handicap
        # Gets 2 extra half strokes on easiest holes (18, 17)

        # Easiest hole (stroke index 18) gets half stroke
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(20.0, 18)
        assert strokes == 0.5

        # 2nd easiest (stroke index 17) gets half stroke
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(20.0, 17)
        assert strokes == 0.5

        # 3rd easiest (stroke index 16) gets NO extra half stroke
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(20.0, 16)
        assert strokes == 1.0  # Regular full stroke

    def test_handicap_24_gets_six_creecher_half_strokes(self):
        """Test that handicap 24 gets maximum 6 half strokes on easiest holes."""
        # Player with 24 handicap
        # Gets 6 extra half strokes on all 6 easiest holes (18, 17, 16, 15, 14, 13)

        easiest_holes = [18, 17, 16, 15, 14, 13]
        for hole in easiest_holes:
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(24.0, hole)
            assert strokes == 0.5, f"Hole {hole} should get half stroke"

        # Hole 12 (7th easiest) gets regular full stroke, not half
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(24.0, 12)
        assert strokes == 1.0

    def test_handicap_30_max_six_creecher_half_strokes(self):
        """Test that even high handicaps only get max 6 Creecher half strokes."""
        # Player with 30 handicap
        # Still only gets 6 half strokes (cap at 6)

        # All 6 easiest holes should get half strokes
        easiest_holes = [18, 17, 16, 15, 14, 13]
        for hole in easiest_holes:
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(30.0, hole)
            assert strokes == 0.5, f"Hole {hole} should get half stroke"

        # Harder holes get full strokes
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(30.0, 12)
        assert strokes == 1.0

    def test_handicap_18_no_creecher_bonus(self):
        """Test that exactly 18 handicap doesn't trigger Creecher feature."""
        # Player with exactly 18 handicap
        # Should NOT get Creecher half strokes (only for >18)

        # Easiest hole should NOT get Creecher half stroke
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(18.0, 18)
        assert strokes == 1.0  # Regular full stroke

        strokes = HandicapValidator.calculate_strokes_received_with_creecher(18.0, 17)
        assert strokes == 1.0


class TestNetScoreCalculation:
    """Test net score calculation with half strokes."""

    def test_net_score_with_half_stroke(self):
        """Test that net scores correctly handle half strokes."""
        # Gross 5, half stroke → net 4.5
        net = HandicapValidator.calculate_net_score(5, 0.5)
        assert net == 4.5

        # Gross 4, half stroke → net 3.5
        net = HandicapValidator.calculate_net_score(4, 0.5)
        assert net == 3.5

    def test_net_score_with_full_stroke(self):
        """Test that net scores work with full strokes."""
        net = HandicapValidator.calculate_net_score(5, 1.0)
        assert net == 4.0

        net = HandicapValidator.calculate_net_score(4, 1.0)
        assert net == 3.0

    def test_net_score_with_multiple_strokes(self):
        """Test net scores with multiple strokes including half."""
        # Gross 6, 1.5 strokes → net 4.5
        net = HandicapValidator.calculate_net_score(6, 1.5)
        assert net == 4.5

        # Gross 7, 2.0 strokes → net 5.0
        net = HandicapValidator.calculate_net_score(7, 2.0)
        assert net == 5.0

    def test_net_score_accepts_int_strokes(self):
        """Test backward compatibility with integer strokes."""
        net = HandicapValidator.calculate_net_score(5, 1)
        assert net == 4.0

        net = HandicapValidator.calculate_net_score(6, 2)
        assert net == 4.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_handicap(self):
        """Test that 0 handicap gets no strokes."""
        for hole in range(1, 19):
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(0.0, hole)
            assert strokes == 0.0

    def test_scratch_golfer_half_handicap(self):
        """Test very low fractional handicap (0.5)."""
        # 0.5 handicap should get half stroke on hardest hole
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(0.5, 1)
        assert strokes == 0.5

        strokes = HandicapValidator.calculate_strokes_received_with_creecher(0.5, 2)
        assert strokes == 0.0

    def test_maximum_handicap(self):
        """Test maximum allowed handicap (54)."""
        # 54 handicap gets full strokes everywhere plus 6 half strokes on easiest

        # Hardest hole gets full stroke
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(54.0, 1)
        assert strokes == 1.0

        # Easiest holes get Creecher half strokes
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(54.0, 18)
        assert strokes == 0.5

    def test_all_possible_fractional_handicaps(self):
        """Test common fractional handicaps."""
        fractional_handicaps = [5.5, 10.5, 15.5, 17.5]  # Use valid stroke indexes

        for hcp in fractional_handicaps:
            full_part = int(hcp)
            # Should get half stroke on hole = full_part + 1
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(hcp, full_part + 1)
            assert strokes == 0.5, f"Handicap {hcp} should get half stroke on hole {full_part + 1}"


class TestValidation:
    """Test validation and error handling."""

    def test_invalid_handicap_raises_error(self):
        """Test that invalid handicaps raise errors."""
        with pytest.raises(HandicapValidationError):
            HandicapValidator.calculate_strokes_received_with_creecher(-1.0, 10)

        with pytest.raises(HandicapValidationError):
            HandicapValidator.calculate_strokes_received_with_creecher(60.0, 10)

    def test_invalid_stroke_index_raises_error(self):
        """Test that invalid stroke indexes raise errors."""
        with pytest.raises(HandicapValidationError):
            HandicapValidator.calculate_strokes_received_with_creecher(10.5, 0)

        with pytest.raises(HandicapValidationError):
            HandicapValidator.calculate_strokes_received_with_creecher(10.5, 19)

    def test_validation_can_be_disabled(self):
        """Test that validation can be bypassed if needed."""
        # Should not raise error even with invalid values when validate=False
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(
            100.0, 1, validate=False
        )
        # Should still compute something (even if nonsensical)
        assert isinstance(strokes, float)


class TestRealWorldScenarios:
    """Test realistic game scenarios."""

    def test_typical_foursome_handicaps(self):
        """Test handicaps from a typical foursome."""
        handicaps = [8.0, 10.5, 15.0, 20.5]

        # Verify each player's strokes on hole with stroke index 10
        expected = {
            8.0: 0.0,   # No stroke (handicap < stroke index)
            10.5: 1.0,  # Full stroke (10 <= 10.5, so gets full stroke)
            15.0: 1.0,  # Full stroke
            20.5: 1.0   # Full stroke
        }

        for hcp, expected_strokes in expected.items():
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(hcp, 10)
            assert strokes == expected_strokes, f"Handicap {hcp} incorrect on hole 10"

    def test_high_handicapper_on_easiest_hole(self):
        """Test high handicapper gets proper strokes on easiest hole."""
        # 25 handicap on easiest hole (stroke index 18)
        # Should get Creecher half stroke (not full stroke)
        strokes = HandicapValidator.calculate_strokes_received_with_creecher(25.0, 18)
        assert strokes == 0.5

    def test_complete_18_hole_stroke_allocation(self):
        """Test complete stroke allocation for a player across all 18 holes."""
        handicap = 10.5

        expected_strokes = {
            1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0,
            6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0,
            11: 0.5,  # Half stroke from fractional
            12: 0.0, 13: 0.0, 14: 0.0, 15: 0.0,
            16: 0.0, 17: 0.0, 18: 0.0
        }

        for hole, expected in expected_strokes.items():
            strokes = HandicapValidator.calculate_strokes_received_with_creecher(handicap, hole)
            assert strokes == expected, f"Hole {hole} should get {expected} strokes, got {strokes}"

        # Verify total strokes = handicap
        total_strokes = sum(expected_strokes.values())
        assert total_strokes == handicap


class TestBackwardCompatibility:
    """Test that old method still works for non-Creecher use cases."""

    def test_old_method_returns_integers(self):
        """Test that old calculate_strokes_received returns integers."""
        strokes = HandicapValidator.calculate_strokes_received(10.5, 10)
        assert isinstance(strokes, int)
        assert strokes == 1

    def test_old_method_rounds_handicap(self):
        """Test that old method rounds fractional handicaps."""
        # Old method rounds 10.5 to 10 (banker's rounding - round half to even)
        strokes = HandicapValidator.calculate_strokes_received(10.5, 10)
        assert strokes == 1  # Gets stroke on hole 10 (10 >= 10)

    def test_new_method_preferred_for_creecher(self):
        """Verify new method gives different (correct) results for Creecher."""
        handicap = 10.5
        hole = 11

        old_strokes = HandicapValidator.calculate_strokes_received(handicap, hole)
        new_strokes = HandicapValidator.calculate_strokes_received_with_creecher(handicap, hole)

        # Old method rounds 10.5 to 10 (banker's rounding), 10 < 11, no stroke
        assert old_strokes == 0  # Old method rounds to 10, doesn't get stroke on hole 11
        assert new_strokes == 0.5  # New method gives half stroke (fractional 0.5)
        assert old_strokes != new_strokes  # Different results!
