# Request-Shape Validation → Pydantic Models — Design

**Date:** 2026-06-15
**Status:** Approved (design)
**Scope:** Backend (`backend/app/routers/`)

## Goal

Move hand-rolled *request-shape* validation out of route handlers and onto the
Pydantic request models that FastAPI already parses, so malformed requests are
rejected by the framework (422) before handler logic runs. Business-state
validation (checks that need the loaded game/DB object) stays in the handlers
where it belongs.

## Background

`backend/app/routers/` contains 43 `raise HTTPException(status_code=400, ...)`
calls. They are not homogeneous. Two kinds:

- **Request-shape** — "is this request well-formed?" (blank name, missing field,
  out-of-range number, required field absent). These belong on the request model.
- **Business-state** — "is this valid *given current game/DB state*?" (game
  already started, game full, tee order not set, player id not in the DB roster).
  These need data the model can't see and stay in the handler.

This spec migrates **only the request-shape subset (~13 checks across 11
endpoints).**

### Why the 400→422 status change is safe

Moving a check to Pydantic flips its rejection status from 400 to 422. Verified
this is invisible to the frontend:

- `frontend/src/hooks/useFetchAsync.jsx:149`, `services/syncManager.jsx`,
  `services/offlineStorage.jsx` all branch on `status >= 400 && status < 500` —
  they do not distinguish 400 from 422.
- The frontend reads `.detail` from the error body. PR #268's
  `RequestValidationError` handler (`backend/app/main.py`) returns
  `{"error": "Validation error", "detail": "<summary>", "fields": [...]}` for
  422 — so `.detail` is populated.
- `frontend/src/utils/__tests__/api.test.js:196` already asserts a 422 path.

## In Scope — the 15 checks

### Group A — model already exists, just add/fix the constraint

| Endpoint | File:line | Current check | Change |
|---|---|---|---|
| `create_custom_game` | `games_players.py:170` | `len(body.players) not in (4,5,6)` | **Delete.** `CreateCustomGameRequest.players` already has `Field(min_length=4, max_length=6)` → the handler check is unreachable dead code. |
| `update_player_name` | `games_players.py:482` | `if not name_update.name.strip()` | Add `field_validator` to `UpdatePlayerNameRequest.name` that strips and rejects blank; handler uses the already-stripped value. `min_length=2` stays but does not catch whitespace-only. |
| `signup_for_tee_sheet` | `tee_sheet.py:134` | `if not request.name` | Add `field_validator` to `SignupRequest.name` (strip + non-blank). |

### Group B — raw `dict` body, introduce a typed model (signature change)

| Endpoint | File:line | New model | Fields / constraints |
|---|---|---|---|
| `update_player_handicap` | `games_players.py:586` | `UpdateHandicapRequest` | `handicap: float = Field(ge=0, le=54)` — covers "not provided" (missing→422), "invalid value" (non-numeric→422), and range. |
| `set_tee_order` | `games.py:399` | `SetTeeOrderRequest` | `player_order: list[str] = Field(min_length=1)`. Lines 420 (count must match DB) and 428 (id in DB roster) **stay in handler** — business-state. |
| `send_test_email` | `email_routes.py:20` | `TestEmailRequest` | `to_email: EmailStr` (or `str` min_length=1 to preserve current behavior — see Decisions). |
| `sync_wgp_sheet_data` | `sheet_integration.py:224` | `CsvUrlRequest` | `csv_url: str = Field(min_length=1)`. |
| `fetch_google_sheet` | `sheet_integration.py:567` | `CsvUrlRequest` (reuse) | same. |
| `compare_sheet_to_db_data` | `sheet_integration.py:620` | `CompareSheetRequest` | `sheet_data: list[dict] = Field(min_length=1)`. |
| `test_oauth2_email` | `admin_oauth.py:250` | `TestEmailRequest` (reuse) | `test_email`/`to_email` required. |
| `test_admin_email` | `admin.py:86` | `AdminTestEmailRequest` | `test_email: str = Field(min_length=1)`, `config: dict = {}`. |

## Out of Scope — stays in the handler

- All business-state 400s: `games.py` 227/253/428/472/476/486/757, the
  count-mismatch in `set_tee_order` (420), `games_players.py:622`.
- Parse / file / external-error 400s: `scorecard.py` 29/33 (upload content-type
  and size — not body fields), `admin.py` 169/193 (JSON file upload + parse),
  `sheet_integration.py` 268/296/560/588/613 (validate *fetched* sheet data and
  network failures, not the request), `signups.py:93` (query-string date parse),
  `legacy_scoring.py:78` (domain-layer error passthrough).
- The 3 other `email_routes.py` endpoints (`send_signup_confirmation`,
  `send_daily_reminder`, `send_weekly_summary`) — they read dict fields **without
  a current 400 check**. Modeling them would *add* new 422s (behavior change).
  YAGNI: leave them untouched.
- Both `legacy_scoring.py` endpoints (`start_simplified_game:36`,
  `score_hole_simplified:72`) — `deprecated=True`, in-memory-only, and their
  presence checks are tangled with state lookup (`game_id not in
  simplified_games`). Not worth touching dead code.

## Architecture / Pattern

- New request models live **next to their router** as module-level
  `BaseModel` subclasses (matches existing `UpdatePlayerNameRequest`,
  `SignupRequest` patterns). No central `schemas/` file — these are
  per-endpoint request shapes.
- One shared non-blank-string validator helper, since the strip+non-blank
  pattern recurs (≥3×). Define once and reference it:

  ```python
  # app/routers/_validators.py
  def non_blank(v: str) -> str:
      v = v.strip()
      if not v:
          raise ValueError("must not be blank")
      return v
  ```

  Used via `field_validator("name")(non_blank)` or
  `Annotated[str, AfterValidator(non_blank)]`. (Plain function so it's testable
  and DRY without a class hierarchy.)
- Handlers drop the moved check and consume the validated field directly. For
  Group B, the `dict` parameter becomes the typed model; downstream
  `request.get("x")` accesses become attribute accesses.

## Error handling

- Missing/invalid body fields → FastAPI raises `RequestValidationError` → the
  existing `main.py` handler returns the normalized 422 envelope. No per-handler
  code needed.
- `ValueError` raised inside a `field_validator` is wrapped by Pydantic into the
  same 422 path. The validator's message ("must not be blank") appears in the
  `fields[].message` of the envelope.

## Testing

- For each migrated endpoint: a test asserting the bad-shape request now returns
  **422** with `.detail` populated (not 400). Where a test currently asserts 400
  for one of these, update it to 422.
- Model-level unit tests for the shared `non_blank` validator and for
  `UpdateHandicapRequest` range bounds (0, 54 inclusive; -1, 55, "abc", missing
  all 422).
- Business-state tests (game-already-started etc.) must **remain 400** — guard
  against accidental over-migration.
- Full gate before push: `ruff check app/ tests/ && ruff format --check app/ tests/ && pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic`.

## Decisions

- **`EmailStr` vs `str`:** use `str = Field(min_length=1)` for email fields, not
  `EmailStr`. The current checks only test presence (`if not test_email`), not
  format. Using `EmailStr` would add format validation = behavior change + a
  `email-validator` dependency. Preserve existing behavior; presence only.
- **No central schema module.** Per-router models match the codebase's existing
  convention and keep request shapes next to the endpoints that own them.
- **`set_tee_order` partial migration is intentional** — only the
  `player_order` presence check moves; the two DB-dependent checks stay.
