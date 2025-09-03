"""
Unit tests for Post-Hole Analytics Module
Tests each function and method in isolation with mock data
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import List, Dict, Any

# Import the module to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.post_hole_analytics import (
    PostHoleAnalyzer,
    PostHoleAnalytics,
    DecisionQuality,
    DecisionPoint,
    PartnershipAnalysis,
    BettingAnalysis,
    ShotAnalysis,
    KeyMoment,
    InsightCategory
)


class TestDecisionPoint:
    """Test DecisionPoint dataclass and related functionality"""
    
    def test_decision_point_creation(self):
        """Test creating a DecisionPoint with all fields"""
        dp = DecisionPoint(
            decision_type="partnership_offer",
            player_id="p1",
            timestamp="2024-01-01T12:00:00",
            options_available=["accept", "decline"],
            decision_made="accept",
            outcome="won",
            quarters_impact=2,
            quality=DecisionQuality.GOOD,
            explanation="Good partnership choice"
        )
        
        assert dp.decision_type == "partnership_offer"
        assert dp.player_id == "p1"
        assert dp.outcome == "won"
        assert dp.quarters_impact == 2
        assert dp.quality == DecisionQuality.GOOD
    
    def test_decision_quality_enum(self):
        """Test DecisionQuality enum values"""
        assert DecisionQuality.EXCELLENT.value == "excellent"
        assert DecisionQuality.POOR.value == "poor"
        assert DecisionQuality.TERRIBLE.value == "terrible"


class TestPartnershipAnalysis:
    """Test PartnershipAnalysis functionality"""
    
    def test_partnership_formed_analysis(self):
        """Test analysis when partnership is formed"""
        pa = PartnershipAnalysis(
            partnership_formed=True,
            captain_id="p1",
            partner_id="p2",
            timing="after_1st_shot",
            success=True,
            chemistry_rating=0.85,
            alternative_partners=[{"id": "p3", "chemistry": 0.6}],
            optimal_choice=True,
            explanation="Strong partnership with compatible player"
        )
        
        assert pa.partnership_formed is True
        assert pa.partner_id == "p2"
        assert pa.chemistry_rating == 0.85
        assert pa.optimal_choice is True
    
    def test_solo_analysis(self):
        """Test analysis when captain goes solo"""
        pa = PartnershipAnalysis(
            partnership_formed=False,
            captain_id="p1",
            partner_id=None,
            timing="went_solo",
            success=False,
            chemistry_rating=0.0,
            alternative_partners=[],
            optimal_choice=False,
            explanation="Solo play was risky given the situation"
        )
        
        assert pa.partnership_formed is False
        assert pa.partner_id is None
        assert pa.timing == "went_solo"
        assert pa.chemistry_rating == 0.0


class TestBettingAnalysis:
    """Test BettingAnalysis functionality"""
    
    def test_aggressive_betting(self):
        """Test analysis of aggressive betting behavior"""
        ba = BettingAnalysis(
            doubles_offered=3,
            doubles_accepted=2,
            doubles_declined=1,
            duncan_used=True,
            timing_quality="perfect",
            aggressive_rating=0.9,
            missed_opportunities=["After excellent tee shot"],
            costly_mistakes=["Doubled when behind"],
            net_quarter_impact=4
        )
        
        assert ba.doubles_offered == 3
        assert ba.duncan_used is True
        assert ba.aggressive_rating == 0.9
        assert ba.timing_quality == "perfect"
        assert len(ba.missed_opportunities) == 1
    
    def test_conservative_betting(self):
        """Test analysis of conservative betting"""
        ba = BettingAnalysis(
            doubles_offered=0,
            doubles_accepted=0,
            doubles_declined=0,
            duncan_used=False,
            timing_quality="poor",
            aggressive_rating=0.1,
            missed_opportunities=["Multiple excellent shots"],
            costly_mistakes=[],
            net_quarter_impact=-2
        )
        
        assert ba.aggressive_rating == 0.1
        assert ba.duncan_used is False
        assert len(ba.costly_mistakes) == 0


class TestShotAnalysis:
    """Test ShotAnalysis functionality"""
    
    def test_shot_quality_distribution(self):
        """Test shot quality distribution analysis"""
        sa = ShotAnalysis(
            total_shots=20,
            shot_quality_distribution={
                "excellent": 2,
                "good": 5,
                "average": 8,
                "poor": 3,
                "terrible": 2
            },
            clutch_shots=[
                {"player": "p1", "quality": "excellent", "pressure": "high"}
            ],
            worst_shot={"player": "p1", "quality": "terrible", "distance": 50},
            best_shot={"player": "p1", "quality": "excellent", "distance": 5},
            pressure_performance=0.75
        )
        
        assert sa.total_shots == 20
        assert sa.shot_quality_distribution["excellent"] == 2
        assert sa.shot_quality_distribution["average"] == 8
        assert sa.pressure_performance == 0.75
        assert len(sa.clutch_shots) == 1


class TestPostHoleAnalyzer:
    """Test PostHoleAnalyzer methods in isolation"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        return PostHoleAnalyzer()
    
    @pytest.fixture
    def mock_hole_state(self):
        """Create mock hole state"""
        hole_state = Mock()
        hole_state.hole_number = 1
        hole_state.hole_par = 4
        hole_state.hole_yardage = 400
        hole_state.hole_complete = True
        hole_state.teams = Mock()
        hole_state.teams.type = "partners"
        hole_state.teams.captain = "p1"
        hole_state.teams.team1 = ["p1", "p2"]
        hole_state.teams.team2 = ["p3", "p4"]
        hole_state.scores = {"p1": 4, "p2": 5, "p3": 4, "p4": 6}
        hole_state.betting = Mock()
        hole_state.betting.current_wager = 2
        hole_state.betting.base_wager = 1
        hole_state.betting.duncan_invoked = False
        hole_state.betting.doubled = False
        return hole_state
    
    @pytest.fixture
    def mock_timeline_events(self):
        """Create mock timeline events"""
        events = []
        
        # Hole start event
        event1 = Mock()
        event1.type = "hole_start"
        event1.timestamp = datetime(2024, 1, 1, 12, 0, 0)
        event1.player_id = "p1"
        event1.description = "Hole 1 begins"
        event1.details = {"hole_number": 1}
        events.append(event1)
        
        # Shot event
        event2 = Mock()
        event2.type = "shot"
        event2.timestamp = datetime(2024, 1, 1, 12, 1, 0)
        event2.player_id = "p1"
        event2.details = {"shot_quality": "good", "distance_to_pin": 150}
        events.append(event2)
        
        # Partnership event
        event3 = Mock()
        event3.type = "partnership_formed"
        event3.timestamp = datetime(2024, 1, 1, 12, 2, 0)
        event3.player_id = "p1"
        event3.details = {"partner_id": "p2", "timing": "after_1st_shot"}
        events.append(event3)
        
        return events
    
    def test_determine_winner_partnership(self, analyzer, mock_hole_state):
        """Test determining winner for partnership game"""
        winner, quarters = analyzer._determine_winner(mock_hole_state)
        
        # Team 1 and Team 2 both have best score of 4, so it's a tie
        assert winner == "tie"
        assert quarters == 0
    
    def test_determine_winner_solo(self, analyzer):
        """Test determining winner for solo play"""
        hole_state = Mock()
        hole_state.teams = Mock()
        hole_state.teams.type = "solo"
        hole_state.teams.solo_player = "p1"
        hole_state.teams.opponents = ["p2", "p3", "p4"]
        hole_state.scores = {"p1": 3, "p2": 4, "p3": 5, "p4": 4}
        hole_state.betting = Mock()
        hole_state.betting.current_wager = 2
        
        winner, quarters = analyzer._determine_winner(hole_state)
        
        assert winner == "solo_player"
        assert quarters == 6  # 2 quarters × 3 opponents
    
    def test_evaluate_decision_quality(self, analyzer, mock_hole_state):
        """Test evaluating quality of a decision"""
        event = Mock()
        event.type = "partnership_request"
        event.details = {"outcome": "won"}
        
        quality, explanation = analyzer._evaluate_decision_quality(event, mock_hole_state)
        
        assert quality == DecisionQuality.GOOD
        assert "winning" in explanation.lower()
    
    def test_calculate_performance_score(self, analyzer):
        """Test overall performance score calculation"""
        decisions = [
            Mock(quality=DecisionQuality.EXCELLENT),
            Mock(quality=DecisionQuality.GOOD),
            Mock(quality=DecisionQuality.POOR)
        ]
        
        partnership = Mock()
        partnership.success = True
        
        betting = Mock()
        
        shots = Mock()
        shots.pressure_performance = 0.8
        
        score = analyzer._calculate_performance_score(decisions, partnership, betting, shots)
        
        assert 0 <= score <= 100
        assert score > 50  # Should be above average due to good decisions
    
    def test_calculate_decision_score(self, analyzer):
        """Test decision-making score calculation"""
        decisions = [
            Mock(quality=DecisionQuality.EXCELLENT),
            Mock(quality=DecisionQuality.GOOD),
            Mock(quality=DecisionQuality.NEUTRAL)
        ]
        
        score = analyzer._calculate_decision_score(decisions)
        
        # (100 + 75 + 50) / 3 = 75
        assert score == 75.0
    
    def test_calculate_risk_score(self, analyzer):
        """Test risk management score calculation"""
        betting = Mock()
        betting.aggressive_rating = 0.8
        betting.net_quarter_impact = 3
        
        partnership = Mock()
        
        score = analyzer._calculate_risk_score(betting, partnership)
        
        assert 0 <= score <= 100
        assert score > 50  # Good risk management (aggressive and won)
    
    def test_shot_quality_value(self, analyzer):
        """Test converting shot quality to numeric value"""
        assert analyzer._shot_quality_value("excellent") == 5
        assert analyzer._shot_quality_value("good") == 4
        assert analyzer._shot_quality_value("average") == 3
        assert analyzer._shot_quality_value("poor") == 2
        assert analyzer._shot_quality_value("terrible") == 1
        assert analyzer._shot_quality_value("unknown") == 3  # Default
    
    def test_calculate_pressure_performance(self, analyzer):
        """Test pressure performance calculation"""
        clutch_shots = [
            {"quality": "excellent"},
            {"quality": "good"},
            {"quality": "poor"},
            {"quality": "terrible"}
        ]
        
        performance = analyzer._calculate_pressure_performance(clutch_shots)
        
        # 2 good shots out of 4 = 0.5
        assert performance == 0.5
    
    def test_calculate_pressure_performance_empty(self, analyzer):
        """Test pressure performance with no clutch shots"""
        performance = analyzer._calculate_pressure_performance([])
        assert performance == 0.5  # Default when no clutch shots
    
    def test_is_key_moment(self, analyzer):
        """Test identifying key moments"""
        event1 = Mock()
        event1.type = "double_accepted"
        assert analyzer._is_key_moment(event1) is True
        
        event2 = Mock()
        event2.type = "shot"
        event2.details = {"holed": True}
        assert analyzer._is_key_moment(event2) is True
        
        event3 = Mock()
        event3.type = "shot"
        event3.details = {"holed": False}
        assert analyzer._is_key_moment(event3) is False
    
    def test_determine_impact_level(self, analyzer):
        """Test determining impact level of events"""
        event1 = Mock()
        event1.details = {"quarters_impact": 5}
        assert analyzer._determine_impact_level(event1) == "game_changing"
        
        event2 = Mock()
        event2.details = {"quarters_impact": 2}
        assert analyzer._determine_impact_level(event2) == "significant"
        
        event3 = Mock()
        event3.details = {"quarters_impact": 1}
        assert analyzer._determine_impact_level(event3) == "minor"
    
    def test_identify_biggest_mistake(self, analyzer):
        """Test identifying the biggest mistake"""
        decisions = [
            Mock(
                quality=DecisionQuality.POOR,
                quarters_impact=-3,
                decision_type="double_declined",
                explanation="Should have accepted"
            ),
            Mock(
                quality=DecisionQuality.TERRIBLE,
                quarters_impact=-5,
                decision_type="partnership",
                explanation="Wrong partner choice"
            )
        ]
        
        mistake = analyzer._identify_biggest_mistake(decisions)
        
        assert "partnership" in mistake
        assert "Wrong partner" in mistake
    
    def test_identify_best_decision(self, analyzer):
        """Test identifying the best decision"""
        decisions = [
            Mock(
                quality=DecisionQuality.EXCELLENT,
                quarters_impact=4,
                decision_type="double_offer",
                explanation="Perfect timing"
            ),
            Mock(
                quality=DecisionQuality.GOOD,
                quarters_impact=2,
                decision_type="partnership",
                explanation="Good partner"
            )
        ]
        
        best = analyzer._identify_best_decision(decisions)
        
        assert "double_offer" in best
        assert "Perfect timing" in best
    
    def test_calculate_aggression_rating(self, analyzer):
        """Test betting aggression calculation"""
        # No doubles offered
        rating1 = analyzer._calculate_aggression_rating(0, 0)
        assert rating1 == 0.3
        
        # Some doubles
        rating2 = analyzer._calculate_aggression_rating(2, 1)
        assert rating2 == 0.75  # (2 + 1) / 4
        
        # Max aggression
        rating3 = analyzer._calculate_aggression_rating(5, 3)
        assert rating3 == 1.0  # Capped at 1.0
    
    def test_analyze_decisions(self, analyzer, mock_hole_state):
        """Test analyzing decision points from timeline"""
        # Create timeline events that will be recognized as decisions
        events = []
        
        # Add a partnership request event (recognized decision type)
        event1 = Mock()
        event1.type = "partnership_request"
        event1.timestamp = datetime(2024, 1, 1, 12, 0, 0)
        event1.player_id = "p1"
        event1.details = {
            "options": ["accept", "decline"],
            "decision": "accept",
            "outcome": "won",
            "quarters_impact": 2
        }
        events.append(event1)
        
        # Add a double offer event
        event2 = Mock()
        event2.type = "double_offer"
        event2.timestamp = datetime(2024, 1, 1, 12, 5, 0)
        event2.player_id = "p2"
        event2.details = {
            "options": ["offer", "pass"],
            "decision": "offer",
            "outcome": "accepted",
            "quarters_impact": 1
        }
        events.append(event2)
        
        decisions = analyzer._analyze_decisions(mock_hole_state, events)
        
        # Should find the partnership and double events
        assert len(decisions) == 2
        
        # Check structure
        for decision in decisions:
            assert hasattr(decision, 'decision_type')
            assert hasattr(decision, 'player_id')
            assert hasattr(decision, 'quality')
            assert hasattr(decision, 'explanation')
    
    def test_generate_learning_points(self, analyzer):
        """Test generating learning points"""
        decisions = [
            Mock(
                quality=DecisionQuality.POOR,
                decision_type="partnership"
            )
        ]
        
        partnership = Mock()
        partnership.success = False
        
        betting = Mock()
        betting.missed_opportunities = ["Double after excellent shot"]
        
        key_moments = []
        
        points = analyzer._generate_learning_points(
            decisions, partnership, betting, key_moments
        )
        
        assert len(points) > 0
        assert any("partnership" in p.lower() for p in points)
    
    def test_generate_tips(self, analyzer):
        """Test generating improvement tips"""
        decisions = [
            Mock(quality=DecisionQuality.POOR),
            Mock(quality=DecisionQuality.POOR)
        ]
        
        partnership = Mock()
        partnership.chemistry_rating = 0.3
        
        betting = Mock()
        
        shots = Mock()
        shots.shot_quality_distribution = {
            "poor": 5,
            "terrible": 3,
            "average": 2
        }
        
        tips = analyzer._generate_tips(decisions, partnership, betting, shots)
        
        assert len(tips) > 0
        assert any("consistency" in t.lower() or "decision" in t.lower() for t in tips)
    
    def test_full_analyze_hole(self, analyzer, mock_hole_state):
        """Test complete hole analysis"""
        game_state = {"current_hole": 1}
        
        # Create mock timeline events for analysis
        events = []
        event = Mock()
        event.type = "shot"
        event.timestamp = datetime.now()
        event.player_id = "p1"
        event.details = {"shot_quality": "good", "distance_to_pin": 150}
        events.append(event)
        
        analytics = analyzer.analyze_hole(
            mock_hole_state,
            game_state,
            events
        )
        
        # Verify structure
        assert isinstance(analytics, PostHoleAnalytics)
        assert analytics.hole_number == 1
        assert analytics.hole_par == 4
        assert analytics.hole_yardage == 400
        assert analytics.overall_performance >= 0
        assert analytics.overall_performance <= 100
        assert analytics.decision_making_score >= 0
        assert analytics.decision_making_score <= 100
        assert analytics.risk_management_score >= 0
        assert analytics.risk_management_score <= 100
        
        # Check for required components
        assert analytics.betting_analysis is not None
        assert analytics.shot_analysis is not None
        assert isinstance(analytics.learning_points, list)
        assert isinstance(analytics.tips_for_improvement, list)


class TestIntegration:
    """Integration tests for the complete analytics flow"""
    
    def test_complete_analytics_generation(self):
        """Test generating analytics for a realistic hole"""
        analyzer = PostHoleAnalyzer()
        
        # Create realistic hole state
        hole_state = Mock()
        hole_state.hole_number = 13  # Vinnie's Variation hole
        hole_state.hole_par = 4
        hole_state.hole_yardage = 310
        hole_state.hole_complete = True
        hole_state.teams = Mock(type="solo", captain="p1", solo_player="p1", opponents=["p2", "p3", "p4"])
        hole_state.scores = {"p1": 3, "p2": 4, "p3": 4, "p4": 5}
        hole_state.betting = Mock(current_wager=2, base_wager=2, duncan_invoked=True, doubled=False)
        
        # Create realistic timeline
        events = []
        for i in range(5):
            event = Mock()
            event.type = "shot"
            event.timestamp = datetime.now()
            event.player_id = f"p{(i % 4) + 1}"
            event.details = {
                "shot_quality": ["excellent", "good", "average", "poor", "terrible"][i % 5],
                "distance_to_pin": 200 - (i * 40),
                "pressure_level": "high" if i > 2 else "normal"
            }
            events.append(event)
        
        game_state = {"current_hole": 13, "game_phase": "vinnie_variation"}
        
        # Generate analytics
        analytics = analyzer.analyze_hole(hole_state, game_state, events)
        
        # Validate comprehensive output
        assert analytics.hole_number == 13
        assert analytics.winner == "solo_player"
        assert analytics.quarters_exchanged > 0
        assert len(analytics.decision_points) >= 0
        assert analytics.overall_performance > 0
        
        # Vinnie's Variation should be noted
        assert analytics.betting_analysis.duncan_used is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])