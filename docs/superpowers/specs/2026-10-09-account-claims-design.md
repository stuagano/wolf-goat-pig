# Admin-approved claims: connect a returning player to their original profile

Date: 2026-10-09 · Status: approved direction (option A), pending spec review

## Problem

Many players have an **original** profile — created before logins existed — that holds
their history but has no email and no Auth0 login. When such a player signs in for the
first time:

1. `get_or_create_player_profile` can't match them (the original has no email), so it
   creates a new profile named after their email (the "stray").
2. Onboarding asks them to pick their roster name (`PUT /players/me/legacy-name`). The
   original already holds that name, so they get 409 *"'X' already has a player profile.
   Ask a club admin to connect your sign-in to that player in Account links."*
3. They stay on the stray until an admin hand-relinks them (retire stray, relink
   original) — what we did for Tom Crowley and Tom McFadden on 2026-10-08.

As of 2026-10-09, 18 originals on Jeff's dropdown have no login and no email
(e.g. Gregg Colburn, Chip Halbert, Dave Gruber) and will each hit this on first sign-in.

## Goal

When a returning player picks a name held by an original profile with **no login**, record
a **claim request** instead of failing, tell the player an admin will connect them, email
the admins, and give admins a one-click **Approve** that does the hand-relink atomically.

## Decisions

- **Admin approval required** (option A). No auto-claim: picking a name must never by
  itself hand over someone else's history (the #319 "everyone is Steve" risk).
- A claim is only created when the target profile is **active and has no Auth0 login**. If
  the target already has a login, keep today's 409 — that's someone else's account.
- **Retired profiles don't hold names.** `is_canonical_name_claimed` ignores inactive
  profiles, so a retired stray that still has a `legacy_name` can't block the real player.
  (Retire already clears email + login since PR #371; it leaves `legacy_name` as history.)
- Approval moves **identity only** (email, Auth0 login, roster name) onto the original
  and retires the stray. Anything recorded on the stray in its first hours (e.g. a
  sign-up row) stays with the retired stray — strays are hours old; documented, not moved.

## Data

New table `account_claims` (model `AccountClaim`, migration
`backend/migrations/add_account_claims_postgres.sql`):

| Column | Type | Notes |
|---|---|---|
| `id` | integer PK | |
| `requester_profile_id` | integer, not null | the stray the player is signed in as |
| `target_profile_id` | integer, not null | the original holding the name |
| `canonical_name` | text, not null | roster name being claimed |
| `requester_email` | text, nullable | verified login email at request time |
| `status` | text, not null, default `pending` | `pending` · `approved` · `dismissed` |
| `created_at` | text | ISO |
| `resolved_at` | text, nullable | |
| `resolved_by` | text, nullable | admin email |

At most one `pending` claim per requester: a repeat request for the same target returns the
existing claim; a request for a different target replaces the old pending one (status
`dismissed`, `resolved_by="superseded"`).

## Player flow (`PUT /players/me/legacy-name`)

When `link_profile_to_canonical_name` returns `claimed`:

- Find the holder: the active profile whose `legacy_name` or `name` matches the canonical
  name (case-insensitive).
- Holder has an Auth0 login → unchanged 409.
- Holder has no login → create/reuse the pending claim, notify admins (non-blocking, same
  pattern as `_notify_admins_of_new_player`), and return **202** with
  `{"status": "claim_pending", "canonical_name": ..., "message": "Request sent — a club admin will connect you to your history."}`.
- The requester must have a verified email (`email_verified`); otherwise 403 asking them to
  verify first (an admin needs a real email to recognize the player).

Frontend (`usePlayerProfile.js` legacy-name call + `LegacyNameSelector.jsx`): on 202
show the message in place of the error and let the player continue into the app (they use
the stray until approved). On next load, if `/players/me` reports a pending claim
(`pending_claim: {canonical_name, created_at}` added to the `/me` response), onboarding
shows "Waiting for a club admin to connect you to <name>" instead of re-asking.

## Admin flow

Admin-only endpoints in a new `backend/app/routers/account_claims.py`, mounted under
`/players/admin` like `account_links.py`:

- `GET /players/admin/claims?status=pending` → list with requester (id, name, email, login
  type, created_at) and target (id, name, roster name, rounds-played count if cheap,
  updated_at).
- `POST /players/admin/claims/{id}/approve` → in one transaction, with the same
  `pg_advisory_xact_lock` identity locks `relink-auth0` uses:
  1. Claim must be `pending`; else 409.
  2. Target must still be active with no Auth0 login; requester must still be active with a
     login. Otherwise 409 with what changed, claim untouched.
  3. Move: clear requester's email + `auth0_id` first (unique email), then set target
     `email`, `preferences.auth0_id`, `legacy_name`, `name` = canonical.
  4. Retire the requester (same effect as `DELETE /players/{id}`: inactive, identity and
     admin flag cleared).
  5. Claim → `approved`, `resolved_by`, `resolved_at`. Log INFO.
- `POST /players/admin/claims/{id}/dismiss` → `dismissed` (idempotent on non-pending: 409).

UI: a **Claim requests** section at the top of the Account links tab
(`AccountLinkingManager.jsx`, or a sibling `ClaimRequests.jsx` it renders, to stay under
500 lines): one row per pending claim — "<requester email> wants to be <canonical name>
(profile #N, last updated …)" with **Approve** (confirm) and **Dismiss**. Empty state:
"No claim requests."

## Error handling

- Notification failures never affect the player's request (thread, logged warning).
- Approve races: the locks plus the step-2 re-check make a concurrent relink or second
  approve fail cleanly with 409 rather than half-moving identity.
- Self-heal: if a requester's login later gets linked some other way (e.g. admin relink),
  approve fails step 2 and the admin dismisses.

## Testing

Backend (pytest, SQLite fixture like `test_account_links.py`):
- picking a name held by a no-login original → 202 + one pending claim + notification
  called; picking it again → same claim; picking another → old one superseded
- name held by a profile **with** a login → 409, no claim
- unverified requester → 403, no claim
- name held only by an inactive profile → links normally (no claim)
- approve moves email/login/name to target, retires requester, claim approved; requester's
  login now resolves to the target via `get_or_create_player_profile`
- approve refused (409, nothing changed) when target gained a login / requester retired /
  claim not pending; dismiss works once
- endpoints admin-only; `/players/me` reports `pending_claim`

Frontend (vitest): onboarding shows the 202 message and the "waiting" state; Claim
requests list renders, Approve/Dismiss call the right endpoints.

Plus the full CI gate and affected `caps` capabilities.

## Out of scope

- Auto-claim without approval; matching by name similarity (player must pick the exact name)
- Moving records created on the stray
- Pre-loading emails onto the 18 originals (option C) — can be done separately any time
