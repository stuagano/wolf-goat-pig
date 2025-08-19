"""
Comprehensive tests for Wolf-Goat-Pig application bootstrapping and initialization.
Tests the startup sequence, data seeding, error recovery, and system readiness.
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test environment before any imports
os.environ["SKIP_SEEDING"] = "true"  # Prevent automatic seeding during tests
os.environ["ENVIRONMENT"] = "testing"

from app.main import app, startup, run_seeding_process
from app.database import Base, SessionLocal
from app import models
from app.seed_data import (
    seed_all_data, 
    get_seeding_status, 
    verify_database_connection,
    seed_courses,
    seed_rules,
    seed_ai_personalities,
    create_default_human_player
)


class TestDatabaseBootstrapping:
    """Test database initialization and connection handling."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        db_url = f"sqlite:///{db_path}"
        
        # Create engine and tables
        engine = create_engine(db_url)
        Base.metadata.create_all(bind=engine)
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        yield TestSessionLocal, db_url
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_database_connection_verification(self, temp_db):
        """Test database connection verification function."""
        TestSessionLocal, _ = temp_db
        
        db = TestSessionLocal()
        try:
            # Test successful connection
            assert verify_database_connection(db) is True
            
            # Test with closed connection (simulate failure)
            db.close()
            # Note: SQLite may still allow some operations on closed connections
            # This test verifies the function doesn't crash
            result = verify_database_connection(db)
            assert isinstance(result, bool)
        finally:
            try:
                db.close()
            except:
                pass
    
    def test_database_initialization_resilience(self):
        """Test that database initialization handles various error conditions."""
        from app.database import init_db
        
        # Test with invalid database URL
        with patch.dict(os.environ, {"DATABASE_URL": "invalid://url"}):
            with pytest.raises(Exception):
                init_db()
        
        # Test with missing database file (should create it)
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "new_test.db")
            with patch.dict(os.environ, {"DATABASE_URL": f"sqlite:///{db_path}"}):
                # This should succeed and create the database
                init_db()
                assert os.path.exists(db_path)


class TestDataSeeding:
    """Test comprehensive data seeding functionality."""
    
    @pytest.fixture
    def seeded_db(self):
        """Create a temporary database with seeded data."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "seeded_test.db")
        db_url = f"sqlite:///{db_path}"
        
        # Patch the database URL
        with patch.dict(os.environ, {"DATABASE_URL": db_url}):
            # Initialize database
            engine = create_engine(db_url)
            Base.metadata.create_all(bind=engine)
            
            # Run seeding
            results = seed_all_data()
            
            yield db_url, results
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_comprehensive_seeding(self, seeded_db):
        """Test that all data is seeded correctly."""
        db_url, results = seeded_db
        
        # Check seeding results
        assert results["status"] in ["success", "warning"]
        assert "results" in results
        
        # Verify specific components were seeded
        expected_components = ["courses", "rules", "ai_personalities", "default_human"]
        for component in expected_components:
            assert component in results["results"]
            if component != "default_human":
                assert results["results"][component]["status"] == "success"
                assert results["results"][component]["added"] >= 0
    
    def test_seeding_idempotency(self, seeded_db):
        """Test that seeding can be run multiple times safely."""
        db_url, first_results = seeded_db
        
        # Run seeding again
        with patch.dict(os.environ, {"DATABASE_URL": db_url}):
            second_results = seed_all_data()
        
        # Second run should report 0 additions (everything already exists)
        assert second_results["status"] in ["success", "warning"]
        for component, result in second_results["results"].items():
            if component not in ["default_human", "sample_games"]:
                # Most components should report 0 additions on second run
                assert result["added"] == 0
    
    def test_seeding_status_check(self, seeded_db):
        """Test seeding status verification."""
        db_url, _ = seeded_db
        
        with patch.dict(os.environ, {"DATABASE_URL": db_url}):
            status = get_seeding_status()
        
        assert status["status"] == "success"
        assert "verification" in status
        assert "overall" in status["verification"]
    
    def test_individual_seeding_functions(self):
        """Test individual seeding components."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "component_test.db")
            db_url = f"sqlite:///{db_path}"
            
            engine = create_engine(db_url)
            Base.metadata.create_all(bind=engine)
            TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            
            db = TestSessionLocal()
            
            try:
                # Test course seeding
                courses_added = seed_courses(db)
                assert courses_added >= 3  # We have at least 3 default courses
                
                # Verify courses in database
                course_count = db.query(models.Course).count()
                assert course_count >= 3
                
                # Test rule seeding
                rules_added = seed_rules(db)
                assert rules_added >= 10  # We have many rules
                
                # Verify rules in database
                rule_count = db.query(models.Rule).count()
                assert rule_count >= 10
                
                # Test AI personality seeding
                personalities_added = seed_ai_personalities(db)
                assert personalities_added >= 4  # We have at least 4 AI personalities
                
                # Verify AI personalities in database
                ai_count = db.query(models.PlayerProfile).filter_by(is_ai=True).count()
                assert ai_count >= 4
                
                # Test default human player creation
                human_player = create_default_human_player(db)
                assert human_player is not None or db.query(models.PlayerProfile).filter_by(is_ai=False).count() > 0
                
            finally:
                db.close()
    
    def test_seeding_error_handling(self):
        """Test seeding behavior with database errors."""
        # Test with invalid database
        with patch('app.seed_data.SessionLocal') as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            results = seed_all_data()
            assert results["status"] == "error"
            assert "Database initialization failed" in results["message"]
    
    def test_seeding_with_missing_data(self):
        """Test seeding resilience with missing or corrupted data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "missing_data_test.db")
            
            # Test with empty default courses (simulate missing data)
            with patch('app.seed_data.DEFAULT_COURSES', []):
                with patch.dict(os.environ, {"DATABASE_URL": f"sqlite:///{db_path}"}):
                    results = seed_all_data()
                    
                    # Should still succeed but with warnings
                    assert results["status"] in ["success", "warning"]
                    assert results["results"]["courses"]["added"] == 0


class TestApplicationStartup:
    """Test the application startup sequence."""
    
    def test_startup_with_healthy_system(self):
        """Test startup behavior when all systems are healthy."""
        with patch('app.main.get_seeding_status') as mock_status:
            mock_status.return_value = {
                "status": "success",
                "verification": {
                    "overall": {"status": "success"}
                }
            }
            
            with patch('app.main.game_state.get_courses') as mock_courses:
                mock_courses.return_value = {"Test Course": {}}
                
                # This should not raise any exceptions
                import asyncio
                asyncio.run(startup())
    
    def test_startup_with_missing_data(self):
        """Test startup behavior when data is missing."""
        with patch('app.main.get_seeding_status') as mock_status:
            mock_status.return_value = {
                "status": "success",
                "verification": {
                    "overall": {"status": "warning"}
                }
            }
            
            with patch('app.main.run_seeding_process') as mock_seed:
                mock_seed.return_value = None
                
                # Should trigger seeding process
                import asyncio
                asyncio.run(startup())
                mock_seed.assert_called_once()
    
    def test_startup_error_resilience(self):
        """Test that startup continues even with errors."""
        with patch('app.main.get_seeding_status') as mock_status:
            mock_status.side_effect = Exception("Seeding check failed")
            
            # Should not raise exception - startup should be resilient
            import asyncio
            asyncio.run(startup())
    
    def test_seeding_process_execution(self):
        """Test the seeding process during startup."""
        with patch('app.main.seed_all_data') as mock_seed:
            mock_seed.return_value = {
                "status": "success",
                "results": {
                    "courses": {"added": 3},
                    "rules": {"added": 25}
                }
            }
            
            import asyncio
            asyncio.run(run_seeding_process())
            mock_seed.assert_called_once_with(force_reseed=False)
    
    def test_skip_seeding_environment_variable(self):
        """Test that SKIP_SEEDING environment variable works."""
        with patch.dict(os.environ, {"SKIP_SEEDING": "true"}):
            with patch('app.main.get_seeding_status') as mock_status:
                # Should not call seeding status when skipping
                import asyncio
                asyncio.run(startup())
                mock_status.assert_not_called()


class TestHealthChecks:
    """Test health check endpoint functionality."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_health_check_all_systems_healthy(self, client):
        """Test health check when all systems are operational."""
        with patch('app.main.database.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            
            with patch('app.main.game_state.get_courses') as mock_courses:
                mock_courses.return_value = {"Course 1": {}, "Course 2": {}}
                
                with patch('app.main.WolfGoatPigSimulation') as mock_sim:
                    mock_sim.return_value = MagicMock()
                    
                    response = client.get("/health")
                    assert response.status_code == 200
                    
                    health_data = response.json()
                    assert health_data["status"] in ["healthy", "degraded"]
                    assert "components" in health_data
                    assert "database" in health_data["components"]
                    assert "courses" in health_data["components"]
                    assert "simulation" in health_data["components"]
    
    def test_health_check_database_failure(self, client):
        """Test health check when database is unavailable."""
        with patch('app.main.database.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db_instance.execute.side_effect = Exception("Database connection failed")
            mock_db.return_value = mock_db_instance
            
            response = client.get("/health")
            assert response.status_code == 503
            
            health_data = response.json()
            assert "Database connection failed" in str(health_data)
    
    def test_health_check_no_courses(self, client):
        """Test health check when no courses are available."""
        with patch('app.main.database.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            
            with patch('app.main.game_state.get_courses') as mock_courses:
                mock_courses.return_value = {}  # No courses
                
                response = client.get("/health")
                assert response.status_code == 503  # Should fail with no courses
    
    def test_health_check_simulation_failure(self, client):
        """Test health check when simulation cannot be created."""
        with patch('app.main.database.SessionLocal') as mock_db:
            mock_db_instance = MagicMock()
            mock_db.return_value = mock_db_instance
            
            with patch('app.main.game_state.get_courses') as mock_courses:
                mock_courses.return_value = {"Course 1": {}}
                
                with patch('app.main.WolfGoatPigSimulation') as mock_sim:
                    mock_sim.side_effect = Exception("Simulation initialization failed")
                    
                    response = client.get("/health")
                    assert response.status_code == 503


class TestGameInitializationResilience:
    """Test game initialization error handling and recovery."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_game_initialization_with_valid_data(self, client):
        """Test successful game initialization."""
        with patch('app.main.game_state.get_courses') as mock_courses:
            mock_courses.return_value = {"Test Course": {}}
            
            with patch('app.main.wgp_simulation') as mock_sim:
                mock_sim.get_game_state.return_value = {"active": True, "current_hole": 1}
                
                response = client.post("/wgp/test-game/action", json={
                    "action_type": "INITIALIZE_GAME",
                    "payload": {
                        "players": [
                            {"id": "p1", "name": "Player 1", "handicap": 10},
                            {"id": "p2", "name": "Player 2", "handicap": 15},
                            {"id": "p3", "name": "Player 3", "handicap": 8},
                            {"id": "p4", "name": "Player 4", "handicap": 20}
                        ],
                        "course_name": "Test Course"
                    }
                })
                
                assert response.status_code == 200
                game_data = response.json()
                assert "Game initialized with 4 players" in game_data["log_message"]
    
    def test_game_initialization_with_missing_player_data(self, client):
        """Test game initialization with incomplete player data."""
        with patch('app.main.game_state.get_courses') as mock_courses:
            mock_courses.return_value = {"Test Course": {}}
            
            with patch('app.main.wgp_simulation') as mock_sim:
                mock_sim.get_game_state.return_value = {"active": True, "current_hole": 1}
                
                # Missing handicap for one player
                response = client.post("/wgp/test-game/action", json={
                    "action_type": "INITIALIZE_GAME",
                    "payload": {
                        "players": [
                            {"name": "Player 1"},  # Missing handicap and id
                            {"id": "p2", "name": "Player 2", "handicap": 15},
                            {"id": "p3", "name": "Player 3", "handicap": 8},
                            {"id": "p4", "name": "Player 4", "handicap": 20}
                        ]
                    }
                })
                
                assert response.status_code == 200
                # Should succeed with defaults applied
    
    def test_game_initialization_with_invalid_course(self, client):
        """Test game initialization with non-existent course."""
        with patch('app.main.game_state.get_courses') as mock_courses:
            mock_courses.return_value = {"Real Course": {}}
            
            with patch('app.main.get_fallback_courses') as mock_fallback:
                mock_fallback.return_value = {"Emergency Course": {}}
                
                with patch('app.main.wgp_simulation') as mock_sim:
                    mock_sim.get_game_state.return_value = {"active": True, "current_hole": 1}
                    
                    response = client.post("/wgp/test-game/action", json={
                        "action_type": "INITIALIZE_GAME",
                        "payload": {
                            "players": [
                                {"id": "p1", "name": "Player 1", "handicap": 10},
                                {"id": "p2", "name": "Player 2", "handicap": 15},
                                {"id": "p3", "name": "Player 3", "handicap": 8},
                                {"id": "p4", "name": "Player 4", "handicap": 20}
                            ],
                            "course_name": "Non-existent Course"
                        }
                    })
                    
                    assert response.status_code == 200
                    # Should fallback to available course
    
    def test_game_initialization_critical_failure(self, client):
        """Test game initialization with critical system failure."""
        with patch('app.main.game_state.get_courses') as mock_courses:
            mock_courses.side_effect = Exception("Critical system failure")
            
            response = client.post("/wgp/test-game/action", json={
                "action_type": "INITIALIZE_GAME",
                "payload": {
                    "players": [
                        {"id": "p1", "name": "Player 1", "handicap": 10},
                        {"id": "p2", "name": "Player 2", "handicap": 15},
                        {"id": "p3", "name": "Player 3", "handicap": 8},
                        {"id": "p4", "name": "Player 4", "handicap": 20}
                    ]
                }
            })
            
            assert response.status_code == 200
            game_data = response.json()
            # Should return emergency state
            assert game_data["game_state"]["active"] is False or "error" in game_data["game_state"]


class TestSystemRecovery:
    """Test system recovery and fallback mechanisms."""
    
    def test_course_data_recovery(self):
        """Test that course data can be recovered from fallbacks."""
        from app.main import get_fallback_courses
        
        fallback_courses = get_fallback_courses()
        
        assert isinstance(fallback_courses, dict)
        assert len(fallback_courses) >= 1
        
        # Verify structure of fallback courses
        for course_name, course_data in fallback_courses.items():
            assert "name" in course_data
            assert "holes" in course_data
            assert len(course_data["holes"]) == 18
            assert "total_par" in course_data
            assert "total_yards" in course_data
            
            # Verify hole structure
            for hole in course_data["holes"]:
                required_fields = ["hole_number", "par", "yards", "stroke_index"]
                for field in required_fields:
                    assert field in hole
    
    def test_database_resilience(self):
        """Test database operation resilience."""
        # Test seeding with database errors
        with patch('app.seed_data.SessionLocal') as mock_session:
            mock_session.side_effect = Exception("Database unavailable")
            
            # Should handle gracefully
            status = get_seeding_status()
            assert status["status"] == "error"
            assert "Database connection failed" in status["message"]
    
    def test_partial_system_failure_recovery(self):
        """Test recovery when some systems fail but others work."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "partial_failure_test.db")
            
            # Initialize database successfully
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(bind=engine)
            
            # Simulate partial seeding failure (courses succeed, rules fail)
            with patch('app.seed_data.seed_rules') as mock_rules:
                mock_rules.side_effect = Exception("Rules seeding failed")
                
                with patch.dict(os.environ, {"DATABASE_URL": f"sqlite:///{db_path}"}):
                    results = seed_all_data()
                    
                    # Should have partial success
                    assert results["status"] in ["success", "warning", "error"]
                    assert "results" in results


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])