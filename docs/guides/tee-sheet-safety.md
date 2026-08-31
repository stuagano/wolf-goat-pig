# Tee-sheet safety: live side effects, preview & cleanup

Signing up in the app can write **directly to the live thousand-cranes.com WGP
tee sheet** — the same shared sheet Jeff and the club see. That live sync is
intentional (it's the whole point of the round-trip), but it surprised testers
who didn't realize a test signup would immediately change the real sheet. This
doc makes the side effects explicit and describes the guardrails added in
issue #323.

## Which actions touch the live sheet

**Current policy (August 30, 2026):** legacy sheet integration is paused at the
user's request. Production configuration explicitly sets both
`LEGACY_SIGNUP_SYNC_ENABLED=false` and `LEGACY_TEE_SHEET_ENABLED=false`.
App signups and cancellations continue in the app database without mirroring
to the external sheet. Existing external entries are left unchanged; July test
entry reconciliation is deferred. The behavior below applies if integration
is deliberately re-enabled.

- `POST /tee-sheet/signup` (used by the **WGP Signup Sheet** UI) posts straight
  to the live CGI. This is the one that mutates the real, shared sheet.
- `POST /signups` (the **Daily Signup** UI) writes to our own DB first and only
  mirrors to the legacy sheet when `LEGACY_SIGNUP_SYNC_ENABLED=true` (off by
  default).

## Guardrails

### 1. Environment gating (no silent prod writes from preview)

`POST /tee-sheet/signup` performs a live write **only** when:

- `ENVIRONMENT=production`, **or**
- `TEE_SHEET_ALLOW_LIVE_WRITES=true` explicitly opts a non-production
  environment in.

In every other case (local, preview, staging) the endpoint returns a **dry-run
preview** and performs no live mutation:

```json
{ "success": true, "live_write": false, "dry_run": true,
  "reason": "live tee-sheet writes disabled for this environment",
  "would_sign_up": { "name": "Jane Doe", "date": "2026-08-02" } }
```

### 2. Explicit dry-run

Any caller can pass `{"dry_run": true}` to preview what would be written without
touching the live sheet, even in production.

### 3. UI confirmation

The signup UI names the **exact player and date** and states that it will
change the **LIVE** tee sheet before you confirm, and shows a **LIVE** vs
**PREVIEW** badge based on the environment. A preview signup is clearly labeled
as a preview, not a real signup.

### 4. Failures are visible

A live CGI failure surfaces as an error to the user (HTTP 502), not a silent
success. The best-effort DB mirror / confirmation email that runs afterward is
logged and reported to Sentry on failure rather than swallowed.

## Testing safely

- **Use a safe future date** you're willing to clean up, and coordinate with
  the tee-sheet owner (Jeff) before writing to the live sheet.
- Prefer **preview/dry-run** for identity/onboarding testing — you do not need
  a live write to verify signup identity; the dry-run response echoes the exact
  name and date that would be written.
- Only flip `TEE_SHEET_ALLOW_LIVE_WRITES=true` (or test against production)
  when you specifically intend to verify the live round-trip.

## Cleanup responsibility

Whoever performs a **live** test signup is responsible for removing the test
row from the live tee sheet afterward (or asking the tee-sheet owner to). Test
rows accidentally written under the wrong name — e.g. the July 2026 "everyone is
Steve" incident — can be investigated with
`scripts/diagnostics/audit_signup_identities.py` (see issue #319). The script
repairs only a verified profile's `legacy_name`; it does **not** cancel database
signups or remove live tee-sheet rows. A name mismatch alone does not prove a
test booking. Reconcile exact rows with the sheet owner before cleanup; preserve
genuine bookings and distinct accounts. See the
[August 30 audit findings and remaining checks](issue-319-identity-audit.md).
