# Manage admins in the app + document admin permissions

Date: 2026-10-08 · Status: approved design, pending spec review

## Goal

Admins can add and remove other admins from the admin page instead of editing
`SUPER_ADMIN_EMAILS` and redeploying. Admin powers stay a single level (no split
between "club ops" and "technical"). What admins can do is written down in one
place, and the admin-like endpoints that are still open get locked down.

## Decisions (from the 2026-10-08 conversation)

- **Model:** one admin level, managed in the app (option B).
- **Who manages admins:** any admin. `SUPER_ADMIN_EMAILS` stays as a permanent
  floor: those emails (today `stuagano@gmail.com`, `greenjs@gmail.com`) are always
  admins and cannot be removed from the UI.
- **Storage:** an `is_admin` flag on `player_profiles` (chosen over a separate
  email-keyed grants table and over Auth0 roles).
- **History:** who granted admin and when, stored on the profile. No general audit
  log of admin actions.

## Data

Migration `backend/migrations/add_profile_admin_flag_postgres.sql` (applied at startup by
`app/migrations_runner.py`; SQLite dev gets the columns via `create_all`):

| Column | Type | Notes |
|---|---|---|
| `is_admin` | boolean, not null, default false | |
| `admin_granted_by` | text, nullable | email of the admin who granted it |
| `admin_granted_at` | text, nullable | ISO timestamp, matching the table's other timestamps |

Revoking sets all three back to false / null.

## Who counts as an admin

`require_admin` (`backend/app/utils/admin_auth.py`) stays the single decision point,
so all ~37 existing gated routes pick up the change with no edits. It passes when
either:

1. the verified login email is in `SUPER_ADMIN_EMAILS` (env floor), or
2. exactly one active profile is linked to the login's Auth0 subject
   (`preferences.auth0_id`) and that profile has `is_admin = true`.

If the subject matches more than one profile, or the matched profile is inactive,
the request is denied (403). No fallback to email matching for the flag — the
flag only counts on a profile actually linked to this login.

`require_admin` needs a DB session for (2), so it gains a `db: Session =
Depends(get_db)` parameter. The env check runs first so env admins never touch the DB.

`/players/me` computes `is_admin` / `is_super_admin` / `role` from the same logic
(`players.py:212`), so the admin page and nav link show or hide to match. `role`
values: `super_admin` for env admins, `admin` for flagged profiles, `normal` otherwise.

## Constraints

- Only profiles that are active **and** have a linked Auth0 login can be made
  admin (otherwise nobody can use the grant). The API rejects others with 400.
- Env-floor admins can't be revoked through the API (400). Their profiles may also
  carry the flag; it's irrelevant while they're on the env list.
- An admin can't revoke their own flag if they aren't on the env list (prevents
  removing your own access by accident; another admin can do it).
- Retiring a profile (`DELETE /players/{id}`, PR #371) also clears the admin
  columns, so a stray duplicate can't carry admin.

## API

New module `backend/app/routers/admin_grants.py`, mounted inside the players router
the same way `account_links.py` is (so paths live under `/players/admin`). All routes
use `require_admin`.

Note: `PlayerProfileResponse.is_admin` keeps meaning *effective* admin (env or flag),
computed as today; the stored column is only read inside `admin_auth.py` and this module.

- `GET /players/admin/admins` → `{ env_admins: [email], profile_admins: [{id, name, legacy_name, email, admin_granted_by, admin_granted_at}] }`
- `POST /players/admin/admins/{player_id}` → grant; returns the profile row.
- `DELETE /players/admin/admins/{player_id}` → revoke; returns the profile row.

Grant/revoke are idempotent (granting an admin again or revoking a non-admin returns 200
with the current state). Each change is logged at INFO with actor email and target id.

## UI

New **Admins** tab in `AdminPage.jsx`:

- Locked rows for env admins ("Set in deployment config — can't be removed here").
- Rows for flagged profiles showing granted-by and granted-at, each with **Remove**
  (with a confirm). Hidden on your own row unless you're an env admin.
- **Add an admin:** a search box reusing the account-links search
  (`GET /players/admin/account-links`); results without a linked Auth0 login show
  "Needs to sign in first" instead of a **Make admin** button.

## Lockdown of still-open admin-like endpoints

| Endpoint | Today | Change |
|---|---|---|
| `POST /admin/ensure-schema` (`health.py`) | no auth, writes schema | `require_admin` |
| `POST /admin/seed-course-holes` (`health.py`) | no auth, writes course data | `require_admin` |
| `POST /callouts/run` (`callouts.py:56`) | no auth; `game_date` param lets a caller bypass the per-window dedup and email the opt-in list repeatedly | require `INTERNAL_JOB_TOKEN` via the existing `_require_job_token` helper (`internal_jobs.py`) |

**Rollout dependency for `/callouts/run`:** `INTERNAL_JOB_TOKEN` is not currently a
GitHub repo secret, and `callout-list.yml` doesn't pass secrets to
`_cron-curl.yml` (which already sends the header when the secret is present).
Before this merges:

1. Add repo secret `INTERNAL_JOB_TOKEN` with the value from GCP Secret Manager
   (user action; the agent can't read it).
2. In `callout-list.yml`, pass `secrets: { INTERNAL_JOB_TOKEN: ${{ secrets.INTERNAL_JOB_TOKEN }} }`
   to the reusable workflow (part of this PR).
3. After deploy, trigger the workflow manually once and confirm a 200.

## Documentation

`docs/admin-permissions.md`: who is an admin and how to add/remove one, then every
admin capability grouped by area (accounts & profiles, roster & signups, data sync,
email & comms, banners & feature flags, badges, LivSOW, database & system), with
destructive actions and actions that send email or touch external systems
flagged. Linked from the Admins tab. Source: the 2026-10-08 route inventory.

## Testing

Backend (pytest):
- env admin passes; flagged + linked + active profile passes; unflagged → 403;
  flagged but inactive → 403; subject matching two profiles → 403
- revoke takes effect on the next request
- grant rejected for a profile with no Auth0 login (400); revoke rejected for an env admin (400);
  self-revoke by a non-env admin rejected (400)
- retiring a profile clears the admin columns
- `/players/me` reports `role: admin` for a flagged profile
- `ensure-schema`, `seed-course-holes` reject unauthenticated callers; `/callouts/run`
  rejects a missing/wrong token and runs with the right one

Frontend (vitest): Admins tab renders env rows as locked, grant and remove call the
right endpoints, "Needs to sign in first" shows for unlinked results.

Plus the full CI gate from CLAUDE.md and the affected `caps` capabilities.

## Out of scope

- Split permission levels (club ops vs technical)
- Audit log of all admin actions
- Public `GET /players` leaking emails/Auth0 IDs and unauthenticated `POST /players` (separate PR)
