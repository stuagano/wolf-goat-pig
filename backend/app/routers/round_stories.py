"""A shareable page for one historical foursome, plus its comments.

The round identity is date + group + location — the same grouping as
GET /data/leaderboard/rounds. Sheet rounds like the Oct 6 game have no
GameRecord, so comments cannot be keyed by an app game id.
"""

from typing import Any
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PlayerProfile, RoundComment
from ..services.auth_service import get_current_auth0_user, get_current_user
from ..services.player_name_index import profile_id_for_member, profile_ids_by_member
from ..services.unified_data_service import get_unified_data_service
from ..utils.admin_auth import admin_role
from ..utils.time import utc_now

router = APIRouter(prefix="/data/rounds", tags=["data"])


class RoundPlayerResponse(BaseModel):
    member: str
    quarters: int
    player_id: int | None = None


class RoundCommentResponse(BaseModel):
    id: int
    author_name: str
    author_profile_id: int
    body: str
    created_at: str
    can_delete: bool = False


class RoundStoryResponse(BaseModel):
    date: str
    date_sortable: str
    location: str
    group: str
    players: list[RoundPlayerResponse]
    comments: list[RoundCommentResponse]


class RoundCommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


def _round_players(date: str, group: str, location: str, db: Session) -> tuple[str, list]:
    service = get_unified_data_service(db=db)
    players = [
        row
        for row in service.get_season_rounds()
        if row.date_sortable == date and row.group == group and (row.location or "") == location
    ]
    if not players:
        raise HTTPException(status_code=404, detail="Round not found")
    return players[0].date, players


def _comments(date: str, group: str, location: str, db: Session) -> list[RoundCommentResponse]:
    rows = (
        db.query(RoundComment, PlayerProfile.name)
        .join(PlayerProfile, PlayerProfile.id == RoundComment.author_profile_id)
        .filter(
            RoundComment.round_date == date,
            RoundComment.round_group == group,
            RoundComment.location == location,
        )
        .order_by(RoundComment.created_at.asc(), RoundComment.id.asc())
        .all()
    )
    return [
        RoundCommentResponse(
            id=comment.id,
            author_name=name or "Player",
            author_profile_id=comment.author_profile_id,
            body=comment.body,
            created_at=comment.created_at,
            can_delete=False,
        )
        for comment, name in rows
    ]


@router.get("/{date}/{group}", response_model=RoundStoryResponse)
def get_round_story(
    date: str,
    group: str,
    location: str = Query("", description="Course name; empty when the sheet left it blank"),
    db: Session = Depends(get_db),
) -> Any:
    """Players, quarter totals, and comments for one foursome."""
    date = unquote(date)
    group = unquote(group)
    shown_date, players = _round_players(date, group, location, db)
    index = profile_ids_by_member(db)
    return RoundStoryResponse(
        date=shown_date,
        date_sortable=date,
        location=location,
        group=group,
        players=[
            RoundPlayerResponse(
                member=row.member,
                quarters=row.score,
                player_id=profile_id_for_member(row.member, index),
            )
            for row in players
        ],
        comments=_comments(date, group, location, db),
    )


@router.post("/{date}/{group}/comments", response_model=RoundCommentResponse)
def add_round_comment(
    date: str,
    group: str,
    payload: RoundCommentCreate,
    location: str = Query(""),
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Signed-in players can add a note. The round must already exist."""
    date = unquote(date)
    group = unquote(group)
    _round_players(date, group, location, db)
    comment = RoundComment(
        round_date=date,
        round_group=group,
        location=location,
        author_profile_id=current_user.id,
        body=payload.body.strip(),
        created_at=utc_now().isoformat(),
    )
    if not comment.body:
        raise HTTPException(status_code=422, detail="Comment cannot be blank")
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return RoundCommentResponse(
        id=comment.id,
        author_name=current_user.name or "Player",
        author_profile_id=current_user.id,
        body=comment.body,
        created_at=comment.created_at,
        can_delete=True,
    )


@router.delete("/comments/{comment_id}")
def delete_round_comment(
    comment_id: int,
    current_user: PlayerProfile = Depends(get_current_user),
    auth0_user: dict[str, Any] = Depends(get_current_auth0_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """The author or an admin can remove a comment."""
    comment = db.query(RoundComment).filter(RoundComment.id == comment_id).first()
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    is_admin = admin_role(db, auth0_user) != "normal"
    if comment.author_profile_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You can only delete your own comment")
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}
