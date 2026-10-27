# Universal game identity: scores are the foundation

Date: 2026-10-27 (America/Los_Angeles)
Status: Draft for written-spec approval; conceptual direction approved, implementation not authorized.
Scope: One coherent consolidation of round identity, results, history navigation, and reconciliation.

## 1. Approval boundary and outcome

### Approved product decisions

- One round → one permanent UUID → one shared game page for spreadsheet imports, manual results, scanned cards, and live scoring.
- Viewing scores is the foundation. Photos, per-hole results, comments, and gameplay enrich that same game, not another game or viewer.
- Backfill existing spreadsheet-only rounds. Repeat imports update the same identity without creating duplicates.
- Base information is date, course, players, and final totals. Unknown information remains unknown; never invent zeroes, holes, courses, or gameplay.
- Preserve existing history links and comments. Persist source-to-game associations rather than rematching by scores on every read.
- Ambiguous identity is flagged for review, never guessed or automatically merged.
- Consolidate the existing storage and viewer; retire the sheet-only display path as callers migrate. No parallel implementation.
- Preserve imported and saved conflicting values side by side, let the user resolve them, and retain an audit record.
- Notify the user through BOTH email and in-app notifications. An unchanged unresolved conflict must not repeatedly alert.

### Recommendations awaiting approval with this written spec

Sections 3–10 specify recommended technical behavior, not additional decisions already made by the user. In particular, stable spreadsheet tokens, provisional counting policy, conflict lifecycle, targeted recipient configuration, and migration safeguards require written-spec review.

This document authorizes no application changes, implementation plan, source-sheet writes, real notifications, merge, deployment, or production-data mutation. After spec review and commit, stop for written approval. Only then invoke `writing-plans`; production migration remains a separate explicit operational approval.

## 2. Current evidence and why consolidation is needed

Read-only code inspection at `931101d`; fetched `origin/main` is `278af1e` (signup-headcount change only). No live database/sheet inspection or application tests were performed for this spec. A separate read-only repository audit informed migration and notification recommendations. A Pi second-opinion attempt failed during authentication and returned no review; the user then directed that Pi not be used. No Pi retry was made; an independent read-only agent review is used instead, without claiming cross-vendor verification.

| Existing surface | Evidence and consequence |
| --- | --- |
| UUID and saved results | `backend/app/models.py`: `GameStateModel.game_id`, `GameRecord`, `GamePlayerResult` already anchor saved games. Reuse them, do not add another round root. |
| Spreadsheet/manual results | `LegacyRound` has per-player results but no game UUID; manual submission in `routers/member_rounds.py` creates only these rows. Its per-member/day constraint cannot represent two rounds on one day. |
| Source import | `services/spreadsheet_sync_service.py:get_all_rounds` reads `Details!A2:F5000`, without a source round ID. Blank quarters become zero and missing course defaults to Wing Point. These defaults must not enter the new canonical path. |
| Cache replacement | `services/email_scheduler.py` and `routers/unified_data.py` delete/replace sheet cache rows. Cache row primary keys are not durable source identities. |
| Read-time matching | `services/unified_data_service.py` uses source/date/group/location grouping and approximate roster OR sorted-total suppression; `services/round_identity.py` links saved cards in memory. Neither is permanent identity. |
| Year inference | `UnifiedDataService._parse_sheet_date` derives a year from the current clock. Reimporting history must not change a round's year. |
| Completion persistence | `services/completed_game_service.py` derives totals/metrics from hole history and commits internally; complete scoring validation requires holes 1–18. Totals-only data must not be sent through fake hole history. |
| Viewers/navigation | `frontend/src/pages/RoundStoryPage.jsx` handles historical totals/comments; `components/game/CompletedRoundView.jsx` handles saved rounds inside `SimpleScorekeeper`. `ScorecardLink.jsx` hides null UUIDs; `roundLink.js` uses date/group fallback. Consolidate into the existing UUID route. |
| Social identity | `RoundComment` and `RoundReaction` use date/group/location; reaction uniqueness includes comment/profile/emoji. Preserve IDs, authors, timestamps, and associations. |
| Alerts | `services/notification_service.py:send_notification` commits its supplied session. Never call it inside a partially written identity transaction. Reuse existing notification and email infrastructure behind safe delivery boundaries. |

The old `sheet_integration.py` profile/statistics sync and outbound `PendingSheetSync` must be included in the caller inventory: a canonical reader alone cannot prevent alternate writers from reintroducing duplicates or double-counted statistics.

## 3. Architecture and invariants

### 3.1 Extend the existing game, not a parallel round subsystem

Use `GameStateModel.game_id` as the permanent identity anchor and `/game/:uuid` as the shared page. Keep `GameRecord` plus `GamePlayerResult` as the canonical accepted final-results projection. A historical totals-only game gets a minimal honest container and final record without fabricated live state. Existing live/scanned UUIDs do not change.

Separate lifecycle (`setup`, `in_progress`, `completed`) from detail coverage (`totals_only`, `partial`, `per_hole_complete`). A completed historical result need not have recorded gameplay. Coverage is derived from actual supplied evidence, not a claim that an 18-hole round was observed. Unknown holes played, metrics, and strokes are nullable/unavailable; missing data is not the number zero. Existing numeric defaults must be explicitly bypassed or migrated for these cases.

Create a focused shared persistence boundary used by current writers. It accepts explicit final totals or validated detailed results, writes the existing projection idempotently, and does not own the outer transaction. Refactor the current internal commit boundary as part of consolidation, not by adding a separate import-only persistence implementation. Live completion retains its current full-hole validation; totals-only finalization is an explicit input mode, not a global validation bypass.

### 3.2 Required invariants

1. A source round maps to at most one canonical game; many sources may enrich one game.
2. The UUID never derives from date, names, totals, row position, or a content hash.
3. One accepted final-result row per game participant; results, social records, and sources reference that game consistently.
4. A repeated request, concurrent sync, or read cannot create a second game or apply totals twice.
5. Raw source observations and prior accepted values remain inspectable after corrections and resolution.
6. Reads use persisted associations only. Matching is an ingestion/reconciliation aid, never a viewer or standings identity function.
7. Ambiguity cannot silently attach evidence, merge games, discard results, or create a second standings contribution.
8. A UUID is an identifier, not authorization. Existing read permissions remain; writes, source binding, and conflict resolution require server-side authorization.

### 3.3 Minimum durable data contracts

These are logical responsibilities; implementation planning chooses exact names and additive migration files, not a new framework.

| Responsibility | Required content and constraints |
| --- | --- |
| Game and accepted results | Existing UUID root; played local date separate from created/completed audit times; nullable course; stable participant slots/profile links and raw name; accepted quarter totals with units/provenance; detail coverage and revision. Uniqueness on game/participant. Never merge distinct guests because their names match. |
| Source association | Source kind, stable source scope (spreadsheet ID + tab ID + configured season where relevant), immutable source-round token, game UUID, binding evidence/actor/time, latest processed revision. Unique scope/token; binding changes require audited review. |
| Source observations | Immutable raw input, participant token, parsed values, parse status, source revision/snapshot identity, observed time and content fingerprint. Distinguish missing, explicit null/removal, zero, and invalid. Retain superseded observations. |
| Historical aliases | Original date/group/location route keys and known corrected spellings → UUID or explicit unresolved candidate set. Preserve original key, even after corrections. Do not enforce a falsely unique natural key. |
| Reconciliation | Identity issue or value conflict; source references, candidate UUIDs, field/participant, proposed/saved values, fingerprint, status, revision; immutable resolution events recording actor, time, reason, selected value and evidence. |
| Delivery intent | Conflict event/revision, designated recipient profile, channel, stable dedupe key, delivery status/attempts/provider receipt/error. Unique event + recipient + channel. |

Add UUID references to legacy results/comments/reactions while retaining original fields for migration evidence and aliases. Legacy rows become source/provenance records or temporary compatibility projections, never a second authoritative result store. Preserve existing comment IDs and reaction semantics. Do not copy comments into another table/viewer as a substitute for migrating their associations.

## 4. Stable source identity and ingestion

### 4.1 An honest limit of the existing sheet

A:F alone cannot guarantee continuity after arbitrary edits: reordering, renamed players, corrected dates/totals, or two identical rounds can produce indistinguishable input. A row number, content fingerprint, roster, or score signature is not a stable source ID. A local mapping cannot recover information the source never preserved.

**Recommended source contract:** add persistent opaque round and participant tokens to the source sheet, outside existing A:F data, after explicit source-write approval. Every participant row belonging to the round carries the same round token and its own participant token. Tokens move with the complete row when sorted; supported editing/sorting must include token columns. Date/course/group corrections do not change tokens. A second round gets a new token even with identical date/course/roster/totals. Do not generate source tokens with volatile sheet formulas.

Token uniqueness is necessary but does not prove token-to-row continuity: an A:F-only sort can attach valid unique tokens to the wrong evidence. The supported editing contract must protect token/data association and require whole-row sorts; continuity checks compare participant/round evidence to the last trusted binding. When a changed snapshot cannot establish continuity, hold affected observations before even filling unknown fields. A:F plus tokens cannot detect every possible permutation, so do not claim that guarantee. Unsupported editing requires a reviewed rebind from a trusted snapshot before ingestion resumes.

Token bootstrap requires a frozen, versioned snapshot and reviewed grouping manifest before writes. Verify permissions, token placement, existing formulas, sorting behavior, and full-history range coverage first; the current 5,000-row read limit is not evidence that all history was read. Detect reused round tokens across incompatible groups and duplicated participant tokens; quarantine affected input instead of choosing a winner. Partial-column sorts or copied IDs are source integrity failures, not automatic canonical corrections.

If source writes are not permitted, retain snapshots and reviewed associations in the database, but quarantine any observation whose continuity cannot be established. An exactly repeated trusted snapshot is replay-safe; a changed source without stable IDs may require human binding again. Do not claim fully automatic correction/reorder safety in this fallback. Source token approval is a rollout prerequisite for that guarantee, not permission granted by this spec.

### 4.2 Bootstrap identity and missing information

- Retain every existing saved UUID. Repair orphaned `GameRecord` UUID containers without changing their IDs, using only available facts.
- Use a fixed configured season/year for yearless source dates, with provenance. Existing inferred dates are evidence to review, not unquestioned truth. If season cannot establish year, retain raw date, show unknown year, and exclude from season-dependent aggregates until resolved.
- Normalize known course/name aliases for candidate discovery but retain original text. Profiles require unique verified roster mapping; unresolved names remain distinct guest/source participants.
- Existing UUIDs, outbound queue evidence, explicit prior bindings, and reviewed migration evidence may establish continuity. Exact day/course/roster/totals can propose a candidate; even a unique score signature alone does not authorize a merge.
- For spreadsheet-only data with no credible existing-game candidate and a trusted distinct source-round token, create one UUID. Possible duplicates or uncertain grouping go to review before a new counted game is created.
- Two rounds on the same day are supported. Date/group/course cannot impose uniqueness. Replace the manual per-member/day assumption with round identity and request idempotency, while preserving current submission permissions/status rules.
- If a legacy composite URL previously combined two genuine rounds, preserve its social records and show an explicit ambiguity/resolution surface. Never attach that combined discussion to one round by guesswork.

### 4.3 Import transaction and retries

Fetch a complete source snapshot outside the database transaction. Failure, truncation, parse errors, or an empty response without verified successful completeness must not be treated as deletion. Keep the previous accepted state visible and expose sync health.

Serialize processing per source scope with a database-backed lease/lock. Validate the snapshot/revision is not older than the last accepted ingestion. Where Sheets offers no atomic revision precondition for the chosen API, revalidate the fetched snapshot under the lease and use a single serialized connector; document that arbitrary external editing cannot be locked by a database transaction. Incomplete/changing snapshots are retried or held for review, not applied as destructive replacements.

For each whole source round, atomically persist its association, immutable observation, accepted enrichments/results, reconciliation events, aliases, and alert intents. Unique constraints are the final protection against races; losing workers re-read the winner instead of creating another UUID. Do not split a group's participant rows across commits. Batch checkpoints advance only after commits; crash/retry returns the same persisted UUID and event keys. Failed transactions create neither partial games nor alerts.

Candidate discovery and first-game creation must also serialize across overlapping source scopes and manual actors. Recommend one database-backed reconciliation lock for first creation/binding in this application, acquired before candidate discovery, followed by a fresh committed-state read. Per-source locks alone do not cover two sheets or two actors creating the same round. A losing creator re-runs reconciliation: possible overlap is held for review, never automatically merged or additionally counted. Date/roster/totals are candidate-search evidence, not a uniqueness key; uncertain dates must not escape this coordination. This cannot identify two indistinguishable real-world rounds without external evidence, so the guarantee is no duplicate creation from known retries/concurrency, with ambiguous identity held—not perfect automatic recognition.

Manual creation requires a stable client request key plus payload fingerprint scoped to the actor; retry returns the original game, and key reuse with different payload is rejected. Enrichment explicitly targets a UUID. A caller with no UUID/source association must reconcile possible existing rounds rather than silently treating every submission as new.

Missing rows in a later sheet snapshot are not deletion instructions. Retain prior accepted results and surface source removal for review. Explicit reviewed deletion/retraction records an audit event and removes counting eligibility without deleting the UUID, evidence, links, or comments.

### 4.4 Outbound sheet sync

Carry canonical UUID/source tokens through `PendingSheetSync`. An update must update the mapped source round, not call append just because its action was classified as update. New writes use stable tokens; following a timeout, read by token before retrying an append. If the connector cannot prove whether a write committed, mark delivery uncertain and reconcile; do not append blindly. App→sheet→app echo is the same source evidence, not another game or conflict merely because it returned through Sheets. Preserve the queue until verified delivery, with bounded retry and visible failure.

## 5. Totals, detail, and conflict behavior

### 5.1 Explicit data semantics

Quarter totals and gross strokes are different measures. Preserve numeric precision compatible with existing APIs; never truncate an imported or detailed value silently. Blank quarters are unknown, explicit `0` is known zero, invalid values are quarantined, and a missing participant cannot be synthesized. A non-zero-sum round is a visible validation issue, not a reason to redistribute scores. Do not invent positions, handicaps, holes won, wagers, or strokes from final quarters.

An accepted totals-only game shows date/course/roster/totals immediately. Photo upload alone changes no totals. Partial per-hole evidence shows only supplied holes and does not replace final totals. Full detailed quarters must agree with accepted final totals per participant before being marked reconciled. If they disagree, show both totals and computed detail with a conflict badge; do not rewrite either silently. Keep the live/scan validators strict for their declared detail mode.

An import can fill a genuinely unknown field when continuity is established and there is no competing evidence. Changing or clearing an already accepted field creates a proposed revision/conflict; the accepted value remains until the user resolves it. Same-source corrections are not an exception to preservation. Accepted data is a materialized projection with provenance, not a second untraceable copy of truth.

### 5.2 Conflict lifecycle and counting recommendation

- `open`: preserve saved and proposed values, provenance, impacted participant/field, and an actionable link on the game page. Identity issues link to a reconciliation surface until a game is known.
- When a bound source/participant/field advances from proposal B to C, supersede the earlier unresolved proposal while retaining its evidence/audit history. Only the current proposal head is ordinarily actionable. Selecting superseded evidence requires an explicit corrected-value decision against current evidence.
- `resolved`: authorized user chooses saved, imported, or an explicit corrected value, or establishes distinct rounds/bindings. Transaction checks game, conflict, and current source proposal/evidence-head revisions; stale resolutions return a conflict response instead of overwriting newer evidence. Record actor/time/reason and evidence revisions, update accepted projection, and invalidate/rebuild affected aggregates atomically or with revision-safe publication.
- Reobserving an identical unresolved fingerprint updates last-seen metadata only. No additional alert intents.
- Choosing saved suppresses that same rejected observation on later syncs. A genuinely new source value/evidence revision opens a new versioned issue and may alert again. A→B→A after a completed resolution is a new change event, distinguishable from an unchanged poll; do not use a permanent value hash as the entire lifecycle key.
- Fingerprints cover normalized disputed values, participant/field, bound source identities, and the accepted revision of the disputed field or identity binding—not a global game revision that changes when an unrelated photo/comment arrives. Do not include polling timestamps, row order, or volatile snapshot timestamps. A changed snapshot with the same dispute is unchanged. Resolution events record the observations they adjudicate, so later unrelated updates cannot reopen an already rejected observation.

**Recommended standings policy:** retain the last accepted contribution for an existing game during a value dispute. New ambiguous source observations contribute nothing additional until identity is resolved; they remain visible in reconciliation with a count of held observations. Do not publish two possible copies. If two existing counted games may be duplicates, keep their pre-migration baseline contributions until reviewed and visibly mark the aggregate provisional; do not silently suppress either based on approximate matching. A disputed new game with no accepted totals is visible but not counted. This prioritizes honest uncertainty over fabricated certainty and is a product policy for written approval.

For partially known rounds, recommend whole-game score eligibility: count the game in score-based standings only when every known roster participant has an accepted final total and no unresolved roster-completeness issue exists. Known partial values remain visible in history but do not enter score sums, score-based round counts, best/worst results, wins, or average denominators until eligible. Participation can be reported separately as known appearances, explicitly labeled and never used as the score-average denominator. Publish scored-round count, known participation count, and incomplete/provisional coverage consistently across standings, personal statistics, weekly summaries, and rebuilt aggregates. Previously accepted complete results remain eligible during a value dispute under the policy above; new incomplete evidence cannot silently erase that baseline.

## 6. Both notification channels, one designated recipient

Reuse `notification_service.py` for the in-app notification and `email_service.py` for email transport. Do not create another provider stack or send to all admins by default.

Recommend one explicit configuration entry identifying the conflict-review recipient by `PlayerProfile.id`, with server-side validation that it is the intended active user profile and has an appropriate verified email linkage. Email comes from that validated account record, not spreadsheet cells, arbitrary request data, or a hardcoded address. Recipient selection is an operational confirmation with the user; current admin email defaults do not establish consent. Store only IDs/non-secret configuration in source control; never expose addresses, credentials, or transport secrets in diagnostics. Missing/invalid recipient configuration retains the issue and pending intents, exposes delivery-unconfigured health, and blocks rollout acceptance of the BOTH-channels requirement.

Create an outbox/delivery intent in the same transaction as the conflict event. A post-commit dispatcher claims each channel independently. Because the current notification helper commits internally, call it only with a dedicated delivery session; make creation of a notification with the stable event/recipient key and its delivered marker atomic in that session. Enforce database-level idempotency for in-app creation. Never let that helper commit a source import or conflict-resolution transaction.

Email uses a stable idempotency key if the current provider supports it. Retry transient failures without re-enqueueing a new conflict; one successful channel does not resend while the other retries. Record provider acceptance separately from confirmed inbox delivery. A timeout after acceptance is uncertain: use provider status/idempotency where available, otherwise hold for reconciliation rather than promise exactly-once email or blindly retry. Surface permanently failed/uncertain channel delivery in-app to the designated reviewer and in operational health without recursive alert creation.

Alerts contain a short issue summary and authorized application link; detailed source evidence stays behind application permissions. Config changes do not broadcast old issues: explicitly requeue outstanding issues for the newly confirmed recipient, preserving the delivery audit. No notification is sent during this design exercise or migration dry runs.

## 7. One viewer and compatible history

Enhance the existing `/game/:uuid` route and completed-round components to accept honest result coverage. Totals/roster appear first; per-hole detail, photo, comments, and gameplay appear only when present. Unknown fields render as unknown/not recorded. Totals-only games do not trigger live-resume/setup flows or offer a fake “complete 18 holes” action. Existing edit permissions remain enforced server-side; imported games with no creator do not grant anonymous editing.

Move the historical discussion/reactions behavior into this same game surface, preserving the original records. Update history, standings, member history, recent rounds, and scorecard links to always use the persisted UUID for resolved games. Detail availability controls detail actions, not whether a valid base game is clickable.

Keep `/rounds/:date/:group?location=...` only as a compatibility resolver. A unique persisted alias navigates to `/game/:uuid`; ambiguous aliases show choices/review state, missing aliases show an honest not-found state. Old comment/reaction endpoints resolve through the same alias mapping and retain existing authorization. New link copying emits the UUID route. Corrected date/course must not break old aliases. Date-only UI normalization must not erase old URLs before lookup.

Remove the independent sheet-only rendering and read-time card matching once callers use this common path. Temporary compatibility routes/projections are migration scaffolding with explicit retirement criteria, not permanent parallel products. A shadow parity check is verification, not another user-facing viewer or source of truth.

## 8. Migration safety and cutover criteria

This is the recommended migration contract, not an execution plan or permission to run it.

### Inventory and dry-run evidence

Use additive schema changes and existing migration tests, but do not execute identity backfill through the current startup runner. `backend/app/migrations_runner.py` sorts filenames lexicographically, splits SQL at semicolons, commits each statement, and logs failures without blocking boot; it does not provide atomic backfill or cross-instance coordination. Backfill requires a separately invoked, explicitly coordinated operation with whole-game transactions and durable checkpoints. Preserve the current string UUID storage type; a native UUID conversion is unrelated scope. `init_db()` runs before migrations and maintains `legacy_rounds_official` using `SELECT *`; explicitly account for view recreation and PostgreSQL/SQLite upgrade ordering when new columns are introduced.

Inventory all readers/writers: all three destructive refreshes (`services/email_scheduler.py`, `routers/spreadsheet_sync.py:/admin/spreadsheet/sync-legacy-rounds`, and `routers/unified_data.py:/data/sync-sheets`); manual posts and attestation; live completion; scanned-card creation/corrections; outbound queue; mounted `routers/sheet_integration.py:/sync-wgp-sheet` and `sheet_integration_service.py` aggregate writers; `player_service.py` result append/statistics increment; raw-cache admin/Commissioner statistics, `weekly_highlights.py`, personal history, social endpoints, and repair/import scripts. Bring all counting paths under one explicit season/eligibility contract. The existing `WGP-{LegacyRound.id}` code is participant-result identity, not whole-game identity; preserve it as a compatibility reference rather than silently redefining it. Existing status and prior-season rules must be preserved deliberately, not accidentally broadened. Restrict or retire old aggregate writers within this consolidation so they cannot bypass the writer fence; do not expand this into unrelated endpoint cleanup.

A read-only dry run on an authorized restored snapshot must output a deterministic manifest: every source round/participant, source scope and fixed season, existing UUID candidates, proposed/reviewed binding, alias/social ownership, data-quality issues, expected accepted values, old/new standings differences and reason codes, and stable operation keys. Totals and source-row counts alone are insufficient: every row must be accounted for as attached, explicitly retired, or held with a reason. Keep snapshots and manifest checksums; logs redact sensitive values where unnecessary. Do not infer permission for a production query from this document.

### Expand, backfill, switch, contract

- Pause ALL destructive syncs and relevant writes/queue workers during the final reconciliation window; enforce a writer fence so stale workers cannot resume the old replace/append path after cutover.
- Take recoverable backups and a final complete source/database snapshot. Reconcile its drift against the approved manifest before applying bindings. Do not backfill concurrently with unaccounted writers.
- Backfill in resumable whole-game transactions, preserving existing UUIDs. Add associations and UUID social references without dropping old columns/data. Unique constraints protect retries and concurrent attempts; checkpoint after durable commits.
- Retain all historical aliases, comments, and reactions. Ambiguous ownership remains explicitly unassigned for review, never duplicated onto candidate games. Verify authors/timestamps/comment IDs and reaction uniqueness, not merely row counts.
- Switch canonical writes and read projections together under the fence. Imported snapshots are provenance only; no union of canonical and unbound cache results in a normal aggregate. Migrate direct statistics writers so the same game cannot increment statistics through two paths.
- Verify complete source accounting, stable UUID reimport, reachable pages, social/alias parity, both alert channels in a safe test environment, and explain every standings delta. Any unresolved issue that changes published standings needs explicit user acceptance before cutover; otherwise cutover is blocked.
- Resume only converted writers and queue workers, with health/error visibility. Remove approximate duplicate suppression, delete/replace cache sync, duplicate statistics mutation, sheet-only viewer, and obsolete read-time identity code after caller migration is proven. Retain legacy source evidence/aliases, not legacy authority.

### Rollback without identity loss

Before publication, stop and revert the cutover transaction/batch using the manifest while preserving backups; no external alerts/source writes occur until the corresponding commit is durable. After UUIDs or writes have been published, rollback means pause ingestion/outbound dispatch, fence incompatible writers, and serve the last verified canonical revision using a compatible build. Keep additive schema, issued UUIDs, associations, observations, social records, resolution events, and delivery records intact. Never roll back to destructive cache replacement or regenerate issued IDs. If an old binary cannot preserve these contracts, remain paused and forward-fix instead of deploying it. Restore a backup only under a separately reviewed recovery process that accounts for every post-backup write and external delivery.

## 9. Verification requirements for later implementation

Use fixtures and a real PostgreSQL integration environment for uniqueness/locking/transaction behavior; SQLite-only tests cannot prove production race safety. Existing starting coverage includes `backend/tests/unit/services/test_round_identity.py`, `backend/tests/unit/routers/test_round_identity_flow.py`, and `frontend/src/pages/__tests__/RoundNavigation.test.jsx`; change expectations to persisted identity, not approximate rematching.

| Scenario | Required observable result |
| --- | --- |
| Historical sheet-only round | One persisted UUID, base scores visible through shared route, no fabricated holes/metrics. |
| Identical import and worker restart | Same UUID/result count and no new conflict/alert; reads create no identity mutations. |
| Row reorder; corrected date/course/name/score | Tokens retain identity; old aliases work; accepted changes require reconciliation; participant correction cannot silently reassign profiles. |
| Missing year, blank score/course, explicit zero, invalid number | Fixed reviewed season or unknown year; missing stays unknown; zero stays zero; invalid held visibly. |
| Same-day repeated roster; equal totals; token corruption | Separate valid tokens remain separate games; ambiguous/corrupt tokens are held, never score-merged. |
| Concurrent first import/manual retry | Database re-read proves one game/participant projection and one association; differing payload with same request key rejected. |
| Snapshot failure/truncation/removal/stale worker | Previous accepted scores stay visible; no inferred deletion; stale/fenced ingestion cannot overwrite newer state. |
| Scan/photo/partial/full detail enrichment | Same UUID; photo does not mutate totals; partial holes remain partial; mismatched detail raises preserved-value conflict; live completion still requires full validation. |
| Conflict resolve versus new import | Optimistic revision check prevents lost update; audit actor/baseline/source/decision is durable. |
| Unchanged/rejected/new/recurrent dispute | No repeated unchanged alert; rejected observation stays suppressed; genuine changed/recurrent event has its own revision and channel intents. |
| Import rollback; alert worker crash; provider timeout | No precommit notification; one in-app item on retry; independent email retry/uncertain state without blind duplicates. |
| Recipient missing/wrong/changed | No blanket admin mail; queued/unconfigured health; explicit validated requeue and audit. |
| Old links/social records and orphaned saved record | Unique aliases reach existing UUID; ambiguous aliases do not guess; comment/reaction IDs/ownership survive; orphan repair keeps UUID. |
| Standings, history, player statistics, outbound echo | One accepted contribution per UUID/participant across every caller; held issues visible; app→sheet→app never adds a second round. |
| Migration rerun and rollback after new writes | Stable mapping/checkpoints; preserved UUIDs and social/audit data; old destructive writers cannot restart. |

Prove browser → API → persisted data → history/standings → shared game page, including a totals-only import enriched later by a photo and detailed scores, using read-after-write assertions. Verify unauthorized conflict resolution/edit attempts fail. No production alerts/data edits are implied by these tests.

Before any implementation push, run the repository's FULL applicable frontend and backend gates from `AGENTS.md`, including frontend typecheck and backend OpenAPI drift check; document real exit codes. Add targeted migration/concurrency/reconciliation tests as above, not just snapshots or mocked success messages. This docs-only draft makes no application test-pass or deploy-readiness claim.

## 10. Review focus and non-goals

Written-spec review should explicitly confirm: stable source-token approach and separate sheet-write approval; keep-last-accepted/provisional standings policy; designated recipient configuration; fill-unknown versus conflicting correction behavior; and safe cutover/rollback rules. If any recommendation is rejected, revise this spec before planning. These are approval topics, not missing implementation placeholders.

Not in scope: a new scoring engine, another history/scorecard viewer, unrelated sheet/profile cleanup, new email provider, automatic fuzzy merging, automatic allocation of final totals across holes, blanket admin notifications, or expanding edit rights. No implementation plan is included. The next authorized deliverable is the reviewed, committed written spec; then stop for the user's approval.
