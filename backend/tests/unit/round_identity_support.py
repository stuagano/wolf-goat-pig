"""Shared, independently seeded local database fixtures for identity tasks."""

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app import models
from app.database import Base


@pytest.fixture
def identity_db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'identity.db'}")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as seed:
        seed.add_all(
            models.PlayerProfile(
                id=i,
                name=name,
                legacy_name=name,
                email=f"player{i}@example.invalid",
                is_active=1,
                preferences={"email_verified": True, "auth0_id": f"auth0|fixture-{i}"},
            )
            for i, name in enumerate(["Reviewer", "Avery", "Blair", "Casey", "Devon"], 1)
        )
        seed.add(
            models.AppConfig(
                name="round_identity",
                value={
                    "mode": "canonical",
                    "epoch": 1,
                    "season": 2026,
                    "reviewer_profile_id": 1,
                    "routing_confirmed": True,
                },
            )
        )
        seed.add(models.GameStateModel(game_id="existing", game_status="completed", state={}))
        seed.commit()
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()
    engine.dispose()


@pytest.fixture
def saved_game(identity_db):
    game_id = str(uuid4())
    with Session(identity_db.get_bind().engine) as seed:
        seed.add(models.GameStateModel(game_id=game_id, game_status="completed", state={}))
        seed.add(models.GameRecord(game_id=game_id, played_on=date(2026, 10, 25)))
        seed.commit()
    return identity_db.query(models.GameStateModel).filter_by(game_id=game_id).one()


@pytest.fixture
def bound_round(identity_db, saved_game):
    from app.models_round_identity import RoundSource

    source = RoundSource(kind="sheet", scope="fixture:tab:2026", round_token="r1", game_id=saved_game.game_id)
    identity_db.add(source)
    identity_db.flush()
    return source


@pytest.fixture
def conflicted_round(identity_db, bound_round):
    from app.models_round_identity import RoundIssue

    issue = RoundIssue(
        source_id=bound_round.id,
        game_id=bound_round.game_id,
        kind="value",
        participant_id="p1",
        field="quarters",
        fingerprint="fixture-conflict",
        accepted_present=True,
        accepted_value=0,
        proposed_present=True,
        proposed_value=1,
    )
    identity_db.add(issue)
    identity_db.flush()
    return issue
