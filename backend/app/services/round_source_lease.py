"""Dedicated source ownership sessions. Lock order: source lease, global lock.

The lease row is locked in the whole-round transaction before the global lock;
expiry/owner/epoch are rechecked before commit, preventing expired owners from
publishing. Network reads never run while that game transaction is open.
"""

from contextlib import contextmanager
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from app.models import RoundIdentityLease
from app.utils.time import utc_now


class SourceLeaseLostError(RuntimeError):
    pass


@contextmanager
def source_lease(engine, scope, *, seconds=120):
    key, owner = f"sheet:{scope}", str(uuid4())
    with Session(engine) as lease_db:
        dialect = engine.dialect.name
        if dialect == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        elif dialect == "sqlite":
            from sqlalchemy.dialects.sqlite import insert
        else:
            raise SourceLeaseLostError("Unsupported lease database")
        lease_db.execute(
            insert(RoundIdentityLease).values(key=key, epoch=0).on_conflict_do_nothing(index_elements=["key"])
        )
        now = utc_now().isoformat()
        claimed = lease_db.execute(
            update(RoundIdentityLease)
            .where(
                RoundIdentityLease.key == key,
                or_(RoundIdentityLease.owner.is_(None), RoundIdentityLease.expires_at <= now),
            )
            .values(
                owner=owner,
                epoch=RoundIdentityLease.epoch + 1,
                expires_at=(utc_now() + timedelta(seconds=seconds)).isoformat(),
            )
        )
        if claimed.rowcount != 1:
            lease_db.rollback()
            raise SourceLeaseLostError("Source refresh already running")
        lease_db.commit()
        epoch = lease_db.get(RoundIdentityLease, key).epoch
        lease_db.rollback()
        try:
            yield key, owner, epoch
        finally:
            lease_db.execute(
                update(RoundIdentityLease)
                .where(
                    RoundIdentityLease.key == key, RoundIdentityLease.owner == owner, RoundIdentityLease.epoch == epoch
                )
                .values(owner=None, expires_at=None)
            )
            lease_db.commit()


def heartbeat(engine, lease, *, seconds=120):
    key, owner, epoch = lease
    with Session(engine) as db:
        changed = db.execute(
            update(RoundIdentityLease)
            .where(
                RoundIdentityLease.key == key,
                RoundIdentityLease.owner == owner,
                RoundIdentityLease.epoch == epoch,
                RoundIdentityLease.expires_at > utc_now().isoformat(),
            )
            .values(expires_at=(utc_now() + timedelta(seconds=seconds)).isoformat())
        )
        if changed.rowcount != 1:
            db.rollback()
            raise SourceLeaseLostError("Source lease expired")
        db.commit()


def fence(db, lease):
    key, owner, epoch = lease
    row = db.query(RoundIdentityLease).filter_by(key=key).populate_existing().with_for_update().one()
    if row.owner != owner or row.epoch != epoch or row.expires_at <= utc_now().isoformat():
        raise SourceLeaseLostError("Source lease superseded or expired")
    return row
