# Tiled Adaptive Scorecard Scanning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the scorecard scanner reliably read dense multi-man phone cards by guiding it with pre-picked roster players and falling back to a tiled (left/right half) per-region scan when a cheap single call fails.

**Architecture:** `scan_scorecard` gains an optional `expected_players` list. It tries one guided whole-card call; if the result fails zero-sum OR is missing an expected player, it deskews and splits the card into left (holes 1–9) and right (holes 10–18) halves, scans each guided by the player list, and merges by player. The endpoint accepts a `players` form field; the frontend pre-picks players from the roster before capture.

**Tech Stack:** FastAPI + Pillow (backend), Groq Vision (existing), React + Vitest (frontend).

## Global Constraints

- Players per round: 4, 5, or 6.
- Preprocessing/working image is capped at 2048px longest side (`_PREPROCESS_MAX_DIM`); never feed full-res phone pics to the OpenCV preprocessing.
- Tiling adds at most 2 Groq calls (total 3 on a hard card). Single-call stays the happy path.
- `is_circled` ⇒ negative; per-hole deltas must sum to zero across players (`_validate_zero_sum`).
- Each tile/step degrades gracefully — a failed tile or non-image bytes must never raise out of `scan_scorecard`; fall back to the single-call result.
- Pre-push gate: `frontend: npm run typecheck && npx vitest run && npm run build`; `backend: venv/bin/python -m ruff check app/ tests/ && venv/bin/python -m ruff format --check app/ tests/ && venv/bin/python -m pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic`.

---

## File Structure

**Backend**
- Modify `backend/app/services/scorecard_scan_service.py` — guided prompt, expected-player check, `_split_horizontal_halves`, `_merge_tile_results`, adaptive orchestration in `scan_scorecard`, `method` in result.
- Modify `backend/app/routers/scorecard.py` — optional `players` form field → `expected_players`.
- Modify `backend/tests/unit/services/test_scorecard_scan_service.py` — unit tests for the new helpers + adaptive flow.
- Modify `backend/tests/live/test_scorecard_accuracy_live.py` — pass known players, assert tiled improvement.

**Frontend**
- Modify `frontend/src/pages/ScorecardScanPage.jsx` — pre-pick players step (new-round mode).
- Modify `frontend/src/components/game/ScorecardPhoto.jsx` — send `players` to `/scorecard/scan`; accept `pickedPlayers`.
- Modify `frontend/src/components/game/ScorecardReview.jsx` — when players are known, render fixed rows (no mapping dropdowns).
- Create `frontend/src/components/game/__tests__/ScorecardPhoto.players.test.jsx`.

---

## Task 1: Guided prompt + expected-player completeness check

**Files:**
- Modify: `backend/app/services/scorecard_scan_service.py`
- Test: `backend/tests/unit/services/test_scorecard_scan_service.py`

**Interfaces:**
- Produces:
  - `_expected_players_suffix(expected_players: list[str] | None) -> str` — prompt text naming the exact players, or `""`.
  - `_missing_expected(result: dict, expected_players: list[str] | None) -> list[str]` — expected names not present in `result["players"]` (normalized match); `[]` when none expected.
  - `_call_groq_vision(..., expected_players=None, hole_range=None)` gains two kwargs (used in later tasks); when given, the prompt is prefixed with the suffix and (if `hole_range`) the hole instruction.

- [ ] **Step 1: Write the failing test**

```python
# append to backend/tests/unit/services/test_scorecard_scan_service.py
class TestGuidedPlayers:
    def test_suffix_names_players(self):
        from app.services.scorecard_scan_service import _expected_players_suffix

        s = _expected_players_suffix(["CK", "SS", "SG"])
        assert "CK" in s and "SS" in s and "SG" in s
        assert "exactly 3" in s
        assert _expected_players_suffix(None) == ""

    def test_missing_expected_normalized(self):
        from app.services.scorecard_scan_service import _missing_expected

        result = {"players": [{"name": "C.K."}, {"name": "ss"}]}
        # CK matches "C.K." normalized; SG is absent
        assert _missing_expected(result, ["CK", "SS", "SG"]) == ["SG"]
        assert _missing_expected(result, None) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_scorecard_scan_service.py::TestGuidedPlayers -v`
Expected: FAIL with ImportError (functions not defined).

- [ ] **Step 3: Implement the helpers**

Add near the top of `scorecard_scan_service.py` (after the existing imports add `import re` if missing):

```python
import re  # if not already imported


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _expected_players_suffix(expected_players: list[str] | None) -> str:
    if not expected_players:
        return ""
    names = ", ".join(expected_players)
    return (
        f"\n\nThe scorers are KNOWN: expect exactly {len(expected_players)} players "
        f"named: {names}. Use these exact names (one row each). Some players may be "
        f"written in a lower band below the Par row — include them. Ignore any "
        f"golf-score rows and handwritten notes; only read the quarter running totals."
    )


def _missing_expected(result: dict, expected_players: list[str] | None) -> list[str]:
    if not expected_players:
        return []
    found = {_norm_name(p.get("name", "")) for p in result.get("players", [])}
    return [n for n in expected_players if _norm_name(n) not in found]
```

Then thread the kwargs into `_call_groq_vision`. Change its signature to:

```python
async def _call_groq_vision(
    image_bytes: bytes,
    content_type: str,
    *,
    strict: bool = False,
    expected_players: list[str] | None = None,
    hole_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
```

Inside, right after `prompt` is built (the `if references: ... else: prompt = EXTRACTION_PROMPT` block) and before `if strict:`, insert:

```python
    prompt += _expected_players_suffix(expected_players)
    if hole_range:
        lo, hi = hole_range
        half = "FRONT nine" if lo == 1 else "BACK nine"
        prompt += (
            f"\n\nThis image is the {half} only. Read running totals for holes "
            f"{lo} through {hi} only; do not invent other holes."
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_scorecard_scan_service.py::TestGuidedPlayers -v`
Expected: PASS

- [ ] **Step 5: Verify existing scan tests still pass (signature change)**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_scorecard_scan_service.py -q`
Expected: PASS (the new kwargs are optional; existing callers unaffected).

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/scorecard_scan_service.py backend/tests/unit/services/test_scorecard_scan_service.py
git commit -m "feat(scorecard): guided prompt + expected-player completeness check"
```

---

## Task 2: Horizontal split helper

**Files:**
- Modify: `backend/app/services/scorecard_scan_service.py`
- Test: `backend/tests/unit/services/test_scorecard_scan_service.py`

**Interfaces:**
- Produces: `_split_horizontal_halves(image_bytes: bytes, content_type: str) -> tuple[tuple[bytes, str], tuple[bytes, str]] | None` — returns `((left_bytes,"image/jpeg"), (right_bytes,"image/jpeg"))` split at width/2, or `None` if the image can't be read (caller falls back).

- [ ] **Step 1: Write the failing test**

```python
class TestSplitHalves:
    @staticmethod
    def _jpeg(w, h):
        from io import BytesIO

        from PIL import Image

        buf = BytesIO()
        Image.new("RGB", (w, h), "white").save(buf, format="JPEG")
        return buf.getvalue()

    def test_splits_into_two_halves(self):
        from io import BytesIO

        from PIL import Image

        from app.services.scorecard_scan_service import _split_horizontal_halves

        out = _split_horizontal_halves(self._jpeg(2000, 1000), "image/jpeg")
        assert out is not None
        (left_b, left_ct), (right_b, right_ct) = out
        lw = Image.open(BytesIO(left_b)).size[0]
        rw = Image.open(BytesIO(right_b)).size[0]
        assert 950 <= lw <= 1050 and 950 <= rw <= 1050  # ~half of 2000
        assert left_ct == "image/jpeg" and right_ct == "image/jpeg"

    def test_returns_none_on_non_image(self):
        from app.services.scorecard_scan_service import _split_horizontal_halves

        assert _split_horizontal_halves(b"nope", "image/jpeg") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_scorecard_scan_service.py::TestSplitHalves -v`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement**

```python
def _split_horizontal_halves(
    image_bytes: bytes, content_type: str
) -> tuple[tuple[bytes, str], tuple[bytes, str]] | None:
    """Split an image at width/2 into (left, right) JPEGs. None if unreadable."""
    try:
        from io import BytesIO

        from PIL import Image

        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        mid = w // 2

        def _enc(box):
            buf = BytesIO()
            img.crop(box).save(buf, format="JPEG", quality=85)
            return buf.getvalue()

        return (_enc((0, 0, mid, h)), "image/jpeg"), (_enc((mid, 0, w, h)), "image/jpeg")
    except Exception:
        return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_scorecard_scan_service.py::TestSplitHalves -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scorecard_scan_service.py backend/tests/unit/services/test_scorecard_scan_service.py
git commit -m "feat(scorecard): horizontal split helper for tiled scanning"
```

---

## Task 3: Merge two tile results by player

**Files:**
- Modify: `backend/app/services/scorecard_scan_service.py`
- Test: `backend/tests/unit/services/test_scorecard_scan_service.py`

**Interfaces:**
- Consumes: `_norm_name` (Task 1).
- Produces: `_merge_tile_results(expected_players: list[str], left_raw: dict, right_raw: dict) -> dict` — returns a RAW extraction `{"players":[{"name","confidence"}], "running_totals":[...]}` with `player_index` remapped to the position of each player in `expected_players`, left contributing holes 1–9 and right holes 10–18. Caller runs `_shape_extraction` on it.

- [ ] **Step 1: Write the failing test**

```python
class TestMergeTiles:
    def test_merges_left_front_right_back_by_name(self):
        from app.services.scorecard_scan_service import _merge_tile_results

        left = {
            "players": [{"name": "SS"}, {"name": "CK"}],  # note: different order than expected
            "running_totals": [
                {"player_index": 0, "hole": 1, "value": 4, "is_circled": False, "confidence": 1.0},
                {"player_index": 1, "hole": 1, "value": 6, "is_circled": False, "confidence": 1.0},
                {"player_index": 0, "hole": 99, "value": 0, "is_circled": False},  # out of range -> dropped
            ],
        }
        right = {
            "players": [{"name": "CK"}, {"name": "SS"}],
            "running_totals": [
                {"player_index": 0, "hole": 10, "value": 130, "is_circled": True, "confidence": 1.0},
                {"player_index": 1, "hole": 10, "value": 70, "is_circled": False, "confidence": 1.0},
            ],
        }
        merged = _merge_tile_results(["CK", "SS"], left, right)
        assert [p["name"] for p in merged["players"]] == ["CK", "SS"]
        # CK is expected index 0
        ck = [r for r in merged["running_totals"] if r["player_index"] == 0]
        assert {(r["hole"], r["value"]) for r in ck} == {(1, 6), (10, 130)}
        ss = [r for r in merged["running_totals"] if r["player_index"] == 1]
        assert {(r["hole"], r["value"]) for r in ss} == {(1, 4), (10, 70)}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_scorecard_scan_service.py::TestMergeTiles -v`
Expected: FAIL with ImportError.

- [ ] **Step 3: Implement**

```python
def _merge_tile_results(expected_players: list[str], left_raw: dict, right_raw: dict) -> dict:
    """Combine left (holes 1-9) and right (holes 10-18) raw extractions into one
    raw extraction keyed by the player's position in expected_players."""
    exp_index = {_norm_name(n): i for i, n in enumerate(expected_players)}
    unified = [{"name": n, "confidence": 1.0} for n in expected_players]
    merged: list[dict] = []
    for raw, lo, hi in ((left_raw, 1, 9), (right_raw, 10, 18)):
        tile_players = raw.get("players", []) if raw else []
        idx_map: dict[int, int] = {}
        for ti, tp in enumerate(tile_players):
            ei = exp_index.get(_norm_name(tp.get("name", "")))
            if ei is None and ti < len(expected_players):
                ei = ti  # positional fallback
            if ei is not None:
                idx_map[ti] = ei
        for rt in (raw.get("running_totals", []) if raw else []):
            if not (lo <= rt.get("hole", 0) <= hi):
                continue
            ei = idx_map.get(rt.get("player_index"))
            if ei is None:
                continue
            merged.append({**rt, "player_index": ei})
    return {"players": unified, "running_totals": merged}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_scorecard_scan_service.py::TestMergeTiles -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scorecard_scan_service.py backend/tests/unit/services/test_scorecard_scan_service.py
git commit -m "feat(scorecard): merge left/right tile results by player"
```

---

## Task 4: Adaptive orchestration in `scan_scorecard`

**Files:**
- Modify: `backend/app/services/scorecard_scan_service.py` (`scan_scorecard`)
- Test: `backend/tests/unit/services/test_scorecard_scan_service.py`

**Interfaces:**
- Consumes: `_call_groq_vision(..., expected_players, hole_range)`, `_split_horizontal_halves`, `_merge_tile_results`, `_missing_expected`, existing `_shape_extraction`, `_validate_zero_sum`, `deskew_to_card`.
- Produces: `scan_scorecard(image_bytes, content_type, expected_players: list[str] | None = None) -> dict` — same result dict plus `result["method"]` ∈ {`"single"`, `"tiled"`}.

**Behavior:** run the existing single-call pipeline guided by `expected_players`. If the single result is valid (zero-sum AND no missing expected players) → return it with `method="single"`. Otherwise deskew the working-size image, split into halves, call each guided (`expected_players`, `hole_range`), merge, shape, validate → return with `method="tiled"`. If splitting/merging can't run, return the single result (graceful).

- [ ] **Step 1: Write the failing test (mock `_call_groq_vision` per call)**

```python
class TestAdaptiveScan:
    def _valid_raw(self, players, holes_per_player):
        # players: list[str]; holes_per_player: dict[name]-> {hole: (value, circled)}
        pls = [{"name": n, "confidence": 1.0} for n in players]
        rts = []
        for i, n in enumerate(players):
            for h, (v, c) in holes_per_player[n].items():
                rts.append({"player_index": i, "hole": h, "value": v, "is_circled": c, "confidence": 1.0})
        return {"players": pls, "running_totals": rts}

    def test_valid_single_call_does_not_tile(self, monkeypatch):
        import app.services.scorecard_scan_service as svc

        # zero-sum balanced 2-player single result for all 18 holes
        single = self._valid_raw(
            ["A", "B"],
            {"A": {h: (2, False) for h in range(1, 19)}, "B": {h: (2, True) for h in range(1, 19)}},
        )
        calls = {"n": 0}

        async def fake_call(image_bytes, ct, *, strict=False, expected_players=None, hole_range=None):
            calls["n"] += 1
            return single

        monkeypatch.setattr(svc, "_call_groq_vision", fake_call)
        result = asyncio.run(svc.scan_scorecard(b"img", "image/jpeg", expected_players=["A", "B"]))
        assert result["method"] == "single"
        assert calls["n"] == 1  # no tiling

    def test_missing_player_triggers_tiling(self, monkeypatch):
        import app.services.scorecard_scan_service as svc

        single = self._valid_raw(  # only 1 of 2 expected players -> missing -> tile
            ["A"], {"A": {h: (0, False) for h in range(1, 19)}}
        )
        left = self._valid_raw(
            ["A", "B"],
            {"A": {h: (2, False) for h in range(1, 10)}, "B": {h: (2, True) for h in range(1, 10)}},
        )
        right = self._valid_raw(
            ["A", "B"],
            {"A": {h: (2, False) for h in range(10, 19)}, "B": {h: (2, True) for h in range(10, 19)}},
        )
        seq = [single, left, right]

        async def fake_call(image_bytes, ct, *, strict=False, expected_players=None, hole_range=None):
            return seq.pop(0)

        monkeypatch.setattr(svc, "_call_groq_vision", fake_call)
        monkeypatch.setattr(svc, "deskew_to_card", lambda b, ct: (b, ct, {}))
        monkeypatch.setattr(
            svc, "_split_horizontal_halves", lambda b, ct: ((b, "image/jpeg"), (b, "image/jpeg"))
        )
        result = asyncio.run(svc.scan_scorecard(b"img", "image/jpeg", expected_players=["A", "B"]))
        assert result["method"] == "tiled"
        assert {p["name"] for p in result["players"]} == {"A", "B"}
        assert result["validation"]["valid"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_scorecard_scan_service.py::TestAdaptiveScan -v`
Expected: FAIL (`scan_scorecard` has no `expected_players` / no `method`).

- [ ] **Step 3: Rewrite `scan_scorecard`**

Replace the body of `scan_scorecard` (keep the preprocessing-cap line from the current code) with:

```python
async def scan_scorecard(
    image_bytes: bytes, content_type: str, expected_players: list[str] | None = None
) -> dict[str, Any]:
    """Single guided Groq call; if it fails zero-sum or is missing an expected
    player, fall back to a tiled (left=holes 1-9 / right=holes 10-18) scan and
    merge by player. Returns the usual shape plus result["method"]."""
    # Cap working size before the (full-res) CV preprocessing — see _PREPROCESS_MAX_DIM.
    image_bytes, content_type = _fit_image_to_budget(
        image_bytes, content_type, max_dim=_PREPROCESS_MAX_DIM, max_b64_chars=10**12
    )
    deskewed_bytes, deskewed_ct, deskew_diag = deskew_to_card(image_bytes, content_type)
    cropped_bytes, cropped_ct, grid_diag = crop_to_grid(deskewed_bytes, deskewed_ct)
    annotated_bytes, annotated_ct, circle_diag = annotate_circles(cropped_bytes, cropped_ct)
    preprocessing_diag = {"deskew": deskew_diag, "grid_crop": grid_diag, "circles": circle_diag}

    def _finalize(raw: dict, method: str) -> dict:
        out = _shape_extraction(raw)
        out["validation"] = _validate_zero_sum(out["per_hole_quarters"])
        out["preprocessing"] = preprocessing_diag
        out["method"] = method
        return out

    # ---- single guided attempt (with one strict retry on bad JSON) ----
    try:
        single_raw = await _call_groq_vision(
            annotated_bytes, annotated_ct, strict=False, expected_players=expected_players
        )
    except json.JSONDecodeError:
        try:
            single_raw = await _call_groq_vision(
                annotated_bytes, annotated_ct, strict=True, expected_players=expected_players
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse vision response: {e}")

    single = _finalize(single_raw, "single")
    if single["validation"]["valid"] and not _missing_expected(single_raw, expected_players):
        return single

    # ---- tiled fallback ----
    halves = _split_horizontal_halves(deskewed_bytes, deskewed_ct)
    if not halves:
        return single  # can't tile — return best single attempt
    (left_b, left_ct), (right_b, right_ct) = halves
    try:
        left_b, left_ct, _ = annotate_circles(left_b, left_ct)
        right_b, right_ct, _ = annotate_circles(right_b, right_ct)
        left_raw = await _call_groq_vision(
            left_b, left_ct, expected_players=expected_players, hole_range=(1, 9)
        )
        right_raw = await _call_groq_vision(
            right_b, right_ct, expected_players=expected_players, hole_range=(10, 18)
        )
    except Exception as e:
        logger.warning("Tiled scan failed (%s); using single-call result", e)
        return single

    merged_raw = _merge_tile_results(expected_players or [], left_raw, right_raw)
    tiled = _finalize(merged_raw, "tiled")
    # Keep whichever attempt is balanced; prefer tiled when both/neither are.
    if tiled["validation"]["valid"] or not single["validation"]["valid"]:
        return tiled
    return single
```

Note: this replaces the old retry-on-zero-sum-only logic with the adaptive single→tiled flow. The strict retry is preserved only for the JSON-parse failure case.

- [ ] **Step 4: Run the new tests + the full scan-service suite**

Run: `cd backend && venv/bin/python -m pytest tests/unit/services/test_scorecard_scan_service.py -v`
Expected: PASS (new adaptive tests + all existing tests). If an existing test asserted the old double-call retry behavior on zero-sum, update it to the new `method`-aware flow (the b"fake" parsing tests are unaffected).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scorecard_scan_service.py backend/tests/unit/services/test_scorecard_scan_service.py
git commit -m "feat(scorecard): adaptive single->tiled scan guided by expected players"
```

---

## Task 5: Endpoint `players` form field

**Files:**
- Modify: `backend/app/routers/scorecard.py`
- Test: `backend/tests/unit/routers/test_scorecard_router.py`

**Interfaces:**
- Consumes: `scan_scorecard(image_bytes, content_type, expected_players)`.
- Produces: `POST /scorecard/scan` accepts optional `players` form field (JSON array string); parsed to `expected_players` and passed through.

- [ ] **Step 1: Write the failing test**

```python
# in backend/tests/unit/routers/test_scorecard_router.py
def test_scan_passes_players_to_service(monkeypatch):
    import app.routers.scorecard as router_mod
    from fastapi.testclient import TestClient
    from app.main import app

    captured = {}

    async def fake_scan(image_bytes, content_type, expected_players=None):
        captured["players"] = expected_players
        return {"players": [], "running_totals": [], "per_hole_quarters": [], "validation": {"valid": True}}

    monkeypatch.setattr(router_mod, "scan_scorecard", fake_scan, raising=False)
    client = TestClient(app)
    resp = client.post(
        "/scorecard/scan",
        files={"file": ("c.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 64, "image/png")},
        data={"players": '["CK","SS","SG"]'},
    )
    assert resp.status_code == 200, resp.text
    assert captured["players"] == ["CK", "SS", "SG"]
```

> If `scan_scorecard` is imported inside the handler (`from ..services... import scan_scorecard`), patch it where the handler looks it up. The current handler does `from ..services.scorecard_scan_service import scan_scorecard` inside the function — so patch `app.services.scorecard_scan_service.scan_scorecard` instead of `router_mod`. Use that target in `monkeypatch.setattr`.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_scorecard_router.py::test_scan_passes_players_to_service -v`
Expected: FAIL (players not parsed/passed).

- [ ] **Step 3: Implement**

In `backend/app/routers/scorecard.py`, change the handler signature and pass-through:

```python
import json as _json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile


@router.post("/scan")
async def scan_scorecard_photo(
    file: UploadFile = File(...),
    players: str | None = Form(None),
) -> dict[str, Any]:
    ...
    expected_players = None
    if players:
        try:
            parsed = _json.loads(players)
            if isinstance(parsed, list) and parsed:
                expected_players = [str(p) for p in parsed]
        except (ValueError, TypeError):
            expected_players = None
    ...
    result = await scan_scorecard(image_bytes, content_type, expected_players=expected_players)
    return result
```

Keep the existing 20MB guard and the (now comment-only) no-downscale note. Pass `expected_players` into the `scan_scorecard` call (replace the existing `result = await scan_scorecard(image_bytes, content_type)`).

- [ ] **Step 4: Run test + router suite**

Run: `cd backend && venv/bin/python -m pytest tests/unit/routers/test_scorecard_router.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/scorecard.py backend/tests/unit/routers/test_scorecard_router.py
git commit -m "feat(scorecard): accept optional players form field on /scorecard/scan"
```

---

## Task 6: Frontend — pre-pick players + send to scan + known-player review

**Files:**
- Modify: `frontend/src/pages/ScorecardScanPage.jsx`
- Modify: `frontend/src/components/game/ScorecardPhoto.jsx`
- Modify: `frontend/src/components/game/ScorecardReview.jsx`
- Test: `frontend/src/components/game/__tests__/ScorecardPhoto.players.test.jsx`

**Interfaces:**
- `ScorecardPhoto` new prop `pickedPlayers: string[]` (names). When non-empty: sent as `players` in the scan form data, and passed to `ScorecardReview` so it renders fixed rows (no mapping).
- `ScorecardScanPage` new-round mode renders a roster multiselect before `ScorecardPhoto`; chosen names become `pickedPlayers`.

- [ ] **Step 1: Write the failing test (ScorecardPhoto sends players)**

```jsx
// frontend/src/components/game/__tests__/ScorecardPhoto.players.test.jsx
import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ScorecardPhoto from '../ScorecardPhoto';

vi.mock('../ScorecardCapture', () => ({
  default: ({ onCapture }) => <button onClick={() => onCapture(new File(['x'], 'c.jpg', { type: 'image/jpeg' }))}>capture</button>,
}));
vi.mock('../ScorecardReview', () => ({ default: () => <div data-testid="review" /> }));
vi.mock('../../../utils/scorecardImage', () => ({ preprocessScorecardImage: async (f) => f }));

beforeEach(() => {
  global.fetch = vi.fn(async () => ({
    ok: true,
    json: async () => ({ players: [], running_totals: [], per_hole_quarters: [], method: 'single' }),
  }));
});

test('new-round scan posts the picked players as a form field', async () => {
  render(
    <ScorecardPhoto mode="new-round" pickedPlayers={['CK', 'SS', 'SG']} rosterNames={[]} players={[]} onSaved={() => {}} onCancel={() => {}} />,
  );
  screen.getByText('capture').click();
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  const body = global.fetch.mock.calls[0][1].body; // FormData
  expect(body.get('players')).toBe('["CK","SS","SG"]');
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/game/__tests__/ScorecardPhoto.players.test.jsx`
Expected: FAIL (no `players` field on the form data).

- [ ] **Step 3: Implement ScorecardPhoto**

In `ScorecardPhoto.jsx`, accept `pickedPlayers = []`, and in `handleCapture` after building `formData`:

```jsx
const ScorecardPhoto = ({ gameId, players, onSaved, onCancel, mode = 'attach', rosterNames = [], pickedPlayers = [], initialStage, initialExtraction }) => {
  ...
  const formData = new FormData();
  formData.append('file', prepped);
  if (pickedPlayers.length > 0) {
    formData.append('players', JSON.stringify(pickedPlayers));
  }
  ...
```

And pass `pickedPlayers` to `ScorecardReview`:

```jsx
<ScorecardReview extraction={extraction} players={players} mode={mode}
  rosterNames={rosterNames} pickedPlayers={pickedPlayers}
  onConfirm={handleConfirm} onCancel={onCancel} />
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/game/__tests__/ScorecardPhoto.players.test.jsx`
Expected: PASS

- [ ] **Step 5: ScorecardReview — fixed rows when players known**

In `ScorecardReview.jsx`, accept `pickedPlayers = []`. When `pickedPlayers.length > 0` (new-round with known players), the per-player rows use `pickedPlayers[pi]` as the name and render the name as plain text (no `<select>`); `handleConfirm`'s new-round branch sends `{ name: pickedPlayers[pi], player_profile_id: null }` (no `unlinked`, since these are real roster picks). Keep the existing mapping-dropdown path only when `pickedPlayers` is empty. Initialize `mapping` to `pickedPlayers` when present.

```jsx
const knownPlayers = pickedPlayers.length > 0;
// in the players.map row: render `{knownPlayers ? (pickedPlayers[pi] ?? ep.name) : <select .../>}`
// in handleConfirm new-round branch:
//   name: knownPlayers ? (pickedPlayers[pi] ?? ep.name) : (mapping[pi] === '__unlinked__' ? ep.name : mapping[pi])
```

- [ ] **Step 6: ScorecardScanPage — pre-pick step**

In `ScorecardScanPage.jsx` new-round mode (`mode === 'new-round'`), before rendering `<ScorecardPhoto>`, gate on a `pickedPlayers` state: if empty, render a roster multiselect (checkboxes over `rosterNames`, enforce 4–6 selected) with a "Continue" button that sets `pickedPlayers`; once set, render `<ScorecardPhoto mode="new-round" pickedPlayers={pickedPlayers} rosterNames={rosterNames} .../>`. Add `const [pickedPlayers, setPickedPlayers] = useState([]);` and reset it in `onCancel`.

- [ ] **Step 7: Frontend gate**

Run: `cd frontend && npm run typecheck && npx vitest run && npm run build`
Expected: all pass (existing ScorecardReview/ScorecardScanPage tests still green; new test passes).

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/ScorecardScanPage.jsx frontend/src/components/game/ScorecardPhoto.jsx frontend/src/components/game/ScorecardReview.jsx frontend/src/components/game/__tests__/ScorecardPhoto.players.test.jsx
git commit -m "feat(scorecard): pre-pick roster players, send to scan, fixed-row review"
```

---

## Task 7: Live accuracy eval with known players + full gate

**Files:**
- Modify: `backend/tests/live/test_scorecard_accuracy_live.py`

**Interfaces:**
- Consumes: `scan_scorecard(image_bytes, content_type, expected_players)`.

- [ ] **Step 1: Update the eval to pass known players and assert the tiled win**

Change the scan call to pass the 5 known players and assert all are found + accuracy beats the single-call baseline:

```python
    expected = [p["name"] for p in ground_truth["players"]]  # CK, SS, KG, BH, SG
    result = asyncio.run(scan_scorecard(image_bytes, "image/jpeg", expected_players=expected))
    # all five players must now be found (the single-call path missed SG)
    found = {_norm(p.get("name", "")) for p in result.get("players", [])}
    assert all(_norm(n) in found for n in expected), f"missing players; method={result.get('method')}"
```

Keep the existing per-cell scoring + printed diff. Raise `_ACCURACY_FLOOR` from `0.5` to `0.7` (tiling should clear it; adjust down only with a comment if real numbers say otherwise).

- [ ] **Step 2: Verify it still skips without a key**

Run: `cd backend && venv/bin/python -m pytest tests/live/test_scorecard_accuracy_live.py -m live -v`
Expected: SKIPPED (missing GROQ_API_KEY).

- [ ] **Step 3: Full backend + frontend gate**

Run:
```
cd backend && venv/bin/python -m ruff check app/ tests/ && venv/bin/python -m ruff format --check app/ tests/ && venv/bin/python -m pytest tests/ --ignore=tests/manual --ignore=tests/_diagnostic -q
cd ../frontend && npm run typecheck && npx vitest run && npm run build
```
Expected: green except the documented Mac-only `tests/infra/startup_test.py::test_server` SOCKS failure.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/live/test_scorecard_accuracy_live.py
git commit -m "test(scorecard): live eval passes known players, asserts all found + higher floor"
```

- [ ] **Step 5: Real-world validation (manual, after deploy)**

With `GROQ_API_KEY` set, run the eval against the 5-man fixture and confirm `method == "tiled"`, all 5 players found, and accuracy ≫ the 16% single-call baseline:
`cd backend && GROQ_API_KEY=<key> venv/bin/python -m pytest tests/live/test_scorecard_accuracy_live.py -m live -s`

---

## Self-Review

- **Spec coverage:** adaptive trigger (T4) ✓; pre-pick players (T6) ✓; Approach A tiling — deskew→split→guided halves→merge (T2/T3/T4) ✓; `players` form field (T5) ✓; review drops mapping when known (T6) ✓; width/2 split (T2) ✓; `method` observability (T4) ✓; graceful degradation (T2 None, T4 try/except → single) ✓; live eval measures vs 16% (T7) ✓.
- **Type consistency:** `_norm_name` (T1) reused in T3; `_call_groq_vision(..., expected_players, hole_range)` defined T1, called T4; `_split_horizontal_halves -> ((bytes,str),(bytes,str))|None` (T2) consumed T4; `_merge_tile_results(list, dict, dict) -> raw dict` (T3) consumed T4 then `_shape_extraction`; `scan_scorecard(..., expected_players)` (T4) consumed by router (T5) and eval (T7); `pickedPlayers` prop threaded ScorecardScanPage→ScorecardPhoto→ScorecardReview (T6).
- **Placeholders:** none — every code step has concrete code; the one prose-only step (T6 Step 6) describes exact state + gating in a known file.
- **Risk noted:** T5 patch target — patch `scan_scorecard` where the handler imports it (inside the function), called out in the test note. T1 — confirm `import re`/`json` already present before re-adding.
