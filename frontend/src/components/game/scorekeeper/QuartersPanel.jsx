// frontend/src/components/game/scorekeeper/QuartersPanel.jsx
// Manual quarters entry: outcome plus an unsigned amount per player.
import React from "react";
import PropTypes from "prop-types";
import {
  parseQuarter,
  normalizeQuarterInput,
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

  // Keep the chosen outcome even when the amount is empty or zero.
  const normalizeOnBlur = (playerId, raw) => {
    const clean = `${isNegativeInput(quarters[playerId]) ? "-" : ""}${normalizeQuarterInput(raw)}`;
    if (clean !== (quarters[playerId] ?? "")) {
      setQuarters({ ...quarters, [playerId]: clean });
    }
  };
  const missingPlayers = players.filter((p) => parseQuarter(quarters[p.id]) === null);
  const remainingPlayer = missingPlayers.length === 1 && players.length > 1 && Number.isFinite(totalSum)
    ? missingPlayers[0] : null;
  const remaining = Number((-totalSum).toFixed(10));
  const remainingLabel = remaining === 0 ? "0 (push)"
    : `${remaining < 0 ? "Lost" : "Won"} ${Math.abs(remaining)}`;

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

  const allEntered = players.length > 0 && missingPlayers.length === 0;
  const isBalanced = allEntered && Math.abs(totalSum) < 0.001;
  const isUnbalanced = allEntered && !isBalanced;

  return (
    <div style={{ marginBottom: "20px" }}>
      <h2 style={{ fontSize: "18px", margin: "0 0 12px" }}>Quarters this hole</h2>
      {/* Balance indicator — sticky so it's always visible */}
      <div
        data-testid="zero-sum-validation"
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
        {missingPlayers.length > 0
          ? `${missingPlayers.length} player${missingPlayers.length === 1 ? "" : "s"} left — enter quarters${remainingPlayer ? " or use Fill remaining" : ""}`
          : isBalanced
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
          const amount = String(quarters[player.id] ?? "").replace(/^-/, "");

          return (
            <div
              key={player.id}
              style={{
                display: "flex", alignItems: "center", flexWrap: "wrap", gap: "8px",
                padding: "8px 12px", background: theme.colors.paper,
                borderRadius: "12px", border: `1px solid ${theme.colors.border}`,
              }}
            >
              <div style={{
                flex: "1 1 100px", minWidth: 0, fontWeight: "bold", fontSize: "14px",
                overflowWrap: "anywhere",
              }}>
                {player.name}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              {["Won", "Lost"].map((outcome) => {
                const loss = outcome === "Lost";
                const selected = loss === negative;
                return (
                  <button
                    key={outcome}
                    type="button"
                    aria-label={`${player.name} ${outcome.toLowerCase()} quarters`}
                    aria-pressed={selected}
                    onClick={() => setQuarters({ ...quarters, [player.id]: `${loss ? "-" : ""}${amount}` })}
                    style={{
                      minHeight: "44px", padding: "8px 10px", borderRadius: "8px",
                      border: `2px solid ${selected ? loss ? "#C62828" : "#2E7D32" : theme.colors.border}`,
                      background: selected ? loss ? "#FFEBEE" : "#E8F5E9" : theme.colors.paper,
                      color: selected ? loss ? "#C62828" : "#2E7D32" : theme.colors.textSecondary,
                      fontWeight: "bold", cursor: "pointer",
                    }}
                  >
                    {outcome}
                  </button>
                );
              })}
              <input
                type="text"
                inputMode="decimal"
                aria-label={`Quarters amount for ${player.name}`}
                data-testid={`quarters-input-${player.id}`}
                value={amount}
                onChange={(e) => {
                  const v = e.target.value;
                  if (/^\d*\.?\d*$/.test(v)) {
                    setQuarters({ ...quarters, [player.id]: `${negative ? "-" : ""}${v}` });
                  }
                }}
                onBlur={(e) => normalizeOnBlur(player.id, e.target.value)}
                placeholder="0"
                style={{
                  width: "72px", minHeight: "44px", boxSizing: "border-box", flexShrink: 0, padding: "8px", fontSize: "18px", fontWeight: "bold",
                  border: `2px solid ${val > 0 ? "#4CAF50" : val < 0 ? "#f44336" : theme.colors.border}`,
                  borderRadius: "10px", textAlign: "center",
                  color: val > 0 ? "#4CAF50" : val < 0 ? "#f44336" : theme.colors.textPrimary,
                }}
              />
              </div>
              {remainingPlayer?.id === player.id && (
                <button
                  type="button"
                  aria-label={`Fill remaining for ${player.name}: ${remainingLabel}`}
                  onClick={() => setQuarters({ ...quarters, [player.id]: String(remaining) })}
                  style={{
                    flexBasis: "100%", minHeight: "44px", padding: "8px 12px",
                    border: `1px solid ${theme.colors.border}`, borderRadius: "8px",
                    background: theme.colors.backgroundSecondary, color: theme.colors.textPrimary,
                    fontWeight: "bold", cursor: "pointer",
                  }}
                >
                  Fill remaining: {remainingLabel}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
        <button
          type="button"
          data-testid="push-hole-button"
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
