# Round card photos — design

**Date:** 2026-10-14 · **Status:** approved in conversation, pending spec review

## Goal

Every round can have its paper scorecard photo attached. People come into the app to look at
the cards, fix the numbers if the card disagrees, and each corrected round becomes scanner
ground truth. The rounds themselves *are* the ground truth: no export step, no separate
labeling tool.

## Decisions (from the user)

- **Any round** may carry a card photo, optionally (not required at round end).
- **The round + its edit screen are the ground truth.** No export pipeline.
- **Who may add a photo or edit a round's numbers:** players in that round, plus admins.

## What already exists (don't rebuild)

| Piece | Where |
|---|---|
| Photo storage per round | `GameStateModel.scorecard_image` (downscaled JPEG, base64, ≤2 MB), set by `POST /games/from-scorecard` |
| Photo read | `GET /games/{id}/scorecard-photo` |
| Photo view | `ScorecardPhotoButton` + `ScorecardPhotoZoom` on `CompletedRoundView` (renders only if a photo exists) |
| Per-hole correction for scanned rounds | `PATCH /games/{id}/scorecard` (recomputes standings = settle-up) |
| Edit a finished live round | "Edit scores" on `CompletedRoundView` → scorekeeper edit mode (`isEditingCompleteGame`) |

## Gaps this change closes

1. **Attach a photo to any round.** New `PUT /games/{id}/scorecard-photo` (multipart image) that
   downscales like the scan path and replaces any existing photo. Numbers are untouched.
   Frontend: when a finished round has no photo, `CompletedRoundView` shows **"Add the card
   photo"** (camera/file input) for players in the round and admins. Once a photo exists, the
   existing 📷 button shows it. A player can replace a photo; no delete in v1.
2. **See the card while editing.** In scorekeeper edit mode for a finished round
   (`isEditingCompleteGame`), show the existing `ScorecardPhotoButton` so the card opens in
   the zoom overlay without leaving the edit.
3. **Lock the round-writing card endpoints** to players in the round + admins:
   `PUT /games/{id}/scorecard-photo` and `PATCH /games/{id}/scorecard`.
   - "Player in the round" = the signed-in user's `PlayerProfile.id` matches a
     `player_profile_id` in the round's players, or their Auth0 `sub` matches a
     player's `user_id`. Admin = `is_super_admin_email` / existing `require_admin` rule.
   - One shared dependency `require_round_member_or_admin(game_id)`, returning 403 for
     signed-in non-members and 401 for anonymous callers.
   - `GET /games/{id}/scorecard-photo` stays public like the rest of a round's results.
   - Frontend gating mirrors this: `usePlayerProfile()` gives the viewer's profile id and
     `isAdmin`; compare the profile id against the round's `players[].player_profile_id`.
     The server check is authoritative; the UI only hides buttons.
4. **Record who edited.** On a successful `PATCH /games/{id}/scorecard` or photo `PUT`,
   write `state["card_edited_by"]` (player name or admin email) and `state["card_edited_at"]`
   (UTC ISO). Last edit only. `CompletedRoundView` shows "Card edited by X · date" when present.

## Ground truth contract

A round is a labeled card when it has `scorecard_image` **and** per-hole numbers in
`hole_history`. Live-scored rounds are labeled the moment a photo is attached (their numbers
were recorded hole by hole). Scanned rounds become labeled once someone fills or corrects the
per-hole grid. A future accuracy check reads these rounds directly.

## Out of scope (add when needed)

- Keeping the scanner's raw guess next to the human correction (only needed to score the
  scanner per round).
- Edit history beyond the last edit.
- Moving photos from Postgres to the `MEDIA_BUCKET` GCS bucket (do it if DB size matters).
- Locking the live-scoring hole endpoints (`POST /games/{id}/scores` etc.), which the
  scorekeeper uses during play and which the "Edit scores" path also uses.
- Requiring a photo at round end.

## Testing

- Backend: photo `PUT` stores a downscaled image and leaves the numbers unchanged; it rejects
  non-images and >20 MB uploads. Membership: member 200, admin 200, signed-in non-member 403,
  anonymous 401, for both `PUT` photo and `PATCH /scorecard`. Audit fields are written on
  success.
- Frontend: the "Add the card photo" button shows only when there's no photo and the viewer
  is a member or admin. The upload sends the bearer token. The photo button is present in
  completed-round edit mode. The "Card edited by" line renders.
- Caps: re-prove the capabilities guarding `games.py` (`game-state-db-authoritative`).
