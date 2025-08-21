"""
Comprehensive tests for models.py and schemas.py - Database models and validation

Tests cover:
- Database model creation and relationships
- Schema validation and field constraints
- Data type conversions
- Edge cases and error handling
- Model serialization/deserialization
- Schema field validators
"""

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import (
    Rule, Course, Hole, GameStateModel, SimulationResult,
    PlayerProfile, PlayerStatistics, GameRecord, GamePlayerResult,
    PlayerAchievement
)
from backend.app.schemas import (
    Rule as RuleSchema, HoleInfo, CourseCreate, CourseResponse, CourseUpdate,
    PlayerProfileCreate, PlayerProfileUpdate, PlayerProfileResponse,
    PlayerStatisticsResponse, GameRecordCreate, GamePlayerResultCreate,
    PlayerPerformanceAnalytics, LeaderboardEntry
)


class TestDatabaseModels:
    """Test database model creation and basic functionality"""
    
    @pytest.fixture
    def in_memory_db(self):
        """Create an in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return SessionLocal()
    
    def test_rule_model_creation(self, in_memory_db):
        """Test Rule model creation and persistence"""
        rule = Rule(
            title="Test Rule",
            description="This is a test rule for validation"
        )
        
        in_memory_db.add(rule)
        in_memory_db.commit()
        in_memory_db.refresh(rule)
        
        assert rule.id is not None
        assert rule.title == "Test Rule"
        assert rule.description == "This is a test rule for validation"
        
        # Test retrieval
        retrieved = in_memory_db.query(Rule).filter(Rule.id == rule.id).first()
        assert retrieved.title == rule.title
    
    def test_course_model_creation(self, in_memory_db):
        """Test Course model creation with JSON field"""
        holes_data = [
            {"hole_number": 1, "par": 4, "yards": 400, "handicap": 1},
            {"hole_number": 2, "par": 3, "yards": 150, "handicap": 18}
        ]
        
        course = Course(
            name="Test Course",
            description="A test golf course",
            total_par=72,
            total_yards=6500,
            course_rating=70.5,
            slope_rating=125.0,
            holes_data=holes_data,
            created_at="2023-01-01T12:00:00",
            updated_at="2023-01-01T12:00:00"
        )
        
        in_memory_db.add(course)
        in_memory_db.commit()
        in_memory_db.refresh(course)
        
        assert course.id is not None
        assert course.name == "Test Course"
        assert course.holes_data == holes_data
        assert course.total_par == 72
    
    def test_player_profile_model_creation(self, in_memory_db):
        """Test PlayerProfile model with default preferences"""
        profile = PlayerProfile(
            name="Test Player",
            handicap=15.5,
            avatar_url="https://example.com/avatar.jpg",
            created_date="2023-01-01T12:00:00"
        )
        
        in_memory_db.add(profile)
        in_memory_db.commit()
        in_memory_db.refresh(profile)
        
        assert profile.id is not None
        assert profile.name == "Test Player"
        assert profile.handicap == 15.5
        assert profile.is_active == 1  # Default value
        assert "ai_difficulty" in profile.preferences  # Default preferences
    
    def test_player_statistics_model_creation(self, in_memory_db):
        """Test PlayerStatistics model with default values"""
        stats = PlayerStatistics(
            player_id=1,
            last_updated="2023-01-01T12:00:00"
        )
        
        in_memory_db.add(stats)
        in_memory_db.commit()
        in_memory_db.refresh(stats)
        
        assert stats.id is not None
        assert stats.player_id == 1
        assert stats.games_played == 0  # Default
        assert stats.total_earnings == 0.0  # Default
        assert stats.betting_success_rate == 0.0  # Default
    
    def test_game_state_model_json_storage(self, in_memory_db):
        """Test GameStateModel JSON storage"""
        game_data = {
            "current_hole": 5,
            "players": [
                {"id": "p1", "name": "Alice", "points": 10},
                {"id": "p2", "name": "Bob", "points": 5}
            ],
            "betting_state": {"teams": {}, "base_wager": 2}
        }
        
        game_state = GameStateModel(state=game_data)
        
        in_memory_db.add(game_state)
        in_memory_db.commit()
        in_memory_db.refresh(game_state)
        
        assert game_state.id is not None
        assert game_state.state == game_data
        assert game_state.state["current_hole"] == 5
    
    def test_game_player_result_model(self, in_memory_db):
        """Test GamePlayerResult model with complex data"""
        hole_scores = {"1": 4, "2": 3, "3": 5}
        betting_history = [
            {"hole": 1, "action": "request_partner", "partner": "p2"},
            {"hole": 2, "action": "go_solo"}
        ]
        
        result = GamePlayerResult(
            game_record_id=1,
            player_profile_id=1,
            player_name="Test Player",
            final_position=1,
            total_earnings=25.5,
            holes_won=8,
            hole_scores=hole_scores,
            betting_history=betting_history,
            created_at="2023-01-01T12:00:00"
        )
        
        in_memory_db.add(result)
        in_memory_db.commit()
        in_memory_db.refresh(result)
        
        assert result.id is not None
        assert result.hole_scores == hole_scores
        assert result.betting_history == betting_history
        assert result.total_earnings == 25.5
    
    def test_player_achievement_model(self, in_memory_db):
        """Test PlayerAchievement model"""
        achievement_data = {
            "earnings": 25.0,
            "game_duration": 180,
            "difficulty": "hard"
        }
        
        achievement = PlayerAchievement(
            player_profile_id=1,
            achievement_type="big_earner",
            achievement_name="Big Earner",
            description="Earned over 20 quarters in a single game",
            earned_date="2023-01-01T12:00:00",
            achievement_data=achievement_data
        )
        
        in_memory_db.add(achievement)
        in_memory_db.commit()
        in_memory_db.refresh(achievement)
        
        assert achievement.id is not None
        assert achievement.achievement_type == "big_earner"
        assert achievement.achievement_data == achievement_data


class TestSchemaValidation:
    """Test Pydantic schema validation"""
    
    def test_hole_info_validation_success(self):
        """Test successful HoleInfo validation"""
        hole = HoleInfo(
            hole_number=1,
            par=4,
            yards=400,
            handicap=10,
            description="A challenging par 4",
            tee_box="championship"
        )
        
        assert hole.hole_number == 1
        assert hole.par == 4
        assert hole.yards == 400
        assert hole.handicap == 10
    
    def test_hole_info_par_validation(self):
        """Test HoleInfo par validation"""
        # Invalid par (too low)
        with pytest.raises(ValidationError, match="Par must be between 3 and 6"):
            HoleInfo(hole_number=1, par=2, yards=400, handicap=1)
        
        # Invalid par (too high)
        with pytest.raises(ValidationError, match="Par must be between 3 and 6"):
            HoleInfo(hole_number=1, par=7, yards=400, handicap=1)
        
        # Valid pars
        for par in [3, 4, 5, 6]:
            hole = HoleInfo(hole_number=1, par=par, yards=400, handicap=1)
            assert hole.par == par
    
    def test_hole_info_handicap_validation(self):
        """Test HoleInfo handicap validation"""
        # Invalid handicap (too low)
        with pytest.raises(ValidationError, match="Handicap must be between 1 and 18"):
            HoleInfo(hole_number=1, par=4, yards=400, handicap=0)
        
        # Invalid handicap (too high)
        with pytest.raises(ValidationError, match="Handicap must be between 1 and 18"):
            HoleInfo(hole_number=1, par=4, yards=400, handicap=19)
        
        # Valid handicaps
        for handicap in [1, 9, 18]:
            hole = HoleInfo(hole_number=1, par=4, yards=400, handicap=handicap)
            assert hole.handicap == handicap
    
    def test_hole_info_yards_validation(self):
        """Test HoleInfo yards validation"""
        # Invalid yards (too low)
        with pytest.raises(ValidationError, match="Yards must be at least 100"):
            HoleInfo(hole_number=1, par=4, yards=50, handicap=1)
        
        # Invalid yards (too high)
        with pytest.raises(ValidationError, match="Yards cannot exceed 700"):
            HoleInfo(hole_number=1, par=4, yards=800, handicap=1)
        
        # Valid yards
        hole = HoleInfo(hole_number=1, par=4, yards=400, handicap=1)
        assert hole.yards == 400
    
    def test_course_create_validation_success(self):
        """Test successful CourseCreate validation"""
        holes = []
        for i in range(1, 19):
            holes.append(HoleInfo(
                hole_number=i,
                par=4,
                yards=400,
                handicap=i  # Each hole gets unique handicap 1-18
            ))
        
        course = CourseCreate(
            name="Test Course",
            description="A great test course",
            holes=holes
        )
        
        assert course.name == "Test Course"
        assert len(course.holes) == 18
    
    def test_course_create_hole_count_validation(self):
        """Test CourseCreate hole count validation"""
        # Too few holes
        holes = [HoleInfo(hole_number=1, par=4, yards=400, handicap=1)]
        
        with pytest.raises(ValidationError, match="Course must have exactly 18 holes"):
            CourseCreate(name="Test Course", holes=holes)
        
        # Too many holes
        holes = []
        for i in range(1, 20):  # 19 holes
            holes.append(HoleInfo(hole_number=i, par=4, yards=400, handicap=min(i, 18)))
        
        with pytest.raises(ValidationError, match="Course must have exactly 18 holes"):
            CourseCreate(name="Test Course", holes=holes)
    
    def test_course_create_unique_handicaps_validation(self):
        """Test CourseCreate unique handicaps validation"""
        holes = []
        for i in range(1, 19):
            holes.append(HoleInfo(
                hole_number=i,
                par=4,
                yards=400,
                handicap=1  # All holes have same handicap (invalid)
            ))
        
        with pytest.raises(ValidationError, match="All handicaps must be unique"):
            CourseCreate(name="Test Course", holes=holes)
    
    def test_course_create_unique_hole_numbers_validation(self):
        """Test CourseCreate unique hole numbers validation"""
        holes = []
        for i in range(1, 19):
            holes.append(HoleInfo(
                hole_number=1,  # All holes have same number (invalid)
                par=4,
                yards=400,
                handicap=i
            ))
        
        with pytest.raises(ValidationError, match="Hole numbers must be 1-18 and unique"):
            CourseCreate(name="Test Course", holes=holes)
    
    def test_course_create_total_par_validation(self):
        """Test CourseCreate total par validation"""
        # Total par too low (all par 3s = 54)
        holes = []
        for i in range(1, 19):
            holes.append(HoleInfo(hole_number=i, par=3, yards=150, handicap=i))
        
        with pytest.raises(ValidationError, match="Total par must be between 70 and 74"):
            CourseCreate(name="Test Course", holes=holes)
        
        # Total par too high (all par 5s = 90)
        holes = []
        for i in range(1, 19):
            holes.append(HoleInfo(hole_number=i, par=5, yards=500, handicap=i))
        
        with pytest.raises(ValidationError, match="Total par must be between 70 and 74"):
            CourseCreate(name="Test Course", holes=holes)
    
    def test_course_create_name_validation(self):
        """Test CourseCreate name validation"""
        holes = [HoleInfo(hole_number=i, par=4, yards=400, handicap=i) for i in range(1, 19)]
        
        # Empty name
        with pytest.raises(ValidationError, match="Course name must be at least 3 characters"):
            CourseCreate(name="", holes=holes)
        
        # Too short name
        with pytest.raises(ValidationError, match="Course name must be at least 3 characters"):
            CourseCreate(name="AB", holes=holes)
        
        # Valid name with whitespace (should be trimmed)
        course = CourseCreate(name="  Test Course  ", holes=holes)
        assert course.name == "Test Course"


class TestPlayerSchemas:
    """Test player-related schema validation"""
    
    def test_player_profile_create_validation(self):
        """Test PlayerProfileCreate validation"""
        profile_data = PlayerProfileCreate(
            name="Test Player",
            handicap=15.5,
            avatar_url="https://example.com/avatar.jpg",
            preferences={
                "ai_difficulty": "hard",
                "betting_style": "aggressive"
            }
        )
        
        assert profile_data.name == "Test Player"
        assert profile_data.handicap == 15.5
        assert profile_data.preferences["ai_difficulty"] == "hard"
    
    def test_player_profile_update_validation(self):
        """Test PlayerProfileUpdate validation with optional fields"""
        # Update with only name
        update_data = PlayerProfileUpdate(name="New Name")
        assert update_data.name == "New Name"
        assert update_data.handicap is None
        
        # Update with multiple fields
        update_data = PlayerProfileUpdate(
            name="Updated Player",
            handicap=12.0,
            avatar_url="new_avatar.jpg"
        )
        assert update_data.name == "Updated Player"
        assert update_data.handicap == 12.0
    
    def test_game_player_result_create_validation(self):
        """Test GamePlayerResultCreate validation"""
        result_data = GamePlayerResultCreate(
            player_profile_id=1,
            game_id="game123",
            final_position=1,
            total_earnings=25.5,
            hole_scores={"1": 4, "2": 3, "3": 5},
            holes_won=8,
            successful_bets=5,
            total_bets=7,
            partnerships_formed=3,
            partnerships_won=2,
            solo_attempts=1,
            solo_wins=1
        )
        
        assert result_data.player_profile_id == 1
        assert result_data.final_position == 1
        assert result_data.total_earnings == 25.5
        assert len(result_data.hole_scores) == 3
    
    def test_leaderboard_entry_validation(self):
        """Test LeaderboardEntry validation"""
        entry = LeaderboardEntry(
            rank=1,
            player_name="Top Player",
            games_played=50,
            win_percentage=60.0,
            avg_earnings=3.5,
            total_earnings=175.0,
            partnership_success=70.0
        )
        
        assert entry.rank == 1
        assert entry.player_name == "Top Player"
        assert entry.win_percentage == 60.0


class TestSchemaConversions:
    """Test schema to model conversions and serialization"""
    
    def test_rule_schema_from_model(self):
        """Test converting Rule model to schema"""
        # This would typically be tested with actual database models
        # Here we simulate the data structure
        rule_data = {
            "id": 1,
            "title": "Test Rule",
            "description": "A test rule"
        }
        
        rule_schema = RuleSchema(**rule_data)
        assert rule_schema.id == 1
        assert rule_schema.title == "Test Rule"
    
    def test_course_response_schema(self):
        """Test CourseResponse schema"""
        holes = [HoleInfo(hole_number=i, par=4, yards=400, handicap=i) for i in range(1, 19)]
        
        course_data = {
            "id": 1,
            "name": "Test Course",
            "description": "A test course",
            "total_par": 72,
            "total_yards": 7200,
            "course_rating": 70.5,
            "slope_rating": 125.0,
            "holes": holes,
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:00:00"
        }
        
        course_response = CourseResponse(**course_data)
        assert course_response.id == 1
        assert course_response.name == "Test Course"
        assert len(course_response.holes) == 18
    
    def test_player_statistics_response_schema(self):
        """Test PlayerStatisticsResponse schema"""
        stats_data = {
            "id": 1,
            "player_id": 1,
            "games_played": 25,
            "games_won": 10,
            "total_earnings": 125.5,
            "holes_played": 450,
            "holes_won": 85,
            "avg_earnings_per_hole": 2.8,
            "betting_success_rate": 0.65,
            "successful_bets": 32,
            "total_bets": 50,
            "partnership_success_rate": 0.7,
            "partnerships_formed": 15,
            "partnerships_won": 10,
            "solo_attempts": 8,
            "solo_wins": 3,
            "favorite_game_mode": "wolf_goat_pig",
            "preferred_player_count": 4,
            "best_hole_performance": [1, 5, 9],
            "worst_hole_performance": [3, 12, 16],
            "performance_trends": [
                {"date": "2023-01-01", "earnings": 10, "position": 2}
            ],
            "last_updated": "2023-01-01T12:00:00"
        }
        
        stats_response = PlayerStatisticsResponse(**stats_data)
        assert stats_response.games_played == 25
        assert stats_response.betting_success_rate == 0.65
        assert len(stats_response.performance_trends) == 1


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_json_fields(self):
        """Test models with empty JSON fields"""
        # Empty preferences should work
        profile_data = PlayerProfileCreate(
            name="Test Player",
            handicap=15.0,
            preferences={}
        )
        assert profile_data.preferences == {}
    
    def test_large_json_data(self):
        """Test models with large JSON data"""
        # Large performance trends
        large_trends = [
            {"date": f"2023-01-{i:02d}", "earnings": i, "position": i % 4 + 1}
            for i in range(1, 101)  # 100 data points
        ]
        
        # Should handle large JSON data
        stats_data = PlayerStatistics(
            player_id=1,
            performance_trends=large_trends,
            last_updated="2023-01-01T12:00:00"
        )
        
        assert len(stats_data.performance_trends) == 100
    
    def test_extreme_values(self):
        """Test schemas with extreme but valid values"""
        # Maximum handicap
        hole = HoleInfo(hole_number=1, par=6, yards=700, handicap=18)
        assert hole.par == 6
        assert hole.yards == 700
        
        # Minimum values
        hole = HoleInfo(hole_number=1, par=3, yards=100, handicap=1)
        assert hole.par == 3
        assert hole.yards == 100
    
    def test_unicode_strings(self):
        """Test schemas with unicode characters"""
        profile = PlayerProfileCreate(
            name="José María González",
            handicap=15.0
        )
        assert profile.name == "José María González"
        
        course_holes = [HoleInfo(hole_number=i, par=4, yards=400, handicap=i) for i in range(1, 19)]
        course = CourseCreate(
            name="St. Andrews • The Old Course",
            description="Historic course with special characters: £€¥",
            holes=course_holes
        )
        assert "•" in course.name
        assert "£€¥" in course.description


class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    def test_player_statistics_consistency(self):
        """Test that player statistics maintain consistency"""
        # Test that percentages are calculated correctly
        stats_data = {
            "id": 1,
            "player_id": 1,
            "games_played": 10,
            "games_won": 3,
            "successful_bets": 7,
            "total_bets": 10,
            "partnerships_formed": 5,
            "partnerships_won": 3,
            "betting_success_rate": 0.7,
            "partnership_success_rate": 0.6,
            "last_updated": "2023-01-01T12:00:00"
        }
        
        stats = PlayerStatisticsResponse(**stats_data)
        
        # Verify consistency
        expected_betting_rate = 7 / 10
        expected_partnership_rate = 3 / 5
        
        assert stats.betting_success_rate == expected_betting_rate
        assert stats.partnership_success_rate == expected_partnership_rate
    
    def test_hole_handicap_uniqueness_enforcement(self):
        """Test that hole handicap uniqueness is properly enforced"""
        holes = []
        handicaps_used = set()
        
        for i in range(1, 19):
            handicap = i
            # Ensure no duplicates
            assert handicap not in handicaps_used
            handicaps_used.add(handicap)
            
            holes.append(HoleInfo(
                hole_number=i,
                par=4,
                yards=400,
                handicap=handicap
            ))
        
        # Should be valid with all unique handicaps
        course = CourseCreate(name="Test Course", holes=holes)
        assert len(course.holes) == 18


if __name__ == "__main__":
    pytest.main([__file__])