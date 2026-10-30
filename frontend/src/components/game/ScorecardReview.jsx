import React, { useState, useCallback, useMemo } from 'react';
import { flipSign, parseQuarter, computeHoleDeltas } from '../../utils/quarters';
import ScorecardPhotoZoom from './ScorecardPhotoZoom';

/**
 * ScorecardReview — editable grid of extracted running totals.
 *
 * Users edit the running total row (what's on the card).
 * Per-hole deltas are computed automatically and shown read-only.
 * Zero-sum validation highlights unbalanced holes.
 */

// computeDeltas extracted to utils/quarters as computeHoleDeltas

const CONFIDENCE_STYLE = (confidence) => {
  if (confidence == null) return 'border-red-400 bg-red-50';
  if (confidence >= 0.85) return 'border-gray-300';
  if (confidence >= 0.50) return 'border-yellow-400 bg-yellow-50';
  return 'border-red-400 bg-red-50';
};

const norm = (s) => (s || '').toLowerCase().replace(/[^a-z0-9]/g, '');

const ScorecardReview = ({ extraction, players, onConfirm, onCancel, mode = 'attach', rosterNames = [], pickedPlayers = [], photoUrl = null }) => {
  const isNewRound = mode === 'new-round';
  const [showPhoto, setShowPhoto] = useState(false);
  const knownPlayers = pickedPlayers.length > 0;

  // Retain OCR row identity. Never attribute a garbled row by its position.
  const { players: extractedPlayers, running_totals: rawTotals } = extraction;
  const targetNames = knownPlayers ? pickedPlayers : (!isNewRound ? players.map(p => p.name) : []);
  const [slotMapping, setSlotMapping] = useState(() => extractedPlayers.map(ep => {
    const matches = targetNames.map((name, i) => norm(name) && norm(name) === norm(ep.name) ? i : -1).filter(i => i >= 0);
    return matches.length === 1 ? String(matches[0]) : '';
  }));
  const needsSlotMapping = knownPlayers || !isNewRound;
  const mappingValid = !needsSlotMapping || (
    slotMapping.length === targetNames.length && slotMapping.every(i => i !== '') &&
    new Set(slotMapping).size === slotMapping.length &&
    (isNewRound || slotMapping.every(i => players[Number(i)]?.id))
  );

  const bestRosterMatch = (name) => {
    const lower = (name || '').trim().toLowerCase();
    // A blank scanned name must NOT default to the first roster entry
    // (startsWith('') matches everything) — leave it unlinked.
    if (!lower) return '__unlinked__';
    return (
      (rosterNames.filter(r => r.toLowerCase() === lower).length === 1
        ? rosterNames.find(r => r.toLowerCase() === lower) : null) ||
      '__unlinked__'
    );
  };
  const [mapping, setMapping] = useState(() =>
    knownPlayers
      ? pickedPlayers
      : extractedPlayers.map(ep => bestRosterMatch(ep.name)),
  );
  const [playedAt, setPlayedAt] = useState(() => new Date().toISOString().slice(0, 10));

  // Build initial running total state: { "playerIdx-hole": value }
  const initialValues = useMemo(() => {
    const map = {};
    for (const entry of rawTotals) {
      map[`${entry.player_index}-${entry.hole}`] = entry.value ?? '';
    }
    return map;
  }, [rawTotals]);

  const [values, setValues] = useState(initialValues);

  // Explicit final totals are independent of optional per-hole evidence.
  const initialTotals = useMemo(() => {
    const byPlayer = {};
    for (const e of rawTotals) {
      const cur = byPlayer[e.player_index];
      if (!cur || e.hole > cur.hole) byPlayer[e.player_index] = { hole: e.hole, value: e.value };
    }
    return extractedPlayers.map((_, pi) => {
      const v = byPlayer[pi]?.value;
      return v == null ? '' : String(v);
    });
  }, [rawTotals, extractedPlayers]);
  const [totals, setTotals] = useState(initialTotals);
  const [totalsMode, setTotalsMode] = useState(isNewRound);

  // Confidence map for cell styling
  const confidenceMap = useMemo(() => {
    const map = {};
    for (const entry of rawTotals) {
      map[`${entry.player_index}-${entry.hole}`] = entry.confidence;
    }
    return map;
  }, [rawTotals]);

  const handleChange = useCallback((playerIdx, hole, raw) => {
    const parsed = raw === '' ? '' : Number(raw);
    setValues(prev => ({ ...prev, [`${playerIdx}-${hole}`]: parsed }));
  }, []);

  // Compute per-hole deltas for each player
  const allDeltas = useMemo(() => {
    const result = {};
    for (let pi = 0; pi < extractedPlayers.length; pi++) {
      const totals = [];
      for (let h = 1; h <= 18; h++) {
        const val = values[`${pi}-${h}`];
        if (val !== '' && val != null) totals.push({ hole: h, value: val });
      }
      result[pi] = computeHoleDeltas(totals);
    }
    return result;
  }, [values, extractedPlayers.length]);

  // Zero-sum validation per hole
  const holeBalance = useMemo(() => {
    const balance = {};
    for (let h = 1; h <= 18; h++) {
      let sum = 0;
      let hasAny = false;
      for (let pi = 0; pi < extractedPlayers.length; pi++) {
        const d = allDeltas[pi]?.[h];
        if (d != null) { sum += d; hasAny = true; }
      }
      if (hasAny) balance[h] = Math.round(sum * 100) / 100;
    }
    return balance;
  }, [allDeltas, extractedPlayers.length]);

  const unbalancedHoles = Object.entries(holeBalance)
    .filter(([, sum]) => sum !== 0)
    .map(([h]) => Number(h));

  const allFilled = useMemo(() => {
    for (let pi = 0; pi < extractedPlayers.length; pi++) {
      for (let h = 1; h <= 18; h++) {
        const v = values[`${pi}-${h}`];
        if (v === '' || v == null) return false;
      }
    }
    return true;
  }, [values, extractedPlayers.length]);

  const totalsFilled = totals.every(t => parseQuarter(t) != null);
  const totalsSum = totals.reduce((a, t) => a + (parseQuarter(t) ?? 0), 0);
  const canConfirm = mappingValid && ((isNewRound && totalsMode)
    ? totalsFilled
    : allFilled && (isNewRound || unbalancedHoles.length === 0));

  // One row-to-slot mapping drives both editor labels and submitted attribution.
  const rowName = pi => {
    if (needsSlotMapping) return targetNames[Number(slotMapping[pi])] && slotMapping[pi] !== ''
      ? targetNames[Number(slotMapping[pi])] : `Unmapped scanned row ${pi + 1}`;
    return mapping[pi] === '__unlinked__' ? extractedPlayers[pi].name : mapping[pi];
  };

  // Shared player payload for both new-round paths (totals + grid).
  const buildNewRoundPlayers = () =>
    extractedPlayers.map((ep, pi) =>
      knownPlayers
        ? { name: pickedPlayers[Number(slotMapping[pi])], player_profile_id: null }
        : (mapping[pi] === '__unlinked__'
            // explicit "keep as typed" — backend must NOT auto-link by name
            ? { name: ep.name, player_profile_id: null, unlinked: true }
            : { name: mapping[pi], player_profile_id: null }));

  const handleConfirm = () => {
    if (!canConfirm) return;
    if (isNewRound && totalsMode) {
      onConfirm({ detail_coverage: 'totals_only', players: buildNewRoundPlayers().map((p, pi) => ({
        ...p, quarters: parseQuarter(totals[pi]),
      })), played_at: playedAt });
      return;
    }
    if (isNewRound) {
      const perHole = [];
      for (let pi = 0; pi < extractedPlayers.length; pi++) {
        for (let h = 1; h <= 18; h++) {
          perHole.push({ player_index: pi, hole: h, quarters: allDeltas[pi]?.[h] ?? 0 });
        }
      }
      onConfirm({ detail_coverage: 'per_hole_complete', players: buildNewRoundPlayers(), per_hole_quarters: perHole, played_at: playedAt });
      return;
    }
    // attach mode — quarters by hole for the scores endpoint
    const quartersByHole = {};
    for (let h = 1; h <= 18; h++) {
      quartersByHole[String(h)] = {};
      for (let pi = 0; pi < extractedPlayers.length; pi++) {
        const slotId = players[Number(slotMapping[pi])].id;
        quartersByHole[String(h)][slotId] = allDeltas[pi][h];
      }
    }
    onConfirm(quartersByHole);
  };

  const showGrid = !(isNewRound && totalsMode);

  const holes = Array.from({ length: 18 }, (_, i) => i + 1);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Review Scorecard</h2>
        <button onClick={onCancel} className="text-sm text-gray-400 hover:text-gray-600">✕ Cancel</button>
      </div>

      <p className="text-sm text-gray-500">
        {isNewRound && totalsMode ? (
          <>Confirm each player's <strong>final total</strong> (read from the card). You can add the hole-by-hole detail later.</>
        ) : (
          <>
            Edit the <strong>running totals</strong> (what's on the card). Per-hole quarters update automatically.
            <span className="ml-1 text-yellow-600">Yellow = check this value.</span>
          </>
        )}
      </p>

      {needsSlotMapping && (
        <fieldset>
          <legend>Confirm scanned player mapping</legend>
          {extractedPlayers.map((ep, pi) => (
            <label key={pi} className="block text-sm">
              {ep.name || `Scanned row ${pi + 1}`}
              <select aria-label={`Map scanned row ${pi + 1}`} value={slotMapping[pi]}
                onChange={e => setSlotMapping(prev => prev.map((v, i) => i === pi ? e.target.value : v))}>
                <option value="">Select player</option>
                {targetNames.map((name, i) => <option key={i} value={String(i)}>{name}</option>)}
              </select>
            </label>
          ))}
        </fieldset>
      )}

      {photoUrl && (
        <button
          type="button"
          onClick={() => setShowPhoto(true)}
          className="self-start text-sm text-blue-600 hover:text-blue-800 underline"
        >
          📷 Check photo (zoom to verify the totals)
        </button>
      )}

      {isNewRound && (
        <div className="flex flex-col gap-3 bg-gray-50 border border-gray-200 rounded-lg p-3">
          <div className="flex flex-col gap-2">
            <span className="text-sm font-semibold text-gray-700">
              {knownPlayers ? 'Players' : 'Map scanned players to roster'}
            </span>
            {extractedPlayers.map((ep, pi) => (
              <div key={pi} className="flex items-center gap-2">
                {knownPlayers ? (
                  <span className="text-sm text-gray-800 font-medium">
                    {rowName(pi)}
                  </span>
                ) : (
                  <>
                    <span className="text-sm text-gray-600 min-w-[90px]">{ep.name || `Player ${pi + 1}`}</span>
                    <span className="text-gray-400">→</span>
                    <select
                      value={mapping[pi]}
                      onChange={e => setMapping(prev => prev.map((m, i) => (i === pi ? e.target.value : m)))}
                      className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-400"
                    >
                      {rosterNames.map(r => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                      <option value="__unlinked__">Keep as typed (unlinked)</option>
                    </select>
                  </>
                )}
                {totalsMode && (
                  <span className="flex items-center gap-1 ml-auto">
                    <span className="text-xs text-gray-500">total</span>
                    <button
                      type="button"
                      onClick={() => setTotals(prev => prev.map((t, i) => (i === pi ? flipSign(t) : t)))}
                      className="px-2 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100"
                      aria-label={`toggle sign for ${rowName(pi)}`}
                    >
                      ±
                    </button>
                    <input
                      type="text"
                      inputMode="numeric"
                      value={totals[pi] ?? ''}
                      aria-label={`${rowName(pi)} final total`}
                      onChange={e => setTotals(prev => prev.map((t, i) => (i === pi ? e.target.value : t)))}
                      className="w-16 text-center text-base font-semibold border border-gray-300 rounded px-1 py-1 focus:outline-none focus:ring-1 focus:ring-blue-400"
                      placeholder="±0"
                    />
                  </span>
                )}
              </div>
            ))}
            {isNewRound && (
              <button
                type="button"
                onClick={() => setTotalsMode(m => !m)}
                className="self-start text-xs text-blue-600 hover:text-blue-800 underline"
              >
                {totalsMode ? '➕ Add hole-by-hole detail' : '← Back to totals only'}
              </button>
            )}
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <span className="font-semibold">Date played</span>
            <input
              type="date"
              value={playedAt}
              onChange={e => setPlayedAt(e.target.value)}
              className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
          </label>
        </div>
      )}

      {isNewRound && totalsMode && totalsSum !== 0 && (
        <div className="bg-amber-50 border border-amber-300 rounded-lg p-3 text-sm text-amber-800">
          ⚠️ Heads up — the totals don't add up to 0 (they should in a zero-sum game), but you can still save.
          <span className="font-semibold ml-1">Off by {totalsSum > 0 ? '+' : ''}{totalsSum}.</span>
        </div>
      )}

      {showGrid && unbalancedHoles.length > 0 && (
        <div className={isNewRound
          ? "bg-amber-50 border border-amber-300 rounded-lg p-3 text-sm text-amber-800"
          : "bg-red-50 border border-red-300 rounded-lg p-3 text-sm text-red-700"}>
          {isNewRound
            ? "⚠️ Heads up — these holes don't sum to 0 (you can still save): "
            : "⚠️ Holes not balanced (must sum to 0): "}
          {unbalancedHoles.map(h => (
            <span key={h} className="font-semibold ml-1">
              #{h} (off by {holeBalance[h] > 0 ? '+' : ''}{holeBalance[h]})
            </span>
          ))}
        </div>
      )}

      {showGrid && (
      <div className="overflow-x-auto">
        <table className="text-sm border-collapse min-w-full">
          <thead>
            <tr className="bg-gray-100">
              <th className="sticky left-0 bg-gray-100 px-2 py-2 text-left font-semibold text-gray-600 min-w-[100px]">Player</th>
              <th className="px-2 py-2 text-left font-semibold text-gray-600 min-w-[60px]">Row</th>
              {holes.map(h => (
                <th key={h} className={`px-1 py-2 text-center font-semibold w-10 ${unbalancedHoles.includes(h) ? 'text-red-600' : 'text-gray-600'}`}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {extractedPlayers.map((ep, pi) => {
              const playerName = rowName(pi);
              return (
                <React.Fragment key={pi}>
                  {/* Running total row — editable */}
                  <tr className="border-t border-gray-200">
                    <td className="sticky left-0 bg-white px-2 py-1 font-medium text-gray-800" rowSpan={2}>
                      {playerName}
                    </td>
                    <td className="px-2 py-1 text-xs text-gray-400 whitespace-nowrap">Running total</td>
                    {holes.map(h => {
                      const key = `${pi}-${h}`;
                      const conf = confidenceMap[key];
                      const val = values[key];
                      return (
                        <td key={h} className="px-1 py-1">
                          <input
                            type="number"
                            value={val ?? ''}
                            aria-label={`${playerName} hole ${h} running total`}
                            onChange={e => handleChange(pi, h, e.target.value)}
                            className={`w-10 text-center text-sm border rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-blue-400 ${CONFIDENCE_STYLE(conf)}`}
                            placeholder="—"
                          />
                        </td>
                      );
                    })}
                  </tr>
                  {/* Per-hole delta row — computed, read-only */}
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <td className="px-2 py-1 text-xs text-gray-400 whitespace-nowrap">Per-hole Δ</td>
                    {holes.map(h => {
                      const delta = allDeltas[pi]?.[h];
                      const isUnbalanced = unbalancedHoles.includes(h);
                      return (
                        <td key={h} className={`px-1 py-1 text-center text-xs font-mono font-semibold ${
                          delta == null ? 'text-gray-300' :
                          delta > 0 ? 'text-green-600' :
                          delta < 0 ? 'text-red-600' :
                          'text-gray-400'
                        } ${isUnbalanced ? 'bg-red-100' : ''}`}>
                          {delta != null ? (delta > 0 ? `+${delta}` : delta) : '—'}
                        </td>
                      );
                    })}
                  </tr>
                </React.Fragment>
              );
            })}
            {/* Zero-sum check row */}
            <tr className="border-t-2 border-gray-300 bg-gray-100">
              <td className="sticky left-0 bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-500" colSpan={2}>Sum (must = 0)</td>
              {holes.map(h => {
                const sum = holeBalance[h];
                const ok = sum === 0;
                return (
                  <td key={h} className={`px-1 py-1 text-center text-xs font-bold ${ok ? 'text-green-600' : 'text-red-600'}`}>
                    {sum != null ? (ok ? '✓' : sum) : '—'}
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>
      )}

      <button
        onClick={handleConfirm}
        disabled={!canConfirm}
        className="w-full py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {canConfirm
          ? (isNewRound && totalsMode ? '✅ Confirm Totals' : '✅ Confirm Quarters')
          : (!mappingValid ? 'Confirm player mapping to continue' : isNewRound && totalsMode
              ? 'Enter each total to continue'
              : unbalancedHoles.length > 0
                ? `Fix ${unbalancedHoles.length} unbalanced hole${unbalancedHoles.length > 1 ? 's' : ''}`
                : 'Fill all values to continue')}
      </button>

      {showPhoto && photoUrl && (
        <ScorecardPhotoZoom src={photoUrl} onClose={() => setShowPhoto(false)} />
      )}
    </div>
  );
};

export default ScorecardReview;
