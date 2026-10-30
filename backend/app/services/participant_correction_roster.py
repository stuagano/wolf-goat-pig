"""Exact legacy roster matching; never infer identity from profile ownership."""

from copy import deepcopy

from fastapi import HTTPException

from app import models


def values(row):
    return {c.name: deepcopy(getattr(row, c.name)) for c in row.__table__.columns}


def refuse(codes):
    raise HTTPException(
        409,
        "Identity review required ["
        + ", ".join(codes)
        + "]; correction refused. Review these categories in round identity reconciliation before retrying; "
        "do not merge profiles or remove protected evidence to bypass this check.",
    )


def roster_context(db, record, result, replacement_id):
    game = (
        db.query(models.GameStateModel)
        .filter_by(game_id=record.game_id)
        .populate_existing()
        .with_for_update()
        .one_or_none()
    )
    players = (
        db.query(models.GamePlayer)
        .filter_by(game_id=record.game_id)
        .order_by(models.GamePlayer.id)
        .populate_existing()
        .with_for_update()
        .all()
    )
    snapshot = {"game": values(game) if game else None, "players": [values(p) for p in players]}
    state_players = (game.state or {}).get("players", []) if game else []
    if not isinstance(state_players, list) or any(not isinstance(p, dict) for p in state_players):
        refuse(["malformed_state_roster"])
    if not state_players and not players:
        return game, players, snapshot, None
    if not game or game.game_status != "completed":
        refuse(["completed_legacy_roster_required"])
    # Exact name and slot matching only; no fuzzy/profile-derived identity guesses.
    matches = [p for p in state_players if p.get("name") == result.player_name]
    normalized_name = " ".join((result.player_name or "").split()).casefold()
    same_names = [
        p
        for p in state_players
        if isinstance(p.get("name"), str) and " ".join(p["name"].split()).casefold() == normalized_name
    ]
    ids = [p.get("id") for p in state_players]
    if (
        len(matches) != 1
        or len(same_names) != 1
        or any(not isinstance(i, str) or not i for i in ids)
        or len(set(ids)) != len(ids)
    ):
        refuse(["ambiguous_state_slot"])
    target = matches[0]
    if target.get("player_profile_id") != result.player_profile_id:
        refuse(["inconsistent_state_link"])
    if any(p is not target and p.get("player_profile_id") == replacement_id for p in state_players):
        refuse(["duplicate_state_profile"])
    if result.player_profile_id is not None and any(
        p is not target and p.get("player_profile_id") == result.player_profile_id for p in state_players
    ):
        refuse(["ambiguous_old_state_profile"])
    slots = set()
    for player in players:
        state = next((p for p in state_players if p.get("id") == player.player_slot_id), None)
        if (
            player.player_slot_id in slots
            or state is None
            or state.get("name") != player.player_name
            or state.get("player_profile_id") != player.player_profile_id
        ):
            refuse(["inconsistent_game_player_roster"])
        slots.add(player.player_slot_id)
        # user_id binds authentication, not just a display profile. Never transfer it.
        if player.player_slot_id == target["id"] and player.user_id is not None:
            refuse(["authenticated_slot_requires_identity_review"])
    return game, players, snapshot, target["id"]


def apply_roster(game, players, slot, replacement_id):
    if slot is None:
        return
    state = deepcopy(game.state)
    next(p for p in state["players"] if p["id"] == slot)["player_profile_id"] = replacement_id
    game.state = state
    for player in players:
        if player.player_slot_id == slot:
            player.player_profile_id = replacement_id


def readback_values(db, row, audit_values):
    result = values(row)
    if "_roster" in audit_values:
        game = (
            db.query(models.GameStateModel)
            .filter_by(game_id=audit_values["_roster"]["game"]["game_id"])
            .populate_existing()
            .one_or_none()
        )
        players = (
            db.query(models.GamePlayer)
            .filter_by(game_id=audit_values["_roster"]["game"]["game_id"])
            .order_by(models.GamePlayer.id)
            .populate_existing()
            .all()
        )
        result["_roster"] = {"game": values(game) if game else None, "players": [values(p) for p in players]}
    return result
