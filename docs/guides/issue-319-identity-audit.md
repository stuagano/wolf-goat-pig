# Issue #319: production signup identity audit

Audited on **2026-08-30 (America/Los_Angeles)** against the production Cloud Run
API, then directly against production Cloud SQL at approximately **16:42 PDT**
after GCP authentication was restored. Source baseline: `2701744`; local repair branch:
`codex/issue-319-identity-audit`.

**Status: production identity links repaired and confirmed test signups #14,
#19, and #20 cancelled.** Brett Saks, Jeff Green, and Steve Sutorius now each
have a distinct profile linked to the email and Auth0 subject supplied from the
user's Auth0 dashboard. No profiles were merged. Live user signup/cancel acceptance
remains unverified. The user subsequently deferred external-sheet reconciliation
and requested that legacy integration be paused; both production flags are now
explicitly disabled (see the final entry below). Keep
[issue #319](https://github.com/stuagano/wolf-goat-pig/issues/319) open.

## Verified production evidence

Read-only sources:

- [Production health](https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app/health)
  returned healthy, `environment=production`, and a healthy database.
- [All profiles, including inactive](https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app/players?active_only=false)
  returned 71 profiles. The response schema includes email, `legacy_name`, and
  preferences; missing fields below were not inferred from display names.
- [Non-cancelled signups](https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app/signups?limit=10000)
  returned 15 rows. This endpoint **excludes cancelled rows**; it is not a full
  historical database audit.

| Golfer | Profile ID | Email | `preferences.auth0_id` | `legacy_name` |
|---|---:|---|---|---|
| Brett Saks | 9 | null | absent | null |
| Jeff Green | 11 | null | absent | null |
| Steve Sutorius | 8 | null | absent | null |

These are separate roster profiles, not verified Auth0 account mappings. No
other profile matched their names or the Brett/Jeff/Steve/Saks/Green/Sutorius
search terms across name, email, and legacy name. That search cannot rule out
an account stored under an unrelated display name or email. Do not assign an
email or Auth0 subject, or set links on these seed rows, merely because their
names match. No target profile currently claims Steve's canonical name.

### Steve-named rows requiring reconciliation

All three rows were returned with `status=signed_up`, null notes, and the exact
stored `player_name` **Steve Sutorius**:

| Signup ID | Golf date | Owning profile | Created at (stored value) |
|---|---|---|---|
| 14 | 2026-07-20 | 1 — Bob | `2026-07-24T01:50:54.673702` |
| 19 | 2026-07-25 | 63 — Billy Moses | `2026-07-24T18:42:10.789787` |
| 20 | 2026-07-24 | 63 — Billy Moses | `2026-07-24T18:47:59.597426` |

Bob and Billy Moses also have null email/legacy-name links and no stored Auth0
subject in the API response. Billy's profile was subsequently updated on July
26, so its present state is not proof of who controlled it on July 24. The old
client-controlled signup identity bug likewise means the stored owner ID is
not proof of the person who submitted a historical signup. Reattributing these
rows to Bob, Billy, Brett, Jeff, or Steve would be a guess.

Direct GETs to the documented legacy CGI read endpoint
`https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi?date=YYYY-MM-DD`
returned **HTTP 403** for July 20, 24, and 25. No legacy slot identifiers or
current occupants could be verified. No alternate access or write was tried.

## Corrections and regression coverage

### Resumed production database audit, 16:42 PDT

- GCP access works with the saved `personal` configuration, account
  `stuart.gano@stuartgano.com`, for project `seventh-country-232522`. The active
  TrueRoll configuration still could not refresh its credentials; it was not
  changed. All successful GCP reads explicitly selected `personal`.
- Verified serving revision `wolf-goat-pig-api-00058-p25` receives 100% of traffic
  and is attached to `seventh-country-232522:us-central1:wgp-postgres`.
- Connected through a temporary localhost Cloud SQL Auth Proxy to database
  `wolf_goat_pig`, role `wgp`. PostgreSQL confirmed `transaction_read_only=on`;
  all audit connections enforced read-only transactions and a statement timeout.
- The full database contains **71 profiles and 26 signup rows**, including **11
  cancelled rows**. The updated diagnostic reported **23 anomalies**: three
  incomplete target identities and 20 historical signup/owner-name mismatches
  across the database. No duplicate legacy-name, email, or Auth0-subject groups
  were reported. Unrelated mismatches were not modified.
- Direct SQL confirms profiles #9, #11, and #8 still have null email and legacy
  names and no Auth0 subject. All three exact names exist in `legacy_roster`.
  Canonical roster membership does not prove ownership of a login account.
- Full history adds two Steve-named rows omitted by the public signup endpoint:

| Signup ID | Golf date | Owner | Status | Created at (stored value) |
|---|---|---|---|---|
| 13 | 2026-07-24 | 1 — Bob | cancelled | `2026-07-24T01:37:33.826598` |
| 18 | 2026-07-24 | 63 — Billy Moses | cancelled | `2026-07-24T17:48:35.128387` |

Rows #14, #19, and #20 remain active as recorded above. None of the five
Steve-named rows belongs to profile #8. No relevant audit/auth history table was
found in the public schema to establish the original submitters.

The deployed revision has `LEGACY_SIGNUP_SYNC_ENABLED=true`. Its cancellation
configuration uses `type=cancel`; the absent separate cancel URL falls back to
the configured `wgp_add_tee_sheet_ajax.cgi` create URL. Thus app cancellation can
send Steve's name/date to the live sheet even though the separate `/tee-sheet`
router is disabled by default. This is why a database mismatch is not sufficient
authorization to cancel through the app. No cancellation or profile update was
performed. Verified golfer login emails/subjects and confirmation of the exact
test entries remain necessary.

### Confirmed test cleanup, 16:45 PDT

The user explicitly confirmed that active signup IDs **14, 19, and 20** were
tests and that Brett Saks, Steve, and Jeff Green are real golfers. This supplied
the evidence required to cancel those exact database rows without guessing a
new owner or changing any real profile.

- In one transaction, locked and checked each expected ID, golf date, owner ID,
  Steve name, and current status. Saved and fsynced a restricted before-state
  snapshot before writing.
- Changed **only `status` to `cancelled` and `updated_at`** for #14, #19, and #20.
  No rows were deleted or reattributed. Already-cancelled #13 and #18 were unchanged.
- Profiles **#8 Steve Sutorius, #9 Brett Saks, and #11 Jeff Green** were locked
  against concurrent updates during the transaction and verified unchanged.
- Used direct SQL so no legacy cancellation, confirmation email, or other app
  side effect could fire. No runtime configuration was changed.
- Verified committed results using a fresh database connection. A fresh production
  `GET /signups?limit=10000` returned **12 active rows, zero active Steve rows**,
  with all three test IDs absent. The three real profiles remained present and
  unchanged in the production API.

Restricted local before/commit/after JSON evidence (mode 0600) and the bounded
cleanup script are retained in:

`/Users/stuart.gano/Documents/wolf-goat-pig-artifacts/issue-319-20260830-s03h2j87/`

The snapshots contain the exact original and resulting signup fields needed for
review or recovery; they contain no database credentials. The temporary SQL
proxy was stopped after verification. External sheet cleanup is still unverified,
and names alone do not establish the golfers' login email/Auth0 mappings.

### Follow-up: captured emails for unknown signup attempts

Read-only production queries after cleanup found **zero rows** in
`pending_legacy_players` across all statuses and no non-null captured emails in
`match_players`. Only six `player_profiles` have email addresses: Stuart, Clint
Knudsen, three Stuart Gmail test aliases, and `test@example.com`. None supplies
Brett's, Jeff's, or Steve's login address.

The capture queue is not a complete login-attempt log: the current Auth0 callback
only queues a successfully created app profile when it has neither an exact
canonical match nor a fuzzy suggestion. Thus an empty queue does not establish
that no one attempted registration. Auth0's own user inventory is the next
source to check for accounts that never reached a correctly linked app profile.

The Auth0 dashboard required sign-in in both the in-app browser and Chrome.
A Chrome Auth0 sign-in tab was left for the user; no credentials were entered,
no Auth0 accounts were inspected or changed, and no production mutation occurred
during this email lookup.

### Identity links repaired from supplied Auth0 evidence, 16:59 PDT

The user supplied the Auth0 dashboard's name, email, and exact Google OAuth
subject for each golfer. These identifiers were used directly, not inferred
from fuzzy name matching. Private identifiers are retained in the restricted
local evidence rather than duplicated into this repository report.

| Golfer | Existing profile ID | Resulting canonical link | Auth0 mapping |
|---|---:|---|---|
| Brett Saks | 9 | Brett Saks | Unique supplied Google subject and email |
| Jeff Green | 11 | Jeff Green | Unique supplied Google subject and email |
| Steve Sutorius | 8 | Steve Sutorius | Unique supplied Google subject and email |

- A read-only preflight checked all 71 profiles for conflicting email, Auth0
  subject, and canonical-name ownership. All checks passed.
- In one transaction, briefly locked profile writes, repeated those checks, and
  saved/fsynced a restricted before-state snapshot. Set only each target's
  `email`, `preferences.auth0_id`, `legacy_name`, and `updated_at`, preserving all
  other preferences and using the existing canonical-link service.
- No profiles were created, deleted, or merged. All other profiles and the
  confirmed-test signup history were verified unchanged in the transaction.
- A fresh database connection and the production profiles API confirmed the
  three distinct mappings after commit. The backend's actual Auth0-subject lookup
  also resolved each supplied subject to the correct profile in a read-only
  production session; no login/profile-creation helper was used.
- The three confirmed test signup IDs remained absent from active production
  signups. No email or external-sheet action was triggered by the link repair.
- The focused audit and signup regression suites were rerun: **45 passed**.
  This is not a live JWT, golfer-browser, or external-sheet acceptance test.

Restricted before/commit/after snapshots and the bounded repair script:

`/Users/stuart.gano/Documents/wolf-goat-pig-artifacts/issue-319-identities-20260830-ajsuan5g/`

### Local code changes

The existing [audit script](../../scripts/diagnostics/audit_signup_identities.py)
could report zero anomalies for separate seed profiles with no login or roster
links. It also skipped orphan signups, omitted internally consistent Steve rows,
and directly assigned a canonical name even when another profile owned it.

The local repair:

- Reports missing requested profiles and missing email/Auth0/legacy-name evidence
  as anomalies; reports duplicate Auth0 subjects and case-insensitive emails
  without printing the subjects. Flags a canonical profile name linked to a
  different canonical golfer, including swapped links that have no duplicates.
- Includes orphan and mismatched signup owners, plus all audited-player signups
  including cancelled rows and rows whose names happen to agree with their owner.
  These are investigation leads, not automatic deletion candidates.
- Rejects a legacy-name repair if another profile claims that name, and reuses
  the existing canonical-link service. Dry-run remains the default; `--yes` only
  changes the chosen profile's link and update timestamp. It never merges
  profiles, changes email/Auth0 ownership, cancels a signup, or contacts the sheet.

[Audit tests](../../backend/tests/unit/services/test_signup_identity_audit.py)
cover those failures, read-only behavior, invalid and conflicting repairs,
dry-run, repeatability, and preserving the other users. Eight new checks failed
against the original script before the repair; a further failing check exposed
swapped links that previously reported clean.

The [three-player regression](../../backend/tests/unit/routers/test_signups_router.py)
uses an isolated database and real profile resolution from mocked verified Auth0
claims. Brett, Jeff, and Steve sign up for the same date while the client always
submits Steve's ID/name. Persisted readback and confirmation dispatch retain each
authenticated identity; cancelling Brett and Jeff leaves Steve signed up. Email
and CGI dispatch are mocked. This is not a live Auth0, browser, email-delivery,
or legacy-sheet acceptance test.

## Remaining operational boundary

1. **Completed:** restore GCP access and verify the service revision, SQL target,
   and legacy sync flags using the explicit `personal` configuration.
2. **Completed:** run the read-only production database audit, including cancelled
   rows. Findings are preserved above without credentials or raw Auth0 subjects.
   Before any eventual write, capture a restricted, transaction-current snapshot
   of the exact affected rows. Do not invoke login/profile-creation helpers as an
   audit: they can update profiles.
3. **Completed:** user-supplied Auth0 dashboard evidence was reconciled with the
   full profile inventory. Each golfer's existing profile now owns the supplied
   email/subject and correct canonical name. No collisions or merges occurred.
4. **Database portion completed:** the user confirmed #14, #19, and #20 as tests;
   those rows are now cancelled, with before/after evidence above. For the external
   sheet, have its owner identify the matching July slots and remove only confirmed
   test entries while preserving genuine bookings. Verify external readback. The repair helper shares the
   application's claim guard; it does not add a database uniqueness constraint
   or guarantee serialization against concurrent account linking.
   Do not use the app's cancellation endpoint before checking its legacy sync
   configuration: it can dispatch a cancellation using the stored Steve name.
5. Ask Brett and Jeff to hard-refresh and perform a coordinated signup/cancel
   check. Confirm `Signing up as: Brett Saks` / `Signing up as: Jeff Green`,
   persisted identity, and any intended sheet readback; verify Steve remains
   correctly linked. No messages were sent to testers or the sheet owner here.
6. Post these findings and the eventual cleanup/readback evidence on #319 before
   closing it. This report remains local; no issue comment or status was changed.

The requested independent `pi-ask` review failed with a model-endpoint HTTP 404;
no second-opinion result was available.

## Validation

- Full backend suite: **1,709 passed, 9 deselected**, exit 0. The configured
  integration/live exclusions remained in effect; 647 deprecation warnings were
  emitted. Command: `venv/bin/python -m pytest tests/ --ignore=tests/manual
  --ignore=tests/_diagnostic -q` from `backend/`, with `ENVIRONMENT=test` and live
  signup/tee-sheet integrations disabled.
- `ruff check app/ tests/` and `ruff format --check app/ tests/`: passed.
- Separate Ruff lint and format checks for the diagnostic script: passed.
- `python scripts/export_openapi.py --check`: passed; no contract changes.
- `git diff --check` and local report-link validation: passed.
- Local runtime: existing `backend/venv`, Python 3.14 with SQLite. CI's Python
  3.11/3.12 and PostgreSQL matrix was not run. No frontend source changed.
- A final production API reread at approximately **08:25 PDT** confirmed the
  three unlinked profiles and all three suspect signups remained unchanged.
- A direct read-only production SQL audit at approximately **16:42 PDT** confirmed
  those findings and identified the two additional cancelled rows above. Only this
  report changed in the resumed run; the previously passing code/tests were not
  modified or rerun.

Repository changes are local and uncommitted; no push, deployment, issue update,
or email occurred. Production mutations were limited to the user-confirmed
cancellation of signup rows #14, #19, and #20 and identity-link updates to real
profiles #8, #9, and #11. Other profiles and unrelated deployment/config changes
were preserved. External-sheet cleanup and live user acceptance remain incomplete
independently of local tests.

## Follow-up verification — August 30, 2026, 22:49–22:51 PDT

- Fresh production health returned healthy with `environment=production`.
- Read all 71 profiles through the production API. Profiles #9 Brett Saks,
  #11 Jeff Green, and #8 Steve Sutorius exactly matched the restricted repair
  snapshot for name, email, canonical name, and Auth0 subject. No other profile
  shared any target's normalized email, Auth0 subject, or canonical name.
  Private identifiers were compared in memory and are not included here.
- The signup API returns an object containing `signups` and `total`; its
  `signups` array contained 12 non-cancelled rows. Confirmed test IDs #14, #19,
  and #20 were absent, and no returned row was named Steve Sutorius. This
  verifies active API state, not the cancelled-row database history.
- The documented external sheet GET endpoint still returned HTTP 403 for
  July 20, 24, and 25. No alternate access, cancellation, or sheet write was
  attempted; external reconciliation remains unverified.
- Existing audit and three-player regression changes passed the full backend
  suite: **1,711 passed, 9 deselected, 257 warnings**, exit 0. Ruff lint and
  format checks across `app/`, `tests/`, and the audit script passed, as did
  OpenAPI `--check` and `git diff --check`. Tests used `backend/venv` with
  Python 3.14, a fresh temporary SQLite database, `ENVIRONMENT=test`, and
  disabled live legacy signup, tee-sheet, and ForeTees integrations. The
  configured integration/live exclusions remained; CI's PostgreSQL and
  Python 3.11/3.12 matrix was not run.
- The regression verifies distinct signup persistence and confirmation
  dispatch with mocked verified claims. Cancellation checks verify which rows
  remain, not owner authorization: the existing cancellation route does not
  declare a current-user dependency or ownership check. That separate concern
  was not changed or tested against production in this cleanup.
- After fetching, this branch and `origin/main` both pointed to `2701744`;
  no PR existed for `codex/issue-319-identity-audit`. Only this report was
  edited in this follow-up. Existing identity code/tests and unrelated
  booking, frontend, and deployment changes were preserved. No production
  mutation, commit, push, deployment, issue comment, or tester message occurred.

Issue #319 remains open. Remaining acceptance requires Brett and Jeff's real
login/signup/cancel checks, Steve's real login check, external sheet readback
and any owner-confirmed cleanup, and publication of the findings on the issue.

## User decision: pause legacy sheet integration — August 30, 2026

The user deferred external-sheet reconciliation and authorized disabling the
integration for now. This supersedes the earlier requirement to reconcile the
July external entries as part of this cleanup. Existing sheet entries were left
untouched; no assertion is made that they were removed or corrected.

- Updated production `wolf-goat-pig-api` in `seventh-country-232522`,
  `us-central1`, using the explicit `personal` GCP configuration and verified
  account. Changed only `LEGACY_SIGNUP_SYNC_ENABLED` from `true` to `false`
  and set `LEGACY_TEE_SHEET_ENABLED=false` explicitly.
- Revision `wolf-goat-pig-api-00060-4lk` is ready and serves 100% of traffic.
  Compared with `wolf-goat-pig-api-00059-rxh`: the container image and all other
  environment entries, including secret references, are unchanged.
- Fresh readback verified both flags are `false`; production health is healthy,
  `GET /tee-sheet?date=2026-08-30` returns 503 with the integration-disabled
  message, and a junk bearer token to `/players/me` returns 401.
- Existing switches stop outbound signup creation, update, and cancellation
  mirroring and disable the direct tee-sheet router. App database signup behavior
  and confirmation email configuration were not changed. No signup or
  cancellation was submitted to verify the setting.
- Updated `deploy/gcp/phase1-cloud-run/env.production.yaml` and the tee-sheet
  safety guide to match. YAML checks, all nine existing legacy-signup/tee-sheet
  tests, and `git diff --check` passed. No application code changed.
- These repository changes remain uncommitted and unpushed. The live pause is
  active now, but the matching config must reach the deployed branch before a
  subsequent deployment from the old config can be considered safe from
  re-enabling mirroring. Unrelated local changes were preserved.

Remaining identity acceptance is limited to real golfer login/signup/cancel
verification and recording the findings on issue #319. External reconciliation
is deferred unless the user asks to resume it. No tester message or issue
comment was sent in this turn.

## Repository delivery

The user requested pushing this work. The change set includes the audit script,
its regression tests, this report, the tee-sheet safety guide, and the two legacy
integration flags in production YAML. The separate ForeTees toggle, booking UI,
hosting, and other deployment edits are excluded. Pushing the feature branch
does not update `main`; the live pause remains in effect, and the config must be
integrated into the deployment branch before a later deployment from `main`.
