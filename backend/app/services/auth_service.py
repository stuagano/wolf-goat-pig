"""
Authentication Service for linking Auth0 users to PlayerProfile records
"""

import logging
import os
import threading
from collections.abc import Generator
from typing import Any

import httpx as _httpx
import sentry_sdk
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..models import EmailPreferences, PlayerProfile
from ..utils.time import utc_now
from .legacy_player_service import capture_pending_player, find_similar_players, get_canonical_name

logger = logging.getLogger(__name__)

# Auth0 configuration — no placeholder defaults; verify_token fails closed if unset
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE", "")
AUTH0_ALGORITHMS = ["RS256"]

# Security scheme for FastAPI
security = HTTPBearer()


def _notify_admins_of_new_player(name: str, email: str | None) -> None:
    """Best-effort, non-blocking admin alert for a newly captured player.

    Runs the (external, potentially slow) email send on a daemon thread so it
    can never add latency to or break the first-login path.
    """

    def _send() -> None:
        try:
            from ..utils.admin_auth import get_admin_emails
            from .email_service import get_email_service

            svc = get_email_service()
            if not svc.is_configured():
                return
            for admin_email in get_admin_emails():
                svc.send_new_player_notification(admin_email, name, email)
        except Exception as exc:  # never surface to the login path
            logger.warning(f"Failed to notify admins of new player '{name}': {exc}")

    threading.Thread(target=_send, daemon=True, name="new-player-notify").start()


def _mark_welcome_email_sent(player_id: int) -> None:
    """Persist that the welcome email was accepted by the provider.

    Opens its own short-lived session because this runs on a detached daemon
    thread, after the request's session is already closed. The timestamp both
    proves delivery (observability, #318) and guards against re-sending on a
    later login.
    """
    db = SessionLocal()
    try:
        player = db.query(PlayerProfile).filter(PlayerProfile.id == player_id).first()
        if player is not None:
            player.welcome_email_sent_at = utc_now().isoformat()
            db.commit()
    except Exception as exc:  # never surface to the login path
        logger.warning(f"Failed to record welcome_email_sent_at for player {player_id}: {exc}")
        db.rollback()
    finally:
        db.close()


def _deliver_welcome_email(name: str, email: str | None, player_id: int) -> None:
    """Synchronously deliver the first-login welcome email. Best-effort.

    Inspects the provider outcome so a *soft* failure (provider returns False
    without raising — e.g. a non-2xx from Resend, or an unconfigured provider)
    is observable, not just an unraised exception. Records the recipient and a
    provider outcome for every send (traceable delivery evidence, #318), and
    persists welcome_email_sent_at only on success so a failed send stays
    retryable. Any exception is swallowed so it can never break the login path
    but is reported to Sentry.
    """
    if not email:
        return
    try:
        from .email_service import get_email_service

        svc = get_email_service()
        if not svc.is_configured():
            logger.warning("Welcome email skipped for player %s <%s>: email provider not configured", player_id, email)
            sentry_sdk.capture_message(f"Welcome email skipped: provider not configured (player_id={player_id})")
            return
        accepted = svc.send_welcome_email(email, name)
        if accepted:
            _mark_welcome_email_sent(player_id)
            logger.info("Welcome email accepted by provider for player %s <%s>", player_id, email)
        else:
            # Soft failure: provider returned False without raising.
            logger.error("Welcome email rejected by provider for player %s <%s>", player_id, email)
            sentry_sdk.capture_message(f"Welcome email rejected by provider (player_id={player_id}, email={email})")
    except Exception as exc:  # never surface to the login path
        logger.warning(f"Failed to send welcome email to '{email}': {exc}")
        sentry_sdk.capture_exception(exc)


def _send_welcome_email(name: str, email: str | None, player_id: int) -> None:
    """Best-effort, non-blocking welcome email on first-login profile creation.

    Runs the (external, potentially slow) send on a daemon thread so it can
    never add latency to or break the first-login path.
    """
    threading.Thread(
        target=_deliver_welcome_email,
        args=(name, email, player_id),
        daemon=True,
        name="welcome-email",
    ).start()


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
    def verify_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> dict[str, Any]:
        """Verify Auth0 JWT token"""
        token = credentials.credentials

        try:
            # Use environment variable to determine auth mode
            if os.getenv("ENVIRONMENT") == "production":
                # Production Auth0 integration
                if not AUTH0_DOMAIN or not AUTH0_API_AUDIENCE:
                    logger.error("Auth0 configuration not set for production")
                    raise HTTPException(status_code=500, detail="Authentication service not configured")

                # Fetch JWKS from Auth0 using httpx (python-jose compatible)
                jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
                resp = _httpx.get(jwks_url, timeout=10.0)
                resp.raise_for_status()
                jwks = resp.json()

                payload = jwt.decode(
                    token,
                    jwks,
                    algorithms=AUTH0_ALGORITHMS,
                    audience=AUTH0_API_AUDIENCE,
                    issuer=f"https://{AUTH0_DOMAIN}/",
                )
                return dict(payload)
            if os.getenv("ENVIRONMENT") == "development":
                # Development mode - allow mock authentication
                logger.warning("Using mock authentication - development mode only")
                return {
                    "sub": "auth0|123456789",
                    "email": "test@example.com",
                    "name": "Test User",
                    "picture": "https://example.com/avatar.jpg",
                }
            # Unknown environment - fail safe
            logger.error(f"Unknown ENVIRONMENT value: {os.getenv('ENVIRONMENT')!r} — refusing to authenticate")
            raise HTTPException(status_code=500, detail="Authentication service misconfigured")

        except JWTError as e:
            logger.error(f"JWT verification failed: {e!s}")
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def _find_player_by_auth0_id(db: Session, auth0_id: str) -> PlayerProfile | None:
        """Look up a profile by preferences.auth0_id.

        If historical bugs left the same Auth0 subject on multiple seed rows,
        prefer a profile that already has a club ``legacy_name``, then the
        lowest id — never an arbitrary heap-ordered ``.first()``.
        """
        if not auth0_id:
            return None
        matches = (
            db.query(PlayerProfile)
            .filter(PlayerProfile.preferences["auth0_id"].as_string() == auth0_id)
            .order_by(PlayerProfile.id.asc())
            .all()
        )
        if not matches:
            return None
        if len(matches) == 1:
            return matches[0]

        # Deterministic pick among duplicates, then strip auth0_id from the rest
        # so the next login cannot reclaim a seed roster row again.
        ranked = sorted(
            matches,
            key=lambda p: (
                0 if (p.legacy_name or "").strip() else 1,
                0 if (p.email or "").strip() else 1,
                p.id or 0,
            ),
        )
        winner = ranked[0]
        for loser in ranked[1:]:
            prefs = dict(loser.preferences) if loser.preferences else {}
            if prefs.pop("auth0_id", None) is not None:
                loser.preferences = prefs
                loser.updated_at = utc_now().isoformat()
                logger.warning(
                    "Cleared duplicate auth0_id from player_profiles.id=%s (%s); keeping id=%s",
                    loser.id,
                    loser.name,
                    winner.id,
                )
        db.commit()
        return winner

    @staticmethod
    def enrich_user_from_userinfo(auth0_user: dict[str, Any], access_token: str) -> dict[str, Any]:
        """Fill email/name/picture from Auth0 /userinfo when the access token omits them.

        Auth0 access tokens for a custom API audience often only contain `sub`.
        Email/profile claims live on the ID token unless an Action copies them.
        /userinfo still returns them when the token was issued with those scopes.
        """
        if auth0_user.get("email") and auth0_user.get("name"):
            return auth0_user
        if not AUTH0_DOMAIN or not access_token:
            return auth0_user

        try:
            resp = _httpx.get(
                f"https://{AUTH0_DOMAIN}/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
            if resp.status_code != 200:
                logger.warning("Auth0 /userinfo returned %s", resp.status_code)
                return auth0_user
            info = resp.json()
        except Exception as exc:
            logger.warning("Auth0 /userinfo failed: %s", exc)
            return auth0_user

        enriched = dict(auth0_user)
        for key in ("email", "name", "picture", "nickname"):
            if not enriched.get(key) and info.get(key):
                enriched[key] = info[key]
        return enriched

    @staticmethod
    def get_or_create_player_profile(db: Session, auth0_user: dict[str, Any]) -> PlayerProfile:
        """Get or create a PlayerProfile based on Auth0 user data"""

        # Extract user info from Auth0 payload
        auth0_id = auth0_user.get("sub")
        email = (auth0_user.get("email") or "").strip() or None
        name = auth0_user.get("name") or (email.split("@")[0] if email else None) or "Unknown Player"
        picture = auth0_user.get("picture")

        if not auth0_id:
            raise HTTPException(status_code=401, detail="Token missing subject")

        # Prefer stable Auth0 subject over email. Never query email IS NULL —
        # that reclaim the first seed roster row with a null email (Dave, etc.).
        player = AuthService._find_player_by_auth0_id(db, auth0_id)

        if not player and email:
            player = db.query(PlayerProfile).filter(PlayerProfile.email == email).first()

        if not player and not email:
            # Creating a brand-new profile with no email would also persist NULL
            # and poison future logins. Fail closed until /userinfo (or Auth0
            # Actions) supplies an email claim.
            raise HTTPException(
                status_code=401,
                detail="Token missing email claim — re-login with email scope or add email to the API token",
            )

        if not player:
            # Match name to the legacy tee sheet system (same session as the
            # profile write so the whole flow is transactionally consistent).
            #
            # Only an EXACT canonical match auto-links: case-folding a name to
            # its roster spelling is deterministic and safe. A *fuzzy* match is a
            # guess — writing it to legacy_name would faithfully sign the golfer
            # up as the wrong person (issue #322). So we never persist a fuzzy
            # hit here; we leave legacy_name unset and surface the suggestion in
            # onboarding (GET /players/me) for the authenticated user to confirm.
            legacy_name = get_canonical_name(name, db)
            fuzzy_suggestion: str | None = None
            if not legacy_name:
                suggestions = find_similar_players(name, max_results=1, db=db)
                if suggestions:
                    fuzzy_suggestion = suggestions[0]
                    logger.info(
                        "Fuzzy legacy suggestion for '%s': '%s' (NOT auto-linked; awaiting confirmation)",
                        name,
                        fuzzy_suggestion,
                    )

            # Create new player profile
            player = PlayerProfile(
                name=name,
                legacy_name=legacy_name,  # Link to legacy tee sheet system
                email=email,
                avatar_url=picture,
                created_at=utc_now().isoformat(),
                updated_at=utc_now().isoformat(),
                handicap=18.0,  # Placeholder until GHIN sync — marked below
                handicap_source="default",  # unknown/pending, not a real 18.0 (#320)
                preferences={
                    "auth0_id": auth0_id,
                    "ai_difficulty": "medium",
                    "preferred_game_modes": ["wolf_goat_pig"],
                    "preferred_player_count": 4,
                    "betting_style": "conservative",
                    "display_hints": True,
                },
            )
            db.add(player)
            db.commit()
            db.refresh(player)

            # Create default email preferences
            email_prefs = EmailPreferences(
                player_profile_id=player.id,
                created_at=utc_now().isoformat(),
                updated_at=utc_now().isoformat(),
            )
            db.add(email_prefs)
            db.commit()

            logger.info(f"Created new player profile for {name} ({email})")

            # Welcome email — fires ONLY on this new-profile branch, never on a
            # returning login. Best-effort and wrapped so even dispatching it can
            # never add latency to or break first login; failures go to Sentry.
            try:
                _send_welcome_email(name, email, player.id)
            except Exception as exc:
                logger.warning(f"Failed to dispatch welcome email for '{name}': {exc}")
                sentry_sdk.capture_exception(exc)

            # No legacy link → decide between "confirm a suggestion" and "brand
            # new golfer". If there's a plausible fuzzy suggestion, onboarding
            # will surface it for the user to accept/reject, so we don't add them
            # to the pending roster yet. Only a truly unknown golfer (no exact
            # match, no suggestion) is captured into the pending queue with an
            # admin alert. Best-effort: never block account creation.
            if not legacy_name and not fuzzy_suggestion:
                try:
                    result = capture_pending_player(name, email=email, player_profile_id=player.id, db=db)
                    if result.get("captured"):
                        _notify_admins_of_new_player(name, email)
                except Exception as exc:
                    logger.warning(f"Failed to capture pending player '{name}': {exc}")
        else:
            # Update existing player with Auth0 info if needed
            update_needed = False

            if email and not player.email:
                player.email = email
                update_needed = True

            if (
                name
                and name != player.name
                and player.name in (None, "", "Unknown Player")
            ):
                player.name = name
                update_needed = True

            if not player.avatar_url and picture:
                player.avatar_url = picture
                update_needed = True

            prefs = dict(player.preferences) if player.preferences else {}
            if prefs.get("auth0_id") != auth0_id:
                prefs["auth0_id"] = auth0_id
                player.preferences = prefs
                update_needed = True

            if update_needed:
                player.updated_at = utc_now().isoformat()
                db.commit()
                logger.info(f"Updated player profile for {player.name}")

        return player

    @staticmethod
    def link_auth0_to_player(db: Session, auth0_id: str, player_id: int) -> bool:
        """Link an Auth0 account to an existing player profile"""

        try:
            player = db.query(PlayerProfile).filter(PlayerProfile.id == player_id).first()

            if not player:
                logger.error(f"Player with ID {player_id} not found")
                return False

            # Store Auth0 ID in preferences
            if not player.preferences:
                player.preferences = {}

            # Create new dict to trigger SQLAlchemy change detection
            updated_prefs = dict(player.preferences) if player.preferences else {}
            updated_prefs["auth0_id"] = auth0_id
            player.preferences = updated_prefs
            player.updated_at = utc_now().isoformat()

            db.commit()
            logger.info(f"Linked Auth0 account {auth0_id} to player {player.name}")
            return True

        except Exception as e:
            logger.error(f"Error linking Auth0 account: {e!s}")
            db.rollback()
            return False


# Global auth service instance
auth_service = AuthService()


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> PlayerProfile:
    """Dependency to get the current authenticated user"""

    # Verify token and get Auth0 user info
    auth0_user = auth_service.verify_token(token)
    # Access tokens often omit email/name — pull them from /userinfo when needed.
    auth0_user = auth_service.enrich_user_from_userinfo(auth0_user, token.credentials)

    # Get or create player profile
    player = auth_service.get_or_create_player_profile(db, auth0_user)

    return player
