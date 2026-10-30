"""Offline physical append-only guards, including direct SQL/bulk operations.

DDL installation is explicit, never boot-time data mutation. PostgreSQL table
owners/superusers can drop triggers: runtime role must not own evidence tables.
"""

import sqlite3

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


def _expected_refusal(exc, dialect):
    if not isinstance(exc, DBAPIError):
        return False
    original = exc.orig
    if dialect == "postgresql":
        code = getattr(original, "pgcode", None) or getattr(original, "sqlstate", None)
        return code == "42501" or (code == "P0001" and "Round evidence is immutable" in str(original))
    return (
        isinstance(original, sqlite3.IntegrityError)
        and getattr(original, "sqlite_errorcode", None) == sqlite3.SQLITE_CONSTRAINT_TRIGGER
        and "Round evidence is immutable" in str(original)
    )


def install_evidence_guards(db):
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        db.execute(
            text("""
            CREATE OR REPLACE FUNCTION round_identity_reject_mutation() RETURNS trigger
            LANGUAGE plpgsql AS $guard$
            BEGIN
                RAISE EXCEPTION 'Round evidence is immutable; append a new event';
            END;
            $guard$
        """)
        )
        for table in ("round_observations", "round_resolutions"):
            db.execute(text(f'DROP TRIGGER IF EXISTS immutable_round_evidence ON "{table}"'))
            db.execute(
                text(
                    f'CREATE TRIGGER immutable_round_evidence BEFORE UPDATE OR DELETE OR TRUNCATE ON "{table}" '
                    "FOR EACH STATEMENT EXECUTE FUNCTION round_identity_reject_mutation()"
                )
            )
    elif dialect == "sqlite":
        for table in ("round_observations", "round_resolutions"):
            for operation in ("UPDATE", "DELETE"):
                db.execute(
                    text(
                        f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation.lower()} "
                        f'BEFORE {operation} ON "{table}" BEGIN '
                        "SELECT RAISE(ABORT, 'Round evidence is immutable'); END"
                    )
                )
    else:
        raise ValueError("Physical evidence guards unsupported on this database")


def prove_evidence_guards(db):
    """Direct-SQL negative probes in savepoints, with actual surviving readback.

    Requires at least one physical row in each table; empty-table checks alone
    are not evidence that immutable records survive attempted mutation.
    """
    proof = {}
    for table in ("round_observations", "round_resolutions"):
        original = db.execute(text(f'SELECT id FROM "{table}" ORDER BY id LIMIT 1')).scalar()
        if not original:
            raise ValueError("Synthetic observation and resolution fixtures required for physical proof")
        operations = [f'UPDATE "{table}" SET id=id WHERE id=:id', f'DELETE FROM "{table}" WHERE id=:id']
        if db.get_bind().dialect.name == "postgresql":
            operations.append(f'TRUNCATE TABLE "{table}" CASCADE')
        for operation in operations:
            blocked = False
            savepoint = db.begin_nested()
            try:
                db.execute(text(operation), {"id": original})
            except Exception as exc:
                blocked = _expected_refusal(exc, db.get_bind().dialect.name)
            finally:
                savepoint.rollback()
            if (
                not blocked
                or db.execute(text(f'SELECT id FROM "{table}" WHERE id=:id'), {"id": original}).scalar() != original
            ):
                raise ValueError("Direct SQL evidence immutability not proven")
        proof[table] = "direct_sql_update_delete_blocked_and_row_preserved"
    return proof
