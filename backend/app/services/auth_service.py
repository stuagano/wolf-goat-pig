"""
Authentication Service for linking Auth0 users to PlayerProfile records
"""

import logging
import os
import threading
from collections.abc import Generator
from typing import Any, cast

import httpx as _httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..models import EmailPreferences, PlayerProfile
from ..observability.report import report_exception, report_message
from ..utils.time import utc_now
from .legacy_player_service import (
    capture_pending_player,
    find_similar_players,
    get_canonical_name,
    link_profile_to_canonical_name,
)

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
            report_message(f"Welcome email skipped: provider not configured (player_id={player_id})")
            return
        accepted = svc.send_welcome_email(email, name)
        if accepted:
            _mark_welcome_email_sent(player_id)
            logger.info("Welcome email accepted by provider for player %s <%s>", player_id, email)
        else:
            # Soft failure: provider returned False without raising.
            logger.error("Welcome email rejected by provider for player %s <%s>", player_id, email)
            report_message(f"Welcome email rejected by provider (player_id={player_id}, email={email})")
    except Exception as exc:  # never surface to the login path
        logger.warning(f"Failed to send welcome email to '{email}': {exc}")
        report_exception(exc)


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
        """Resolve a stable subject without silently choosing between accounts."""
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
        if len(matches) > 1:
            raise HTTPException(
                status_code=409,
                detail="This login matches multiple profiles. Ask a club admin to review Account links.",
            )
        if not matches[0].is_active:
            raise HTTPException(
                status_code=403, detail="This player profile is inactive. Ask a club admin to review Account links."
            )
        return matches[0]

    @staticmethod
    def enrich_user_from_userinfo(auth0_user: dict[str, Any], access_token: str) -> dict[str, Any]:
        """Fill missing verified profile claims from subject-matched Auth0 /userinfo."""
        if auth0_user.get("email") and auth0_user.get("name") and isinstance(auth0_user.get("email_verified"), bool):
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

        if info.get("sub") != auth0_user.get("sub"):
            raise HTTPException(status_code=401, detail="Your sign-in could not be verified. Please sign in again.")
        enriched = dict(auth0_user)
        for key in ("email", "name", "picture", "nickname"):
            if not enriched.get(key) and info.get(key):
                enriched[key] = info[key]
        if (info.get("email") or "").strip().lower() == (enriched.get("email") or "").strip().lower():
            enriched["email_verified"] = info.get("email_verified") is True
        return enriched

    @staticmethod
    def get_or_create_player_profile(db: Session, auth0_user: dict[str, Any]) -> PlayerProfile:
        """Get or create a PlayerProfile based on Auth0 user data"""

        auth0_id = auth0_user.get("sub")
        email = (auth0_user.get("email") or "").strip().lower() or None
        name = auth0_user.get("name") or (email.split("@")[0] if email else None) or "Unknown Player"
        picture = auth0_user.get("picture")

        if not auth0_id:
            raise HTTPException(status_code=401, detail="Token missing subject")

        player = AuthService._find_player_by_auth0_id(db, auth0_id)
        # Lock only first-login claims; returning requests should not serialize.
        if not player and db.get_bind().dialect.name == "postgresql":
            identities = [f"auth0:{auth0_id}"] + ([f"email:{email}"] if email else [])
            for identity in sorted(identities):
                db.execute(
                    text("SELECT pg_advisory_xact_lock(hashtext(:identity))"), {"identity": f"account-link:{identity}"}
                )
            # Another request may have linked this subject while we waited.
            player = AuthService._find_player_by_auth0_id(db, auth0_id)

        if not player and email:
            matches = db.query(PlayerProfile).filter(func.lower(PlayerProfile.email) == email).with_for_update().all()
            if len(matches) > 1:
                raise HTTPException(
                    status_code=409,
                    detail="Multiple profiles use this email. Ask an admin to review the account link.",
                )
            player = matches[0] if matches else None
            linked_subject = (player.preferences or {}).get("auth0_id") if player else None
            if linked_subject and linked_subject != auth0_id:
                raise HTTPException(
                    status_code=409,
                    detail="This email is linked to a different login. Ask an admin to review the account link.",
                )
            if player and auth0_user.get("email_verified") is not True:
                raise HTTPException(
                    status_code=403,
                    detail="Verify your email address, then sign in again to connect your existing player profile.",
                )
            if player and not player.is_active:
                raise HTTPException(
                    status_code=403, detail="This player profile is inactive. Ask a club admin to review Account links."
                )

        if not player and not email:
            # Unknown subjects need an email; established subject links do not.
            raise HTTPException(
                status_code=401,
                detail="Token missing email claim — re-login with email scope or add email to the API token",
            )

        if not player:
            # Suggest fuzzy matches; only unused exact roster names can link here.
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

            # A display name is not proof of roster identity. Preserve the seed
            # row and let an admin link it rather than hitting its unique name.
            if db.query(PlayerProfile.id).filter(func.lower(PlayerProfile.name) == name.lower()).first():
                fuzzy_suggestion = legacy_name or fuzzy_suggestion
                legacy_name = None
                name = email

            # Create new player profile
            player = PlayerProfile(
                name=name,
                legacy_name=None,
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
            db.flush()
            if legacy_name:
                link_result = link_profile_to_canonical_name(db, cast("int", player.id), legacy_name)
                if not link_result["linked"]:
                    # A name alone cannot claim another profile's roster identity.
                    logger.warning(
                        "Did not auto-link new profile id=%s: legacy name '%s' belongs to another profile",
                        player.id,
                        legacy_name,
                    )
                    fuzzy_suggestion = legacy_name
                    legacy_name = None
            # Create default email preferences
            email_prefs = EmailPreferences(
                player_profile_id=player.id,
                created_at=utc_now().isoformat(),
                updated_at=utc_now().isoformat(),
            )
            db.add(email_prefs)
            db.commit()
            db.refresh(player)

            logger.info(f"Created new player profile for {name} ({email})")

            # Welcome mail only on creation, never on returning sign-in.
            try:
                _send_welcome_email(name, email, player.id)
            except Exception as exc:
                logger.warning(f"Failed to dispatch welcome email for '{name}': {exc}")
                report_exception(exc)

            # Only genuinely unknown golfers enter the pending roster queue.
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

            # Retry exact unclaimed roster matches added since first sign-in.
            if not player.legacy_name:
                legacy_name = get_canonical_name(cast("str", player.name), db) if player.name else None
                if not legacy_name:
                    legacy_name = get_canonical_name(name, db)
                if legacy_name:
                    link_result = link_profile_to_canonical_name(db, cast("int", player.id), legacy_name)
                    if link_result["linked"]:
                        update_needed = link_result["status"] == "linked"
                        logger.info(
                            "Linked returning player profile id=%s to newly canonical legacy name '%s'",
                            player.id,
                            legacy_name,
                        )
                    elif link_result["status"] == "claimed":
                        logger.warning(
                            "Did not auto-link returning profile id=%s: legacy name '%s' belongs to another profile",
                            player.id,
                            legacy_name,
                        )

            if email and not player.email and auth0_user.get("email_verified") is True:
                conflict = (
                    db.query(PlayerProfile)
                    .filter(func.lower(PlayerProfile.email) == email, PlayerProfile.id != player.id)
                    .first()
                )
                if not conflict:
                    player.email = email
                    update_needed = True

            if name and name != player.name and player.name in (None, "", "Unknown Player"):
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


def get_current_auth0_user(
    token: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Return identity claims from a verified Auth0 access token."""
    auth0_user = auth_service.verify_token(token)
    return auth_service.enrich_user_from_userinfo(auth0_user, token.credentials)


def get_current_user(
    auth0_user: dict[str, Any] = Depends(get_current_auth0_user),
    db: Session = Depends(get_db),
) -> PlayerProfile:
    """Dependency to get the current authenticated user"""

    # Get or create player profile
    try:
        player = auth_service.get_or_create_player_profile(db, auth0_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Your account could not be linked uniquely. Ask a club admin to review Account links.",
        ) from exc

    return player
