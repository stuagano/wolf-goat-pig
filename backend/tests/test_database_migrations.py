"""
Test database migrations and schema validation.

This ensures that required migrations have been applied and that the
database schema matches what the application expects.
"""
import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models import GamePlayer, GameStateModel
from startup import run_migrations


class TestDatabaseSchema:
    """Test that the database schema has all required columns."""

    def test_game_players_has_tee_order_column(self):
        """Test that game_players table has tee_order column.

        This test ensures the tee_order migration has been applied.
        Without this column, the game lobby endpoint will fail with 500 errors.
        """
        inspector = inspect(engine)

        # Get columns for game_players table
        columns = [col['name'] for col in inspector.get_columns('game_players')]

        assert 'tee_order' in columns, \
            "game_players table missing tee_order column - migration not applied"

    def test_game_players_tee_order_is_nullable(self):
        """Test that tee_order column is nullable.

        The column must be nullable to support existing games that don't have
        tee order set yet.
        """
        inspector = inspect(engine)

        columns = {col['name']: col for col in inspector.get_columns('game_players')}

        assert 'tee_order' in columns, "tee_order column does not exist"
        assert columns['tee_order']['nullable'], \
            "tee_order column should be nullable for backward compatibility"

    def test_game_state_has_required_columns(self):
        """Test that game_state table has all required columns."""
        inspector = inspect(engine)

        required_columns = [
            'id',
            'game_id',
            'created_at',
            'updated_at',
            'join_code',
            'creator_user_id',
            'game_status'
        ]

        columns = [col['name'] for col in inspector.get_columns('game_state')]

        for required_col in required_columns:
            assert required_col in columns, \
                f"game_state table missing required column: {required_col}"

    def test_game_players_has_required_columns(self):
        """Test that game_players table has all required columns."""
        inspector = inspect(engine)

        required_columns = [
            'id',
            'game_id',
            'player_slot_id',
            'user_id',
            'player_profile_id',
            'player_name',
            'handicap',
            'tee_order',  # The new column that caused production errors
            'join_status',
            'joined_at',
            'created_at'
        ]

        columns = [col['name'] for col in inspector.get_columns('game_players')]

        for required_col in required_columns:
            assert required_col in columns, \
                f"game_players table missing required column: {required_col}"

    def test_tee_order_index_exists(self):
        """Test that the tee_order index exists for performance."""
        inspector = inspect(engine)

        # Get indexes for game_players table
        indexes = inspector.get_indexes('game_players')
        index_names = [idx['name'] for idx in indexes]

        # Check if the tee_order index exists
        assert 'idx_game_players_tee_order' in index_names, \
            "Missing index idx_game_players_tee_order for game_players(game_id, tee_order)"


class TestMigrations:
    """Test that migrations can be applied successfully."""

    @pytest.mark.asyncio
    async def test_run_migrations_completes_successfully(self):
        """Test that run_migrations() executes without errors."""
        result = await run_migrations()

        assert result is not None, "Migration result should not be None"
        assert isinstance(result, dict), "Migration result should be a dictionary"
        assert 'success' in result, "Migration result should have 'success' key"
        assert result['success'] is True, \
            f"Migrations should succeed: {result.get('message', 'No message')}"

    @pytest.mark.asyncio
    async def test_migrations_are_idempotent(self):
        """Test that migrations can be run multiple times safely."""
        # Run migrations twice
        result1 = await run_migrations()
        result2 = await run_migrations()

        # Both should succeed
        assert result1['success'] is True, "First migration run should succeed"
        assert result2['success'] is True, "Second migration run should succeed"

        # Second run should report no migrations needed
        assert 'No migrations needed' in result2['message'] or \
               'migration' in result2['message'].lower(), \
            "Second run should indicate migrations are up-to-date"


class TestModelDefinitions:
    """Test that SQLAlchemy models match the database schema."""

    def test_game_player_model_has_tee_order_attribute(self):
        """Test that GamePlayer model defines tee_order attribute."""
        assert hasattr(GamePlayer, 'tee_order'), \
            "GamePlayer model missing tee_order attribute"

        # Verify it's a Column
        assert hasattr(GamePlayer.tee_order, 'type'), \
            "tee_order should be a SQLAlchemy Column"

    def test_game_player_model_matches_table(self):
        """Test that GamePlayer model matches game_players table structure."""
        inspector = inspect(engine)
        table_columns = {col['name'] for col in inspector.get_columns('game_players')}

        # Get model columns (excluding internal SQLAlchemy attributes)
        model_columns = {
            attr for attr in dir(GamePlayer)
            if not attr.startswith('_') and
            hasattr(getattr(GamePlayer, attr), 'type')
        }

        # Model should have all columns that exist in the table
        for col in ['tee_order', 'player_name', 'handicap', 'game_id']:
            if col in table_columns:
                assert col in model_columns or hasattr(GamePlayer, col), \
                    f"GamePlayer model missing column that exists in table: {col}"


class TestDatabaseIntegration:
    """Integration tests for database operations with new schema."""

    def test_can_create_game_player_with_tee_order(self):
        """Test that we can create a GamePlayer with tee_order set."""
        db = next(get_db())

        try:
            # Create a game player with tee_order
            player = GamePlayer(
                game_id="test-game-id",
                player_slot_id=1,
                player_name="Test Player",
                handicap=10.0,
                tee_order=1
            )

            db.add(player)
            db.commit()
            db.refresh(player)

            assert player.tee_order == 1, "tee_order should be saved correctly"

            # Clean up
            db.delete(player)
            db.commit()

        except Exception as e:
            db.rollback()
            pytest.fail(f"Failed to create GamePlayer with tee_order: {e}")
        finally:
            db.close()

    def test_can_create_game_player_without_tee_order(self):
        """Test that we can create a GamePlayer without tee_order (NULL).

        This ensures backward compatibility with existing games.
        """
        db = next(get_db())

        try:
            # Create a game player without tee_order
            player = GamePlayer(
                game_id="test-game-id-2",
                player_slot_id=1,
                player_name="Test Player 2",
                handicap=15.0
            )

            db.add(player)
            db.commit()
            db.refresh(player)

            assert player.tee_order is None, "tee_order should be NULL when not set"

            # Clean up
            db.delete(player)
            db.commit()

        except Exception as e:
            db.rollback()
            pytest.fail(f"Failed to create GamePlayer without tee_order: {e}")
        finally:
            db.close()

    def test_can_query_game_players_ordering_by_tee_order(self):
        """Test that we can query and order by tee_order."""
        db = next(get_db())

        try:
            game_id = "test-game-ordering"

            # Create multiple players with different tee orders
            players = [
                GamePlayer(game_id=game_id, player_slot_id=1, player_name="Player 1",
                          handicap=10.0, tee_order=3),
                GamePlayer(game_id=game_id, player_slot_id=2, player_name="Player 2",
                          handicap=15.0, tee_order=1),
                GamePlayer(game_id=game_id, player_slot_id=3, player_name="Player 3",
                          handicap=20.0, tee_order=2),
            ]

            for player in players:
                db.add(player)
            db.commit()

            # Query ordered by tee_order
            ordered = db.query(GamePlayer)\
                .filter(GamePlayer.game_id == game_id)\
                .order_by(GamePlayer.tee_order)\
                .all()

            assert len(ordered) == 3, "Should have 3 players"
            assert ordered[0].player_name == "Player 2", "First should be Player 2 (tee_order=1)"
            assert ordered[1].player_name == "Player 3", "Second should be Player 3 (tee_order=2)"
            assert ordered[2].player_name == "Player 1", "Third should be Player 1 (tee_order=3)"

            # Clean up
            for player in players:
                db.delete(player)
            db.commit()

        except Exception as e:
            db.rollback()
            pytest.fail(f"Failed to query with tee_order ordering: {e}")
        finally:
            db.close()
