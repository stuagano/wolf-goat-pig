"""Explicit adjudicated operations for the single final-results writer.

No inference from missing rows, and no deletion of historical result evidence.
Callers authorize these accepted operations before invoking the writer.
"""

from copy import deepcopy

from fastapi import HTTPException


def active_projection(record, rows, *, roster_complete):
    """Shared accepted roster policy; historical rows never imply active scores."""
    active = [r for r in rows if not r.is_retracted]
    totals = {r.participant_id: r.total_earnings for r in active}
    eligible = bool(
        not record.is_retracted and roster_complete and active and all(r.total_earnings is not None for r in active)
    )
    return active, totals, eligible


def apply_projection_operations(game, record, rows, draft, *, retracted=None, restore_participants=()):
    by_slot = {r.participant_id: r for r in rows}
    requested = set(draft.removed_participant_ids) | set(restore_participants)
    if not requested <= set(by_slot):
        raise HTTPException(400, "Explicit operation references an unknown accepted slot")
    for slot in draft.removed_participant_ids:
        by_slot[slot].is_retracted = True
    for slot in restore_participants:
        by_slot[slot].is_retracted = False
    if retracted is not None:
        record.is_retracted = retracted
    settings = deepcopy(record.game_settings or {})
    cleared = set(settings.get("explicit_clears", []))
    cleared.update(draft.clear_fields)
    for player in draft.players:
        if player.quarters is not None and f"players.{player.participant_id}.quarters" not in draft.clear_fields:
            cleared.discard(f"players.{player.participant_id}.quarters")
    if cleared or "explicit_clears" in settings:
        settings["explicit_clears"] = sorted(cleared)
    for path in draft.clear_fields:
        parts = path.split(".")
        if len(parts) == 1:
            setattr(record, path, None)
            if path == "played_on":
                settings.pop("played_at", None)
        else:
            row = by_slot.get(parts[1])
            if row is None:
                raise HTTPException(400, "Clear requires an accepted stable slot")
            setattr(row, {"quarters": "total_earnings", "profile_id": "player_profile_id"}[parts[2]], None)
    record.game_settings = settings
    previous_order = {p["id"]: i for i, p in enumerate((game.state or {}).get("players", []))}
    active, totals, eligible = active_projection(record, rows, roster_complete=record.roster_complete)
    active.sort(key=lambda r: (previous_order.get(r.participant_id, len(previous_order)), r.participant_id))
    state = deepcopy(dict(game.state or {}))
    previous = {p["id"]: p for p in state.get("players", [])}
    state["players"] = [
        {
            **previous.get(r.participant_id, {}),
            "id": r.participant_id,
            "name": r.player_name,
            "player_profile_id": r.player_profile_id,
            "total_points": r.total_earnings,
        }
        for r in active
    ]
    state["standings"] = totals
    for field in ("course_name", "group"):
        if field in draft.clear_fields:
            state.pop(field, None)
    record.final_scores = totals
    record.player_count = len(active)
    record.score_eligible = eligible
    for rank, row in enumerate(sorted(active, key=lambda r: r.total_earnings or 0, reverse=True), 1):
        row.final_position = rank if record.score_eligible else None
    for row in rows:
        if row.is_retracted:
            row.final_position = None
    game.state = state
