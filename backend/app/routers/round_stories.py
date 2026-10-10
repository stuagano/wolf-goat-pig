"""A shareable page for one historical foursome, plus its comments.

The round identity is date + group + location — the same grouping as
GET /data/leaderboard/rounds. Sheet rounds like the Oct 6 game have no
GameRecord, so comments cannot be keyed by an app game id.
"""

from datetime import datetime
from typing import Any
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PlayerProfile, RoundComment, RoundReaction
from ..services.auth_service import get_current_auth0_user, get_current_user
from ..services.player_name_index import profile_id_for_member, profile_ids_by_member
from ..services.unified_data_service import get_unified_data_service
from ..utils.admin_auth import admin_role
from ..utils.time import utc_now

router = APIRouter(prefix="/data/rounds", tags=["data"])

# Static "comments" paths have to exist before /{date}/{group}, or "comments"
# is captured as a date and the request looks up a round that isn't there.


class RoundPlayerResponse(BaseModel):
    member: str
    quarters: int
    player_id: int | None = None


# Short golf set. Adding one means a new picker button, nothing else.
ROUND_REACTION_EMOJIS = ("🏌️", "😂", "😭", "🔥", "👏", "🤔")


class RoundReactionResponse(BaseModel):
    emoji: str
    count: int
    reactor_names: list[str]
    mine: bool = False


class RoundReactionToggle(BaseModel):
    emoji: str


class RoundCommentResponse(BaseModel):
    id: int
    author_name: str
    author_profile_id: int
    body: str
    created_at: str
    can_delete: bool = False
    reactions: list[RoundReactionResponse] = Field(default_factory=list)


class RoundStoryResponse(BaseModel):
    date: str
    date_sortable: str
    location: str
    group: str
    players: list[RoundPlayerResponse]
    comments: list[RoundCommentResponse]
    reactions: list[RoundReactionResponse] = Field(default_factory=list)


class RoundCommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


def _display_dates(dt: datetime) -> set[str]:
    """Sheet dates are "6-Oct" or "06-Oct". Don't use %-d; glibc-only."""
    padded = dt.strftime("%d-%b")
    return {padded, padded.lstrip("0")}


def _date_keys(date: str) -> set[str]:
    """Accept YYYY-MM-DD and the sheet display form (6-Oct or 06-Oct).

    Shared links from the first deploy used the display date. The year isn't
    on the sheet, so a display date matches any season round on that day.
    """
    keys = {date}
    try:
        keys.update(_display_dates(datetime.strptime(date, "%Y-%m-%d")))
        return keys
    except ValueError:
        pass
    # Year is a dummy; only the day and month are added to the key set.
    try:
        keys.update(_display_dates(datetime.strptime(f"{date}-2000", "%d-%b-%Y")))
    except ValueError:
        pass
    return keys


def _round_players(date: str, group: str, location: str, db: Session) -> tuple[str, list]:
    service = get_unified_data_service(db=db)
    wanted = _date_keys(date)
    players = [
        row
        for row in service.get_season_rounds()
        if (row.date_sortable in wanted or row.date in wanted)
        and row.group == group
        and (row.location or "") == location
    ]
    if not players:
        raise HTTPException(status_code=404, detail="Round not found")
    return players[0].date, players


def _reaction_buckets(rows, viewer_id: int | None) -> list[RoundReactionResponse]:
    grouped: dict[str, RoundReactionResponse] = {}
    for reaction, name in rows:
        bucket = grouped.get(reaction.emoji)
        if bucket is None:
            bucket = RoundReactionResponse(emoji=reaction.emoji, count=0, reactor_names=[])
            grouped[reaction.emoji] = bucket
        bucket.count += 1
        bucket.reactor_names.append(name or "Player")
        if viewer_id is not None and reaction.profile_id == viewer_id:
            bucket.mine = True
    return list(grouped.values())


def _load_reactions(date: str, group: str, location: str, db: Session):
    return (
        db.query(RoundReaction, PlayerProfile.name)
        .join(PlayerProfile, PlayerProfile.id == RoundReaction.profile_id)
        .filter(
            RoundReaction.round_date == date,
            RoundReaction.round_group == group,
            RoundReaction.location == location,
        )
        .order_by(RoundReaction.created_at.asc(), RoundReaction.id.asc())
        .all()
    )


def _reactions(
    date: str, group: str, location: str, db: Session, viewer_id: int | None = None
) -> list[RoundReactionResponse]:
    """Emoji on the round itself, not on a comment."""
    rows = [row for row in _load_reactions(date, group, location, db) if row[0].comment_id is None]
    return _reaction_buckets(rows, viewer_id)


def _comment_reactions(rows, comment_id: int, viewer_id: int | None) -> list[RoundReactionResponse]:
    return _reaction_buckets([row for row in rows if row[0].comment_id == comment_id], viewer_id)


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
    reactions = _load_reactions(date, group, location, db)
    return [
        RoundCommentResponse(
            id=comment.id,
            author_name=name or "Player",
            author_profile_id=comment.author_profile_id,
            body=comment.body,
            created_at=comment.created_at,
            can_delete=False,
            reactions=_comment_reactions(reactions, comment.id, None),
        )
        for comment, name in rows
    ]


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
    # Comment reactions go with the comment. Round reactions stay.
    db.query(RoundReaction).filter(RoundReaction.comment_id == comment.id).delete(synchronize_session=False)
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}


@router.post("/comments/{comment_id}/reactions", response_model=list[RoundReactionResponse])
def toggle_comment_reaction(
    comment_id: int,
    payload: RoundReactionToggle,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add this player's emoji to one comment, or remove it."""
    comment = db.query(RoundComment).filter(RoundComment.id == comment_id).first()
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    emoji = payload.emoji.strip()
    if emoji not in ROUND_REACTION_EMOJIS:
        raise HTTPException(status_code=422, detail="Pick one of the round reactions")
    _toggle_reaction(comment.round_date, comment.round_group, comment.location, emoji, comment.id, current_user, db)
    rows = _load_reactions(comment.round_date, comment.round_group, comment.location, db)
    return _comment_reactions(rows, comment.id, current_user.id)


@router.get("/{date}/{group}", response_model=RoundStoryResponse)
def get_round_story(
    date: str,
    group: str,
    location: str = Query("", description="Course name; empty when the sheet left it blank"),
    db: Session = Depends(get_db),
) -> Any:
    """Players, quarter totals, comments, and reactions for one foursome."""
    date = unquote(date)
    group = unquote(group)
    shown_date, players = _round_players(date, group, location, db)
    # Always key comments and reactions on YYYY-MM-DD, even if the URL used 6-Oct.
    key = players[0].date_sortable
    index = profile_ids_by_member(db)
    return RoundStoryResponse(
        date=shown_date,
        date_sortable=key,
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
        comments=_comments(key, group, location, db),
        reactions=_reactions(key, group, location, db),
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
    _shown_date, players = _round_players(date, group, location, db)
    key = players[0].date_sortable
    comment = RoundComment(
        round_date=key,
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
        reactions=[],
    )


def _toggle_reaction(
    date: str,
    group: str,
    location: str,
    emoji: str,
    comment_id: int | None,
    current_user: PlayerProfile,
    db: Session,
) -> None:
    existing = (
        db.query(RoundReaction)
        .filter(
            RoundReaction.round_date == date,
            RoundReaction.round_group == group,
            RoundReaction.location == location,
            RoundReaction.comment_id == comment_id,
            RoundReaction.profile_id == current_user.id,
            RoundReaction.emoji == emoji,
        )
        .first()
    )
    if existing is None:
        db.add(
            RoundReaction(
                round_date=date,
                round_group=group,
                location=location,
                comment_id=comment_id,
                profile_id=current_user.id,
                emoji=emoji,
                created_at=utc_now().isoformat(),
            )
        )
    else:
        db.delete(existing)
    db.commit()


@router.post("/{date}/{group}/reactions", response_model=list[RoundReactionResponse])
def toggle_round_reaction(
    date: str,
    group: str,
    payload: RoundReactionToggle,
    location: str = Query(""),
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add this player's emoji to the round, or remove it if it's already theirs."""
    date = unquote(date)
    group = unquote(group)
    emoji = payload.emoji.strip()
    if emoji not in ROUND_REACTION_EMOJIS:
        raise HTTPException(status_code=422, detail="Pick one of the round reactions")
    _shown_date, players = _round_players(date, group, location, db)
    key = players[0].date_sortable
    _toggle_reaction(key, group, location, emoji, None, current_user, db)
    return _reactions(key, group, location, db, viewer_id=current_user.id)
