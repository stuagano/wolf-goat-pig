import React, { useState, useCallback, useMemo } from 'react';

/**
 * ScorecardReview — editable grid of extracted running totals.
 *
 * Users edit the running total row (what's on the card).
 * Per-hole deltas are computed automatically and shown read-only.
 * Zero-sum validation highlights unbalanced holes.
 */

const CONFIDENCE_STYLE = (confidence) => {
  if (confidence == null) return 'border-red-400 bg-red-50';
  if (confidence >= 0.85) return 'border-gray-300';
  if (confidence >= 0.50) return 'border-yellow-400 bg-yellow-50';
  return 'border-red-400 bg-red-50';
};

const computeDeltas = (runningTotals) => {
  // runningTotals: array of { hole, value } sorted by hole
  const sorted = [...runningTotals].sort((a, b) => a.hole - b.hole);
  const deltas = {};
  let prev = 0;
  for (const { hole, value } of sorted) {
    const v = value ?? 0;
    deltas[hole] = v - prev;
    prev = v;
  }
  return deltas;
};

const ScorecardReview = ({ extraction, players, onConfirm, onCancel }) => {
  const { players: extractedPlayers, running_totals: rawTotals } = extraction;

  // Build initial running total state: { "playerIdx-hole": value }
  const initialValues = useMemo(() => {
    const map = {};
    for (const entry of rawTotals) {
      map[`${entry.player_index}-${entry.hole}`] = entry.value ?? '';
    }
    return map;
  }, [rawTotals]);

  const [values, setValues] = useState(initialValues);

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
      result[pi] = computeDeltas(totals);
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

  const canConfirm = allFilled && unbalancedHoles.length === 0;

  const handleConfirm = () => {
    // Build hole_quarters payload: { "1": { "playerName": delta, ... }, ... }
    const hole_quarters = {};
    for (let h = 1; h <= 18; h++) {
      hole_quarters[String(h)] = {};
      for (let pi = 0; pi < extractedPlayers.length; pi++) {
        const playerName = players[pi]?.name || extractedPlayers[pi]?.name || `Player ${pi + 1}`;
        hole_quarters[String(h)][playerName] = allDeltas[pi]?.[h] ?? 0;
      }
    }
    onConfirm(hole_quarters);
  };

  const holes = Array.from({ length: 18 }, (_, i) => i + 1);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Review Scorecard</h2>
        <button onClick={onCancel} className="text-sm text-gray-400 hover:text-gray-600">✕ Cancel</button>
      </div>

      <p className="text-sm text-gray-500">
        Edit the <strong>running totals</strong> (what's on the card). Per-hole quarters update automatically.
        <span className="ml-1 text-yellow-600">Yellow = check this value.</span>
      </p>

      {unbalancedHoles.length > 0 && (
        <div className="bg-red-50 border border-red-300 rounded-lg p-3 text-sm text-red-700">
          ⚠️ Holes not balanced (must sum to 0): {unbalancedHoles.map(h => (
            <span key={h} className="font-semibold ml-1">
              #{h} (off by {holeBalance[h] > 0 ? '+' : ''}{holeBalance[h]})
            </span>
          ))}
        </div>
      )}

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
              const playerName = players[pi]?.name || ep.name || `Player ${pi + 1}`;
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

      <button
        onClick={handleConfirm}
        disabled={!canConfirm}
        className="w-full py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {canConfirm ? '✅ Confirm Quarters' : unbalancedHoles.length > 0 ? `Fix ${unbalancedHoles.length} unbalanced hole${unbalancedHoles.length > 1 ? 's' : ''}` : 'Fill all values to continue'}
      </button>
    </div>
  );
};

export default ScorecardReview;
