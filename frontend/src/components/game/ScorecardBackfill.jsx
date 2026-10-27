import React, { useState, useMemo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { computeHoleDeltas } from '../../utils/quarters';
import ScorecardPhotoButton from './ScorecardPhotoButton';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { apiConfig } from '../../config/api.config';
import { readDraft, keepDraft, clearDraft } from './roundWriteDraft';

const API_URL = apiConfig.baseUrl;

const HOLES = Array.from({ length: 18 }, (_, i) => i + 1);

/**
 * Convert hole_history deltas back to per-player running totals.
 * hole_history entries: { hole, points_delta: { playerId: delta } }
 * Returns a map: { "playerIdx-hole": runningTotal }
 */
function holeHistoryToRunningTotals(holeHistory, players) {
  // Build cumulative running totals per player per hole
  // First accumulate deltas per player per hole
  const deltasByPlayerHole = {};
  for (const entry of holeHistory) {
    const hole = entry.hole;
    const deltas = entry.points_delta || {};
    for (let i = 0; i < players.length; i++) {
      const playerId = players[i].id;
      const delta = deltas[playerId];
      const key = `${i}-${hole}`;
      if (Number.isFinite(delta)) deltasByPlayerHole[key] = delta;
    }
  }

  // Convert deltas to running totals
  const running = {};
  for (let i = 0; i < players.length; i++) {
    let cumulative = 0;
    for (const h of HOLES) {
      const key = `${i}-${h}`;
      const delta = deltasByPlayerHole[key];
      if (delta == null) break; // no inferred zero across a missing hole
      cumulative += delta;
      running[key] = cumulative;
    }
  }
  return running;
}

/**
 * ScorecardBackfill — editable per-hole running-total grid for backfilling
 * hole-by-hole quarter details on a completed round.
 *
 * Props:
 *   gameId      — game identifier
 *   players     — [{id, name}, ...] (order = player_index)
 *   holeHistory — [{hole, points_delta: {playerId: delta}}, ...]
 *   standings   — {playerId: signedTotal}
 *   onSaved     — called after a successful PATCH
 *   onCancel    — called when the user cancels
 */
const ScorecardBackfill = ({
  gameId,
  players,
  holeHistory,
  standings,
  onSaved,
  onCancel,
  expectedRevision,
}) => {
  const authenticatedFetch = useAuthenticatedFetch();
  // Pre-fill running totals from existing hole_history
  const initialValues = useMemo(
    () => holeHistoryToRunningTotals(holeHistory, players),
    [holeHistory, players],
  );

  const [recovered] = useState(() => readDraft(gameId, 'backfill'));
  const sameSlots = recovered?.slots?.join('|') === players.map(p => p.id).join('|');
  const [values, setValues] = useState(sameSlots ? recovered.values : initialValues);
  const [revision, setRevision] = useState(sameSlots ? recovered.revision : expectedRevision);
  const [needsReview, setNeedsReview] = useState(Boolean(recovered));
  const [rosterDraftHeld, setRosterDraftHeld] = useState(Boolean(recovered && !sameSlots));
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [acceptedStandings, setAcceptedStandings] = useState(standings);
  const retain = (next, rev = revision) => {
    // Index-keyed cells cannot be relabeled using a changed accepted roster.
    // Preserve the original copy until the user explicitly discards it.
    if (rosterDraftHeld) return;
    keepDraft(gameId, 'backfill', { values: next, revision: rev, slots: players.map(p => p.id) });
  };
  const discardRosterDraft = () => {
    try {
      keepDraft(gameId, 'backfill', { values, revision, slots: players.map(p => p.id) });
      setRosterDraftHeld(false);
      // Still require the existing explicit reload/review before any submission.
      setNeedsReview(true);
    } catch { setSaveError('Could not replace the retained draft on this device. Original draft is still held.'); }
  };
  const reloadAccepted = async () => {
    if (rosterDraftHeld) return;
    try {
      const res = await authenticatedFetch(`${API_URL}/games/${gameId}/state`);
      if (!res.ok) throw new Error('Could not reload accepted round. Your draft is retained.');
      const snapshot = await res.json();
      if (!Number.isInteger(snapshot.revision)) throw new Error('Round revision unavailable.');
      setRevision(snapshot.revision);
      setAcceptedStandings(snapshot.standings || {});
      retain(values, snapshot.revision);
      setNeedsReview(false);
      setSaveError('Accepted round reloaded. Compare locked totals, then explicitly save your retained detail.');
    } catch (err) { setSaveError(err.message); }
  };

  const handleChange = useCallback((playerIdx, hole, raw) => {
    const parsed = raw === '' ? undefined : Number(raw);
    setValues((prev) => {
      const next = { ...prev };
      const key = `${playerIdx}-${hole}`;
      if (raw === '' || parsed == null || !Number.isFinite(parsed)) {
        delete next[key];
      } else {
        next[key] = parsed;
      }
      try { retain(next); }
      catch { setSaveError('Could not retain edits on this device. Keep this editor open and copy your entries before leaving.'); }
      return next;
    });
  }, [gameId, revision, players, rosterDraftHeld]);

  // Compute per-hole deltas for each player from the running-total grid
  const allDeltas = useMemo(() => {
    const result = {};
    for (let i = 0; i < players.length; i++) {
      const totalsArr = [];
      for (const h of HOLES) {
        const v = values[`${i}-${h}`];
        if (v != null) totalsArr.push({ hole: h, value: v });
      }
      result[i] = computeHoleDeltas(totalsArr);
    }
    return result;
  }, [values, players.length]);

  // Per-player final running total (last entered cell)
  const playerFinalTotals = useMemo(() => {
    const finals = {};
    for (let i = 0; i < players.length; i++) {
      let last = null;
      for (const h of HOLES) {
        const v = values[`${i}-${h}`];
        if (v != null) last = v;
      }
      finals[i] = last;
    }
    return finals;
  }, [values]);

  // Mismatch: player's entered final total doesn't match their locked standing
  const mismatches = useMemo(() => {
    return players
      .map((player, i) => {
        const locked = acceptedStandings[player.id];
        const entered = playerFinalTotals[i];
        if (entered == null) return null; // nothing entered yet — no warning
        if (entered !== locked) {
          return {
            name: player.name,
            entered,
            locked,
          };
        }
        return null;
      })
      .filter(Boolean);
  }, [players, acceptedStandings, playerFinalTotals]);

  const handleSave = async () => {
    if (needsReview || !Number.isInteger(revision)) {
      setNeedsReview(true);
      setSaveError('Reload accepted round before submitting retained detail.');
      return;
    }
    if (!players.every((_, i) => HOLES.every(h => Number.isFinite(values[`${i}-${h}`])))) {
      setSaveError('Enter every running total; missing holes cannot be inferred as zero.');
      return;
    }
    setSaving(true);
    setSaveError(null);

    // A full-detail write requires explicitly observed/entered cells.
    const perHoleQuarters = [];
    for (let i = 0; i < players.length; i++) {
      const deltas = allDeltas[i] || {};
      for (const h of HOLES) {
        perHoleQuarters.push({ player_index: i, hole: h, quarters: deltas[h] });
      }
    }

    try {
      retain(values);
      const res = await authenticatedFetch(`${API_URL}/games/${gameId}/scorecard`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ per_hole_quarters: perHoleQuarters, expected_revision: revision }),
      });
      const body = await res.json().catch(() => ({}));
      if (res.status === 409) {
        // Held, not staged durably: retained locally for an explicit reload.
        setNeedsReview(true);
        retain(values);
        throw new Error('Round changed. Your edits are retained locally; reload accepted round, then resubmit.');
      }
      if (!res.ok) throw new Error(body.detail || `Save failed (${res.status})`);
      if (Number.isInteger(body.revision)) setRevision(body.revision);
      clearDraft(gameId, 'backfill');
      onSaved();
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Fill in hole-by-hole detail</h2>
        <button
          type="button"
          onClick={onCancel}
          className="text-sm text-gray-400 hover:text-gray-600"
        >
          ✕ Cancel
        </button>
      </div>

      <p className="text-sm text-gray-500">
        Enter each player's <strong>running total</strong> through each hole. Per-hole
        quarters are computed automatically. The <strong>locked final total</strong>{' '}
        (from the completed round) is shown per player.
      </p>

      {/* Photo button — self-probing: renders nothing when no photo on server */}
      <ScorecardPhotoButton gameId={gameId} />

      {/* Mismatch warnings (non-blocking) */}
      {mismatches.length > 0 && (
        <div className="bg-amber-50 border border-amber-300 rounded-lg p-3 text-sm text-amber-800">
          ⚠️ The following players' entered running totals don't reach locked total:
          {mismatches.map((m) => (
            <div key={m.name} className="ml-2 mt-1 font-semibold">
              {m.name}: entered {m.entered}, locked {m.locked}
            </div>
          ))}
          <div className="mt-1 text-amber-700">You can still save — this is a warning only.</div>
        </div>
      )}

      {rosterDraftHeld && (
        <div role="alert" className="bg-amber-50 border border-amber-300 rounded-lg p-3 text-sm text-amber-800">
          The accepted roster changed. Your original draft is held below with its original slot IDs and cell indices.
          Copy this JSON to recover all entries, including removed players. Current grid edits will not replace it
          or be submitted until you explicitly discard the original. Current grid edits are not retained while it is held.
          <textarea aria-label="Retained backfill draft JSON" readOnly value={JSON.stringify(recovered, null, 2)}
            className="block w-full mt-2" rows={6} />
          <button type="button" onClick={discardRosterDraft} className="underline font-semibold">
            Discard retained draft and use current grid
          </button>
        </div>
      )}

      {needsReview && !rosterDraftHeld && (
        <div role="alert" className="bg-amber-50 border border-amber-300 rounded-lg p-3 text-sm text-amber-800">
          Your retained edits were not accepted and are not staged on the server.
          <button type="button" onClick={reloadAccepted} className="ml-2 underline font-semibold">
            Reload accepted round
          </button>
        </div>
      )}

      {/* Save error */}
      {saveError && (
        <div className="bg-red-50 border border-red-300 rounded-lg p-3 text-sm text-red-700">
          {saveError}
        </div>
      )}

      {/* Per-hole grid */}
      <div className="overflow-x-auto">
        <table className="text-sm border-collapse min-w-full">
          <thead>
            <tr className="bg-gray-100">
              <th className="sticky left-0 bg-gray-100 px-2 py-2 text-left font-semibold text-gray-600 min-w-[100px]">
                Player
              </th>
              <th className="px-2 py-2 text-center font-semibold text-gray-600 min-w-[60px]">
                Locked
              </th>
              {HOLES.map((h) => (
                <th
                  key={h}
                  className="px-1 py-2 text-center font-semibold text-gray-600 w-10"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {players.map((player, i) => {
              const locked = acceptedStandings[player.id];
              const finalEntered = playerFinalTotals[i];
              const mismatch =
                finalEntered != null && finalEntered !== locked;

              return (
                <React.Fragment key={player.id}>
                  {/* Running total row — editable */}
                  <tr className="border-t border-gray-200">
                    <td
                      className="sticky left-0 bg-white px-2 py-1 font-medium text-gray-800"
                      rowSpan={2}
                    >
                      <div>{player.name}</div>
                      <div
                        className={`text-xs font-semibold mt-0.5 ${
                          mismatch ? 'text-amber-600' : 'text-gray-500'
                        }`}
                      >
                        Locked: {locked != null ? locked : '—'}
                      </div>
                    </td>
                    <td className="px-2 py-1 text-center text-xs text-gray-400 whitespace-nowrap">
                      Running total
                    </td>
                    {HOLES.map((h) => {
                      const key = `${i}-${h}`;
                      const val = values[key];
                      return (
                        <td key={h} className="px-1 py-1">
                          <input
                            type="number"
                            value={val ?? ''}
                            onChange={(e) => handleChange(i, h, e.target.value)}
                            className="w-10 text-center text-sm border border-gray-300 rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-blue-400"
                            placeholder="—"
                            aria-label={`running total ${player.name} hole ${h}`}
                          />
                        </td>
                      );
                    })}
                  </tr>
                  {/* Per-hole delta row — read-only */}
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <td className="px-2 py-1 text-xs text-gray-400 whitespace-nowrap">
                      Per-hole Δ
                    </td>
                    {HOLES.map((h) => {
                      const delta = allDeltas[i]?.[h];
                      return (
                        <td
                          key={h}
                          className={`px-1 py-1 text-center text-xs font-mono font-semibold ${
                            delta == null
                              ? 'text-gray-300'
                              : delta > 0
                              ? 'text-green-600'
                              : delta < 0
                              ? 'text-red-600'
                              : 'text-gray-400'
                          }`}
                        >
                          {delta != null
                            ? delta > 0
                              ? `+${delta}`
                              : delta
                            : '—'}
                        </td>
                      );
                    })}
                  </tr>
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="flex-1 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Save hole detail"
        >
          {saving ? 'Saving…' : '✅ Save hole detail'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="py-3 px-6 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
        >
          Cancel
        </button>
      </div>

    </div>
  );
};

ScorecardBackfill.propTypes = {
  gameId: PropTypes.string.isRequired,
  players: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
    }),
  ).isRequired,
  holeHistory: PropTypes.arrayOf(
    PropTypes.shape({
      hole: PropTypes.number.isRequired,
      points_delta: PropTypes.objectOf(PropTypes.number),
    }),
  ).isRequired,
  standings: PropTypes.objectOf(PropTypes.number).isRequired,
  expectedRevision: PropTypes.number,
  onSaved: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

export default ScorecardBackfill;
