"""Regression: unattested member rounds (status='pending') must never leak into
Commissioner standings/stat answers.

Two read paths are guarded here against a real SQLite session:
  1. `_build_data_context()` — the leaderboard aggregation injected into the chat
     system prompt.
  2. `_execute_readonly_sql()` against the `legacy_rounds_official` view — the
     data-chat SQL executor.

Both must exclude a pending round while including an attested one for the same
member.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, ensure_legacy_rounds_official_view
from app.models import LegacyRound


@pytest.fixture
def db_session():
    """In-memory SQLite with the full schema + the legacy_rounds_official view."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    # Same helper prod/dev use, so the view's filter is exercised identically.
    ensure_legacy_rounds_official_view(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Attested round for Alice; pending self-post for Bob.
    session.add_all(
        [
            LegacyRound(
                date="2026-06-15",
                member="Alice Park",
                score=7,
                source="primary_sheet",
                status="attested",
                synced_at="x",
                created_at="x",
            ),
            LegacyRound(
                date="2026-06-15",
                member="Bob Jones",
                score=99,
                source="member",
                status="pending",
                synced_at="x",
                created_at="x",
            ),
        ]
    )
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_build_data_context_excludes_pending(db_session):
    from app.routers.commissioner import _build_data_context

    context = _build_data_context(db_session)
    assert "Alice Park" in context  # attested → visible
    assert "Bob Jones" not in context  # pending → hidden
    assert "99" not in context  # pending score must not leak


def test_official_view_excludes_pending_in_sql_executor(db_session):
    from app.routers.commissioner import _execute_readonly_sql

    results = _execute_readonly_sql(
        db_session,
        "SELECT member, SUM(score) AS quarters FROM legacy_rounds_official GROUP BY member ORDER BY quarters DESC",
    )
    assert "error" not in results, results
    members = {row[0] for row in results["rows"]}
    assert "Alice Park" in members  # attested → returned
    assert "Bob Jones" not in members  # pending → excluded


def test_raw_legacy_rounds_table_is_rejected_by_validator():
    """Even if the LLM names the raw table, the query is refused (no pending leak)."""
    from app.routers.commissioner import _validate_sql

    assert _validate_sql("SELECT member, score FROM legacy_rounds_official") is True
    assert _validate_sql("SELECT member, score FROM legacy_rounds") is False


def test_quoted_and_qualified_raw_legacy_rounds_refs_are_rejected():
    """Quoting / schema-qualification must not let the raw table evade the allow-list."""
    from app.routers.commissioner import _validate_sql

    # (a) plain double-quoted raw table
    assert _validate_sql('SELECT * FROM "legacy_rounds"') is False
    # (b) quoted raw-table ref inside a subquery
    assert _validate_sql('SELECT * FROM (SELECT * FROM "legacy_rounds") x') is False
    # (b') quoted raw-table ref inside a CTE
    assert _validate_sql('WITH leaked AS (SELECT * FROM "legacy_rounds") SELECT * FROM leaked') is False
    # (c) schema-qualified quoted refs
    assert _validate_sql('SELECT * FROM public."legacy_rounds"') is False
    assert _validate_sql('SELECT * FROM "public"."legacy_rounds"') is False
    # JOIN target quoted raw table is also rejected
    assert (
        _validate_sql('SELECT * FROM legacy_rounds_official o JOIN "legacy_rounds" r ON o.member = r.member') is False
    )
    # Sanity: the genuinely-allowed view still passes, even quoted/qualified.
    assert _validate_sql('SELECT member FROM "legacy_rounds_official"') is True
    assert _validate_sql('SELECT member FROM public."legacy_rounds_official"') is True


def test_cte_alias_named_after_denied_table_is_rejected():
    """A CTE named like the forbidden raw table cannot whitelist it (denylist wins)."""
    from app.routers.commissioner import _validate_sql

    # (a) CTE named legacy_rounds, quoted raw-table body
    assert _validate_sql('WITH legacy_rounds AS (SELECT * FROM "legacy_rounds") SELECT * FROM legacy_rounds') is False
    # (b) same idea, unquoted raw-table body
    assert _validate_sql("WITH legacy_rounds AS (SELECT * FROM legacy_rounds) SELECT * FROM legacy_rounds") is False
    # (c) CTE named legacy_rounds whose body selects from the raw table via a
    #     schema-qualified quoted ref
    assert (
        _validate_sql('WITH legacy_rounds AS (SELECT * FROM public."legacy_rounds") SELECT * FROM legacy_rounds')
        is False
    )
    # A legitimate CTE over the sanctioned view still passes.
    assert _validate_sql("WITH r AS (SELECT * FROM legacy_rounds_official) SELECT * FROM r") is True


def test_legitimate_cte_over_official_view_excludes_pending(db_session):
    """A valid CTE over the official view passes and still hides pending rows."""
    from app.routers.commissioner import _execute_readonly_sql, _validate_sql

    sql = "WITH r AS (SELECT * FROM legacy_rounds_official) SELECT member FROM r"
    assert _validate_sql(sql) is True
    results = _execute_readonly_sql(db_session, sql)
    assert "error" not in results, results
    members = {row[0] for row in results["rows"]}
    assert "Alice Park" in members  # attested → returned
    assert "Bob Jones" not in members  # pending → excluded


def test_comma_separated_raw_legacy_rounds_refs_are_rejected():
    """Implicit (comma) joins must not slip a raw-table ref past the validator."""
    from app.routers.commissioner import _validate_sql

    # (a) comma join, second table is raw legacy_rounds
    assert _validate_sql("SELECT lr.member, lr.score FROM legacy_rounds_official o, legacy_rounds lr") is False
    # (b) comma join with a quoted raw ref
    assert _validate_sql('SELECT * FROM player_profiles p, "legacy_rounds" lr') is False
    # (c) comma join with a schema-qualified quoted raw ref
    assert _validate_sql('SELECT * FROM legacy_rounds_official o, public."legacy_rounds" lr') is False


def test_prior_adversarial_cases_still_rejected():
    """All previously-closed bypasses remain rejected under the AST validator."""
    from app.routers.commissioner import _validate_sql

    # bare / quoted / schema-qualified raw table
    assert _validate_sql("SELECT * FROM legacy_rounds") is False
    assert _validate_sql('SELECT * FROM "legacy_rounds"') is False
    assert _validate_sql('SELECT * FROM public."legacy_rounds"') is False
    assert _validate_sql('SELECT * FROM "public"."legacy_rounds"') is False
    # raw ref inside a subquery
    assert _validate_sql('SELECT * FROM (SELECT * FROM "legacy_rounds") x') is False
    # CTE named after the denied table (alias collision)
    assert _validate_sql('WITH legacy_rounds AS (SELECT * FROM "legacy_rounds") SELECT * FROM legacy_rounds') is False
    # nested CTE whose inner body pulls from the raw table
    assert (
        _validate_sql(
            "WITH outer_cte AS ("
            "  WITH inner_cte AS (SELECT * FROM legacy_rounds) SELECT * FROM inner_cte"
            ") SELECT * FROM outer_cte"
        )
        is False
    )
    # UNION pulling from the raw table on one side
    assert _validate_sql("SELECT member FROM legacy_rounds_official UNION SELECT member FROM legacy_rounds") is False


def test_fail_closed_on_unparseable_sql():
    """If sqlglot cannot parse the statement, the validator must reject it."""
    from app.routers.commissioner import _validate_sql

    assert _validate_sql("SELECT * FROM legacy_rounds_official WHERE ((( ") is False
    assert _validate_sql("not valid sql at all ~~~") is False


def test_comma_join_over_allowed_tables_still_passes():
    """An implicit join over only allowed tables must still validate."""
    from app.routers.commissioner import _validate_sql

    assert _validate_sql("SELECT * FROM legacy_rounds_official o, player_profiles p") is True


def test_official_view_quoted_query_still_excludes_pending(db_session):
    """A valid quoted query against the official view passes and hides pending rows."""
    from app.routers.commissioner import _execute_readonly_sql, _validate_sql

    sql = 'SELECT member FROM "legacy_rounds_official"'
    assert _validate_sql(sql) is True
    results = _execute_readonly_sql(db_session, sql)
    assert "error" not in results, results
    members = {row[0] for row in results["rows"]}
    assert "Alice Park" in members  # attested → returned
    assert "Bob Jones" not in members  # pending → excluded


def test_pending_becomes_visible_after_attestation(db_session):
    """Flipping pending→attested makes the round surface through both read paths."""
    from app.routers.commissioner import _build_data_context, _execute_readonly_sql

    row = db_session.query(LegacyRound).filter(LegacyRound.member == "Bob Jones").one()
    row.status = "attested"
    db_session.commit()

    context = _build_data_context(db_session)
    assert "Bob Jones" in context

    results = _execute_readonly_sql(
        db_session,
        "SELECT member FROM legacy_rounds_official WHERE member = 'Bob Jones'",
    )
    assert "error" not in results, results
    assert {row[0] for row in results["rows"]} == {"Bob Jones"}
