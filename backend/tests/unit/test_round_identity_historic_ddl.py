"""Upgrade actual old column shapes, not current metadata with columns removed."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

from app import database
from app.migrations_runner import _statements
from tests.unit.round_identity_postgres_support import identity_pg

METRICS = [
    "holes_won",
    "successful_bets",
    "total_bets",
    "partnerships_formed",
    "partnerships_won",
    "solo_attempts",
    "solo_wins",
    "ping_pongs",
    "ping_pongs_won",
    "invisible_aardvark_holes",
    "invisible_aardvark_holes_won",
    "duncan_attempts",
    "duncan_wins",
    "tunkarri_attempts",
    "tunkarri_wins",
    "big_dick_attempts",
    "big_dick_wins",
]


def historic_tables(conn, *, required):
    """931101d column names/types, plus deployed NOT NULL/server-default variants.

    Original models defaulted metrics on the Python side; deployed databases may
    also retain server defaults. Both nullable and stricter historical variants
    must be rehearsed. All fixture data is synthetic.
    """
    null = " NOT NULL" if required else ""
    for table in ("game_records", "game_player_results", "legacy_rounds"):
        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
    conn.execute(
        text(
            f"CREATE TABLE game_records (id INTEGER PRIMARY KEY, game_id VARCHAR UNIQUE, course_name VARCHAR, "
            f"game_mode VARCHAR, player_count INTEGER, total_holes_played INTEGER{null} DEFAULT 18, "
            "game_duration_minutes INTEGER, created_at VARCHAR, completed_at VARCHAR, game_settings JSON, final_scores JSON)"
        )
    )
    metrics = ", ".join(f"{metric} INTEGER{null} DEFAULT 0" for metric in METRICS)
    conn.execute(
        text(
            f"CREATE TABLE game_player_results (id INTEGER PRIMARY KEY, game_record_id INTEGER, player_profile_id INTEGER, "
            f"player_name VARCHAR, final_position INTEGER{null}, total_earnings FLOAT{null} DEFAULT 0, {metrics}, "
            "hole_scores JSON, betting_history JSON, performance_metrics JSON, created_at VARCHAR)"
        )
    )
    conn.execute(text("CREATE TABLE legacy_rounds (id INTEGER PRIMARY KEY, member VARCHAR, status VARCHAR)"))
    conn.execute(text("INSERT INTO game_records (id, game_id) VALUES (91, 'original-uuid')"))
    conn.execute(
        text(
            "INSERT INTO game_player_results (id, game_record_id, final_position, total_earnings) VALUES (92, 91, 1, 7.5)"
        )
    )
    conn.execute(text("INSERT INTO legacy_rounds VALUES (93, 'Original', 'attested')"))
    conn.execute(text("CREATE VIEW legacy_rounds_official AS SELECT * FROM legacy_rounds WHERE status <> 'pending'"))


@pytest.mark.parametrize("required", [False, True])
def test_pg15_historic_defaults_nullable_and_view_order_restart(identity_pg, required):
    h = identity_pg
    with h.engine.begin() as conn:
        historic_tables(conn, required=required)
    sql = (
        Path(__file__).resolve().parents[2] / "migrations/zz_20261027_round_identity_expand_postgres.sql"
    ).read_text()
    statements = _statements(sql)
    # Deliberately interrupted independently-committed startup expansion.
    with h.engine.connect() as conn:
        for statement in statements[:5] + statements + statements:
            conn.execute(text(statement))
            conn.commit()
    with h.engine.begin() as conn:
        conn.execute(text("INSERT INTO game_records (id, game_id) VALUES (94, 'unknown-uuid')"))
        conn.execute(text("INSERT INTO game_player_results (id, game_record_id) VALUES (95, 94)"))
    with h.engine.connect() as conn:
        assert conn.execute(text("SELECT id, game_id, total_holes_played FROM game_records ORDER BY id")).all() == [
            (91, "original-uuid", 18),
            (94, "unknown-uuid", None),
        ]
        assert conn.execute(text("SELECT id, total_earnings FROM game_player_results ORDER BY id")).all() == [
            (92, 7.5),
            (95, None),
        ]
        assert conn.execute(text("SELECT " + ", ".join(METRICS) + " FROM game_player_results WHERE id=95")).one() == (
            None,
        ) * len(METRICS)
        assert conn.execute(text("SELECT id, member, game_id FROM legacy_rounds_official")).all() == [
            (93, "Original", None)
        ]
        assert conn.scalar(text("SELECT count(*) FROM round_sources")) == 0
    for table, columns in (
        ("game_records", ["total_holes_played"]),
        ("game_player_results", ["total_earnings", *METRICS]),
    ):
        actual = {c["name"]: c for c in inspect(h.engine).get_columns(table)}
        assert all(actual[c]["nullable"] and actual[c]["default"] is None for c in columns)


@pytest.mark.parametrize("required", [False, True])
def test_sqlite_historic_defaults_require_offline_upgrade_without_loss(tmp_path, required):
    engine = create_engine(f"sqlite:///{tmp_path / 'historic.db'}")
    null = " NOT NULL" if required else ""
    with engine.begin() as conn:
        conn.execute(
            text(f"CREATE TABLE game_records (id INTEGER PRIMARY KEY, total_holes_played INTEGER{null} DEFAULT 18)")
        )
        conn.execute(
            text(
                f"CREATE TABLE game_player_results (id INTEGER PRIMARY KEY, total_earnings FLOAT{null} DEFAULT 0, holes_won INTEGER DEFAULT 0)"
            )
        )
        conn.execute(text("INSERT INTO game_records VALUES (1, 18)"))
        conn.execute(text("INSERT INTO game_player_results VALUES (2, 7.5, 3)"))
        conn.execute(text("CREATE TABLE legacy_rounds (id INTEGER PRIMARY KEY, member VARCHAR, status VARCHAR)"))
        conn.execute(text("INSERT INTO legacy_rounds VALUES (3, 'Original', 'attested')"))
    database.ensure_legacy_rounds_official_view(engine)
    for _ in range(2):
        with pytest.raises(RuntimeError, match="offline SQLite upgrade"):
            database.expand_round_identity_schema(engine)
        with engine.connect() as conn:
            assert conn.execute(text("SELECT * FROM game_player_results")).all() == [(2, 7.5, 3)]
            assert conn.execute(text("SELECT id, member FROM legacy_rounds_official")).all() == [(3, "Original")]
    engine.dispose()
