# Admin permissions

Who is an admin in Wolf Goat Pig, and everything an admin can do.
Admin tools live on the Admin page (tabs named below). Actions without a tab are
API endpoints, shown in code.

Markers: ⚠️ destructive, ✉️ sends email or touches an outside system.

## Who is an admin

There are two ways to be an admin. Both have exactly the same powers.

| Kind | Where it is set | Who can change it |
|---|---|---|
| Config admins | `SUPER_ADMIN_EMAILS` in `deploy/gcp/phase1-cloud-run/env.production.yaml`. Currently `stuagano@gmail.com` and `greenjs@gmail.com`. | Edit the file and redeploy. Cannot be changed in the app. |
| In-app admins | Admin page, **🔑 Admins** tab. | Any admin. |

Rules:

- Config admins are always admins and can't be removed in the app.
- To make someone an in-app admin, their profile must be active and linked to an
  Auth0 login (they have signed in). Otherwise the tab shows "Needs to sign in first".
- You can't remove your own in-app admin access; ask another admin. Config admins are
  exempt from this rule (they can't lose access this way anyway).
- Retiring a profile (see Accounts & profiles) also clears its admin access.
- If one login matches two profiles, that login gets no in-app admin access until the
  duplicate is fixed in the **👤 Account links** tab. Config admins are unaffected,
  since they are matched by email.
- Removing someone from `SUPER_ADMIN_EMAILS` does not remove an in-app grant on
  their profile. Remove that in the Admins tab too.

## What admins can do

### Accounts & profiles

| Action | Where | Notes |
|---|---|---|
| Search accounts and their Auth0 links | **Account links** tab (`GET /players/admin/account-links`) | |
| Relink a login to a different profile | **Account links** tab (`POST /players/admin/relink-auth0`) | Relinking a profile to a different login removes its admin access; re-grant it in the Admins tab. |
| Read any profile | `GET /players/{id}` | Includes email and Auth0 ID. |
| Edit any profile | `PUT /players/{id}` | |
| ⚠️ Retire a profile | `DELETE /players/{id}` | Deactivates it and clears its email, Auth0 link, GHIN ID, and admin access. |
| See who is an admin | **Admins** tab (`GET /players/admin/admins`) | |
| Grant or remove in-app admin | **Admins** tab (`POST` / `DELETE /players/admin/admins/{id}`) | See rules above. |

### Roster & signups

| Action | Where | Notes |
|---|---|---|
| Add a roster name | `POST /legacy-players` | |
| List pending new players | `GET /legacy-players/pending` | |
| Promote a pending player | `POST /legacy-players/pending/{id}/promote` | |
| Dismiss a pending player | `POST /legacy-players/pending/{id}/dismiss` | |

### Data sync

| Action | Where | Notes |
|---|---|---|
| ⚠️ ✉️ Sync from Google Sheets | `POST /data/sync-sheets` | Empties and reloads `legacy_rounds`. |
| ✉️ Queue a finished round for the Google Sheet | `POST /admin/spreadsheet/sync-round` | Adds the round to a queue; a background job (every 5 minutes) writes new or changed rounds to the sheet and skips duplicates. |
| ⚠️ ✉️ Re-sync legacy rounds from the sheets | `POST /admin/spreadsheet/sync-legacy-rounds` | Deletes all `legacy_rounds` rows from the primary and writable sheets and reloads them from Google Sheets. |
| ✉️ Copy missing rounds, primary sheet to writable sheet | `POST /admin/spreadsheet/reconcile/primary-to-writable` | Previews only unless `dry_run=false`; then writes to the writable sheet. |
| ✉️ Copy missing rounds, writable sheet to primary sheet | `POST /admin/spreadsheet/reconcile/writable-to-primary` | Previews only unless `dry_run=false`; then writes to the primary sheet. |
| Read-only spreadsheet views | `GET /admin/spreadsheet/` `leaderboard`, `rounds`, `rounds/by-date/{date}`, `player/{name}`, `sync-status`, `config`, `reconcile/status`, `reconcile/diff` | Leaderboard, rounds and player history come from the database; status, config and diff show the sheet queue and primary-vs-writable comparison. |

### Email & comms

| Action | Where | Notes |
|---|---|---|
| View or change email settings | **Email Settings** tab (`GET` / `POST /admin/email-config`) | |
| ✉️ Send a test welcome email | `POST /admin/test-welcome-email` | |
| ✉️ Send a test email | `POST /admin/test-email` | |
| Gmail OAuth2 status and authorize | `GET /admin/oauth2-status`, `POST /admin/oauth2-authorize` | |
| ✉️ Send an OAuth2 test email | `POST /admin/oauth2-test-email` | |
| ✉️ Upload Gmail credentials | `POST /admin/upload-credentials` | Replaces the Gmail OAuth2 credential file. |
| ✉️ Send a callout test email | `POST /callouts/test-email?to=` | |
| ✉️ List GroupMe groups | `GET /groupme/groups` | Reads from GroupMe. |

### Banners & feature flags

| Action | Where | Notes |
|---|---|---|
| List, create, edit, delete banners | **Banners** tab (`/admin/banner`, `/admin/banner/{id}`) | The public banner read is not admin-only. |
| Turn features on or off | **Toggles** tab (`POST /config/features`) | Flags: `foretees`, `scorecard_scan`, `livsow`, `commissioner_chat`, `stuart_mode`. Reading flags is public. |

### Badges

| Action | Where | Notes |
|---|---|---|
| Check achievements for a player | `POST /api/badges/admin/check-achievements/{player_id}` | |
| List holders of a badge | `GET /api/badges/admin/badge/{badge_id}/holders` | |
| Backfill career badges | `POST /admin/badges/backfill-career` | |

### LivSOW

| Action | Where | Notes |
|---|---|---|
| Seed team starters | `POST /data/livsow/teams/seed-starters` | |
| Set official team logos | `POST /data/livsow/teams/set-official-logos` | |
| Delete a transaction | `DELETE /data/livsow/transactions/{id}` | Soft delete. |
| Edit any team's franchise page | `PUT /data/livsow/teams/{slug}/content` | Also allowed for that team's captain. |

### Database & system

| Action | Where | Notes |
|---|---|---|
| Browse schemas, tables, and rows | **Database** tab (`/admin/db/schemas...`) | Table view is capped at 100 rows. |
| View database stats | `GET /admin/cleanup/database-stats` | |
| List orphaned games | `GET /admin/cleanup/orphaned-games` | |
| ⚠️ Delete orphaned games | `DELETE /admin/cleanup/orphaned-games?dry_run=false` | |
| ⚠️ Run a migration | `POST /admin/run-migration?migration=` | |
| ⚠️ Delete all match records | `DELETE /admin/matches` | |
| Ensure schema | `POST /admin/ensure-schema` | |
| Seed course holes | `POST /admin/seed-course-holes` | |
| Deployment and path checks | `GET /test-deployment`, `GET /debug/paths` | |

## Not admin-gated by design

| Endpoint | Protected by |
|---|---|
| `POST /callouts/run` and `/internal/jobs/*` | `INTERNAL_JOB_TOKEN` (used by scheduled GitHub Actions) |
| `GET /health/external` | `MONITOR_KEY` |

## Known gaps

- Public `GET /players` and `/players/all` expose email and Auth0 IDs.
- `POST /players` needs no login.
- There is no audit log of admin actions. Admin grants and removals are written to the
  server log, and each in-app grant records who granted it and when.
