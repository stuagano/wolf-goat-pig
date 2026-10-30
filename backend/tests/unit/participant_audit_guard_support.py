"""Physical mutation probes shared by SQLite and PostgreSQL correction tests."""

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app import models


def assert_audit_guard(sessions, operation):
    table = models.ParticipantCorrectionAudit.__table__
    with sessions() as db:
        original = dict(db.execute(select(table)).mappings().one())
    with sessions() as db:
        with pytest.raises(DBAPIError, match="Participant correction audit is immutable"):
            if operation == "bulk_update":
                db.query(models.ParticipantCorrectionAudit).update({"reason": "tampered"}, synchronize_session=False)
            elif operation == "bulk_delete":
                db.query(models.ParticipantCorrectionAudit).delete(synchronize_session=False)
            else:
                db.execute(text(operation))
            db.commit()
        db.rollback()
    with sessions() as db:
        assert dict(db.execute(select(table)).mappings().one()) == original
        assert db.get(models.GamePlayerResult, 20).player_profile_id == 20


MUTATIONS = [
    "UPDATE participant_correction_audits SET reason='tampered'",
    "DELETE FROM participant_correction_audits",
    "bulk_update",
    "bulk_delete",
]
