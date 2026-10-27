"""Durable round contracts: unknowns, evidence, and database arbitration."""

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from tests.unit.round_identity_support import bound_round, conflicted_round, identity_db, saved_game


def test_unknown_is_not_zero():
    from app.schemas.round_identity import RoundParticipant

    assert RoundParticipant(participant_id="p1", name="Avery", profile_id=None, quarters=None).quarters is None


@pytest.mark.parametrize(
    "quarters", [float("nan"), float("inf"), float("-inf"), 9007199254740993, "0.1234567890123456789"]
)
def test_nonfinite_totals_rejected(quarters):
    from app.schemas.round_identity import RoundParticipant

    with pytest.raises(ValidationError):
        RoundParticipant(participant_id="p1", name="Avery", quarters=quarters)


def test_draft_validates_slots_profiles_and_dates():
    from app.schemas.round_identity import RoundDraft

    payload = {
        "players": [
            {"participant_id": "p1", "name": "Guest", "quarters": 1.25},
            {"participant_id": "p2", "name": "Guest", "quarters": None},
        ]
    }
    assert RoundDraft(**payload).players[0].quarters == 1.25
    for invalid in (
        {**payload, "played_on": "2026-02-30"},
        {"players": [payload["players"][0]] * 2},
        {"players": [{**p, "profile_id": 2} for p in payload["players"]]},
    ):
        with pytest.raises(ValidationError):
            RoundDraft(**invalid)


def test_source_binding_is_unique(identity_db):
    from app.models_round_identity import RoundSource

    for _ in range(2):
        identity_db.add(RoundSource(kind="sheet", scope="fixture:tab:2026", round_token="r1", game_id="existing"))
    with pytest.raises(IntegrityError):
        identity_db.flush()


def test_unknown_persisted_metrics_do_not_acquire_zero_defaults(identity_db, saved_game):
    from app.models import GamePlayerResult, GameRecord

    record = identity_db.query(GameRecord).filter_by(game_id=saved_game.game_id).one()
    result = GamePlayerResult(game_record_id=record.id, participant_id="p1", player_name="Guest")
    identity_db.add(result)
    identity_db.flush()
    identity_db.expire_all()
    assert result.total_earnings is None
    assert result.holes_won is None
    assert result.final_position is None
    assert record.total_holes_played is None


@pytest.mark.parametrize(
    "model_name,values",
    [
        ("RoundObservation", {"source_id": 1, "observation_key": "event", "raw_payload": {}}),
        ("RoundFieldHead", {"source_id": 1, "participant_id": "", "field": "course_name"}),
        ("RoundRequest", {"actor_profile_id": 1, "request_key": "retry", "fingerprint": "payload"}),
        ("RoundDelivery", {"issue_event_key": "issue:1", "recipient_profile_id": 1, "channel": "email"}),
        ("RoundMigrationCheckpoint", {"manifest_checksum": "checksum", "game_id": "existing", "operation_key": "bind"}),
    ],
)
def test_retry_keys_are_database_unique(identity_db, bound_round, model_name, values):
    from app import models_round_identity

    if "source_id" in values:
        values = {**values, "source_id": bound_round.id}
    model = getattr(models_round_identity, model_name)
    identity_db.add_all([model(**values), model(**values)])
    with pytest.raises(IntegrityError):
        identity_db.flush()


def test_alias_preserves_multiple_candidates_but_not_duplicate_target(identity_db, saved_game):
    from app.models_round_identity import RoundAlias

    key = {"date_key": "10/25", "group": "B", "location": "Original course"}
    identity_db.add_all([RoundAlias(**key, game_id="existing"), RoundAlias(**key, game_id=saved_game.game_id)])
    identity_db.flush()
    identity_db.add(RoundAlias(**key, game_id="existing"))
    with pytest.raises(IntegrityError):
        identity_db.flush()


@pytest.mark.parametrize("model_name", ["RoundObservation", "RoundResolution"])
def test_evidence_is_append_only(identity_db, bound_round, conflicted_round, model_name):
    from app.models_round_identity import RoundObservation, RoundResolution

    row = (
        RoundObservation(source_id=bound_round.id, observation_key="event", raw_payload={})
        if model_name == "RoundObservation"
        else RoundResolution(issue_id=conflicted_round.id, actor_profile_id=1, action="keep", reason="Reviewed")
    )
    identity_db.add(row)
    identity_db.flush()
    row.id = "changed"
    with pytest.raises(ValueError, match="immutable"):
        identity_db.flush()


def test_metadata_foreign_keys_target_only_new_evidence_tables():
    from app import models_round_identity
    from app.database import Base

    tables = {table.name for table in Base.metadata.tables.values()}
    for table in Base.metadata.tables.values():
        if table.name.startswith("round_") and table.name not in ("round_comments", "round_reactions"):
            for foreign_key in table.foreign_keys:
                assert foreign_key.column.table.name in tables
                assert foreign_key.column.table.name in {"round_sources", "round_observations", "round_issues"}


def test_participant_result_and_notification_delivery_are_unique(identity_db, saved_game):
    from app.models import GamePlayerResult, GameRecord, Notification

    record = identity_db.query(GameRecord).filter_by(game_id=saved_game.game_id).one()
    identity_db.add_all([GamePlayerResult(game_record_id=record.id, participant_id="p1") for _ in range(2)])
    with pytest.raises(IntegrityError):
        identity_db.flush()
    identity_db.rollback()
    identity_db.add_all([Notification(delivery_key="issue:recipient:in_app") for _ in range(2)])
    with pytest.raises(IntegrityError):
        identity_db.flush()


def test_missing_configuration_is_legacy_without_writing(identity_db):
    from app.models import AppConfig
    from app.schemas.round_identity import read_round_identity_config

    identity_db.delete(identity_db.get(AppConfig, "round_identity"))
    identity_db.flush()
    config = read_round_identity_config(identity_db)
    assert config.mode == "legacy" and config.epoch == 0
    assert config.routing_confirmed is False
    assert identity_db.get(AppConfig, "round_identity") is None
