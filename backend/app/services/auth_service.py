"""
Authentication Service for linking Auth0 users to PlayerProfile records
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import EmailPreferences, PlayerProfile

logger = logging.getLogger(__name__)

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-domain.auth0.com")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE", "your-api-audience")
AUTH0_ALGORITHMS = ["RS256"]

# Security scheme for FastAPI
security = HTTPBearer()

class AuthService:
    """Service for handling authentication and user management"""

    @staticmethod
    def get_db() -> Generator[Session, None, None]:
        """Get a database session"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Verify Auth0 JWT token"""
        token = credentials.credentials

        try:
            # Use environment variable to determine auth mode
            if os.getenv("ENVIRONMENT") == "production":
                # Production Auth0 integration
                if AUTH0_DOMAIN == "your-domain.auth0.com" or AUTH0_API_AUDIENCE == "your-api-audience":
                    logger.error("Auth0 configuration not set for production")
                    raise HTTPException(status_code=500, detail="Authentication service not configured")

                jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
                jwks_client = jwt.PyJWKClient(jwks_url)
                signing_key = jwks_client.get_signing_key_from_jwt(token)

                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=AUTH0_ALGORITHMS,
                    audience=AUTH0_API_AUDIENCE,
                    issuer=f"https://{AUTH0_DOMAIN}/"
                )
                return dict(payload)
            else:
                # Development mode - allow mock authentication
                logger.warning("Using mock authentication - development mode only")
                return {
                    "sub": "auth0|123456789",
                    "email": "test@example.com",
                    "name": "Test User",
                    "picture": "https://example.com/avatar.jpg"
                }

        except JWTError as e:
            logger.error(f"JWT verification failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def get_or_create_player_profile(db: Session, auth0_user: Dict[str, Any]) -> PlayerProfile:
        """Get or create a PlayerProfile based on Auth0 user data"""

        # Extract user info from Auth0 payload
        auth0_id = auth0_user.get("sub")
        email = auth0_user.get("email")
        name = auth0_user.get("name", email.split("@")[0] if email else "Unknown Player")
        picture = auth0_user.get("picture")

        # Try to find existing player by email
        player = db.query(PlayerProfile).filter(
            PlayerProfile.email == email
        ).first()

        if not player:
            # Create new player profile
            player = PlayerProfile(
                name=name,
                email=email,
                avatar_url=picture,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                handicap=18.0,  # Default handicap
                preferences={
                    "auth0_id": auth0_id,
                    "ai_difficulty": "medium",
                    "preferred_game_modes": ["wolf_goat_pig"],
                    "preferred_player_count": 4,
                    "betting_style": "conservative",
                    "display_hints": True
                }
            )
            db.add(player)
            db.commit()
            db.refresh(player)

            # Create default email preferences
            email_prefs = EmailPreferences(
                player_profile_id=player.id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            db.add(email_prefs)
            db.commit()

            logger.info(f"Created new player profile for {name} ({email})")
        else:
            # Update existing player with Auth0 info if needed
            update_needed = False

            if not player.avatar_url and picture:
                player.avatar_url = picture
                update_needed = True

            if player.preferences and "auth0_id" not in player.preferences:
                # Create new dict to trigger SQLAlchemy change detection
                updated_prefs = dict(player.preferences)
                updated_prefs["auth0_id"] = auth0_id
                player.preferences = updated_prefs
                update_needed = True

            if update_needed:
                setattr(player, 'updated_at', datetime.now().isoformat())
                db.commit()
                logger.info(f"Updated player profile for {player.name}")

        return player

    @staticmethod
    def link_auth0_to_player(db: Session, auth0_id: str, player_id: int) -> bool:
        """Link an Auth0 account to an existing player profile"""

        try:
            player = db.query(PlayerProfile).filter(
                PlayerProfile.id == player_id
            ).first()

            if not player:
                logger.error(f"Player with ID {player_id} not found")
                return False

            # Store Auth0 ID in preferences
            if not player.preferences:
                setattr(player, 'preferences', {})

            # Create new dict to trigger SQLAlchemy change detection
            updated_prefs = dict(player.preferences) if player.preferences else {}
            updated_prefs["auth0_id"] = auth0_id
            player.preferences = updated_prefs
            setattr(player, 'updated_at', datetime.now().isoformat())

            db.commit()
            logger.info(f"Linked Auth0 account {auth0_id} to player {player.name}")
            return True

        except Exception as e:
            logger.error(f"Error linking Auth0 account: {str(e)}")
            db.rollback()
            return False

# Global auth service instance
auth_service = AuthService()

def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(AuthService.get_db)
) -> PlayerProfile:
    """Dependency to get the current authenticated user"""

    # Verify token and get Auth0 user info
    auth0_user = auth_service.verify_token(token)

    # Get or create player profile
    player = auth_service.get_or_create_player_profile(db, auth0_user)

    return player
