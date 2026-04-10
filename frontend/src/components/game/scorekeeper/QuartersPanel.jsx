// frontend/src/components/game/scorekeeper/QuartersPanel.jsx
// Quick wager + tap-winners as primary UX. Manual mode for edits/overrides.
import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

const WAGER_PRESETS = [1, 2, 4, 8, 12, 16, 20, 24];

const QuartersPanel = ({
  players,
  quarters,
  scores,
  expandedPlayers,
  setExpandedPlayers,
  setQuarters,
  theme,
  editingHole,
  currentWager,
}) => {
  const [wager, setWager] = useState(currentWager || null);
  const [winners, setWinners] = useState(new Set());
  const [showManual, setShowManual] = useState(false);

  // Default to manual when editing an existing hole (values already set)
  useEffect(() => {
    if (editingHole) {
      setShowManual(true);
    } else {
      setShowManual(false);
      setWinners(new Set());
      setWager(currentWager || null);
    }
  }, [editingHole, currentWager]);

  const totalSum = players.reduce(
    (acc, p) => acc + (parseFloat(quarters[p.id]) || 0),
    0,
  );
  const hasAnyValue = Object.values(quarters).some((v) => v !== "" && v !== undefined && v !== null);

  // Distribute wager among winners/losers
  const applyDistribution = (w, wins) => {
    if (!w || wins.size === 0 || wins.size === players.length) return;
    const loserCount = players.length - wins.size;
    const winnerCount = wins.size;
    const perWinner = (w * loserCount) / winnerCount;
    const perLoser = -w;

    const newQ = {};
    players.forEach((p) => {
      newQ[p.id] = wins.has(p.id) ? perWinner.toString() : perLoser.toString();
    });
    setQuarters(newQ);
  };

  const handleWagerSelect = (w) => {
    setWager(w);
    if (winners.size > 0 && winners.size < players.length) {
      applyDistribution(w, winners);
    }
  };

  const handlePlayerTap = (playerId) => {
    const next = new Set(winners);
    if (next.has(playerId)) {
      next.delete(playerId);
    } else {
      next.add(playerId);
    }
    setWinners(next);
    if (wager && next.size > 0 && next.size < players.length) {
      applyDistribution(wager, next);
    } else if (next.size === 0) {
      const cleared = {};
      players.forEach((p) => { cleared[p.id] = ""; });
      setQuarters(cleared);
    }
  };

  const handlePush = () => {
    const allZero = {};
    players.forEach((p) => { allZero[p.id] = "0"; });
    setQuarters(allZero);
    setWinners(new Set());
  };

  const handleClear = () => {
    const cleared = {};
    players.forEach((p) => { cleared[p.id] = ""; });
    setQuarters(cleared);
    setWinners(new Set());
    setWager(currentWager || null);
  };

  // --- Sum badge ---
  const sumColor = hasAnyValue && Math.abs(totalSum) < 0.001
    ? "#4CAF50"
    : Math.abs(totalSum) > 0.001
      ? "#f44336"
      : theme.colors.textSecondary;
  const sumText = Math.abs(totalSum) < 0.001
    ? hasAnyValue ? "0 \u2713" : "0"
    : (totalSum > 0 ? "+" : "") + totalSum.toFixed(1);

  return (
    <div style={{ marginBottom: "20px" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "10px",
          padding: "6px 12px",
          background: theme.colors.backgroundSecondary,
          borderRadius: "8px",
        }}
      >
        <h3
          style={{
            margin: 0, textTransform: "uppercase", letterSpacing: "0.5px",
            fontSize: "12px", fontWeight: "bold", color: theme.colors.textSecondary,
          }}
        >
          Quarters
        </h3>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "13px", fontWeight: "bold", color: sumColor }}>
            {sumText}
          </span>
          <button
            onClick={() => setShowManual(!showManual)}
            style={{
              padding: "2px 8px", fontSize: "10px", fontWeight: "600",
              border: `1px solid ${theme.colors.border}`, borderRadius: "4px",
              background: showManual ? theme.colors.primary : "transparent",
              color: showManual ? "white" : theme.colors.textSecondary,
              cursor: "pointer",
            }}
          >
            {showManual ? "Quick" : "Edit"}
          </button>
        </div>
      </div>

      {!showManual ? (
        /* ── QUICK MODE ── */
        <>
          {/* Wager grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: "6px",
              marginBottom: "10px",
            }}
          >
            {WAGER_PRESETS.map((w) => (
              <button
                key={w}
                onClick={() => handleWagerSelect(w)}
                className="touch-optimized"
                style={{
                  padding: "10px 4px", borderRadius: "10px",
                  border: `2px solid ${wager === w ? theme.colors.primary : theme.colors.border}`,
                  background: wager === w ? theme.colors.primary : theme.colors.paper,
                  color: wager === w ? "white" : theme.colors.textPrimary,
                  fontWeight: "bold", fontSize: "15px", cursor: "pointer",
                  transition: "all 0.12s ease",
                }}
              >
                {w}Q
              </button>
            ))}
          </div>

          {/* Custom wager */}
          <div style={{ display: "flex", gap: "6px", alignItems: "center", marginBottom: "12px" }}>
            <input
              type="text"
              inputMode="numeric"
              placeholder="Other"
              value={wager && !WAGER_PRESETS.includes(wager) ? wager : ""}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (!isNaN(val) && val > 0) handleWagerSelect(val);
                else if (e.target.value === "") setWager(null);
              }}
              style={{
                flex: 1, padding: "8px 12px", fontSize: "14px",
                border: `1px solid ${theme.colors.border}`, borderRadius: "8px",
                textAlign: "center", outline: "none",
              }}
            />
            <span style={{ fontSize: "12px", color: theme.colors.textSecondary, fontWeight: "600" }}>Q</span>
          </div>

          {/* Tap winners */}
          {wager && (
            <div
              style={{
                fontSize: "11px", fontWeight: "bold", color: theme.colors.textSecondary,
                textTransform: "uppercase", marginBottom: "6px",
              }}
            >
              Tap winners
            </div>
          )}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {players.map((player) => {
              const isWinner = winners.has(player.id);
              const val = parseFloat(quarters[player.id]) || 0;
              const hasVal = quarters[player.id] !== "" && quarters[player.id] !== undefined;

              return (
                <button
                  key={player.id}
                  onClick={() => handlePlayerTap(player.id)}
                  className="touch-optimized"
                  style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "14px 16px", borderRadius: "12px",
                    border: `2px solid ${isWinner ? "#4CAF50" : hasVal && val < 0 ? "#EF5350" : theme.colors.border}`,
                    background: isWinner
                      ? "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)"
                      : hasVal && val < 0
                        ? "linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%)"
                        : theme.colors.paper,
                    cursor: "pointer", transition: "all 0.12s ease", textAlign: "left",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ fontSize: "20px" }}>
                      {isWinner ? "\uD83C\uDFC6" : "\uD83D\uDC64"}
                    </span>
                    <span style={{ fontWeight: "bold", fontSize: "16px", color: theme.colors.textPrimary }}>
                      {player.name}
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: "22px", fontWeight: "bold", minWidth: "50px", textAlign: "right",
                      color: hasVal
                        ? val > 0 ? "#2E7D32" : val < 0 ? "#C62828" : theme.colors.textSecondary
                        : theme.colors.textSecondary,
                    }}
                  >
                    {hasVal ? (val > 0 ? `+${val}` : val) : "\u2014"}
                  </span>
                </button>
              );
            })}
          </div>
        </>
      ) : (
        /* ── MANUAL / EDIT MODE ── */
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {players.map((player) => {
            const val = parseFloat(quarters[player.id]) || 0;
            const adjust = (delta) => {
              const base = parseFloat(quarters[player.id]) || 0;
              setQuarters({ ...quarters, [player.id]: (base + delta).toString() });
            };

            return (
              <div
                key={player.id}
                style={{
                  display: "flex", alignItems: "center", gap: "8px",
                  padding: "8px 12px", background: theme.colors.paper,
                  borderRadius: "12px", border: `1px solid ${theme.colors.border}`,
                }}
              >
                <div style={{ flex: 1, fontWeight: "bold", fontSize: "14px" }}>
                  {player.name}
                </div>
                <button
                  onClick={() => adjust(-1)}
                  className="touch-optimized"
                  style={{
                    width: "36px", height: "36px", borderRadius: "8px",
                    border: "1px solid #EF5350", background: "#FFEBEE",
                    color: "#C62828", fontWeight: "bold", fontSize: "18px",
                    cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                  }}
                >
                  -
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
                  placeholder="0"
                  style={{
                    width: "64px", padding: "8px", fontSize: "18px", fontWeight: "bold",
                    border: `2px solid ${val > 0 ? "#4CAF50" : val < 0 ? "#f44336" : theme.colors.border}`,
                    borderRadius: "10px", textAlign: "center", outline: "none",
                    color: val > 0 ? "#4CAF50" : val < 0 ? "#f44336" : theme.colors.textPrimary,
                  }}
                />
                <button
                  onClick={() => adjust(1)}
                  className="touch-optimized"
                  style={{
                    width: "36px", height: "36px", borderRadius: "8px",
                    border: "1px solid #66BB6A", background: "#E8F5E9",
                    color: "#2E7D32", fontWeight: "bold", fontSize: "18px",
                    cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                  }}
                >
                  +
                </button>
              </div>
            );
          })}
        </div>
      )}

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
  scores: PropTypes.object.isRequired,
  expandedPlayers: PropTypes.object.isRequired,
  setExpandedPlayers: PropTypes.func.isRequired,
  setQuarters: PropTypes.func.isRequired,
  theme: PropTypes.object.isRequired,
  editingHole: PropTypes.number,
  currentWager: PropTypes.number,
};

export default QuartersPanel;
