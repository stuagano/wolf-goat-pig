"""Build + persist a completed Wolf Goat Pig game.

Shared by the live game-completion endpoint and the scorecard-scan
"record a finished round" endpoint so both produce identical
GameRecord / GamePlayerResult rows.
"""

from __future__ import annotations

import logging
import math
from copy import deepcopy
from datetime import date
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.round_identity import RoundDraft

logger = logging.getLogger(__name__)

REQUIRED_HOLES = frozenset(range(1, 19))


def round_played_at(record: Any, game: Any = None) -> str | None:
    """Keep round dates separate from completion audit timestamps."""
    settings = record.game_settings
    if isinstance(settings, dict) and settings.get("played_at"):
        return settings["played_at"]
    # Older scorecard posts stored the played date only in created_at.
    if game is not None and (game.state or {}).get("source") == "scorecard_scan":
        return game.created_at
    return record.completed_at or record.created_at


def validate_round_players(players: list[dict]) -> None:
    """Reject repeated identities and names that cannot distinguish guests."""
    slots: set[str] = set()
    profiles: set[int] = set()
    names: dict[str, int | None] = {}
    for player in players:
        slot = player.get("id")
        profile = player.get("player_profile_id")
        name = " ".join((player.get("name") or "").casefold().split())
        if not slot or slot in slots or not name:
            raise HTTPException(status_code=400, detail="Round requires distinct players with nonblank names")
        if profile is not None and profile in profiles:
            raise HTTPException(status_code=400, detail="Round contains a duplicate player profile")
        if name in names and (profile is None or names[name] is None):
            raise HTTPException(status_code=400, detail="Duplicate player names require distinct player profiles")
        slots.add(slot)
        if profile is not None:
            profiles.add(profile)
        names[name] = profile


def validate_round_scores(players: list[dict], hole_history: list[dict], *, complete: bool = True) -> None:
    """Require explicit quarters for the roster; missing scores are not zeroes."""
    player_ids = {p.get("id") for p in players}
    if not player_ids or None in player_ids or len(player_ids) != len(players):
        raise HTTPException(status_code=400, detail="Round requires a valid player roster")
    holes = {entry.get("hole") for entry in hole_history}
    if len(holes) != len(hole_history):
        raise HTTPException(status_code=400, detail="Duplicate holes are not allowed")
    if (
        any(type(h) is not int for h in holes)
        or not holes.issubset(REQUIRED_HOLES)
        or (complete and holes != REQUIRED_HOLES)
    ):
        raise HTTPException(status_code=400, detail="Completion requires all holes 1-18")
    for entry in hole_history:
        quarters = entry.get("points_delta") or {}
        if set(quarters) != player_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Hole {entry.get('hole')}: scores must include every roster player and no unknown players",
            )
        if any(
            isinstance(q, bool) or not isinstance(q, (int, float)) or not math.isfinite(q) for q in quarters.values()
        ):
            raise HTTPException(status_code=400, detail="Quarter scores must be finite numbers")


def build_hole_history(
    players: list[dict[str, Any]],
    per_hole_quarters: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """Convert per-(index, hole) quarter deltas into hole_history + standings.

    player_index refers to the position of the player in `players`.
    """
    id_by_index = {i: p["id"] for i, p in enumerate(players)}
    holes: dict[int, dict[str, float]] = {}
    for entry in per_hole_quarters:
        pid = id_by_index.get(entry["player_index"])
        if pid is None or entry["hole"] not in REQUIRED_HOLES:
            raise HTTPException(status_code=400, detail="Unknown player index or hole")
        scores = holes.setdefault(entry["hole"], {})
        if pid in scores:
            raise HTTPException(status_code=400, detail="Duplicate player/hole score")
        scores[pid] = entry["quarters"]

    hole_history = [{"hole": h, "points_delta": holes[h]} for h in sorted(holes)]

    standings: dict[str, float] = {}
    for entry in hole_history:
        for pid, q in entry["points_delta"].items():
            standings[pid] = standings.get(pid, 0) + q
    return hole_history, standings


def merge_hole_history(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """Patch supplied detail only; omission is not evidence of removal."""
    merged = {h["hole"]: deepcopy(h) for h in existing}
    for entry in incoming:
        target = merged.setdefault(entry["hole"], {})
        for key, value in entry.items():
            if value is None:
                continue
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                target[key] = {**target[key], **deepcopy(value)}
            else:
                target[key] = deepcopy(value)
    return [merged[h] for h in sorted(merged)]


def persist_final_results(
    db: Session,
    game: Any,
    draft: RoundDraft,
    *,
    retracted: bool | None = None,
    accepted_roster_complete: bool | None = None,
    restore_participants: tuple[str, ...] = (),
) -> int:
    """Materialize accepted input without committing or inventing gameplay.

    This is an accepted-projection writer, not source reconciliation. Task 3
    decides which proposed field changes are accepted before invoking it.
    Explicit totals outrank computed detail; discrepancies remain inspectable
    in game_settings for reconciliation rather than silently replacing totals.
    """
    from app import models
    from app.utils.time import utc_now

    from .round_cutover import guard_writer

    guard_writer(db)
    players = [{"id": p.participant_id, "name": p.name, "player_profile_id": p.profile_id} for p in draft.players]
    if not players or any(not p["name"].strip() for p in players):
        raise HTTPException(status_code=400, detail="Round requires a nonblank roster")
    if draft.detail_coverage == "totals_only" and draft.hole_history:
        raise HTTPException(status_code=400, detail="Totals-only input cannot contain hole history")
    record = db.query(models.GameRecord).filter_by(game_id=game.game_id).one_or_none()
    rows = db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).all() if record else []
    if draft.detail_coverage != "totals_only":
        # Historical participants remain in accepted_draft and stored results.
        # New detail must cover exactly the effective ACTIVE roster, including
        # active slots omitted from the draft (omission never retracts them).
        # Only persisted retraction or explicit adjudicated operations change it;
        # never infer the roster from the cells being validated.
        inactive = ({r.participant_id for r in rows if r.is_retracted} - set(restore_participants)) | set(
            draft.removed_participant_ids
        )
        required = (
            {r.participant_id for r in rows if r.participant_id is not None} | {p["id"] for p in players}
        ) - inactive
        validate_round_scores(
            [{"id": pid} for pid in required], draft.hole_history, complete=draft.detail_coverage == "per_hole_complete"
        )

    now = utc_now().isoformat()
    is_new = record is None
    if is_new:
        record = models.GameRecord(game_id=game.game_id, created_at=game.created_at or now, completed_at=now)
        db.add(record)
        db.flush()
    rows = db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).all()
    before = _projection_snapshot(record, rows)
    state = deepcopy(dict(game.state or {}))
    prior_players = {p["id"]: p for p in state.get("players", [])}
    for result in rows:
        if result.participant_id is not None:
            prior_players.setdefault(
                result.participant_id,
                {
                    "id": result.participant_id,
                    "name": result.player_name,
                    "player_profile_id": result.player_profile_id,
                    "total_points": result.total_earnings,
                },
            )
    effective_players = {**prior_players, **{p["id"]: p for p in players}}
    history = merge_hole_history(state.get("hole_history", []), draft.hole_history)
    # Coverage describes evidence actually retained, never a fabricated round.
    coverage = "totals_only"
    if history:
        # Historic holes can predate an accepted roster extension. Validate the
        # cells that exist without manufacturing missing participant scores.
        for hole in history:
            observed = set(hole.get("points_delta") or {})
            if not observed or not observed.issubset(effective_players):
                raise HTTPException(status_code=400, detail="Retained detail contains unknown players")
            validate_round_scores([effective_players[pid] for pid in observed], [hole], complete=False)
        complete_cells = all(set(h["points_delta"]) == set(effective_players) for h in history)
        coverage = (
            "per_hole_complete" if complete_cells and {h["hole"] for h in history} == REQUIRED_HOLES else "partial"
        )
    computed = {
        pid: sum(h["points_delta"][pid] for h in history if pid in h["points_delta"]) for pid in effective_players
    }
    settings = deepcopy(record.game_settings or {})
    provenance = settings.setdefault("field_provenance", {})
    for field in ("played_on", "raw_date", "course_name", "group"):
        value = getattr(draft, field)
        if value is not None:
            if getattr(record, field) != value:
                provenance[field] = {"actor_profile_id": draft.actor_profile_id, "kind": "accepted_input"}
            setattr(record, field, value)
    if draft.played_on is not None:
        settings["played_at"] = draft.played_on.isoformat()
    added_slots = set(effective_players) - set(prior_players)
    record.roster_complete = (
        accepted_roster_complete
        if accepted_roster_complete is not None
        else bool(draft.roster_complete or (record.roster_complete and not added_slots))
    )
    record.detail_coverage = coverage
    record.total_holes_played = len(history) if history else None
    discrepancies = {}
    totals = dict(record.final_scores or {})
    # Flush state/events/record before results; any later failure still rolls
    # everything back through the caller-owned transaction.
    db.flush()
    ordered_players = sorted(draft.players, key=lambda p: computed[p.participant_id], reverse=True)
    for participant in ordered_players:
        pid = participant.participant_id
        result = next((r for r in rows if r.participant_id == pid), None)
        if result is None:
            # Adopt pre-expansion rows only with an unambiguous existing roster
            # association, never collapse distinct same-name guests.
            candidates = [
                r
                for r in rows
                if r.participant_id is None
                and (
                    r.player_profile_id == participant.profile_id
                    if participant.profile_id is not None
                    else r.player_profile_id is None and r.player_name == participant.name
                )
            ]
            matching_slots = [
                p
                for p in players
                if (
                    p["player_profile_id"] == participant.profile_id
                    if participant.profile_id is not None
                    else p["player_profile_id"] is None and p["name"] == participant.name
                )
            ]
            if candidates:
                if len(candidates) != 1 or len(matching_slots) != 1:
                    raise HTTPException(status_code=409, detail="Legacy participant association requires review")
                result = candidates[0]
            else:
                result = models.GamePlayerResult(game_record_id=record.id, created_at=now)
                db.add(result)
                rows.append(result)
        if result.is_retracted and pid not in restore_participants:
            continue
        result.participant_id = pid
        result.player_name = participant.name
        if participant.profile_id is not None:
            result.player_profile_id = participant.profile_id
        total = participant.quarters
        if total is None:
            total = result.total_earnings
        if (
            draft.detail_coverage == "per_hole_complete"
            and participant.quarters is None
            and f"players.{pid}.quarters" not in settings.get("explicit_clears", [])
            and (total is None or provenance.get(f"players.{pid}.quarters", {}).get("kind") == "complete_detail")
        ):
            total = computed[pid]
        if participant.quarters is not None or total != result.total_earnings:
            provenance[f"players.{pid}.quarters"] = {
                "actor_profile_id": draft.actor_profile_id,
                "kind": "explicit_total" if participant.quarters is not None else "complete_detail",
            }
        result.total_earnings = total
        totals[pid] = total
        if coverage == "per_hole_complete" and total != computed[pid]:
            discrepancies[pid] = {"accepted": total, "computed": computed[pid]}
        if history:
            result.hole_scores = [
                {
                    **deepcopy(h),
                    "quarters": h["points_delta"][pid],
                    "gross_score": (h.get("gross_scores") or {}).get(pid),
                }
                for h in history
                if pid in h["points_delta"]
            ]
        if coverage == "per_hole_complete":
            result.holes_won = sum(h["points_delta"][pid] > 0 for h in history)
            metrics = dict(result.performance_metrics or {})
            metrics.update(holes_played=len(history), avg_quarters_per_hole=computed[pid] / len(history))
            handicap = prior_players.get(pid, {}).get("handicap")
            if handicap is not None:
                metrics["handicap"] = handicap
            result.performance_metrics = metrics
        old_player = prior_players.get(pid, {})
        prior_players[pid] = {
            **old_player,
            "id": pid,
            "name": participant.name,
            "player_profile_id": result.player_profile_id,
            "total_points": total,
        }
        db.flush()
    settings["detail_discrepancies"] = discrepancies
    record.game_settings = settings
    record.final_scores = totals
    record.player_count = len(rows)
    record.score_eligible = bool(record.roster_complete and rows and all(r.total_earnings is not None for r in rows))
    ranked = sorted(
        rows, key=lambda r: r.total_earnings if r.total_earnings is not None else float("-inf"), reverse=True
    )
    for rank, result in enumerate(ranked, 1):
        result.final_position = rank if record.score_eligible else None
    state.update(
        game_status="completed", players=list(prior_players.values()), standings=totals, detail_coverage=coverage
    )
    if history:
        state["hole_history"] = history
        if "hole_quarters" in state:
            state["hole_quarters"] = {str(h["hole"]): deepcopy(h["points_delta"]) for h in history}
    for field in ("course_name", "group"):
        if getattr(record, field) is not None:
            state[field] = getattr(record, field)
    game.state = state
    game.game_status = "completed"
    from .round_projection_operations import apply_projection_operations

    apply_projection_operations(
        game, record, rows, draft, retracted=retracted, restore_participants=restore_participants
    )
    if is_new or before != _projection_snapshot(record, rows):
        game.revision = (game.revision or 0) + 1
        record.accepted_revision = game.revision
    db.flush()
    return game.revision


def _projection_snapshot(record: Any, rows: list) -> tuple:
    """Compare accepted content, excluding revision/audit timestamps."""
    fields = (
        "played_on",
        "raw_date",
        "course_name",
        "group",
        "roster_complete",
        "detail_coverage",
        "total_holes_played",
        "final_scores",
        "game_settings",
        "score_eligible",
        "is_retracted",
    )
    result_fields = (
        "participant_id",
        "is_retracted",
        "player_name",
        "player_profile_id",
        "total_earnings",
        "final_position",
        "holes_won",
        "hole_scores",
        "performance_metrics",
    )
    return deepcopy(
        (tuple(getattr(record, f) for f in fields), [tuple(getattr(r, f) for f in result_fields) for r in rows])
    )


def persist_completed_game(db: Session, game: Any) -> int:
    """Strict live/scan accepted correction entry point; caller owns commit."""
    from app import models

    state = game.state or {}
    players = state.get("players", [])
    validate_round_players(players)
    history = state.get("hole_history", [])
    validate_round_scores(players, history)
    existing = db.query(models.GameRecord).filter_by(game_id=game.game_id).one_or_none()
    count_before = db.query(models.GamePlayerResult).filter_by(game_record_id=existing.id).count() if existing else 0
    if existing and existing.detail_coverage is None:
        settings = deepcopy(existing.game_settings or {})
        provenance = settings.setdefault("field_provenance", {})
        for player in players:
            provenance.setdefault(
                f"players.{player['id']}.quarters", {"kind": "complete_detail", "actor_profile_id": None}
            )
        existing.game_settings = settings
    played_at = state.get("played_at")
    draft = RoundDraft(
        played_on=date.fromisoformat(played_at[:10]) if played_at else None,
        course_name=state.get("course_name"),
        players=[
            {"participant_id": p["id"], "name": p["name"], "profile_id": p.get("player_profile_id"), "quarters": None}
            for p in players
        ],
        roster_complete=True,
        detail_coverage="per_hole_complete",
        hole_history=history,
    )
    persist_final_results(db, game, draft)
    record = db.query(models.GameRecord).filter_by(game_id=game.game_id).one()
    return db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).count() - count_before
