# Score-save PostgreSQL regression tests

`test_score_save_postgres.py` is intentionally collected by the normal backend
suite. It is not under `integration/` or marked `integration`: those are excluded
by the default pytest configuration. Locally, tests skip without the dedicated
URL. CI sets `SCORE_SAVE_REQUIRE_POSTGRES=1`, so a missing URL fails instead.

The URL is explicit permission to create/drop test schemas in a **disposable**
PostgreSQL database. Only localhost TCP URLs, database names ending in `_test`,
and no URL query parameters are accepted. Never point this at a shared database
or a tunnel/proxy to one. These tests never fall back to `DATABASE_URL`.

Each test uses a unique schema and drops only that schema. Connections use
`NullPool`, request sessions use `autoflush=False` and `expire_on_commit=True`,
and readback opens another physical PostgreSQL connection. There is no outer
rollback fixture. A PostgreSQL trigger injects an actual UPDATE failure after
prior writes, and fresh reads verify the whole transaction rolled back.

## Disposable local instance (Homebrew PostgreSQL)

From the repository root, select an unused port and run:

```bash
PG_BIN=/opt/homebrew/opt/postgresql@17/bin
PG_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/score-save-pg.XXXXXX")
PG_PORT=55439
"$PG_BIN/initdb" -D "$PG_ROOT/data" -A trust -U score_save_test --no-locale -E UTF8
"$PG_BIN/pg_ctl" -D "$PG_ROOT/data" -l "$PG_ROOT/postgres.log" \
  -o "-h 127.0.0.1 -p $PG_PORT -k $PG_ROOT" start
"$PG_BIN/createdb" -h 127.0.0.1 -p "$PG_PORT" -U score_save_test wolf_goat_pig_score_save_test

export SCORE_SAVE_TEST_DATABASE_URL="postgresql://score_save_test@127.0.0.1:$PG_PORT/wolf_goat_pig_score_save_test"
export SCORE_SAVE_REQUIRE_POSTGRES=1
(cd backend && venv/bin/python -m pytest tests/unit/test_score_save_postgres.py -q)

# Stop the disposable instance when finished. Keep PG_ROOT if logs are useful.
"$PG_BIN/pg_ctl" -D "$PG_ROOT/data" stop -m fast
```

Trust authentication is limited to this disposable localhost instance. Do not
reuse these settings for an existing server. The CI workflow uses its existing
PostgreSQL 15 service; no additional infrastructure is needed.

Coverage: completed-round corrections, all four persisted representations,
stable row identities and creation/completion timestamps, repeated saves,
real member/admin/outsider authorization, invalid payloads, rollback/recovery,
no ORM SQL after commit, and safe correlated diagnostics ordered after commit.
Event `recorded_at` intentionally changes on replay; idempotence means no new
rows or score/result changes, not suppression of that audit timestamp.
