# Universal Game Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One permanent UUID and one scores-first page for every resolved round, with honest detail, persisted source associations, audited reconciliation, and single-count statistics.

**Architecture:** Extend `GameStateModel`, `GameRecord`, and `GamePlayerResult`; do not add a second round root or viewer. Consolidate existing writers into caller-owned transactions, persist immutable source evidence and conflicts, and dispatch both alert channels after commit. Migrate readers/writers together behind a database writer fence and preserve existing UUIDs/social records/URLs.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL 15, SQLite unit tests, Pydantic, React/JSX, pytest, Vitest, existing notification/email providers. No new runtime dependency.

**Spec:** `docs/superpowers/specs/2026-10-27-universal-game-identity-design.md`, approved 2026-10-27. Read the spec before this plan.

## Global Constraints

- “One round → one permanent UUID → one shared game page for spreadsheet imports, manual results, scanned cards, and live scoring.”
- “Unknown information remains unknown; never invent zeroes, holes, courses, or gameplay.”
- “Ambiguous identity is flagged for review, never guessed or automatically merged.”
- “No parallel implementation.”
- “Notify the user through BOTH email and in-app notifications. An unchanged unresolved conflict must not repeatedly alert.”
- Preserve UUIDs, comment/reaction IDs, author/timestamp history, aliases, participant-result codes, submission permissions, pending exclusions, and prior-season boundaries.
- No Pi. No automatic fuzzy merge, native-UUID conversion, new scoring engine, provider replacement, or unrelated cleanup.
- This approval authorizes planning only. Do not execute the tasks until execution is explicitly chosen. Production queries/migrations, sheet writes, real email, merge, and deployment require separate approval.
- Use the existing Orca checkout `stuagano/universal-game-identity`; no competing checkout or parallel implementation. Preserve the unrelated root `package-lock.json` modification. Use `backend/venv`, never `backend/.venv`.
- This is one ordered consolidation, not independently deployable parallel subsystems. Intermediate commits are not production cutovers. Do not push to main.

## Starting state and execution gates

Base: `931101d`; spec commit: `55da609`; fetched `origin/main`: `278af1e` (signup headcount only). Reinspect Git/Orca/live PR state before execution; reconcile newer base changes without overwriting local work. No `SUMMARY.md` was found in this checkout or inspected ancestor levels.

Before **every** mutation, inspect symlinks and existing diffs. Before each commit invoke `git-workflow-discipline`; stage explicit paths only. Tests use synthetic fixtures/local disposable PostgreSQL and mocked transports, never production credentials.

**Gate A — start:** user selects execution approach. **Gate B — source contract:** user approves exact token-column placement, protection/sorting behavior, source season, and specific sheet writes after a read-only fixture/restored-snapshot rehearsal. **Gate C — recipient:** user confirms their active profile ID and verified email linkage; no all-admin fallback. **Gate D — cutover:** approved manifest, backups, writer fence, and every standings difference accepted. Gate B/C/D are not satisfied by approval of this plan.

## File structure and ownership

Existing roots remain authoritative. New files below are narrow functions/contracts, not alternate pipelines.

| File(s) | Responsibility |
| --- | --- |
| `backend/app/models.py` | Extend existing game/result/social/queue/notification models; import new identity models for metadata registration. Avoid unrelated reformat/splitting of this already large file. |
| `backend/app/models_round_identity.py` (new, under 500 lines) | Source/evidence/field-head/issue/audit/alias/request/lease/checkpoint models on existing `Base`; string game UUID references, not a new game root. |
| `backend/app/schemas/round_identity.py` (new) | Explicit input/result/decision/view contracts. |
| `backend/app/services/completed_game_service.py` | Existing final-results writer, generalized for explicit totals versus detail; no internal commit. |
| `backend/app/services/round_identity.py` | Replace read-time fuzzy linking with source binding, creation coordination, and persisted alias lookup. |
| `backend/app/services/round_reconciliation.py` (new) | Immutable observations, per-field heads, conflicts, resolution and audit. |
| `backend/app/services/round_delivery.py` (new) | Durable channel intents/leases and existing notification/email service integration. |
| `backend/app/services/spreadsheet_sync_service.py`, `email_scheduler.py` | Complete source snapshots, stable tokens, one import caller and safe outbound updates. |
| `backend/app/routers/round_reconciliation.py` (new) | Authenticated reviewer APIs, aliases and sync health; no unauthenticated binding operations. |
| `backend/app/routers/games.py`, `games_holes.py`, `member_rounds.py` | Existing creation, enrichment and correction callers; revisions/idempotency and outer commits. |
| `backend/app/routers/round_stories.py`, `services/unified_data_service.py` | UUID social operations and canonical read projections. |
| `backend/scripts/migrate_round_identity.py` (new) | Explicit offline dry-run/apply/verify CLI; never boot-time backfill. |
| `backend/app/services/round_identity_migration.py` (new) | Deterministic manifest, whole-game batches, checkpoints, parity and forward-recovery verification. |
| `backend/migrations/zz_20261027_round_identity_expand_postgres.sql` (new) | Restart-safe additive DDL, deliberately after older lexicographic migration names. No data backfill. |
| `frontend/src/pages/SimpleScorekeeperPage.jsx`, `hooks/useGameData.js`, `components/game/CompletedRoundView.jsx` | Existing shared UUID route branches to passive completed view before live hooks. |
| `frontend/src/components/game/RoundDiscussion.jsx`, `RoundConflictReview.jsx` (new) | Reusable discussion and reconciliation sections mounted on that same game page. |
| `frontend/src/pages/RoundReconciliationPage.jsx` (new) | Designated-reviewer identity issue inbox; not another score viewer. |
| `docs/guides/universal-game-identity-cutover.md` (new) | Explicit operational gates, accounting and rollback procedure. |

Import `Base`/UUID helper into the new model file without circular dependencies: new models use `String` for existing UUIDs and string foreign-key references; `models.py` imports new classes after its current model declarations. Add actual foreign keys only after orphan accounting; never silently drop orphan data to satisfy a constraint.

## Shared interface contract

All named functions/types below are introduced by the identified task. No executor should invent different names between tasks.

```python
# backend/app/schemas/round_identity.py (Task 1)
# Pydantic fields; values below describe exact public attributes.
# RoundParticipant: participant_id: str; name: str;
#   profile_id: int | None; quarters: float | None
# RoundDraft: played_on: date | None; raw_date: str | None;
#   course_name: str | None; group: str | None;
#   players: list[RoundParticipant]; roster_complete: bool;
#   detail_coverage: Literal['totals_only', 'partial', 'per_hole_complete'];
#   hole_history: list[dict]; actor_profile_id: int | None
# SourceRef: kind: str; scope: str; round_token: str
# IngestOutcome: status: Literal['accepted', 'unchanged', 'held'];
#   game_id: str | None; issue_ids: list[str]; revision: int | None
# ResolutionDecision: action: Literal['keep', 'accept', 'correct',
#   'bind_existing', 'confirm_distinct', 'retract']; value: object | None;
#   target_game_id: str | None; reason: str; expected_game_revision: int | None;
#   expected_issue_revision: int; expected_head_revision: int
```

`RoundDraft` rejects nonfinite quarters, duplicate participant tokens/profile IDs, and invalid dates; distinct guest slots may share a display name. Use floats only within existing numeric compatibility, reject values the public contract cannot represent, and never `int()`-truncate quarters. Store unknown totals as SQL NULL; preserve raw input separately. Missing observations never imply a clearing operation; clearing requires explicit presence/removal evidence.

```python
# Task 2: services/completed_game_service.py; never commit internally
persist_final_results(db: Session, game: GameStateModel,
                      draft: RoundDraft) -> int  # accepted game revision
# Existing persist_completed_game(db, game) remains the detail entry point,
# delegates to the same writer and returns its existing created-row count.

# Task 3: services/round_reconciliation.py; caller owns transaction
observe_round(db: Session, source: SourceRef, draft: RoundDraft,
              *, observation_key: str, raw_payload: dict,
              continuity_verified: bool,
              create_without_candidate: bool = False) -> IngestOutcome
resolve_issue(db: Session, issue_id: str, decision: ResolutionDecision,
              *, actor_profile_id: int) -> IngestOutcome
# Task 3: services/round_identity.py
acquire_reconciliation_lock(db: Session) -> None
resolve_round_alias(db: Session, date_key: str, group: str,
                    location: str) -> list[str]  # zero/one/many UUIDs

# Task 4: services/spreadsheet_sync_service.py
fetch_round_snapshot(scope: str, *, season_year: int | None) -> SheetSnapshot
# SheetSnapshot (Task 4 schema): scope, fingerprint, complete: bool,
# source_version: str | None, rounds: list[SheetRound], errors: list[str].
# SheetRound: source: SourceRef, draft: RoundDraft, raw_payload: dict,
# observation_key: str, continuity_verified: bool.
# Task 4: services/round_identity.py
sync_round_snapshot(db: Session, snapshot: SheetSnapshot) -> list[IngestOutcome]
# Task 6: services/round_delivery.py (dedicated delivery sessions)
dispatch_round_deliveries(*, limit: int = 50) -> dict[str, int]
# Task 11: services/round_identity_migration.py
build_manifest(db: Session, snapshot: SheetSnapshot) -> dict
apply_manifest(db: Session, manifest: dict, *, expected_checksum: str,
               batch_size: int = 50) -> dict
verify_manifest(db: Session, manifest: dict) -> dict
```

### Task 1: Add durable contracts, evidence tables, and a writer fence

**Files:** Modify `backend/app/models.py`, `backend/app/database.py`; create `models_round_identity.py`, `schemas/round_identity.py`, the expand SQL migration, `backend/tests/unit/test_round_identity_schema.py` and `backend/tests/unit/test_round_identity_upgrade.py`.

**Consumes:** Existing `Base`, string UUID columns, `AppConfig`. **Produces:** Types above; new ORM models `RoundSource`, `RoundObservation`, `RoundFieldHead`, `RoundIssue`, `RoundResolution`, `RoundAlias`, `RoundRequest`, `RoundDelivery`, `RoundIdentityLease`, `RoundMigrationCheckpoint`. Add `backend/tests/unit/round_identity_support.py` in this task with `identity_db`, `saved_game`, `bound_round`, and `conflicted_round` fixtures: temporary SQLite engine, `Base.metadata.create_all`, active reviewer and four verified roster profiles, persisted completed UUID for bound cases, explicit `AppConfig` test mode/epoch, independently committed fixture seed and per-test rollback. API tests include relevant routers and override `get_db`/`get_current_user` using the existing `round_api` pattern. Later tasks extend this same helper rather than inventing implicit production sessions.

- [ ] Write failing schema/upgrade tests. Include this concrete minimum:

```python
def test_unknown_is_not_zero():
    from app.schemas.round_identity import RoundParticipant
    assert RoundParticipant(participant_id='p1', name='Avery',
                            profile_id=None, quarters=None).quarters is None

def test_source_binding_is_unique(identity_db):
    from sqlalchemy.exc import IntegrityError
    from app.models_round_identity import RoundSource
    import pytest
    for _ in range(2):
        identity_db.add(RoundSource(kind='sheet', scope='fixture:tab:2026',
                                    round_token='r1', game_id='existing'))
    with pytest.raises(IntegrityError):
        identity_db.flush()
```

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/test_round_identity_schema.py backend/tests/unit/test_round_identity_upgrade.py -v` from repository root. Expect failure on missing contracts, not a database connection error. Fixtures create temporary SQLite schemas, seed `existing`, and roll back after each case.
- [ ] Implement additive schema: `GameStateModel.revision`; `GameRecord.played_on`, raw date, group, coverage, `roster_complete`, score eligibility and accepted revision; `GamePlayerResult.participant_id`, nullable total/position/detail-derived metrics. Keep existing IDs. Nullable UUID links on `LegacyRound`, comments/reactions, queue; queue source token/operation key/expected revision; notification nullable unique `delivery_key`.
- [ ] Implement table constraints: unique source kind/scope/token; immutable observation source/content-event key; unique field head source/participant/field; issue generation/head/baseline revisions; immutable resolution rows; alias unique exact original key + target UUID (multiple candidates allowed); request unique actor/key + fingerprint/outcome; delivery unique issue event/recipient/channel; migration checkpoint unique manifest/game operation. Use JSON raw/accepted/proposed values with explicit present flags. Use `AppConfig(name='round_identity')` for mode (`legacy`, `paused`, `canonical`), epoch, season, reviewer profile and confirmed routing state. Default absent config to `legacy`; never auto-cut over at boot.
- [ ] Implement SQLite column upgrades and PostgreSQL DDL restart behavior without destructive schema downgrade. New constraints involving migrated data remain staged until Task 11 accounting. Do not rebuild arbitrary existing tables at boot; explicitly support the disposable/restored SQLite rehearsal. Test view initialization before and after expansion, rerunning DDL, and partially applied migrations. Keep data backfill out of `run_sql_migrations`.
- [ ] Rerun tests; inspect metadata and foreign-key targets. Commit only this schema slice: `git commit -m "feat(rounds): add durable identity and reconciliation contracts"` after staging its explicit paths.

### Task 2: Make existing result persistence totals-aware and transaction-owned

**Files:** Modify `backend/app/services/completed_game_service.py`, `backend/app/routers/games.py`, `backend/app/routers/games_holes.py`; create `backend/tests/unit/services/test_final_results.py`; extend `backend/tests/unit/test_score_save_postgres.py` in Task 12 for physical readback.

**Consumes:** Task 1 `RoundDraft`/columns. **Produces:** `persist_final_results` and retained `persist_completed_game` signature; strict detail validation; outer commit ownership.

- [ ] Write tests around an actual SQLAlchemy session, including:

```python
def test_totals_only_rollback_has_no_projection(identity_db, saved_game):
    from app.services.completed_game_service import persist_final_results
    from app.schemas.round_identity import RoundDraft
    from app import models
    draft = RoundDraft(played_on=None, raw_date='unknown', course_name=None,
        group=None, players=[dict(participant_id='p1', name='Avery',
        profile_id=None, quarters=0)], roster_complete=True,
        detail_coverage='totals_only', hole_history=[], actor_profile_id=None)
    persist_final_results(identity_db, saved_game, draft)
    identity_db.rollback()
    assert identity_db.query(models.GameRecord).count() == 0
```

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/services/test_final_results.py backend/tests/unit/routers/test_round_posting_p1.py -v`; establish red for explicit totals and no internal commit.
- [ ] Implement one final-results writer: stable participant-key upsert, no additive statistics increments, field provenance/revision updates, unknown metrics as NULL, honest minimal completed state, and no default Wing Point/18 holes/handicap. Explicit zero counts as known. Partial detail never replaces totals; full detail disagreement produces evidence for Task 3, not silent replacement. Preserve existing gross scores, teams, notes, and other supplied detail on targeted corrections.
- [ ] Remove internal commit from `persist_completed_game`, update every caller to commit once after its entire domain operation, and capture primitive response values before commit. Reject duplicate holes instead of last-write-wins. Keep live completion requiring all 18 explicit holes; distinguish totals-only finalization at the input boundary. Existing live non-complete save semantics remain.
- [ ] Rerun the two modules and existing score-save tests. Verify one transaction rollback removes game/results together, repeated saves preserve result IDs, and no ORM refresh occurs after commit. Commit: `git commit -m "refactor(rounds): unify explicit totals and detailed result persistence"`.

### Task 3: Persist binding, conflict heads, and audited resolution

**Files:** Replace identity behavior in `backend/app/services/round_identity.py`; create `backend/app/services/round_reconciliation.py`, `backend/tests/unit/services/test_round_reconciliation.py`, and `backend/tests/unit/services/test_round_creation_races.py`.

**Consumes:** Tasks 1–2 contracts/writer. **Produces:** `observe_round`, `resolve_issue`, `acquire_reconciliation_lock`, `resolve_round_alias`; pending channel intents through `RoundDelivery` rows (delivery implemented in Task 6).

- [ ] Write first behavior tests:

```python
def test_changed_total_preserves_accepted_value(bound_round):
    db, source, draft, game_id = bound_round
    from app.services.round_reconciliation import observe_round
    draft.players[0].quarters = 12
    result = observe_round(db, source, draft, observation_key='change-1',
        raw_payload={'quarters': 12}, continuity_verified=True)
    assert result.game_id == game_id
    assert result.issue_ids
    db.flush()
    from app import models
    assert db.query(models.GamePlayerResult).filter_by(
        participant_id=draft.players[0].participant_id).one().total_earnings != 12
```

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/services/test_round_reconciliation.py -v` and establish red.
- [ ] Preserve existing `normalized`, `course_name`, `group_rounds`, `round_day` and legacy imports while dependent readers migrate. Legacy `link_saved_cards` may remain only in fenced pre-cutover mode until Task 12 removes it; never use it as canonical identity proof. Implement first-create lock using PostgreSQL transaction advisory lock with one constant key for the application; SQLite uses serialized fixture transactions (not a claimed concurrency proof). Read committed candidates after acquiring the lock. Existing bindings take precedence; candidate matches only cause `held` outcomes without auto-merge. Trusted new source tokens create only when no credible candidate or explicit reviewed distinct-round decision exists. Stable slot identity must not be replaced by name similarity. Reassignment requires audit.
- [ ] Implement immutable observation dedupe, accepted per-field evidence/baseline revisions, unknown-only fill with verified continuity, and change/removal conflicts. Fingerprints omit row order, poll times, and unrelated game revisions. One current proposed head per source/participant/field; new proposals supersede old issues. A repeated rejected observation stays adjudicated; a later real transition has a new event generation. Record non-zero-sum/parse/roster integrity issues without manufacturing balancing values.
- [ ] Implement resolution authorization as an explicit caller/service check for the designated active reviewer or existing admin, never inferred from a UUID. Compare issue/head/game revisions under lock; stale returns domain conflict mapped to HTTP 409. Keep/import/correct/bind/distinct/retract decisions retain raw evidence, selected values, actor/reason/time, aliases, and immutable audit. Stale proposals cannot be ordinarily accepted. Resolutions update canonical eligibility; current accepted contributions survive value disputes.
- [ ] Add parameterized tests for repeated import, blank/zero, distinct guests, same-day rounds, orphan UUID, no score-based merge, unrelated photo revision, B→C supersession, rejected B replay and A→B→A transitions. Test no alerts/domain rows survive rollback. Run and commit: `git commit -m "feat(rounds): reconcile source evidence without silent merges"`.

### Task 4: Replace all sheet refreshes with one complete-snapshot ingestion

**Files:** Modify `backend/app/services/spreadsheet_sync_service.py`, `services/round_identity.py`, `services/email_scheduler.py`, `routers/spreadsheet_sync.py`, `routers/unified_data.py`; create `backend/tests/unit/services/test_round_snapshot_sync.py`.

**Consumes:** Tasks 1–3. **Produces:** `SheetSnapshot`/`SheetRound`, `fetch_round_snapshot`, `sync_round_snapshot`; all three refresh entry points call the same operation.

- [ ] Write parser/sync tests using mocked Sheets responses:

```python
def test_blank_sheet_total_stays_unknown(monkeypatch):
    from app.services import spreadsheet_sync_service as sheet
    monkeypatch.setattr(sheet, '_sheets_api_get', lambda *a, **k: {
        'values': [['6-Oct', 'B', 'Avery', '', '', '', 'r1', 's1']]})
    snapshot = sheet.fetch_round_snapshot('fixture:tab:2026', season_year=2026)
    assert snapshot.rounds[0].draft.players[0].quarters is None
    assert snapshot.rounds[0].draft.course_name is None
```

The fixture adapter supplies verified metadata and complete response markers; never make this unit test reach Google.

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/services/test_round_snapshot_sync.py -v`; expect blank/default/token behaviors to fail initially.
- [ ] Implement full-history reads using verified tab ID/dimensions and complete-range detection, configured fixed season, raw preservation, finite numeric validation, and distinct missing/explicit-null/zero states. Parse G/H token columns only in the fixture/proposed layout; production placement remains Gate B. Without approved tokens, only a reviewed manifest or an identical trusted snapshot may establish continuity. Unknown year stays unknown.
- [ ] Enforce per-source lease plus global first-binding lock in fixed order (source lease then reconciliation lock); snapshot revalidation before mutation, monotonically processed connector generation, stale-worker epoch fence, and whole-round transactions. Fetch outside game transactions. A source lease uses dedicated session ownership/expiry/heartbeat; expired owner must abort before commit. Empty/failed/truncated/changing snapshots never delete prior accepted data.
- [ ] Replace destructive delete/insert bodies in all three refresh callers. Old mode remains available only before cutover; canonical mode has no fallback to cache replacement. Publish parse/sync health and held counts without returning private source rows publicly. Source disappearance creates review evidence, not deletion.
- [ ] Test row reorder, copied token, partial-column displacement, repeated snapshot, changed source version, missing rows, >5,000 rows, clock/year rollover and concurrent refresh endpoints. Unsupported edits/uncertain continuity are held before unknown-field fills. Commit: `git commit -m "feat(rounds): preserve source identity across spreadsheet sync"`.

### Task 5: Route manual, scanned, live, and offline writes through one identity

**Files:** Modify `backend/app/routers/member_rounds.py`, `games.py`, `games_holes.py`, `utils/round_card.py`; `frontend/src/components/rounds/PostRoundForm.jsx`, `services/rounds.js`, `components/game/ScorecardPhoto.jsx`, `ScorecardReview.jsx`, `services/syncManager.jsx`, `hooks/useScorekeeperSync.js`; create `backend/tests/unit/routers/test_round_identity_writes.py` and `frontend/src/components/game/__tests__/ScorecardIdentity.test.jsx`.

**Consumes:** Tasks 1–4. **Produces:** Existing creation endpoints return `{game_id, revision, status, issue_ids}`; reviewable ambiguous creation returns HTTP 202 with `game_id: null`. Existing response fields needed by callers remain. Enrichment routes require a UUID and `expected_revision`; HTTP 409 returns `{code:'stale_round', game_id, revision, issue_ids}`. Creation takes `Idempotency-Key`; actor/key reuse with different content returns 409.

- [ ] Add the following API contract test and companion assertions for authorization/retry/body mismatch:

```python
def test_manual_retry_returns_same_uuid(round_api):
    from tests.unit.routers.test_round_posting_p1 import sign_in
    client, app, sessions = round_api
    sign_in(app)
    body = {'date': '2026-10-25', 'group': 'B', 'location': 'Example',
            'results': [{'member': f'Player {i}', 'score': q}
                        for i, q in enumerate([3, -3, 0, 0], 1)]}
    # Fixture seeds matching canonical roster names/profile links.
    headers = {'Idempotency-Key': 'manual-fixture-1'}
    a = client.post('/players/me/round', json=body, headers=headers)
    b = client.post('/players/me/round', json=body, headers=headers)
    assert a.status_code == b.status_code == 201
    assert a.json()['game_id'] == b.json()['game_id']
```

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/routers/test_round_identity_writes.py backend/tests/unit/routers/test_round_posting_p1.py -v`; verify red on missing UUID/idempotency.
- [ ] Convert member posting to canonical totals-only game creation with source evidence and retained participant-result references; preserve attestation/status/participant permission rules. Drop/replace `ux_member_round_per_day` only during coordinated cutover after dependent callers migrate; request keys and stable round participants replace its retry purpose, allowing two confirmed distinct rounds in one day. Do not use conflict approval to grant general scoring permissions.
- [ ] Convert scan creation to shared binding/creation and explicit coverage. Totals-only extraction must submit explicit totals, never zeroes on holes 1–17 plus a final-hole balancing value. Full scans retain strict hole validation. Remove positional player-name fallbacks; require explicit slot mapping when uncertain. Attach payloads use stable slot IDs, not display names. Persist attach photo through the existing photo endpoint and report independent photo failure without duplicating the round.
- [ ] Live creation/completion/correction retains its UUID. Completed corrections stage evidence and a reviewable proposed revision rather than silently replacing competing accepted values. Uncontested active-game saves remain live scoring. Require expected server revision for completed edits/backfill, preserve known gross/team/note detail on partial edits, and reject duplicate hole IDs. Keep whole-snapshot `/scores` semantics explicit; a one-hole UI must merge against the current full snapshot/revision before submitting, never discard other holes.
- [ ] Generate one `crypto.randomUUID()` request key per new form submission and retain it on retry/offline queue. Store expected server revision separately from local queue version. Do not auto-upload completed state on page view, failed read, or stale queue reconciliation. A 409 becomes visible review/reload state, not an automatic retry/overwrite; 202 navigates to review state without inventing a UUID. Manual success returns/copies `/game/:uuid`.
- [ ] Add Vitest assertions: totals-only confirmation contains no fabricated per-hole records; ambiguous player mapping blocks save; retry reuses key; stale queue preserves pending evidence. Run `cd frontend && npx vitest run src/components/game/__tests__/ScorecardIdentity.test.jsx` and backend tests. Commit: `git commit -m "feat(rounds): unify manual scan and live identity writes"`.

### Task 6: Deliver one targeted conflict event through both existing channels

**Files:** Create `backend/app/services/round_delivery.py`, `backend/tests/unit/services/test_round_delivery.py`; modify `services/notification_service.py`, `services/email_service.py`, `services/email_scheduler.py`, `routers/notifications.py`, `frontend/src/components/ui/NotificationBell.jsx`; add bell tests in `frontend/src/components/ui/__tests__/NotificationBell.rounds.test.jsx`.

**Consumes:** `RoundIssue` events/`RoundDelivery` rows, `AppConfig.round_identity` reviewer routing. **Produces:** `dispatch_round_deliveries`, `EmailService.send_round_conflict_notification(*, to_email: str, issue_id: str, path: str) -> bool`; notification type `round_conflict`, safe same-origin `data.path`, unique `delivery_key`.

- [ ] Write transaction/dedup tests with mocked provider:

```python
def test_unchanged_conflict_enqueues_two_channels_once(conflicted_round):
    db, issue = conflicted_round
    from app.models_round_identity import RoundDelivery
    rows = db.query(RoundDelivery).filter_by(issue_id=issue.id).all()
    assert sorted(r.channel for r in rows) == ['email', 'in_app']
    assert len({r.dedupe_key for r in rows}) == 2
```

Add a dispatcher crash injection before/after notification flush and provider acceptance. Read notifications from a second transaction, not the mock's return value.

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/services/test_round_delivery.py -v`; expect missing dispatcher/uniqueness behavior to fail.
- [ ] Validate configured active recipient profile and verified account linkage, not admin email lists. Use existing `AppConfig` confirmed routing (recipient ID + confirming actor/time/linkage evidence). No configured reviewer means retained unconfigured intents/health, not dropped events or blanket mail. Add explicit admin-only requeue for confirmed recipient changes; do not silently replay history.
- [ ] Extend `NotificationService.send_notification` with keyword-only `delivery_key: str | None = None` and `commit: bool = True`; preserve old caller default. Dispatcher calls it with a dedicated delivery session and `commit=False`, atomically inserts notification + delivered marker + unique key, and commits once. This removes the spec's existing-helper commit hazard without a parallel notification path.
- [ ] Claim durable deliveries with row lock/lease and bounded exponential backoff. Treat channels independently. Email uses current HTML/text template and provider; current Boolean transports do not prove inbox delivery or idempotency. Before sending mark claimed intent durably; timeout/crash after possible acceptance becomes `uncertain`, requiring provider evidence or explicit operator decision, never blind resend. Definitive pre-send/rejection errors may retry. Add provider idempotency/receipt support only if supported by the configured provider and tested; do not promise universal exactly-once email.
- [ ] Add scheduler drain with fresh dedicated sessions; no daemon-thread-only delivery. Add `round_conflict` to bell visibility/click handling. Apply type filtering server-side before limit/pagination or display all supported backend types so unrelated notifications cannot hide conflicts. Existing recipient scoping and mark-read remain intact. Failed/uncertain health updates must not recursively enqueue conflict events.
- [ ] Test both transports, missing/changed recipient, successful channel not resent, rejected/uncertain provider, source transaction rollback, duplicate workers, safe links and bell rendering/navigation. Run backend module and `cd frontend && npx vitest run src/components/ui/__tests__/NotificationBell.rounds.test.jsx`. Commit: `git commit -m "feat(rounds): deliver targeted conflict alerts without repeat spam"`.

### Task 7: Expose authorized conflict review, alias lookup, and health

**Files:** Create `backend/app/routers/round_reconciliation.py`, `backend/tests/unit/routers/test_round_reconciliation_api.py`; modify `backend/app/main.py`, `routers/games.py`, `routers/admin.py`; extend Task 1 schema file.

**Consumes:** Tasks 3 and 6. **Produces:**

```text
GET  /games/{uuid}/round-summary       public accepted results + safe issue badge
GET  /round-reconciliation/issues      designated reviewer/admin only, paginated
GET  /round-reconciliation/issues/{id} reviewer/admin, full evidence/audit
POST /round-reconciliation/issues/{id}/resolve  ResolutionDecision -> IngestOutcome
GET  /round-reconciliation/aliases?date=...&group=...&location=...
                                      public zero/one/many accessible UUIDs
GET  /round-reconciliation/health      admin/reviewer, redacted status/counts
PUT  /round-reconciliation/recipient   admin only, explicit confirmed profile ID
POST /round-reconciliation/requeue     admin only, explicit outstanding issue IDs
```

`round-summary` response contains `game_id`, `revision`, `played_on`, `raw_date`, `course_name`, `detail_coverage`, `roster_complete`, `score_eligible`, participant slot/name/profile/nullable quarters, actual `hole_history`, safe conflict count and detail capabilities. Accepted data and proposed detail are separately labeled. Never expose raw source payload or recipient addresses to anonymous readers.

- [ ] Write concrete auth/stale tests:

```python
def test_anonymous_cannot_resolve(round_api):
    client, app, sessions = round_api
    response = client.post('/round-reconciliation/issues/issue-1/resolve', json={
        'action': 'keep', 'value': None, 'target_game_id': None, 'reason': 'review',
        'expected_game_revision': 1, 'expected_issue_revision': 1,
        'expected_head_revision': 1})
    assert response.status_code in (401, 403)
```

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/routers/test_round_reconciliation_api.py -v`; verify routes fail before implementation.
- [ ] Implement thin routers that authenticate, call shared services, and own commits/rollbacks. Return 404 for unavailable objects without leaking private candidate evidence; 409 for stale revision; 422 for invalid value/reason; 202 for held identity. Public alias resolution returns only accessible IDs and `resolved`, `ambiguous`, or `missing`, never picks first. `round-summary` is a projection of the existing UUID root/results, not another persisted game representation.
- [ ] Add fixed gate validation: recipient changes require confirmed active linked profile; mode changes require expected epoch and valid manifest verification report; HTTP requests cannot bypass a paused writer fence. No public toggle runs migration or sheet writes. Wire route ordering so static paths are not swallowed by UUID parameters.
- [ ] Test stale superseded head, unauthorized participant resolution, public redaction, old UUID reachability, aliases with two candidates, confirmed recipient rejection and safe health. Commit: `git commit -m "feat(rounds): expose audited reconciliation and canonical round summaries"`.

### Task 8: Count canonical accepted results exactly once everywhere

**Files:** Modify `backend/app/services/unified_data_service.py`, `player_service.py`, `statistics_service.py`, `weekly_highlights.py`, `sheet_integration_service.py`; `backend/app/routers/unified_data.py`, `players.py`, `member_rounds.py`, `spreadsheet_sync.py`, `commissioner.py`, `sheet_integration.py`; `backend/app/database.py`; create `backend/tests/unit/services/test_canonical_round_statistics.py`.

**Consumes:** Canonical results/eligibility/played date and status. **Produces:** Existing read APIs use persisted UUIDs and one season/eligibility definition; explicit coverage counts. `UnifiedRound.score` becomes nullable and detail-aware; its `game_key` is UUID/participant, never name-score hash.

- [ ] Write tests for the exact counting policy:

```python
def test_partial_round_never_enlarges_score_average(canonical_history):
    service = canonical_history  # seeded complete round + incomplete round
    rows = service.get_unified_leaderboard()
    avery = next(r for r in rows if r.member == 'Avery')
    assert avery.rounds == 1
    assert avery.quarters == 8
    assert avery.average == 8
    assert avery.known_participation_count == 2
```

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/services/test_canonical_round_statistics.py -v`; establish red.
- [ ] Replace canonical-mode cache/app union and `_drop_sheet_duplicates` with UUID/result queries. Use whole-game eligibility, known played date and explicit source-season configuration. Return incomplete rounds in history with NULL totals/provisional coverage but exclude from score sums/count/average/best/worst/wins. Distinct participant slots never collapse because names/totals match; profile aggregates use verified profile association only. Saved accepted totals remain during disputes. No `1900-01-01`, current-clock year inference, or score-to-int conversion in canonical reads.
- [ ] Convert member/public history, extreme scores, weekly highlights, admin statistics and Commissioner SQL to canonical eligibility. Replace `legacy_rounds_official` with an explicit canonical read projection at cutover or restrict Commissioner to a canonical view named `canonical_round_results`; update its allowlist/schema documentation and tests. Do not leave a hidden raw-cache statistics authority.
- [ ] Rebuild `PlayerStatistics` deterministically from eligible UUID/participant results, not increments from source imports or repeat writes. Unsupported detailed metrics remain unknown; consumers must render unavailable instead of treating defaults as observations. Retire/restrict old CSV `/sync-wgp-sheet` and service aggregate overwrites in canonical mode; `PlayerService.record_game_result` delegates stable-key upsert/rebuild rather than append/increment. Preserve user-facing profile features and existing pending exclusions.
- [ ] Test each entry point with app→sheet echo, two same-day games, guest name collision, disputed result, held evidence, prior season and unknown year. Account explicitly for changes versus old approximate suppression; don't silently assert parity where old output was wrong. Commit: `git commit -m "refactor(rounds): count accepted UUID results across all statistics"`.

### Task 9: Make the existing UUID page passive, scores-first, and socially complete

**Files:** Modify `frontend/src/pages/SimpleScorekeeperPage.jsx`, `RoundStoryPage.jsx`, `hooks/useGameData.js`, `components/game/CompletedRoundView.jsx`, `components/game/leaderboard/ScorecardLink.jsx`, and `frontend/src/components/game/leaderboard/roundLink.js`; create `components/game/RoundDiscussion.jsx`, `RoundConflictReview.jsx`, `pages/RoundReconciliationPage.jsx`, and `services/roundIdentity.js`; modify `App.jsx`, `Navigation.jsx`, `AdminPage.jsx`, `backend/app/routers/round_stories.py`; tests in `frontend/src/pages/__tests__/UniversalRoundPage.test.jsx`, existing `RoundNavigation.test.jsx`, and `backend/tests/unit/routers/test_round_social_identity.py`.

**Consumes:** Task 7 APIs and Task 8 canonical reads. **Produces:** One `/game/:gameId` page with accepted totals, actual detail, existing photo UI, discussion/reactions and permission-gated conflict section; reviewer inbox `/round-reconciliation`. Existing composite route is a resolver only.

- [ ] Write this UI test with mocked network, existing Auth0 test wrappers, and a spy on `syncManager.queueSync`:

```jsx
it('shows a completed totals-only game without live sync or fabricated holes', async () => {
  renderRound('/game/fixture-round', {detail_coverage: 'totals_only',
    game_status: 'completed', players: [{participant_id: 'p1', name: 'Avery',
      quarters: null}], hole_history: []});
  expect(await screen.findByText('Avery')).toBeVisible();
  expect(screen.getByText('Not recorded')).toBeVisible();
  expect(screen.queryByRole('button', {name: /mark complete/i})).toBeNull();
  expect(queueSync).not.toHaveBeenCalled();
});
```

`renderRound` is a local test helper using `MemoryRouter`, the real page route, and mocked `/round-summary`/state/card endpoints; `queueSync` is the mocked sync-manager method. Add explicit loading/error/ambiguous alias cases rather than silently falling back to cached completed data.

- [ ] Run `cd frontend && npx vitest run src/pages/__tests__/UniversalRoundPage.test.jsx src/pages/__tests__/RoundNavigation.test.jsx`; establish red.
- [ ] Branch on server lifecycle before mounting `SimpleScorekeeper`/live hooks. Extend existing `CompletedRoundView` for totals-only/partial/complete coverage with nullable values and capabilities. Retain photo/extraction comparison components; no course fetch, carry-over logic, recomputed totals, or auto-upload on passive view. Active games continue through existing live editor. A photo does not alter totals; partial holes are labeled and do not imply completion. Use correct accepted revision when entering edits.
- [ ] Move current story discussion into `RoundDiscussion`, loaded by UUID. Backend adds UUID comment/reaction operations on existing records and maintains permission/delete behavior. Aliases resolve legacy endpoints to the same records; ambiguous aliases never accept writes until disambiguated. Preserve IDs, author/time and reaction uniqueness; do not duplicate records onto candidate games. Existing broad comment notification behavior is not expanded or reused for targeted conflict routing.
- [ ] Make `RoundStoryPage` resolve then navigate; ambiguous shows candidate links plus review state, missing shows honest not found. No sheet-only score rendering remains. All new history/scorecard/copied links use UUID regardless of detail availability. Preserve old display-date/course aliases. Reviewer inbox links to same game or unbound issue; conflict section shows accepted/proposed values side by side, provenance, current revision, reason input and audit. Stale 409 prompts reload, not resubmission. No invented game for an unbound issue.
- [ ] Add discoverable reviewer/admin navigation, URL-addressable review tabs if using `AdminPage`, and a confirmed-recipient status form with IDs/status rather than exposed transport secrets. Client visibility is not backend authorization. Test unauthorized actions, different UUID navigation reset, NULL score rendering, both notification links, existing photo controls, comments/reactions and old aliases. Run backend social tests plus frontend modules. Commit: `git commit -m "feat(rounds): converge scores discussion and review on the UUID page"`.

### Task 10: Make outbound sheet jobs UUID-bound and uncertainty-safe

**Files:** Modify `backend/app/services/spreadsheet_sync_service.py`, `email_scheduler.py`, `routers/spreadsheet_sync.py`, `models.py`; create `backend/tests/unit/services/test_round_sheet_delivery.py`.

**Consumes:** `PendingSheetSync` UUID/token/operation/revision fields and source bindings. **Produces:** Token-keyed update/insert with verified receipt, safe leases and app→sheet→app echo.

- [ ] Write a fake connector test where an append commits externally then raises timeout:

```python
def test_accepted_then_timeout_is_not_appended_twice(sheet_job_fixture):
    worker, connector, job = sheet_job_fixture
    connector.accept_then_timeout = True
    worker(job.id)
    worker(job.id)
    assert len(connector.rounds_by_token[job.source_round_token]) == 1
    assert connector.append_calls == 1
```

The fixture executes the real queue processor against an isolated database; fake connector stores source rows by token and exposes read-after-write evidence.

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/services/test_round_sheet_delivery.py -v`; expect old append/update behavior to fail.
- [ ] Require UUID-bound operation/revision when enqueueing; preserve old unbound jobs for manifest review, never guess by date/roster. Claim leased jobs with epoch fence and crash recovery. Update mapped rows for updates after verifying token/participant continuity and expected source version; re-read token after ambiguous write. No automatic network retry that can append again after uncertain acceptance. Missing mapped token is an identity issue, not permission to append. New source writes require Gate B and are disabled in normal tests/dry run.
- [ ] Serialize outbound connector with inbound source lease; preserve raw observed sheet values and audit conflicts rather than overwrite unreviewed source changes. Confirm provider response/readback before marking done. Reimport known outbound evidence binds to same UUID without spurious conflicts. Add tests for missing tokens, changed source, duplicate workers, expired claims, update never append, and unbound historical queue. Commit: `git commit -m "fix(rounds): bind sheet delivery to canonical identity and receipts"`.

### Task 11: Build an explicit migration manifest and guarded cutover tool

**Files:** Create `backend/app/services/round_identity_migration.py`, `backend/scripts/migrate_round_identity.py`, `backend/tests/unit/services/test_round_identity_migration.py`, `docs/guides/universal-game-identity-cutover.md`; modify `backend/app/database.py` and expand migration only for required final constraint/view handling. No boot backfill.

**Consumes:** Tasks 1–10. **Produces:** `build_manifest`, `apply_manifest`, `verify_manifest`; CLI commands below; deterministic fixtures and operational gate report.

- [ ] Write a rerun/rollback test:

```python
def test_manifest_rerun_keeps_uuid_and_social_ids(migration_fixture):
    db, snapshot, original_comment_id = migration_fixture
    from app.services.round_identity_migration import (
        build_manifest, apply_manifest, verify_manifest)
    manifest = build_manifest(db, snapshot)
    first = apply_manifest(db, manifest, expected_checksum=manifest['checksum'])
    second = apply_manifest(db, manifest, expected_checksum=manifest['checksum'])
    assert first['game_ids'] == second['game_ids']
    report = verify_manifest(db, manifest)
    assert report['unaccounted_source_rows'] == 0
    assert original_comment_id in report['preserved_comment_ids']
```

- [ ] Run `backend/venv/bin/python -m pytest backend/tests/unit/services/test_round_identity_migration.py -v`; expect missing manifest functions to fail.
- [ ] Implement deterministic source accounting: source rows/participant tokens, prior IDs, status/season, candidate existing UUIDs, reviewed bindings/new distinct decisions, aliases/comments/reactions, outbound queue, canonical accepted values, held reasons, per-player standings differences and checkpoints. Generated UUIDs are assigned once into the manifest and checksum; regenerating a dry run may propose different IDs but must not mutate/publish them, and applying a manifest never regenerates IDs. No accepted manifest can silently drop an old source row/result/social record. Capture pre-migration counting baseline separately from canonical eligibility; every correction delta requires reason and approval.
- [ ] Implement CLI with `argparse` and explicit commands:

```bash
# Only against a separately approved restored/disposable database, not production.
backend/venv/bin/python backend/scripts/migrate_round_identity.py dry-run --snapshot <approved-local-json> --output <local-manifest-json>
backend/venv/bin/python backend/scripts/migrate_round_identity.py verify --manifest <local-manifest-json>
backend/venv/bin/python backend/scripts/migrate_round_identity.py apply --manifest <local-manifest-json> --expect-checksum <checksum> --ack-paused-writers
```

The placeholders here are operator-supplied artifact paths/checksum, not missing implementation. CLI must refuse `apply` without paused mode + matching writer epoch, complete snapshot and manifest checksum; never print a database URL/secret. `dry-run` opens a read-only transaction and emits no email/source writes. `apply` commits whole-game batches with lock/re-read/checkpoint, preserving original UUIDs, social IDs and explicit ambiguities. Historical conflicts may create pending review intents but dispatch remains fenced until the user approves real notifications/recipient and activation; no historical “new game” broadcasts.

- [ ] Fence every converted writer before final snapshot/apply: all three refreshes, manual/scan/live completed saves, legacy CSV/statistics writers, queue, social association mutations and repair tools. Every converted writer holds a shared lock on the configuration fence row while committing; cutover takes the exclusive lock, drains those transactions, advances epoch/mode, and only then begins apply. Epoch checks alone are insufficient if cutover can race between check and commit. Old binaries that never check the fence must be drained/stopped and their database writer access disabled in the separately authorized operational window; a new application flag cannot fence an already-running incompatible binary. Source snapshot drift invalidates affected manifest decisions; require a new reviewed checksum. Existing canonical live writes during a rehearsal are fixture-only; production final-window writes are paused, not dual-written.
- [ ] Verify aliases, comment/reaction IDs, pending/retired rows, orphan state repairs, duplicate candidate holds, partial totals, season boundaries and all counting callers. Final constraints enforce source and participant uniqueness without deleting offending rows. Turn canonical mode on only with an accepted verification report and separate Gate D authorization. Remove boot/current-reader reliance on `legacy_rounds_official` and refresh explicit canonical view safely.
- [ ] Document forward rollback: pause connector/dispatch, keep issued UUIDs/evidence/audit/new writes, serve last verified compatible revision, prohibit old destructive writer activation, and require separately approved reconciliation before any backup restore. Test rollback after a new game/comment/conflict was committed. Commit: `git commit -m "feat(rounds): add resumable identity migration and cutover verification"`.

### Task 12: Prove PostgreSQL races, end-to-end flow, and retire old authority

**Files:** Create `backend/tests/unit/round_identity_postgres_support.py`, `backend/tests/unit/test_round_identity_postgres.py`; extend `backend/tests/unit/routers/test_round_identity_flow.py`, frontend `UniversalRoundPage.test.jsx` and existing navigation tests; remove obsolete matching/import branches from `round_identity.py`, `unified_data_service.py`, `email_scheduler.py`, `RoundStoryPage.jsx` and migrated callers. Update cutover guide and OpenAPI artifacts through the repository sync script.

**Consumes:** Entire consolidation. **Produces:** Evidence of invariants under real connections and one shared browser flow; no duplicate counting/viewer/persistence path.

- [ ] Extend the existing `score_save_postgres_support.py` pattern in a separate focused helper: `identity_pg` fixture uses `SCORE_SAVE_TEST_DATABASE_URL`, localhost disposable `*_test` database, isolated schema, PostgreSQL 15, independent physical connections and `expire_on_commit=True`. Include all identity/social/notification/config tables. Respect `SCORE_SAVE_REQUIRE_POSTGRES=1` so missing service fails required verification rather than silently skips. Never allow production hosts.
- [ ] Add real concurrent-transaction tests with barriers/time-bounded joins, not sleeps. Test two imports of same token, two scopes creating overlapping candidates, two actors posting same real round, stale source lease, superseded evidence versus resolution, rollback-trigger failure, duplicate channel workers and migration rerun. Assert rows/UUIDs from a new physical connection. Known retries produce one result; ambiguous cross-source identity produces held evidence and no additional counted game.

```python
def test_failed_issue_commit_leaves_no_game_or_alert(identity_pg):
    # Fixture injects a PostgreSQL trigger rejecting the issue insert.
    outcome = identity_pg.ingest_with_rejected_issue()
    assert outcome.failed
    durable = identity_pg.read_from_new_connection()
    assert durable['new_games'] == 0
    assert durable['new_results'] == 0
    assert durable['delivery_intents'] == 0
    assert durable['notifications'] == 0
```

`ingest_with_rejected_issue` and `read_from_new_connection` are test-helper methods introduced in this task and call the real service transaction; the fixture always removes its trigger/schema in teardown.

- [ ] Run from backend: `venv/bin/python -m pytest tests/unit/test_round_identity_postgres.py tests/unit/test_score_save_postgres.py -v`, with the existing disposable PostgreSQL environment explicitly configured. No passing claim if required PostgreSQL tests skip.
- [ ] Add fixture end-to-end test: approved source tokens → totals-only game → independent persistence read → standings/history UUID links → shared page → comment/reaction → photo → partial detail → conflicting full detail → both mocked channel receipts → authorized resolution → same UUID and single standings contribution. Test unknown values and unauthorized resolve. Browser rehearsal uses local app/test transport, never real email or production data.
- [ ] Audit repository references before retiring paths: `rg 'link_saved_cards|_drop_sheet_duplicates|sync-wgp-sheet|LegacyRound|PendingSheetSync|record_game_result' backend/app frontend/src`. Keep provenance/model/alias references; remove old authoritative union, approximate read-time matching, delete/reinsert refresh, append-as-update, duplicate statistics mutation and sheet-only rendering. Tests prove compatibility resolver survives. Do not delete unrelated legacy-profile functionality or user work.
- [ ] Sync API artifacts with `./scripts/sync_openapi.sh` and commit `backend/openapi.json` and `frontend/src/api/schema.d.ts` after inspecting their diffs. Run FULL gates, with real exit status:

```bash
# Run in frontend directory:
npm run typecheck && npx vitest run && npm run build
# Run in backend directory with backend/venv active:
ruff check app/ tests/ && ruff format --check app/ tests/ && python scripts/export_openapi.py --check && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic
```

Also run the targeted PostgreSQL suite with required service and record coverage of every spec scenario. If a baseline failure blocks the full gate, report it and fix only authorized scope; do not push with a subset or claim green. No source-sheet write, recipient confirmation, production cutover or deployment occurs merely because tests pass.
- [ ] Commit: `git commit -m "test(rounds): prove canonical identity and retire legacy authority"` with explicit paths. Before any authorized push invoke Git discipline and inspect the whole branch against current base. Push/PR/cleanup follow Orca lifecycle only when authorized and all required checks pass; this plan does not grant merge/deploy.

## Spec coverage and acceptance checklist

| Spec requirement | Tasks |
| --- | --- |
| One UUID/root/shared scores-first page | 1, 2, 5, 7, 9 |
| Honest unknowns/totals/partial/full detail; live validation | 1, 2, 4, 5, 8, 9 |
| Stable source IDs, years, reorder/corruption, full range | 3, 4, 10, 11 |
| Concurrent imports/cross-source/manual retry | 1, 3, 4, 5, 12 |
| Conflicts/side-by-side/audit/stale heads/re-alert lifecycle | 3, 5, 6, 7, 9, 12 |
| Both channels, recipient confirmation, uncertainty | 6, 7, 9, 12 |
| Existing history URLs/comments/reactions/codes | 1, 3, 5, 7, 9, 11 |
| One counting authority and incomplete denominators | 2, 8, 11, 12 |
| Outbound update/retry/echo and source drift | 4, 10, 11, 12 |
| Backfill/dry run/source accounting/fence/rollback | 1, 4, 8, 10, 11, 12 |
| Retirement, full CI mirror and read-after-write proof | 8, 9, 11, 12 |

## Plan review and handoff

- [ ] Before execution confirm Gate A and read both approved spec and plan.
- [ ] After implementation, require Gate B/C/D evidence before any operational action.
- [ ] Never treat commit/test success as production authorization.

Planning self-review must check every spec section against the table, scan for unfinished steps, verify interface names/nullable score handling, and confirm file references. This plan contains no implementation changes or application test results. Execution remains awaiting the user's choice of subagent-driven task-by-task work (sequential implementation, review between tasks) or inline execution with checkpoints.
