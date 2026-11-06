"""Sheets representation and durable source-slot bindings, never name matching."""

import math
from uuid import uuid4

from app import models
from app.schemas.round_identity import RoundDraft

from .round_evidence import fingerprint
from .round_snapshot import _date


def cell_fingerprint(value):
    """JSON numbers 1 and 1.0 denote one cell value; NULL/blank/bool stay distinct."""

    def canonical(item):
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError("Nonfinite sheet number")
            return int(item) if item.is_integer() else item
        if isinstance(item, list):
            return [canonical(v) for v in item]
        if isinstance(item, dict):
            return {k: canonical(v) for k, v in item.items()}
        return item

    normalized = canonical(value)
    if isinstance(normalized, list) and all(isinstance(row, list) for row in normalized):
        normalized = sorted(normalized, key=fingerprint)
    return fingerprint(normalized)


def participant_tokens(db, source, draft):
    evidence = source.binding_evidence or {}
    mapping = evidence.get("participant_tokens")
    if mapping is None:
        if evidence.get("outbound_operation"):
            mapping = {p.participant_id: uuid4().hex for p in draft.players}
        else:
            # Existing reviewed source slots already ARE trusted external tokens.
            # Never rename them or infer another association from display names.
            prior = db.query(models.RoundObservation).filter_by(source_id=source.id, continuity_verified=True).all()
            slots = {p["participant_id"] for o in prior if o.parsed_values for p in o.parsed_values["players"]}
            if not slots or slots != {p.participant_id for p in draft.players}:
                raise ValueError("Reviewed participant token mapping required")
            mapping = {slot: slot for slot in slots}
        source.binding_evidence = {**evidence, "participant_tokens": mapping}
    if set(mapping) != {p.participant_id for p in draft.players} or len(set(mapping.values())) != len(mapping):
        raise ValueError("Participant mapping changed; review required")
    return mapping


def mapped_draft(source, draft):
    mapping = (source.binding_evidence or {}).get("participant_tokens", {})
    if not mapping:
        return draft
    reverse = {token: slot for slot, token in mapping.items()}
    data = draft.model_dump(mode="json")
    for player in data["players"]:
        if player["participant_id"] not in reverse:
            return draft  # continuity review handles unknown tokens; never guess
        player["participant_id"] = reverse[player["participant_id"]]
    return RoundDraft.model_validate(data)


def date_cell(payload, contract):
    raw = payload.get("raw_date")
    if raw:
        try:
            if _date(raw, contract.season).isoformat() == payload["played_on"]:
                return raw
        except (ValueError, TypeError, AttributeError):
            pass
    return payload["played_on"]
