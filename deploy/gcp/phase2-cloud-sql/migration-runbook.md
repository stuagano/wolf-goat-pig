# Phase 2 — Database migration runbook (Render Postgres → Cloud SQL)

Follows design doc §8. **Option A: lift-and-shift** — same schema, same ORM, same
queries. Nothing in `backend/` changes except the `DATABASE_URL` secret.

> **Pool sizing.** `app/database.py` reads `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` /
> `DB_POOL_RECYCLE` / `DB_POOL_TIMEOUT` / `DB_CONNECT_TIMEOUT` /
> `DB_STATEMENT_TIMEOUT_MS` from the environment (defaults match the Render free
> tier). Cloud SQL can afford a larger pool — bump `DB_POOL_SIZE`/`DB_MAX_OVERFLOW`
> in `env.production.yaml` (commented stubs are there) rather than editing code.

> Do a full **dry run** against a staging instance first (steps 1–5 below into a
> throwaway DB) and run the backend test suite against it before touching prod.

## 0. Prerequisites

- Phase 1 is live (Cloud Run serving off Render Postgres).
- `deploy/gcp/phase2-cloud-sql/10-provision.sh` has created the instance/db/user.
- `psql`, `pg_dump`, `pg_restore` locally (matching the target major version).
- The current Render `DATABASE_URL` (source) and the new Cloud SQL one (target).

## 1. Confirm version parity

```sql
-- against Render:
SELECT version();
```
`SQL_VERSION` in `config.env` must match the major version. Fix and re-provision
if not — a major-version mismatch can break the restore.

## 2. Dump from Render

```bash
pg_dump --no-owner --no-privileges --format=custom \
  "$RENDER_DATABASE_URL" > wgp.dump
```

## 3. Open a path to Cloud SQL

Easiest for a one-off migration — the Cloud SQL Auth Proxy (no public IP):

```bash
cloud-sql-proxy "$(gcloud sql instances describe "$SQL_INSTANCE" \
  --format='value(connectionName)')" &   # listens on 127.0.0.1:5432
```

## 4. Restore into Cloud SQL

```bash
pg_restore --no-owner --no-privileges --clean --if-exists \
  -d "postgresql://${SQL_USER}:${DB_PASSWORD}@127.0.0.1:5432/${SQL_DB}" \
  wgp.dump
```

## 5. Verify parity

- Row counts on the big tables match Render (`game_state`, `game_players`,
  `hole_events`, `player_profiles`, `player_statistics`).
- The app already ships `ensure_schema.py` / `migrations_runner.py` — run them
  against Cloud SQL to confirm the schema is complete.
- Point a local backend at the Cloud SQL URL and run:
  `cd backend && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic`.

## 6. Cutover (short maintenance window)

1. Freeze writes (put the app in maintenance / stop schedulers).
2. Final incremental `pg_dump` → `pg_restore` to catch late rows.
3. Attach Cloud SQL to the service and flip the secret:
   ```bash
   CONN="$(gcloud sql instances describe "$SQL_INSTANCE" --format='value(connectionName)')"
   gcloud run services update "$RUN_SERVICE" --region "$GCP_REGION" \
     --add-cloudsql-instances="$CONN"
   printf '%s' "postgresql://${SQL_USER}:${DB_PASSWORD}@/${SQL_DB}?host=/cloudsql/${CONN}" \
     | gcloud secrets versions add DATABASE_URL --data-file=-
   ```
4. Redeploy (or `gcloud run services update ... --update-secrets=DATABASE_URL=DATABASE_URL:latest`)
   so the new secret version is picked up.
5. Smoke test: `/health` → `environment=production`; junk Bearer to `/players/me`
   → 401 not 500.

## 7. Rollback

The `DATABASE_URL` flip is instantly reversible — add a new secret version with
the Render URL and redeploy. Keep **Render Postgres warm and read-only for N days**
(§8) before decommissioning in Phase 6.

## Note on the connection string scheme

Use the plain **`postgresql://`** scheme (not `postgresql+psycopg2://`).
`app/database.py` detects Postgres with `startswith("postgresql://")`; a
`+driver` scheme would fall through to the SQLite branch. The `?host=/cloudsql/…`
Unix-socket form works with the default psycopg2 driver.
