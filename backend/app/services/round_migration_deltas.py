"""Identity-explicit pre-published contributions and per-identity delta review."""

from .round_evidence import fingerprint

METRICS = ("score", "scored", "participation")
ZERO = {"score": 0.0, "scored": 0, "participation": 0}


def contributions(db, season):
    from .unified_data_service import UnifiedDataService

    result = []
    for ordinal, row in enumerate(UnifiedDataService(db=db).get_legacy_rounds(use_sheet_cache=True)):
        if not row.date_sortable or not row.date_sortable.startswith(f"{season}-"):
            continue
        facts = {
            "member": row.member,
            "date": row.date_sortable,
            "source": row.source,
            "game_id": row.game_id,
            "game_key": row.game_key,
            "score": row.score,
        }
        result.append(
            {
                "key": fingerprint([ordinal, facts]),
                "facts": facts,
                "values": {
                    "score": row.score if row.score is not None else 0.0,
                    "scored": int(row.score is not None),
                    "participation": 1,
                },
            }
        )
    return result


def delta_ledger(manifest, new):
    """Recompute, never accept arbitrary old totals or name/profile inference."""
    mapping = manifest.get("identity_mapping", {})
    old = {}
    contributions_ = manifest["baseline_contributions"]
    if set(mapping) != {c["key"] for c in contributions_}:
        raise ValueError("Every published contribution requires explicit identity mapping")
    for contribution in contributions_:
        decision = mapping[contribution["key"]]
        identity = decision.get("identity", "")
        if (
            not (identity.startswith("profile:") or identity.startswith("guest:"))
            or not identity.split(":", 1)[1]
            or not decision.get("actor_profile_id")
            or not str(decision.get("reason", "")).strip()
        ):
            raise ValueError("Reviewed profile/guest identity mapping required; names are not identity")
        item = old.setdefault(identity, dict(ZERO))
        for metric in METRICS:
            item[metric] += contribution["values"][metric]
    return {
        identity: {
            "old": old.get(identity, dict(ZERO)),
            "new": new.get(identity, dict(ZERO)),
            "delta": {m: new.get(identity, ZERO)[m] - old.get(identity, ZERO)[m] for m in METRICS},
        }
        for identity in sorted(set(old) | set(new))
    }


def validate_deltas(manifest, new):
    expected = delta_ledger(manifest, new)
    approvals = (manifest.get("approval") or {}).get("deltas", {})
    if set(approvals) != set(expected):
        raise ValueError("Exact per-identity standings delta ledger required")
    for identity, computed in expected.items():
        entry = approvals[identity]
        if any(entry.get(k) != computed[k] for k in ("old", "new", "delta")):
            raise ValueError("Standings delta ledger differs from recomputation")
        if any(computed["delta"].values()) and not (
            entry.get("actor_profile_id") and str(entry.get("reason", "")).strip()
        ):
            raise ValueError("Every nonzero standings correction requires individual reason and actor approval")
    return expected
