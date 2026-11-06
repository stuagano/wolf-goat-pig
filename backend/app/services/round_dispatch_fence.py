"""Drain the external-effect interval while preserving durable send uncertainty.

Postgres session advisory locks survive the claim commit. Pause takes the same
exclusive key before the ordinary transaction fence. SQLite's local-only
rehearsal uses a process lock; it is not a multi-process production drain.
"""

from contextlib import contextmanager
from threading import RLock

from sqlalchemy import event, text

KEY = 870284190312
_local = RLock()


@contextmanager
def dispatch_fence(engine):
    if engine.dialect.name == "postgresql":
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text("SELECT pg_advisory_lock_shared(:key)"), {"key": KEY})
            try:
                yield
            finally:
                connection.execute(text("SELECT pg_advisory_unlock_shared(:key)"), {"key": KEY})
    else:
        with _local:
            yield


def drain_dispatch(db):
    """Exclusive gate retained through the pause commit, before config locks."""
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": KEY})
    elif not db.info.get("dispatch_drain"):
        _local.acquire()
        db.info["dispatch_drain"] = True

        # Root transaction completion only; nested probe rollbacks must not drain.
        def release(session, transaction):
            if transaction.parent is None and session.info.pop("dispatch_drain", False):
                _local.release()

        event.listen(db, "after_transaction_end", release)
        db.connection()
