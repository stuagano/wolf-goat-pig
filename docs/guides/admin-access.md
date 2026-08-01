# Admin access (roster & commissioner tools)

Some routes — `/admin/roster`, `/admin`, and the promote/dismiss/add-player
roster operations — are intentionally **admin-only**. This doc explains who has
access, how access is granted, and what testers should expect. It exists
because testers following the July 2026 checklist hit `Access Denied` at
`/admin/roster` with no explanation of why or how to get in (issue #316).

## Who is an admin

Admin status is decided by an **email allowlist** configured on the server via
the `ADMIN_EMAILS` environment variable (comma-separated). If unset, the code
falls back to a small default set (the commissioner). The allowlist lives in
`backend/app/utils/admin_auth.py`.

The frontend no longer keeps its own separate hardcoded list as the source of
truth: `GET /players/me` now returns an `is_admin` boolean computed from the
same server allowlist, and the admin screens use that. This removes the old
drift where the backend `ADMIN_EMAILS` and a hardcoded frontend list could
disagree (a user could be a backend admin but still see `Access Denied`).

## Granting access

1. An existing admin (the commissioner) adds the new admin's **login email** to
   `ADMIN_EMAILS` in the Cloud Run service configuration.
2. Deploy a new revision so the value is picked up.
3. The new admin hard-refreshes and re-opens `/admin/roster`.

Do not commit real admin emails beyond the commissioner default into the repo.
Keep the production allowlist in Cloud Run configuration.

## What testers should expect

- **Not signed in** → the page prompts you to sign in (this is normal).
- **Signed in but not an admin** → you see a clear "you're signed in as
  `<email>` but this area is admin-only; ask the commissioner to grant admin
  access" message. This is expected for most testers — admin steps are **not**
  part of the general tester checklist.
- **Admin** → you can open `/admin/roster` and promote / dismiss / add players.

## Tester checklist guidance

The test plan should name **one responsible admin tester** (the commissioner or
a designated admin) to perform the roster/admin steps, rather than asking every
tester to reach `/admin/roster`. Non-admin testers seeing the
authenticated-but-not-authorized message is a **pass**, not a bug.
