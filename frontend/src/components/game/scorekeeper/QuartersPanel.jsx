// frontend/src/components/game/scorekeeper/QuartersPanel.jsx
// Manual quarters entry: +/- buttons and direct input per player.
import React from "react";
import PropTypes from "prop-types";
import {
  parseQuarter,
  normalizeQuarterInput,
  flipSign,
  isNegativeInput,
} from "../../../utils/quarters";

const QuartersPanel = ({
  players,
  quarters,
  setQuarters,
  theme,
}) => {
  const totalSum = players.reduce(
    (acc, p) => acc + (parseQuarter(quarters[p.id]) ?? 0),
    0,
  );

  // On blur, collapse a half-typed "-"/"." or "1." to a clean value so it
  // never lingers and silently zeroes on submit.
  const normalizeOnBlur = (playerId, raw) => {
    const clean = normalizeQuarterInput(raw);
    if (clean !== (quarters[playerId] ?? "")) {
      setQuarters({ ...quarters, [playerId]: clean });
    }
  };
  const hasAnyValue = Object.values(quarters).some((v) => v !== "" && v !== undefined && v !== null);

  const sumColor = hasAnyValue && Math.abs(totalSum) < 0.001
    ? "#4CAF50"
    : Math.abs(totalSum) > 0.001
      ? "#f44336"
      : theme.colors.textSecondary;
  const sumText = Math.abs(totalSum) < 0.001
    ? hasAnyValue ? "0 \u2713" : "0"
    : (totalSum > 0 ? "+" : "") + totalSum.toFixed(1);

  const handlePush = () => {
    const allZero = {};
    players.forEach((p) => { allZero[p.id] = "0"; });
    setQuarters(allZero);
  };

  const handleClear = () => {
    const cleared = {};
    players.forEach((p) => { cleared[p.id] = ""; });
    setQuarters(cleared);
  };

  const isBalanced = hasAnyValue && Math.abs(totalSum) < 0.001;
  const isUnbalanced = hasAnyValue && Math.abs(totalSum) > 0.001;

  return (
    <div style={{ marginBottom: "20px" }}>
      {/* Balance indicator — sticky so it's always visible */}
      <div
        style={{
          position: "sticky",
          top: 0,
          zIndex: 10,
          padding: "10px 16px",
          marginBottom: "10px",
          borderRadius: "10px",
          textAlign: "center",
          fontWeight: "bold",
          fontSize: "15px",
          background: isBalanced
            ? "#E8F5E9"
            : isUnbalanced
              ? "#FFEBEE"
              : theme.colors.backgroundSecondary,
          color: isBalanced
            ? "#2E7D32"
            : isUnbalanced
              ? "#C62828"
              : theme.colors.textSecondary,
          border: isUnbalanced
            ? "2px solid #f44336"
            : isBalanced
              ? "2px solid #4CAF50"
              : `1px solid ${theme.colors.border}`,
          transition: "all 0.2s ease",
        }}
      >
        {isBalanced
          ? "Balanced"
          : isUnbalanced
            ? `Off by ${totalSum > 0 ? "+" : ""}${totalSum.toFixed(1)} — must equal zero`
            : "Quarters must add up to zero"}
      </div>

      {/* Per-player rows */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {players.map((player) => {
          const val = parseQuarter(quarters[player.id]) ?? 0;
          const negative = isNegativeInput(quarters[player.id]);
          const adjust = (delta) => {
            const base = parseQuarter(quarters[player.id]) ?? 0;
            setQuarters({ ...quarters, [player.id]: (base + delta).toString() });
          };
          const toggleSign = () =>
            setQuarters({
              ...quarters,
              [player.id]: flipSign(quarters[player.id]),
            });

          return (
            <div
              key={player.id}
              style={{
                display: "flex", alignItems: "center", gap: "8px",
                padding: "8px 12px", background: theme.colors.paper,
                borderRadius: "12px", border: `1px solid ${theme.colors.border}`,
              }}
            >
              <div style={{
                flex: 1, minWidth: 0, fontWeight: "bold", fontSize: "14px",
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              }}>
                {player.name}
              </div>
              {/* Sign toggle — tap BEFORE typing to make the value negative
                  (mobile keypads have no minus key); shows current sign. */}
              <button
                onClick={toggleSign}
                className="touch-optimized"
                aria-label={`Set sign for ${player.name} (negative or positive)`}
                title="Tap to set negative / positive"
                style={{
                  width: "40px", height: "40px", flexShrink: 0, borderRadius: "8px",
                  border: `2px solid ${negative ? "#EF5350" : val > 0 ? "#66BB6A" : "#CBD5E1"}`,
                  background: negative ? "#FFEBEE" : val > 0 ? "#E8F5E9" : theme.colors.backgroundSecondary,
                  color: negative ? "#C62828" : val > 0 ? "#2E7D32" : theme.colors.textSecondary,
                  fontWeight: "bold", fontSize: "20px",
                  cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                }}
              >
                {negative ? "−" : val > 0 ? "+" : "±"}
              </button>
              <input
                type="text"
                inputMode="numeric"
                pattern="-?[0-9]*\.?[0-9]*"
                value={quarters[player.id] ?? ""}
                onChange={(e) => {
                  const v = e.target.value;
                  if (v === "" || v === "-" || /^-?\d*\.?\d*$/.test(v)) {
                    setQuarters({ ...quarters, [player.id]: v });
                  }
                }}
                onBlur={(e) => normalizeOnBlur(player.id, e.target.value)}
                placeholder="0"
                style={{
                  width: "64px", flexShrink: 0, padding: "8px", fontSize: "18px", fontWeight: "bold",
                  border: `2px solid ${val > 0 ? "#4CAF50" : val < 0 ? "#f44336" : theme.colors.border}`,
                  borderRadius: "10px", textAlign: "center", outline: "none",
                  color: val > 0 ? "#4CAF50" : val < 0 ? "#f44336" : theme.colors.textPrimary,
                }}
              />
              {/* ±1 steppers for quick nudges (also work without the keyboard) */}
              <button
                onClick={() => adjust(-1)}
                className="touch-optimized"
                aria-label={`Decrease quarters for ${player.name} by 1`}
                style={{
                  width: "36px", height: "36px", flexShrink: 0, borderRadius: "8px",
                  border: "1px solid #EF5350", background: "#FFEBEE",
                  color: "#C62828", fontWeight: "bold", fontSize: "18px",
                  cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                }}
              >
                −1
              </button>
              <button
                onClick={() => adjust(1)}
                className="touch-optimized"
                aria-label={`Increase quarters for ${player.name} by 1`}
                style={{
                  width: "36px", height: "36px", flexShrink: 0, borderRadius: "8px",
                  border: "1px solid #66BB6A", background: "#E8F5E9",
                  color: "#2E7D32", fontWeight: "bold", fontSize: "18px",
                  cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                }}
              >
                +1
              </button>
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
        <button
          onClick={handlePush}
          className="touch-optimized"
          style={{
            padding: "10px 16px", borderRadius: "8px", fontSize: "13px",
            fontWeight: "bold", border: `2px solid ${theme.colors.border}`,
            background: "white", cursor: "pointer",
          }}
        >
          Push (all 0)
        </button>
        <button
          onClick={handleClear}
          className="touch-optimized"
          style={{
            padding: "10px 16px", borderRadius: "8px", fontSize: "13px",
            fontWeight: "bold", border: `2px solid ${theme.colors.border}`,
            background: "white", cursor: "pointer",
          }}
        >
          Clear
        </button>
      </div>
    </div>
  );
};

QuartersPanel.propTypes = {
  players: PropTypes.array.isRequired,
  quarters: PropTypes.object.isRequired,
  setQuarters: PropTypes.func.isRequired,
  theme: PropTypes.object.isRequired,
};

export default QuartersPanel;
