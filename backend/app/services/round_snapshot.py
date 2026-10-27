"""Complete Sheets read and honest parsing. G/H is a fixture-only proposal.

No production token layout is approved. Changed evidence must be reviewed; even
unique tokens cannot prove that an A:F-only sort preserved their association.
"""

from dataclasses import dataclass, field
from datetime import datetime

from app.schemas.round_identity import RoundDraft, RoundParticipant, SourceRef

from .round_evidence import fingerprint


@dataclass
class SheetRound:
    source: SourceRef
    draft: RoundDraft
    raw_payload: dict
    observation_key: str
    continuity_verified: bool


@dataclass
class SheetSnapshot:
    scope: str
    fingerprint: str
    complete: bool
    source_version: str | None
    rounds: list[SheetRound] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    season_year: int | None = None


def _date(raw, year):
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        if year is None:
            # Validate month/day without consulting the current clock.
            datetime.strptime(f"{raw}-2000", "%d-%b-%Y")
            return None
        return datetime.strptime(f"{raw}-{year}", "%d-%b-%Y").date()


def fetch_round_snapshot(scope: str, *, season_year: int | None) -> SheetSnapshot:
    from . import spreadsheet_sync_service as connector

    failed = SheetSnapshot(scope, "", False, None, season_year=season_year)
    try:
        workbook, tab, season = scope.rsplit(":", 2)
        if season != (str(season_year) if season_year is not None else "unknown"):
            raise ValueError("Source season mismatch")
        metadata = connector._sheets_metadata_get(workbook)
        properties = next(s["properties"] for s in metadata["sheets"] if str(s["properties"]["sheetId"]) == tab)
        grid = properties["gridProperties"]
        rows, columns = int(grid["rowCount"]), int(grid["columnCount"])
        if rows < 2 or columns < 6:
            raise ValueError("Source dimensions unavailable")
        fixture = workbook == "fixture" and metadata.get("fixture_token_contract") is True
        end = "H" if fixture and columns >= 8 else "F"
        title = properties["title"].replace("'", "''")
        requested = f"'{title}'!A2:{end}{rows}"
        data = connector._sheets_api_get(workbook, requested)
        if not data or data.get("range") != requested or data.get("majorDimension") != "ROWS":
            raise ValueError("Incomplete source range")
        values = data.get("values")
        if (
            not isinstance(values, list)
            or len(values) > rows - 1
            or any(len(r) > (8 if end == "H" else 6) for r in values)
        ):
            raise ValueError("Invalid source coverage")
        # Sheets omits trailing empty rows. An exact bounded response range plus
        # verified grid dimensions accounts for those, not a magic row ceiling.
        digest = fingerprint([scope, properties, sorted(values, key=lambda r: fingerprint(r))])
        snapshot = SheetSnapshot(scope, digest, True, digest, season_year=season_year)
        if not any(any(v not in (None, "") for v in r) for r in values):
            snapshot.errors.append("empty_source")
            return snapshot
        groups = {}
        for row in values:
            if not any(v not in (None, "") for v in row):
                continue
            token = str(row[6]).strip() if fixture and len(row) > 6 and row[6] else ""
            # Unapproved/absent tokens identify quarantine evidence only, never a
            # UUID or an automatically accepted association.
            token = token or f"unbound:{fingerprint([row[:2], row[4:5]])}"
            groups.setdefault(token, []).append(row)
        seen = set()
        for token, group in sorted(groups.items()):
            group = sorted(group, key=fingerprint)
            errors, players = [], []
            raw = group[0][0] if group[0] else None
            course = group[0][4] if len(group[0]) > 4 else None
            letter = group[0][1] if len(group[0]) > 1 else None
            try:
                played_on = _date(raw, season_year)
            except (ValueError, TypeError):
                played_on = None
                errors.append("invalid_date")
            for index, row in enumerate(group):
                if (row[:2], row[4:5]) != (group[0][:2], group[0][4:5]):
                    errors.append("incompatible_round_token")
                slot = str(row[7]).strip() if fixture and len(row) > 7 and row[7] else ""
                if not slot or "." in slot:
                    errors.append("missing_participant_token")
                    slot = f"unbound-{index}"
                if fixture and slot in seen:
                    errors.append("duplicate_participant_token")
                if fixture:
                    seen.add(slot)
                name = row[2] if len(row) > 2 else None
                total = row[3] if len(row) > 3 and row[3] != "" else None
                try:
                    player = RoundParticipant(participant_id=slot, name=name, quarters=total)
                except ValueError:
                    errors.append("invalid_player_or_total")
                    player = RoundParticipant(participant_id=slot, name=name or "Unparsed source row")
                # Keep duplicate raw rows but avoid manufacturing duplicate slots
                # in the validated proposal; the entire proposal is held.
                if not any(p.participant_id == slot for p in players):
                    players.append(player)
            payload = {
                "rows": sorted(group, key=fingerprint),
                "presence": [
                    [
                        "missing" if i >= len(r) else "null" if r[i] is None else "blank" if r[i] == "" else "value"
                        for i in range(8)
                    ]
                    for r in group
                ],
                "parse_errors": sorted(set(errors)),
                "snapshot_fingerprint": digest,
                "source_version": digest,
            }
            draft = RoundDraft(
                played_on=played_on,
                raw_date=raw or None,
                course_name=course or None,
                group=letter or None,
                players=players,
                roster_complete=True,
            )
            snapshot.rounds.append(
                SheetRound(
                    SourceRef(kind="sheet", scope=scope, round_token=token),
                    draft,
                    payload,
                    fingerprint([token, sorted(group, key=fingerprint)]),
                    fixture and not errors and not token.startswith("unbound:"),
                )
            )
        # A copied slot corrupts all affected rounds, not only the last row.
        counts = {}
        for round_ in snapshot.rounds:
            for player in round_.draft.players:
                counts[player.participant_id] = counts.get(player.participant_id, 0) + 1
        for round_ in snapshot.rounds:
            if fixture and any(counts[p.participant_id] > 1 for p in round_.draft.players):
                round_.raw_payload["parse_errors"].append("duplicate_participant_token")
                round_.continuity_verified = False
        return snapshot
    except (ValueError, TypeError, KeyError, StopIteration, AttributeError):
        failed.errors = ["source_read_or_coverage_failed"]
        return failed
