"""UUID discussions over existing social records, with legacy alias compatibility."""

import logging
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
from ..services.round_cutover import guard_writer
from ..services.round_social import _date_keys, _notify_site_of_comment
from ..services.unified_data_service import get_unified_data_service
from ..utils.admin_auth import admin_role
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data/rounds", tags=["data"])

# Static "comments" paths have to exist before /{date}/{group}, or "comments"
# is captured as a date and the request looks up a round that isn't there.


class RoundPlayerResponse(BaseModel):
    member: str
    quarters: float | None
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
    game_id: str | None = None
    players: list[RoundPlayerResponse]
    comments: list[RoundCommentResponse]
    reactions: list[RoundReactionResponse] = Field(default_factory=list)


class RoundCommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)


def _round_players(date: str, group: str, location: str, db: Session) -> tuple[str, list]:
    service = get_unified_data_service(db=db)
    try:
        datetime.strptime(date, "%Y-%m-%d")
        is_iso_date = True
    except ValueError:
        is_iso_date = False
    # ISO links identify a year, including prior seasons. Display-date links
    # remain season-scoped for compatibility with the original shared URLs.
    rounds = service.get_all_rounds() if is_iso_date else service.get_season_rounds()
    wanted = _date_keys(date)
    players = [
        row
        for row in rounds
        if (row.date_sortable == date if is_iso_date else row.date_sortable in wanted or row.date in wanted)
        and row.group == group
        and (row.location or "") == location
    ]
    if not players:
        raise HTTPException(status_code=404, detail="Round not found")
    return players[0].date, players


def _reaction_buckets(rows, viewer_id: int | None) -> list[RoundReactionResponse]:
    grouped: dict[str, RoundReactionResponse] = {}
    seen = set()
    for reaction, name in rows:
        logical_key = (reaction.profile_id, reaction.emoji, reaction.comment_id)
        if logical_key in seen:
            continue
        seen.add(logical_key)
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
    guard_writer(db)  # Serialize ownership lookup with alias binding and other social writes.
    comment = db.query(RoundComment).filter(RoundComment.id == comment_id).first()
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    from ..services.round_social import comment_game

    comment_game(db, comment)  # Reject ambiguous unbound ownership before any write.
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
    guard_writer(db)  # Serialize ownership lookup with alias binding and other social writes.
    comment = db.query(RoundComment).filter(RoundComment.id == comment_id).first()
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    emoji = payload.emoji.strip()
    if emoji not in ROUND_REACTION_EMOJIS:
        raise HTTPException(status_code=422, detail="Pick one of the round reactions")
    from ..services.round_social import comment_game

    game_id = comment_game(db, comment)
    if game_id:
        _toggle_uuid(db, game_id, emoji, comment.id, current_user)
        return _comment_reactions(_uuid_reactions(db, game_id), comment.id, current_user.id)
    _toggle_reaction(comment.round_date, comment.round_group, comment.location, emoji, comment.id, current_user, db)
    rows = _load_reactions(comment.round_date, comment.round_group, comment.location, db)
    return _comment_reactions(rows, comment.id, current_user.id)


def _uuid_reactions(db, game_id):
    from ..services.round_social import owned_rows

    rows = owned_rows(db, RoundReaction, game_id).order_by(RoundReaction.created_at, RoundReaction.id).all()
    return [(row, db.get(PlayerProfile, row.profile_id).name) for row in rows]


@router.get("/uuid/{game_id}/discussion")
def uuid_discussion(game_id: str, db: Session = Depends(get_db)):
    from ..services.round_social import owned_rows, require_game

    require_game(db, game_id)
    reactions = _uuid_reactions(db, game_id)
    comments = owned_rows(db, RoundComment, game_id).order_by(RoundComment.created_at, RoundComment.id).all()
    return {
        "comments": [
            RoundCommentResponse(
                id=c.id,
                author_name=db.get(PlayerProfile, c.author_profile_id).name or "Player",
                author_profile_id=c.author_profile_id,
                body=c.body,
                created_at=c.created_at,
                reactions=_comment_reactions(reactions, c.id, None),
            )
            for c in comments
        ],
        "reactions": _reaction_buckets([r for r in reactions if r[0].comment_id is None], None),
    }


@router.post("/uuid/{game_id}/comments", response_model=RoundCommentResponse)
def uuid_comment(
    game_id: str,
    payload: RoundCommentCreate,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..services.round_social import require_game

    guard_writer(db)
    require_game(db, game_id)
    body = payload.body.strip()
    if not body:
        raise HTTPException(422, "Comment cannot be blank")
    comment = RoundComment(
        game_id=game_id,
        round_date=f"uuid:{game_id}",
        round_group="",
        location="",
        author_profile_id=current_user.id,
        body=body,
        created_at=utc_now().isoformat(),
    )
    db.add(comment)
    _notify_site_of_comment(comment, "Round", current_user, db)
    db.commit()
    db.refresh(comment)
    return RoundCommentResponse(
        id=comment.id,
        author_name=current_user.name or "Player",
        author_profile_id=current_user.id,
        body=body,
        created_at=comment.created_at,
        can_delete=True,
    )


def _toggle_uuid(db, game_id, emoji, comment_id, current_user):
    from ..services.round_social import owned_rows, require_game

    guard_writer(db)
    require_game(db, game_id)
    if emoji not in ROUND_REACTION_EMOJIS:
        raise HTTPException(422, "Pick one of the round reactions")
    existing = (
        owned_rows(db, RoundReaction, game_id)
        .filter_by(comment_id=comment_id, profile_id=current_user.id, emoji=emoji)
        .all()
    )
    if existing:
        for row in existing:
            db.delete(row)
    else:
        db.add(
            RoundReaction(
                game_id=game_id,
                round_date=f"uuid:{game_id}",
                round_group="",
                location="",
                comment_id=comment_id,
                profile_id=current_user.id,
                emoji=emoji,
                created_at=utc_now().isoformat(),
            )
        )
    db.commit()


@router.post("/uuid/{game_id}/reactions", response_model=list[RoundReactionResponse])
def uuid_reaction(
    game_id: str,
    payload: RoundReactionToggle,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _toggle_uuid(db, game_id, payload.emoji.strip(), None, current_user)
    return _reaction_buckets([r for r in _uuid_reactions(db, game_id) if r[0].comment_id is None], current_user.id)


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
    from ..services.round_review import round_summary
    from ..services.round_social import alias_game

    resolved = alias_game(db, date, group, location)
    if resolved:
        from ..schemas.round_identity import RoundSummary

        summary = RoundSummary(**round_summary(db, resolved))
        discussion = uuid_discussion(resolved, db)
        return RoundStoryResponse(
            date=summary.raw_date or summary.played_on or date,
            date_sortable=summary.played_on or date,
            location=location,
            group=group,
            game_id=resolved,
            players=[
                RoundPlayerResponse(member=p.name or "Player", quarters=p.quarters, player_id=p.profile_id)
                for p in summary.players
                if not p.is_retracted
            ],
            **discussion,
        )
    shown_date, players = _round_players(date, group, location, db)
    # Always key comments and reactions on YYYY-MM-DD, even if the URL used 6-Oct.
    key = players[0].date_sortable
    index = profile_ids_by_member(db)
    # The discussion URL predates saved-game UUIDs and can cover more than
    # one game. Only expose a card when every result identifies the same one.
    game_ids = {row.game_id for row in players}
    game_id = next(iter(game_ids)) if len(game_ids) == 1 else None
    return RoundStoryResponse(
        date=shown_date,
        date_sortable=key,
        location=location,
        group=group,
        game_id=game_id,
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
    from ..services.round_social import alias_game

    guard_writer(db)
    game_id = alias_game(db, date, group, location)
    if game_id:
        return uuid_comment(game_id, payload, current_user, db)
    shown_date, players = _round_players(date, group, location, db)
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
    _notify_site_of_comment(comment, shown_date, current_user, db)
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
    from ..services.round_social import alias_game

    guard_writer(db)
    game_id = alias_game(db, date, group, location)
    if game_id:
        return uuid_reaction(game_id, payload, current_user, db)
    _shown_date, players = _round_players(date, group, location, db)
    key = players[0].date_sortable
    _toggle_reaction(key, group, location, emoji, None, current_user, db)
    return _reactions(key, group, location, db, viewer_id=current_user.id)
