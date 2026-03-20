"""
Matchmaking Router

Handles match suggestions, accept/decline responses, and the
"create a tee time together" flow once all players accept a match.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.auth_service import get_current_user
from ..services.email_service import get_email_service
from ..services.matchmaking_service import MatchmakingService
from ..services.notification_service import get_notification_service
from ..utils.api_helpers import ApiResponse, handle_api_errors

logger = logging.getLogger("app.routers.matchmaking")

router = APIRouter(prefix="/matchmaking", tags=["matchmaking"])

# Frontend URL for deep links in emails
_APP_URL = os.getenv("FRONTEND_URL", "")


# ============================================================================
# Helper: build player availability data for matchmaking
# ============================================================================


def _get_all_players_availability(db: Session) -> List[Dict[str, Any]]:
    """Fetch all players with their availability for matchmaking."""
    players = db.query(models.PlayerProfile).filter(
        models.PlayerProfile.is_active == 1
    ).all()

    all_players_data: List[Dict[str, Any]] = []
    for player in players:
        player_data: Dict[str, Any] = {
            "player_id": player.id,
            "player_name": player.name,
            "email": player.email,
            "availability": [],
        }
        availability = (
            db.query(models.PlayerAvailability)
            .filter(models.PlayerAvailability.player_profile_id == player.id)
            .all()
        )
        for avail in availability:
            player_data["availability"].append({
                "day_of_week": avail.day_of_week,
                "is_available": avail.is_available,
                "available_from_time": avail.available_from_time,
                "available_to_time": avail.available_to_time,
                "notes": avail.notes,
            })
        all_players_data.append(player_data)

    return all_players_data


def _get_recent_match_history(db: Session, days: int = 7) -> List[Dict[str, Any]]:
    """Get recent match history for filtering."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    recent_matches = (
        db.query(models.MatchSuggestion)
        .filter(models.MatchSuggestion.created_at >= cutoff)
        .all()
    )
    history: List[Dict[str, Any]] = []
    for match in recent_matches:
        match_players = (
            db.query(models.MatchPlayer)
            .filter(models.MatchPlayer.match_suggestion_id == match.id)
            .all()
        )
        history.append({
            "created_at": match.created_at,
            "players": [{"player_id": mp.player_profile_id} for mp in match_players],
        })
    return history


def _save_match_to_db(
    db: Session,
    match_data: Dict[str, Any],
) -> models.MatchSuggestion:
    """Save a match suggestion and its players to the database."""
    now = datetime.now(timezone.utc).isoformat()
    expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    match = models.MatchSuggestion(
        day_of_week=match_data["day_of_week"],
        overlap_start=match_data["overlap_start"],
        overlap_end=match_data["overlap_end"],
        suggested_tee_time=match_data["suggested_tee_time"],
        match_quality_score=match_data["match_quality"],
        status="pending",
        created_at=now,
        expires_at=expires,
    )
    db.add(match)
    db.flush()  # get the match.id

    for player in match_data["players"]:
        mp = models.MatchPlayer(
            match_suggestion_id=match.id,
            player_profile_id=player["player_id"],
            player_name=player["player_name"],
            player_email=player.get("email", ""),
            created_at=now,
        )
        db.add(mp)

    db.commit()
    db.refresh(match)
    return match


def _notify_match_players(
    db: Session,
    match: models.MatchSuggestion,
    match_data: Dict[str, Any],
) -> int:
    """Send in-app notifications AND emails to all players in a match."""
    notification_service = get_notification_service()
    email_service = get_email_service()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_name = day_names[match_data["day_of_week"]]

    player_names = [p["player_name"] for p in match_data["players"]]
    group_str = ", ".join(player_names[:-1]) + f" and {player_names[-1]}"

    count = 0
    for player in match_data["players"]:
        # In-app notification
        try:
            notification_service.send_notification(
                player_id=player["player_id"],
                notification_type="match_found",
                message=(
                    f"Golf match found for {day_name}! "
                    f"You've been matched with {group_str}. "
                    f"Available {match_data['overlap_start']} - {match_data['overlap_end']}. "
                    f"Suggested tee time: {match_data['suggested_tee_time']}."
                ),
                db=db,
                data={
                    "match_suggestion_id": match.id,
                    "day_of_week": match_data["day_of_week"],
                    "day_name": day_name,
                    "overlap_start": match_data["overlap_start"],
                    "overlap_end": match_data["overlap_end"],
                    "suggested_tee_time": match_data["suggested_tee_time"],
                    "players": player_names,
                },
            )
            count += 1
        except Exception as e:
            logger.error(f"Failed to send in-app notification to player {player['player_id']}: {e}")

        # Email notification
        player_email = player.get("email")
        if player_email and email_service.is_configured():
            try:
                email_service.send_match_found(
                    to_email=player_email,
                    player_name=player["player_name"],
                    match_day=day_name,
                    overlap_start=match_data["overlap_start"],
                    overlap_end=match_data["overlap_end"],
                    suggested_tee_time=match_data["suggested_tee_time"],
                    group_players=player_names,
                    match_id=cast(int, match.id),
                    app_url=_APP_URL,
                )
                logger.info(f"Sent match-found email to {player_email}")
            except Exception as e:
                logger.error(f"Failed to email player {player_email}: {e}")

    return count


# ============================================================================
# Auto-trigger: called after availability is saved
# ============================================================================


def run_matchmaking_for_player(
    player_id: int,
    db: Session,
    min_overlap_hours: float = 2.0,
) -> List[Dict[str, Any]]:
    """
    Run matchmaking for a specific player after they save availability.

    Only creates matches that include this player and that haven't
    been suggested before (within the last 7 days).

    Returns list of new match data dicts that were created.
    """
    all_players_data = _get_all_players_availability(db)

    # Find all potential matches
    matches = MatchmakingService.find_matches(
        all_players_data,
        min_overlap_hours=min_overlap_hours,
    )

    # Only keep matches that include this player
    player_matches = [
        m for m in matches
        if any(p["player_id"] == player_id for p in m["players"])
    ]

    if not player_matches:
        return []

    # Filter out recently suggested matches
    recent_history = _get_recent_match_history(db, days=7)
    filtered = MatchmakingService.filter_recent_matches(
        player_matches, recent_history, days_between_matches=3
    )

    # Also check for exact duplicate player groups already in DB
    existing_groups = set()
    recent_db_matches = (
        db.query(models.MatchSuggestion)
        .filter(
            models.MatchSuggestion.created_at >= (
                datetime.now(timezone.utc) - timedelta(days=7)
            ).isoformat(),
            models.MatchSuggestion.status.in_(["pending", "accepted"]),
        )
        .all()
    )
    for dbm in recent_db_matches:
        players = (
            db.query(models.MatchPlayer)
            .filter(models.MatchPlayer.match_suggestion_id == dbm.id)
            .all()
        )
        group_key = tuple(sorted(p.player_profile_id for p in players))
        existing_groups.add(group_key)

    new_matches: List[Dict[str, Any]] = []
    for match_data in filtered[:3]:  # limit to top 3 new matches
        group_key = tuple(sorted(p["player_id"] for p in match_data["players"]))
        if group_key in existing_groups:
            continue

        # Save to DB
        db_match = _save_match_to_db(db, match_data)

        # Send in-app notifications
        notified = _notify_match_players(db, db_match, match_data)

        match_data["match_suggestion_id"] = db_match.id
        match_data["notifications_sent"] = notified
        new_matches.append(match_data)
        existing_groups.add(group_key)

    return new_matches


# ============================================================================
# GET /matchmaking/my-matches - Get matches for the current user
# ============================================================================


@router.get("/my-matches", response_model=List[schemas.MatchSuggestionResponse])
@handle_api_errors(operation_name="get my matches")
async def get_my_matches(
    status: Optional[str] = Query(None, description="Filter by status: pending, accepted, declined, expired"),
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[schemas.MatchSuggestionResponse]:
    """Get all match suggestions that include the current user."""
    # Find match IDs where current user is a player
    my_match_ids = (
        db.query(models.MatchPlayer.match_suggestion_id)
        .filter(models.MatchPlayer.player_profile_id == current_user.id)
        .subquery()
    )

    query = db.query(models.MatchSuggestion).filter(
        models.MatchSuggestion.id.in_(my_match_ids)
    )

    if status:
        query = query.filter(models.MatchSuggestion.status == status)

    matches = query.order_by(models.MatchSuggestion.created_at.desc()).all()

    result: List[schemas.MatchSuggestionResponse] = []
    for match in matches:
        players = (
            db.query(models.MatchPlayer)
            .filter(models.MatchPlayer.match_suggestion_id == match.id)
            .all()
        )
        player_responses = [
            schemas.MatchPlayerResponse(
                id=cast(int, p.id),
                match_suggestion_id=cast(int, p.match_suggestion_id),
                player_profile_id=cast(int, p.player_profile_id),
                player_name=cast(str, p.player_name),
                player_email=cast(str, p.player_email),
                response=p.response,
                responded_at=p.responded_at,
                created_at=cast(str, p.created_at),
            )
            for p in players
        ]
        result.append(schemas.MatchSuggestionResponse(
            id=cast(int, match.id),
            day_of_week=cast(int, match.day_of_week),
            suggested_date=match.suggested_date,
            overlap_start=cast(str, match.overlap_start),
            overlap_end=cast(str, match.overlap_end),
            suggested_tee_time=cast(str, match.suggested_tee_time),
            match_quality_score=cast(float, match.match_quality_score),
            status=cast(str, match.status),
            notification_sent=bool(match.notification_sent),
            created_at=cast(str, match.created_at),
            expires_at=cast(str, match.expires_at),
            players=player_responses,
        ))

    return result


# ============================================================================
# POST /matchmaking/matches/{match_id}/respond - Accept or decline
# ============================================================================


@router.post("/matches/{match_id}/respond")
@handle_api_errors(operation_name="respond to match")
async def respond_to_match(
    match_id: int = Path(description="Match suggestion ID"),
    response_body: schemas.MatchResponseRequest = ...,
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Accept or decline a match suggestion.

    When all players accept, the match status changes to 'accepted'
    and players are notified that they can book a tee time together.
    """
    # Verify match exists
    match = db.query(models.MatchSuggestion).filter(
        models.MatchSuggestion.id == match_id
    ).first()
    if not match:
        raise HTTPException(status_code=404, detail=f"Match suggestion {match_id} not found")

    if match.status not in ("pending",):
        raise HTTPException(
            status_code=400,
            detail=f"Match is already '{match.status}' and cannot be responded to",
        )

    # Verify current user is in this match
    match_player = (
        db.query(models.MatchPlayer)
        .filter(
            models.MatchPlayer.match_suggestion_id == match_id,
            models.MatchPlayer.player_profile_id == current_user.id,
        )
        .first()
    )
    if not match_player:
        raise HTTPException(status_code=403, detail="You are not part of this match")

    if match_player.response is not None:
        raise HTTPException(
            status_code=400,
            detail=f"You have already responded with '{match_player.response}'",
        )

    now = datetime.now(timezone.utc).isoformat()
    match_player.response = response_body.response  # type: ignore
    match_player.responded_at = now  # type: ignore
    match_player.updated_at = now  # type: ignore
    db.commit()

    response_action = response_body.response
    logger.info(
        f"Player {current_user.id} ({current_user.name}) "
        f"{response_action} match {match_id}"
    )

    # If declined, mark the whole match as declined
    if response_action == "declined":
        match.status = "declined"  # type: ignore
        db.commit()

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = day_names[cast(int, match.day_of_week)]

        # Notify other players (in-app + email)
        notification_service = get_notification_service()
        email_service = get_email_service()
        all_players = (
            db.query(models.MatchPlayer)
            .filter(models.MatchPlayer.match_suggestion_id == match_id)
            .all()
        )
        for p in all_players:
            if p.player_profile_id != current_user.id:
                try:
                    notification_service.send_notification(
                        player_id=cast(int, p.player_profile_id),
                        notification_type="match_declined",
                        message=(
                            f"{current_user.name} declined the match. "
                            f"We'll keep looking for new matches!"
                        ),
                        db=db,
                        data={"match_suggestion_id": match_id},
                    )
                except Exception as e:
                    logger.error(f"Failed to send decline notification: {e}")

                # Email
                if p.player_email and email_service.is_configured():
                    try:
                        email_service.send_match_declined(
                            to_email=cast(str, p.player_email),
                            player_name=cast(str, p.player_name),
                            decliner_name=cast(str, current_user.name),
                            match_day=day_name,
                            app_url=_APP_URL,
                        )
                    except Exception as e:
                        logger.error(f"Failed to email decline to {p.player_email}: {e}")

        return {
            "match_id": match_id,
            "your_response": "declined",
            "match_status": "declined",
            "message": "Match declined. Other players have been notified.",
        }

    # If accepted, check if all players have accepted
    all_players = (
        db.query(models.MatchPlayer)
        .filter(models.MatchPlayer.match_suggestion_id == match_id)
        .all()
    )

    all_accepted = all(p.response == "accepted" for p in all_players)

    if all_accepted:
        match.status = "accepted"  # type: ignore
        db.commit()

        # Notify all players that the match is confirmed (in-app + email)
        notification_service = get_notification_service()
        email_service = get_email_service()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = day_names[cast(int, match.day_of_week)]
        player_names = [cast(str, p.player_name) for p in all_players]

        for p in all_players:
            try:
                notification_service.send_notification(
                    player_id=cast(int, p.player_profile_id),
                    notification_type="match_confirmed",
                    message=(
                        f"Everyone's in! Your {day_name} match with "
                        f"{', '.join(n for n in player_names if n != p.player_name)} "
                        f"is confirmed. Time to book a tee time!"
                    ),
                    db=db,
                    data={
                        "match_suggestion_id": match_id,
                        "day_name": day_name,
                        "overlap_start": match.overlap_start,
                        "overlap_end": match.overlap_end,
                        "suggested_tee_time": match.suggested_tee_time,
                        "players": player_names,
                        "action": "book_tee_time",
                    },
                )
            except Exception as e:
                logger.error(f"Failed to send confirmation notification: {e}")

            # Email — "match confirmed, go book!"
            if p.player_email and email_service.is_configured():
                try:
                    email_service.send_match_confirmed(
                        to_email=cast(str, p.player_email),
                        player_name=cast(str, p.player_name),
                        match_day=day_name,
                        overlap_start=cast(str, match.overlap_start),
                        overlap_end=cast(str, match.overlap_end),
                        suggested_tee_time=cast(str, match.suggested_tee_time),
                        group_players=player_names,
                        app_url=_APP_URL,
                    )
                except Exception as e:
                    logger.error(f"Failed to email confirmation to {p.player_email}: {e}")

        return {
            "match_id": match_id,
            "your_response": "accepted",
            "match_status": "accepted",
            "all_accepted": True,
            "message": (
                "All players have accepted! "
                "You can now book a tee time together."
            ),
            "players": [p.player_name for p in all_players],
        }

    # Some players haven't responded yet
    pending_count = sum(1 for p in all_players if p.response is None)
    accepted_count = sum(1 for p in all_players if p.response == "accepted")

    # Notify other players that someone accepted
    notification_service = get_notification_service()
    day_name = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday",
    ][match.day_of_week]

    for p in all_players:
        if p.player_profile_id != current_user.id and p.response is None:
            try:
                notification_service.send_notification(
                    player_id=cast(int, p.player_profile_id),
                    notification_type="match_player_accepted",
                    message=(
                        f"{current_user.name} accepted the match! "
                        f"{accepted_count}/{len(all_players)} players confirmed. "
                        f"Waiting for your response."
                    ),
                    db=db,
                    data={"match_suggestion_id": match_id},
                )
            except Exception as e:
                logger.error(f"Failed to send acceptance notification: {e}")

            # Email nudge — "someone accepted, we need you!"
            if p.player_email and email_service.is_configured():
                try:
                    email_service.send_match_player_accepted(
                        to_email=cast(str, p.player_email),
                        player_name=cast(str, p.player_name),
                        accepter_name=cast(str, current_user.name),
                        match_day=day_name,
                        accepted_count=accepted_count,
                        total_count=len(all_players),
                        app_url=_APP_URL,
                    )
                except Exception as e:
                    logger.error(f"Failed to email nudge to {p.player_email}: {e}")

    return {
        "match_id": match_id,
        "your_response": "accepted",
        "match_status": "pending",
        "all_accepted": False,
        "accepted_count": accepted_count,
        "pending_count": pending_count,
        "message": (
            f"You've accepted! Waiting for {pending_count} more "
            f"player{'s' if pending_count != 1 else ''} to respond."
        ),
    }


# ============================================================================
# GET /matchmaking/matches/{match_id} - Get match details
# ============================================================================


@router.get("/matches/{match_id}")
@handle_api_errors(operation_name="get match details")
async def get_match_details(
    match_id: int = Path(description="Match suggestion ID"),
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get full details of a match suggestion including all player responses."""
    match = db.query(models.MatchSuggestion).filter(
        models.MatchSuggestion.id == match_id
    ).first()
    if not match:
        raise HTTPException(status_code=404, detail=f"Match suggestion {match_id} not found")

    # Verify current user is in this match
    my_player = (
        db.query(models.MatchPlayer)
        .filter(
            models.MatchPlayer.match_suggestion_id == match_id,
            models.MatchPlayer.player_profile_id == current_user.id,
        )
        .first()
    )
    if not my_player:
        raise HTTPException(status_code=403, detail="You are not part of this match")

    all_players = (
        db.query(models.MatchPlayer)
        .filter(models.MatchPlayer.match_suggestion_id == match_id)
        .all()
    )

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    return {
        "id": match.id,
        "day_of_week": match.day_of_week,
        "day_name": day_names[cast(int, match.day_of_week)],
        "suggested_date": match.suggested_date,
        "overlap_start": match.overlap_start,
        "overlap_end": match.overlap_end,
        "suggested_tee_time": match.suggested_tee_time,
        "match_quality_score": match.match_quality_score,
        "status": match.status,
        "created_at": match.created_at,
        "expires_at": match.expires_at,
        "players": [
            {
                "player_profile_id": p.player_profile_id,
                "player_name": p.player_name,
                "response": p.response,
                "responded_at": p.responded_at,
                "is_me": p.player_profile_id == current_user.id,
            }
            for p in all_players
        ],
        "all_accepted": all(p.response == "accepted" for p in all_players),
        "can_book": (
            match.status == "accepted"
            and all(p.response == "accepted" for p in all_players)
        ),
    }
