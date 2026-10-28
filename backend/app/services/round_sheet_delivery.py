"""The existing sheet queue's single fenced processor. No blind network retries.

A database lease serializes our connector, not arbitrary external Sheets edits.
Sheets has no atomic content precondition; unexpected/uncertain evidence is held.
"""

from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import read_round_identity_config
from app.utils.time import utc_now

from .round_evidence import accepted_draft, fingerprint, issue_for
from .round_identity import acquire_reconciliation_lock
from .round_sheet_contract import approved_contract
from .round_sheet_values import cell_fingerprint, date_cell
from .round_source_lease import SourceLeaseLostError, fence, source_lease


def enqueue_sheet_sync(
    db,
    *,
    game_id,
    source_scope,
    source_round_token,
    operation_key,
    expected_revision,
    expected_epoch,
    expected_source_version,
    action,
):
    UUID(game_id)
    if not all((source_scope.strip(), source_round_token.strip(), operation_key.strip(), expected_source_version)):
        raise ValueError("UUID/token/operation/source version required")
    if action not in {"insert", "update"}:
        raise ValueError("Explicit insert/update required")
    acquire_reconciliation_lock(db)
    db.query(models.AppConfig).filter_by(name="round_identity").with_for_update().all()
    config = read_round_identity_config(db)
    if config.mode != "canonical" or config.epoch != expected_epoch:
        raise ValueError("Writer epoch changed or canonical delivery unavailable")
    db.query(models.AppConfig).filter_by(name="round_sheet_contracts").with_for_update().all()
    contract = approved_contract(db, source_scope, action)
    if not contract:
        raise ValueError("Gate B contract/write approval required")
    game = db.query(models.GameStateModel).filter_by(game_id=game_id).one_or_none()
    if not game:
        raise ValueError("Accepted game UUID not found")
    draft = accepted_draft(db, game_id)
    record = db.query(models.GameRecord).filter_by(game_id=game_id).one_or_none()
    if (
        not record
        or record.is_retracted
        or game.revision != expected_revision
        or not draft
        or draft.removed_participant_ids
        or not draft.roster_complete
        or not draft.played_on
        or draft.played_on.year != contract.season
        or not draft.players
    ):
        raise ValueError("Current accepted complete participant mapping required")
    payload = draft.model_dump(mode="json")
    source = (
        db.query(models.RoundSource)
        .filter_by(kind="sheet", scope=source_scope, round_token=source_round_token)
        .one_or_none()
    )
    if (action == "update" and (not source or source.game_id != game_id)) or (source and source.game_id != game_id):
        raise ValueError("Reviewed source binding required")
    if action == "update":
        trusted_versions = [
            j.verified_readback.get("source_version")
            for j in db.query(models.PendingSheetSync).filter_by(
                source_scope=source_scope, source_round_token=source_round_token, status="done"
            )
            if j.verified_readback
        ]
        trusted_versions.extend(
            o.raw_payload.get("payload", {}).get("source_version")
            for o in db.query(models.RoundObservation).filter_by(source_id=source.id, continuity_verified=True)
        )
        if (
            expected_source_version not in trusted_versions
            or db.query(models.RoundIssue).filter_by(source_id=source.id, status="open").count()
        ):
            raise ValueError("Reviewed source baseline with no unresolved issues required")
    if source is None:
        source = models.RoundSource(
            kind="sheet",
            scope=source_scope,
            round_token=source_round_token,
            game_id=game_id,
            binding_evidence={"outbound_operation": operation_key},
        )
        db.add(source)
    from .round_sheet_values import participant_tokens

    payload["source_participant_tokens"] = participant_tokens(db, source, draft)
    digest = fingerprint(
        [
            game_id,
            source_scope,
            source_round_token,
            action,
            expected_revision,
            expected_epoch,
            expected_source_version,
            payload,
        ]
    )
    old = db.query(models.PendingSheetSync).filter_by(operation_key=operation_key).one_or_none()
    if old:
        if old.payload_fingerprint != digest:
            raise ValueError("Operation key reused with different payload")
        return old
    job = models.PendingSheetSync(
        game_id=game_id,
        source_scope=source_scope,
        source_round_token=source_round_token,
        operation_key=operation_key,
        expected_revision=expected_revision,
        expected_epoch=expected_epoch,
        expected_source_version=expected_source_version,
        payload=payload,
        payload_fingerprint=digest,
        contract_fingerprint=fingerprint(db.get(models.AppConfig, "round_sheet_contracts").value[source_scope]),
        date=payload["played_on"],
        group=draft.group,
        location=draft.course_name,
        player_scores={p.participant_id: p.quarters for p in draft.players},
        dedup_action=action,
        status="pending",
        claim_generation=0,
        created_at=utc_now().isoformat(),
    )
    db.add(job)
    db.flush()
    return job


def _rows(job, contract, snapshot=None):
    width = max(contract.round_column, contract.participant_column, contract.operation_column)
    rows = []
    for player in job.payload["players"]:
        token = job.payload["source_participant_tokens"][player["participant_id"]]
        existing = (
            next(
                (
                    r
                    for r in snapshot.source_rows
                    if len(r) >= max(contract.round_column, contract.participant_column)
                    and r[contract.round_column - 1] == job.source_round_token
                    and r[contract.participant_column - 1] == token
                ),
                None,
            )
            if snapshot
            else None
        )
        row = list(existing) + [""] * (width - len(existing)) if existing else [""] * width
        row[:6] = [
            date_cell(job.payload, contract),
            job.payload["group"] or "",
            player["name"],
            player["quarters"] if player["quarters"] is not None else "",
            job.payload["course_name"] or "",
            job.duration if job.duration is not None else (existing[5] if existing and len(existing) > 5 else ""),
        ]
        for index, value in (
            (contract.round_column, job.source_round_token),
            (contract.participant_column, token),
            (contract.operation_column, job.operation_key),
        ):
            row[index - 1] = value
        rows.append(row)
    return rows


def _claim(engine, job_id):
    owner = str(uuid4())
    now = utc_now().isoformat()
    with Session(engine) as db, db.begin():
        claimed = db.execute(
            update(models.PendingSheetSync)
            .where(
                models.PendingSheetSync.id == job_id,
                or_(
                    models.PendingSheetSync.status == "pending",
                    (models.PendingSheetSync.status == "processing")
                    & or_(
                        models.PendingSheetSync.lease_expires_at <= now,
                        models.PendingSheetSync.lease_expires_at.is_(None),
                    ),
                ),
            )
            .values(
                status="processing",
                lease_owner=owner,
                lease_expires_at=(utc_now() + timedelta(seconds=120)).isoformat(),
            )
        )
        if claimed.rowcount != 1:
            return None
        job = db.get(models.PendingSheetSync, job_id)
        job.claim_generation = (job.claim_generation or 0) + 1
        return owner, job.claim_generation


def _job(db, job_id, claim):
    job = db.query(models.PendingSheetSync).filter_by(id=job_id).populate_existing().with_for_update().one()
    if (job.lease_owner, job.claim_generation) != claim or job.lease_expires_at <= utc_now().isoformat():
        raise SourceLeaseLostError("Job claim lost")
    return job


def _guard(db, job, lease):
    fence(db, lease)
    acquire_reconciliation_lock(db)
    db.query(models.AppConfig).filter_by(name="round_identity").with_for_update().all()
    config = read_round_identity_config(db)
    db.query(models.AppConfig).filter_by(name="round_sheet_contracts").populate_existing().with_for_update().all()
    contract = approved_contract(db, job.source_scope, job.dedup_action)
    game = db.query(models.GameStateModel).filter_by(game_id=job.game_id).one_or_none()
    if (
        not contract
        or config.mode != "canonical"
        or config.epoch != job.expected_epoch
        or config.season != contract.season
    ):
        raise ValueError("Gate B approval or writer epoch changed")
    if not contract or job.contract_fingerprint != fingerprint(
        db.get(models.AppConfig, "round_sheet_contracts").value[job.source_scope]
    ):
        raise ValueError("Approved source contract changed")
    digest = fingerprint(
        [
            job.game_id,
            job.source_scope,
            job.source_round_token,
            job.dedup_action,
            job.expected_revision,
            job.expected_epoch,
            job.expected_source_version,
            job.payload,
        ]
    )
    if digest != job.payload_fingerprint:
        raise ValueError("Queued payload changed")
    source = (
        db.query(models.RoundSource)
        .filter_by(kind="sheet", scope=job.source_scope, round_token=job.source_round_token)
        .one_or_none()
    )
    mapping = job.payload.get("source_participant_tokens")
    if not mapping or not source or (source.binding_evidence or {}).get("participant_tokens") != mapping:
        raise ValueError("Reviewed participant token mapping changed")
    record = db.query(models.GameRecord).filter_by(game_id=job.game_id).one_or_none()
    if not game or game.revision != job.expected_revision or not record or record.is_retracted:
        raise ValueError("Accepted revision changed")
    return contract


def _held(db, job, reason, snapshot=None):
    job.status, job.error = "held", reason
    if not job.source_scope or not job.source_round_token:
        return
    source = (
        db.query(models.RoundSource)
        .filter_by(kind="sheet", scope=job.source_scope, round_token=job.source_round_token)
        .one_or_none()
    )
    if not source:
        return
    raw = {
        "reason": reason,
        "operation": job.operation_key,
        "source_version": snapshot.source_version if snapshot else None,
        "source_rows": snapshot.source_rows if snapshot else [],
        "errors": snapshot.errors if snapshot else [],
        "rounds": [{"token": r.source.round_token, "raw": r.raw_payload} for r in snapshot.rounds] if snapshot else [],
    }
    key = "outbound-held:" + fingerprint(raw)
    observation = db.query(models.RoundObservation).filter_by(source_id=source.id, observation_key=key).one_or_none()
    if observation is None:
        observation = models.RoundObservation(
            source_id=source.id, observation_key=key, raw_payload=raw, parse_status="held", continuity_verified=False
        )
        db.add(observation)
        db.flush()
    issue_for(db, source, observation, "outbound_identity" if "token" in reason else "outbound_conflict", value=raw)


def _read(contract):
    from .spreadsheet_sync_service import fetch_round_snapshot

    return fetch_round_snapshot(contract.scope, season_year=contract.season, contract=contract)


def _other_rows(snapshot, job, contract):
    index = contract.round_column - 1
    return fingerprint(
        sorted(
            [r for r in snapshot.source_rows if len(r) <= index or r[index] != job.source_round_token], key=fingerprint
        )
    )


def _verified(job, snapshot, matches, wanted, contract):
    return bool(
        snapshot.complete
        and not snapshot.errors
        and len(matches) == 1
        and matches[0].continuity_verified
        and cell_fingerprint(matches[0].raw_payload["rows"]) == cell_fingerprint(wanted)
        and job.prewrite
        and job.prewrite.get("source_version") == job.expected_source_version
        and job.prewrite.get("operation") == job.operation_key
        and job.prewrite.get("written_rows") == cell_fingerprint(matches[0].raw_payload["rows"])
        and job.prewrite.get("payload_fingerprint") == job.payload_fingerprint
        and job.prewrite.get("contract_fingerprint") == fingerprint(contract.model_dump())
        and job.prewrite.get("other_rows") == _other_rows(snapshot, job, contract)
    )


def _finish(db, job, snapshot, item, receipt):
    job.provider_receipt = receipt or {
        "kind": "provider_readback_after_uncertainty",
        "operation": job.operation_key,
        "scope": snapshot.scope,
        "source_version": snapshot.source_version,
        "rows": snapshot.source_rows,
    }
    job.verified_readback = {
        "source_version": snapshot.source_version,
        "round_fingerprint": fingerprint(item.raw_payload["rows"]),
        "operation": job.operation_key,
        "payload_fingerprint": job.payload_fingerprint,
    }
    job.status, job.error, job.processed_at = "done", None, utc_now().isoformat()


def process_sheet_job(engine, job_id):
    claim = _claim(engine, job_id)
    if not claim:
        return
    with Session(engine) as db, db.begin():
        job = _job(db, job_id, claim)
        if (
            not all(
                (
                    job.game_id,
                    job.source_scope,
                    job.source_round_token,
                    job.operation_key,
                    job.payload,
                    job.payload_fingerprint,
                    job.expected_source_version,
                )
            )
            or job.expected_epoch is None
        ):
            _held(db, job, "Historical unbound job requires manifest review")
            return
        scope = job.source_scope
    try:
        with source_lease(engine, scope) as lease:
            _deliver(engine, job_id, claim, lease)
    except (SourceLeaseLostError, ValueError):
        # Ownership must be rechecked in the new transaction, never mutate a
        # rolled-back ORM row that could overwrite a newer owner's state.
        with Session(engine) as db, db.begin():
            try:
                job = _job(db, job_id, claim)
            except SourceLeaseLostError:
                return
            _held(db, job, "Approval/epoch/source lease changed; review required")


def _deliver(engine, job_id, claim, lease):
    from . import spreadsheet_sync_service as sheet

    with Session(engine) as db, db.begin():
        job = _job(db, job_id, claim)
        contract = _guard(db, job, lease)
        recovering = bool(job.prewrite)
    snapshot = _read(contract)
    with Session(engine) as db, db.begin():
        job = _job(db, job_id, claim)
        contract = _guard(db, job, lease)
        matches = [r for r in snapshot.rounds if r.source.round_token == job.source_round_token]
        wanted = sorted(_rows(job, contract, snapshot), key=fingerprint)
        exact = _verified(job, snapshot, matches, wanted, contract)
        if not snapshot.complete or snapshot.errors:
            _held(db, job, "Source readback unavailable; no network retry", snapshot)
            return
        source = (
            db.query(models.RoundSource)
            .filter_by(kind="sheet", scope=job.source_scope, round_token=job.source_round_token)
            .one()
        )
        if source.game_id != job.game_id:
            _held(db, job, "Source token binding changed", snapshot)
            return
        if recovering:
            if exact:
                _finish(db, job, snapshot, matches[0], job.provider_receipt)
            else:
                _held(db, job, "Ambiguous acceptance; operator readback review required", snapshot)
            return
        if (job.dedup_action == "update" and len(matches) != 1) or (job.dedup_action == "insert" and matches):
            _held(db, job, "Missing or unexpected mapped token", snapshot)
            return
        if snapshot.source_version != job.expected_source_version:
            _held(db, job, "Unreviewed external source version change", snapshot)
            return
        if matches:
            expected_slots = set(job.payload["source_participant_tokens"].values())
            if (
                not matches[0].continuity_verified
                or {p.participant_id for p in matches[0].draft.players} != expected_slots
            ):
                _held(db, job, "Participant token continuity changed", snapshot)
                return
        # This durable marker precedes every possible external side effect.
        job.prewrite = {
            "source_version": snapshot.source_version,
            "payload_fingerprint": job.payload_fingerprint,
            "operation": job.operation_key,
            "lease_generation": lease[2],
            "contract_fingerprint": fingerprint(contract.model_dump()),
            "approved_contract": db.get(models.AppConfig, "round_sheet_contracts").value[job.source_scope],
            "other_rows": _other_rows(snapshot, job, contract),
            "written_rows": cell_fingerprint(wanted),
        }
    # Recheck under the same source lease. Config/global locks remain held across
    # the one write and readback; no helper commits can release them underneath us.
    with Session(engine) as db, db.begin():
        job = _job(db, job_id, claim)
        contract = _guard(db, job, lease)
        current = _read(contract)
        if current.source_version != snapshot.source_version or not current.complete or current.errors:
            _held(db, job, "Source changed before write", current)
            return
        receipt = None
        try:
            receipt = sheet.write_identity_round(job, contract, current)
        except (OSError, TimeoutError, ValueError):
            # Acceptance is unknown. Only readback may settle this operation.
            pass
        observed = _read(contract)
        found = [r for r in observed.rounds if r.source.round_token == job.source_round_token]
        fence(db, lease)
        _job(db, job_id, claim)
        if _verified(job, observed, found, wanted, contract):
            _finish(db, job, observed, found[0], receipt)
        else:
            job.provider_receipt = receipt
            _held(db, job, "Ambiguous provider acceptance/readback; no network retry", observed)


def process_pending_sheet_syncs(engine, *, limit=50):
    with Session(engine) as db:
        ids = [
            r.id
            for r in db.query(models.PendingSheetSync)
            .filter(models.PendingSheetSync.status.in_(["pending", "processing"]))
            .order_by(models.PendingSheetSync.id)
            .limit(limit)
        ]
    for job_id in ids:
        process_sheet_job(engine, job_id)
