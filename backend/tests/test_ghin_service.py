"""
Unit tests for GHINService

Tests GHIN (Golf Handicap Information Network) integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, PlayerProfile
from app.services.ghin_service import GHINService


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_ghin.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestGHINServiceInitialization:
    """Test GHIN service initialization"""

    def test_service_initialization(self, db):
        """Test service initializes with database session"""
        service = GHINService(db)

        assert service.db is db
        assert service.initialized is False
        assert service.jwt_token is None

    @patch.dict('os.environ', {}, clear=True)
    def test_no_credentials_configured(self, db):
        """Test service handles missing credentials"""
        service = GHINService(db)

        assert service.ghin_username is None
        assert service.ghin_password is None


class TestGHINAvailability:
    """Test GHIN service availability"""

    def test_is_available_not_initialized(self, db):
        """Test service reports unavailable when not initialized"""
        service = GHINService(db)

        assert service.is_available() is False

    def test_is_available_after_initialization(self, db):
        """Test service reports available after successful init"""
        service = GHINService(db)
        service.initialized = True

        assert service.is_available() is True


class TestGHINAuthentication:
    """Test GHIN authentication"""

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'GHIN_USERNAME': 'test_user',
        'GHIN_PASSWORD': 'test_pass'
    })
    @patch('httpx.AsyncClient')
    async def test_initialize_success(self, mock_client, db):
        """Test successful GHIN authentication"""
        service = GHINService(db)

        # Mock successful authentication response
        mock_response = Mock()
        mock_response.json.return_value = {
            'golfer_user': {
                'golfer_user_token': 'test_jwt_token_123'
            }
        }
        mock_response.raise_for_status = Mock()

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await service.initialize()

        assert result is True
        assert service.initialized is True
        assert service.jwt_token == 'test_jwt_token_123'

    @pytest.mark.asyncio
    @patch.dict('os.environ', {}, clear=True)
    async def test_initialize_no_credentials(self, db):
        """Test initialization without credentials"""
        service = GHINService(db)

        result = await service.initialize()

        assert result is False
        assert service.initialized is False

    @pytest.mark.asyncio
    @patch.dict('os.environ', {
        'GHIN_USERNAME': 'test_user',
        'GHIN_PASSWORD': 'wrong_pass'
    })
    @patch('httpx.AsyncClient')
    async def test_initialize_auth_failure(self, mock_client, db):
        """Test failed authentication"""
        service = GHINService(db)

        # Mock failed authentication
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = Exception("Auth failed")
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await service.initialize()

        assert result is False
        assert service.initialized is False


class TestSyncPlayerHandicap:
    """Test player handicap syncing"""

    @pytest.mark.asyncio
    async def test_sync_handicap_service_not_available(self, db):
        """Test sync when service is not available"""
        service = GHINService(db)

        result = await service.sync_player_handicap(player_id=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_sync_handicap_player_no_ghin_id(self, db):
        """Test sync for player without GHIN ID"""
        service = GHINService(db)
        service.initialized = True

        # Create player without GHIN ID
        player = PlayerProfile(
            name="Test Player",
            email="test@example.com",
            handicap=15.0,
            ghin_id=None,
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.commit()

        result = await service.sync_player_handicap(player_id=player.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_sync_handicap_success(self, db):
        """Test successful handicap sync"""
        service = GHINService(db)
        service.initialized = True
        service.jwt_token = "test_token"

        # Create player with GHIN ID
        player = PlayerProfile(
            name="Test Player",
            email="test@example.com",
            handicap=15.0,
            ghin_id="1234567",
            created_at=datetime.now().isoformat()
        )
        db.add(player)
        db.commit()

        # Mock the GHIN API call
        with patch.object(service, '_fetch_handicap_from_ghin', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {
                'handicap_index': 14.2,
                'last_updated': datetime.now().isoformat()
            }

            result = await service.sync_player_handicap(player_id=player.id)

            # Should call the fetch method
            mock_fetch.assert_called_once()


class TestGHINConfiguration:
    """Test GHIN configuration"""

    @patch.dict('os.environ', {
        'GHIN_USERNAME': 'user',
        'GHIN_PASSWORD': 'pass'
    })
    def test_env_var_loading(self, db):
        """Test environment variables are loaded"""
        service = GHINService(db)

        assert service.ghin_username == 'user'
        assert service.ghin_password == 'pass'

    def test_api_base_url(self, db):
        """Test API base URL is set"""
        service = GHINService(db)

        assert service.GHIN_API_BASE_URL == "https://api2.ghin.com/api/v1"
