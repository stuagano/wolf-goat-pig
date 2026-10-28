# Universal game identity: offline rehearsal and guarded cutover

## Authorization boundary

Task 11 implements tooling, not permission to run a production migration. This
revision's CLI accepts only explicit SQLite files or loopback PostgreSQL databases
whose names end in `_test`, with no URL query parameters. Use synthetic data or a
separately approved disposable restore. Never pass production credentials. Source
approval, final snapshot approval (Gates B/C), canonical activation (Gate D),
recipient consent, connector writes, and notification dispatch are separate gates.
No step below grants any of them implicitly.

## Before the final window

1. Inventory **all** writers: sheet history/statistics/leaderboard refreshes,
   manual/scan/live completed saves, CSV/statistics repair scripts, social
   association mutations, delivery workers, and administrative SQL tools.
2. Converted writers acquire the reconciliation transaction lock and a shared
   `app_config.round_identity` row lock. Keep that transaction open through the
   actual commit. Do not insert an early commit between fence validation and
   writing. The current reconciliation advisory lock serializes these writers;
   this is deliberately conservative, not concurrent shared-writer throughput.
3. Stop/drain incompatible binaries and scheduled jobs and revoke their database
   write privileges in the separately authorized operational window. A new flag
   cannot fence a binary that never checks it. Include raw SQL and repair tools.
4. Disable connector/dispatch transports operationally. `dispatch_paused` remains
   true after activation; recipient/dispatch approvals are not implied.
5. Use a non-owner runtime database role with no trigger/DDL bypass rights.
   Table owners and superusers can remove append-only triggers. SQLite filesystem
   access likewise lies outside application authorization.

## Rehearsal CLI

Supply `DATABASE_URL` privately in the process environment. Do not print it or
save it in the manifest/report. The CLI redacts exception detail and emits only
status/checksum/mode/epoch. Manifests contain sensitive retained evidence; keep
artifacts private and local, outside public serving paths.

```bash
# From the repository root, against an approved disposable database only.
backend/venv/bin/python backend/scripts/migrate_round_identity.py pause \
  --expect-epoch <current-epoch> --reason '<approved-window-reason>'
backend/venv/bin/python backend/scripts/migrate_round_identity.py dry-run \
  --snapshot <approved-local-json> --output <new-local-manifest-json>
backend/venv/bin/python backend/scripts/migrate_round_identity.py apply \
  --manifest <reviewed-local-manifest-json> --expect-checksum <reviewed-checksum> \
  --ack-paused-writers
backend/venv/bin/python backend/scripts/migrate_round_identity.py verify \
  --manifest <reviewed-local-manifest-json>
```

Pause takes the exclusive configuration lock, waits for converted transactions,
advances the epoch, and clears prior verification. Capture the final complete,
fixed-season snapshot **after** draining writers. Dry-run uses a read-only
transaction, performs no source reads/writes or notifications, and exclusively
creates a new artifact (no overwrite/symlink following).

### Manifest review

Every snapshot round must appear exactly once with unchanged source, draft, raw
payload, observation key and continuity evidence. UUIDs are proposed once in the
manifest; applying never generates replacements. A regenerated dry-run is a new
proposal, not a replacement for an already issued manifest.

Review each game with `bind_existing`, `confirm_distinct`, or `hold`, and each
inventoried row with `preserve`, `attach`, `hold`, or `retire`. Every decision
requires `actor_profile_id` and a nonempty reason. Attach legacy rows only with
explicit participant slots; pending submissions cannot become accepted scores.
For existing scored results lacking slots, provide `result_slots` keyed by the
original result ID. Use `source_participant_tokens` only from reviewed stable
source evidence; duplicate source-global tokens are refused. Never infer merges
from names, dates, roster order, or equal scores. `retire` records an accounting
decision only: it does not delete or silently rewrite the row.

The inventory includes legacy/source/participant projections, containers,
observations/heads/issues/resolutions, aliases, social rows, pending queues,
deliveries and request identities. Preserve pending, retired, ambiguous and
orphan rows. Review `baseline_pre_cutover` separately from
`baseline_canonical_eligibility`; the former uses the existing cached counting
caller. Approve the expected per-player standings in
`approval.expected_standings` with actor/reason. Reseal reviewed artifacts using
`seal_manifest`; checksum agreement is integrity, not an independent approval.

Apply commits one whole source game and its checkpoint atomically. A crash before
checkpoint rolls back that entire game. Rerun the **same** manifest/checksum to
resume. Database drift invalidates the proposal; do not bypass it by editing
checkpoint digests. Rebuild, review deltas, and approve a new checksum. Held
ambiguities remain explicit issues, not silently accepted scores or broadcasts.

## Offline constraints, physical proof and activation

These are explicit offline service operations, not boot backfills. With a clean,
paused, matching-epoch session:

- Run CLI `finalize --manifest <reviewed-json> --expect-checksum <checksum>
  --ack-paused-writers` (or `finalize_constraints(db, manifest)` offline). It
  commits constraints and evidence guard installation only after verification succeeds. Duplicate/null-slot/orphan results fail rather than being deleted.
  It enforces result-slot/source uniqueness and removes the old member/day index.
- Install `install_evidence_guards(db)` and commit. PostgreSQL blocks direct SQL
  UPDATE/DELETE/TRUNCATE on observations/resolutions; SQLite blocks UPDATE/DELETE.
- Refresh `ensure_canonical_round_results_view(engine)` explicitly if needed.
  SQLite refresh is DROP/CREATE, PostgreSQL CREATE OR REPLACE. Boot does not create
  `legacy_rounds_official`; old legacy Commissioner prompts still require that
  compatibility view if serving legacy mode. Canonical Commissioner SQL rejects
  legacy counting tables and uses `canonical_round_results` instead.
- Run CLI `verify --manifest <reviewed-json> --store`. It recomputes accounting,
  requires paused epoch, probes physical guards using surviving rows in both
  evidence tables, and stores the manifest/inventory/epoch/proof server-side.
  Empty evidence tables cannot establish physical proof; use legitimate reviewed
  rehearsal evidence, not a fabricated passing flag.
- Obtain **separate Gate D** authorization in `round_identity_gate_d`, bound to
  `manifest_checksum`, `epoch`, `actor_profile_id`, `reason`, and `approved_at`.
  This revision does not offer an endpoint to mint that approval.
- The authenticated admin activation endpoint accepts canonical mode, current
  `expected_epoch`, and `verification_report.manifest_checksum`. Arbitrary JSON
  `passed` booleans have no authority. Activation rechecks inventory, manifest,
  physical guards and Gate D, then advances epoch. Dispatch stays paused.

Old clients without the required epoch are rejected after activation. Clients
retain queued edits when epochs differ; reload and review rather than replaying
old corrections into a new writer epoch.

## Forward rollback

1. Stop connector/dispatch transports; drain converted writers and call
   `forward_rollback(db, expected_epoch=..., reason=...)`, committing the pause.
2. Preserve issued UUIDs, all observations/resolutions, social IDs, queue evidence,
   accepted revisions and post-migration writes. Do not renumber or delete them.
3. Serve the last verified **compatible** read revision while writes stay paused.
   Never reactivate a destructive legacy writer or a binary lacking the fence.
4. Inventory the failure and reconcile forward under a new reviewed manifest and
   epoch. Any backup restore needs a separate reconciliation/approval that accounts
   for every new game, comment and conflict since the backup. A database restore
   is not the automated rollback path.

Do not proceed to Task 12 or a real operational window until independent review
accepts the Task 11 report and all outstanding requirements are resolved.
