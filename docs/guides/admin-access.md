# Admin access (roster & commissioner tools)

Some routes — `/admin/roster`, `/admin`, and the promote/dismiss/add-player
roster operations — are intentionally **super-admin-only**. This doc explains who has
access, how access is granted, and what testers should expect. It exists
because testers following the July 2026 checklist hit `Access Denied` at
`/admin/roster` with no explanation of why or how to get in (issue #316).

## Who is a super admin

Super-admin status is decided by a normalized **Auth0 login email allowlist**
configured on the server via the `SUPER_ADMIN_EMAILS` environment variable
(comma-separated). `ADMIN_EMAILS` remains a temporary compatibility fallback for
existing deployments. If neither is set, the code falls back to the commissioner.
The allowlist lives in `backend/app/utils/admin_auth.py`.

The backend verifies the Auth0 bearer token and compares the **verified token
email claim** to the allowlist — never the mutable DB profile email, display
name, browser storage, or caller-supplied identity headers. `GET /players/me`
returns `role`, `is_super_admin`, and a temporary `is_admin` compatibility
alias. Everyone not on the allowlist has the `normal` role.

## Granting access

1. An existing super admin adds the new super admin's exact **Auth0 login
   email** to `SUPER_ADMIN_EMAILS` in the Cloud Run service configuration.
2. Deploy a new revision so the value is picked up.
3. The new admin hard-refreshes and re-opens `/admin/roster`.

Do not grant access by display name; names are not unique or verified.
Keep the production allowlist in Cloud Run configuration.

## What testers should expect

- **Not signed in** → the page prompts you to sign in (this is normal).
- **Signed in but not a super admin** → you see a clear "you're signed in as
  `<email>` but this area is super-admin-only; ask a super admin to grant
  access" message. This is expected for most testers — admin steps are **not**
  part of the general tester checklist.
- **Super admin** → you can open `/admin/roster` and promote / dismiss / add players.

## Tester checklist guidance

The test plan should name **one responsible admin tester** (the commissioner or
a designated admin) to perform the roster/admin steps, rather than asking every
tester to reach `/admin/roster`. Non-admin testers seeing the
authenticated-but-not-authorized message is a **pass**, not a bug.
