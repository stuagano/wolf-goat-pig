// frontend/src/components/game/scorekeeper/QuartersPanel.jsx
// Compact wager-based quarters entry — tap winners, losers auto-calculate
import React, { useState } from "react";
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
}) => {
  const [wager, setWager] = useState(null);
  const [winners, setWinners] = useState(new Set());
  const [mode, setMode] = useState("quick"); // "quick" (wager+tap) or "manual"

  // Compute the sum of current quarters
  const totalSum = players.reduce(
    (acc, p) => acc + (parseFloat(quarters[p.id]) || 0),
    0,
  );

  // Apply wager + winners to quarters
  const applyWagerDistribution = (w, wins) => {
    if (!w || wins.size === 0 || wins.size === players.length) return;

    const losers = players.filter((p) => !wins.has(p.id));
    const winnerCount = wins.size;
    const loserCount = losers.length;

    // Total pot = wager * number of losers (each loser pays the wager to the pot)
    // Split evenly among winners
    const totalPot = w * loserCount;
    const perWinner = totalPot / winnerCount;
    const perLoser = -(totalPot / loserCount);

    const newQuarters = {};
    players.forEach((p) => {
      if (wins.has(p.id)) {
        newQuarters[p.id] = perWinner.toString();
      } else {
        newQuarters[p.id] = perLoser.toString();
      }
    });
    setQuarters(newQuarters);
  };

  const handleWagerSelect = (w) => {
    setWager(w);
    if (winners.size > 0) {
      applyWagerDistribution(w, winners);
    }
  };

  const handlePlayerTap = (playerId) => {
    const newWinners = new Set(winners);
    if (newWinners.has(playerId)) {
      newWinners.delete(playerId);
    } else {
      newWinners.add(playerId);
    }
    setWinners(newWinners);
    if (wager && newWinners.size > 0 && newWinners.size < players.length) {
      applyWagerDistribution(wager, newWinners);
    } else if (newWinners.size === 0) {
      // Clear quarters when no winners selected
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
    setWager(null);
  };

  const handleClear = () => {
    const cleared = {};
    players.forEach((p) => { cleared[p.id] = ""; });
    setQuarters(cleared);
    setWinners(new Set());
    setWager(null);
  };

  return (
    <div style={{ marginBottom: "20px" }}>
      {/* Header with mode toggle and sum */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "12px",
          padding: "8px 12px",
          background: theme.colors.backgroundSecondary,
          borderRadius: "8px",
        }}
      >
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button
            onClick={() => setMode("quick")}
            style={{
              padding: "4px 10px",
              fontSize: "11px",
              fontWeight: "bold",
              border: `1px solid ${mode === "quick" ? theme.colors.primary : theme.colors.border}`,
              borderRadius: "6px",
              background: mode === "quick" ? theme.colors.primary : "transparent",
              color: mode === "quick" ? "white" : theme.colors.textSecondary,
              cursor: "pointer",
            }}
          >
            Quick
          </button>
          <button
            onClick={() => setMode("manual")}
            style={{
              padding: "4px 10px",
              fontSize: "11px",
              fontWeight: "bold",
              border: `1px solid ${mode === "manual" ? theme.colors.primary : theme.colors.border}`,
              borderRadius: "6px",
              background: mode === "manual" ? theme.colors.primary : "transparent",
              color: mode === "manual" ? "white" : theme.colors.textSecondary,
              cursor: "pointer",
            }}
          >
            Manual
          </button>
        </div>
        <div style={{ fontSize: "14px", fontWeight: "bold" }}>
          {(() => {
            const color = Math.abs(totalSum) < 0.001 && Object.values(quarters).some((v) => v !== "" && v !== undefined)
              ? "#4CAF50"
              : Math.abs(totalSum) > 0.001
                ? "#f44336"
                : theme.colors.textSecondary;
            const displaySum = Math.abs(totalSum) < 0.001
              ? Object.values(quarters).some((v) => v !== "" && v !== undefined) ? "0 \u2713" : "0"
              : (totalSum > 0 ? "+" : "") + totalSum.toFixed(1);
            return <span style={{ color }}>Sum: {displaySum}</span>;
          })()}
        </div>
      </div>

      {mode === "quick" ? (
        <>
          {/* Wager selector */}
          <div style={{ marginBottom: "12px" }}>
            <div
              style={{
                fontSize: "11px",
                fontWeight: "bold",
                color: theme.colors.textSecondary,
                textTransform: "uppercase",
                marginBottom: "6px",
              }}
            >
              Wager per player
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: "6px",
              }}
            >
              {WAGER_PRESETS.map((w) => (
                <button
                  key={w}
                  onClick={() => handleWagerSelect(w)}
                  className="touch-optimized"
                  style={{
                    padding: "10px 4px",
                    borderRadius: "10px",
                    border: `2px solid ${wager === w ? theme.colors.primary : theme.colors.border}`,
                    background: wager === w ? theme.colors.primary : theme.colors.paper,
                    color: wager === w ? "white" : theme.colors.textPrimary,
                    fontWeight: "bold",
                    fontSize: "16px",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  {w}Q
                </button>
              ))}
            </div>
            {/* Custom wager input */}
            <div style={{ marginTop: "6px", display: "flex", gap: "6px", alignItems: "center" }}>
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                placeholder="Custom"
                value={wager && !WAGER_PRESETS.includes(wager) ? wager : ""}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10);
                  if (!isNaN(val) && val > 0) {
                    handleWagerSelect(val);
                  } else if (e.target.value === "") {
                    setWager(null);
                  }
                }}
                style={{
                  flex: 1,
                  padding: "8px 12px",
                  fontSize: "14px",
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: "8px",
                  textAlign: "center",
                  outline: "none",
                }}
              />
              <span style={{ fontSize: "12px", color: theme.colors.textSecondary }}>Q</span>
            </div>
          </div>

          {/* Player tap-to-win grid */}
          <div style={{ marginBottom: "12px" }}>
            <div
              style={{
                fontSize: "11px",
                fontWeight: "bold",
                color: theme.colors.textSecondary,
                textTransform: "uppercase",
                marginBottom: "6px",
              }}
            >
              Tap winners
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {players.map((player) => {
                const isWinner = winners.has(player.id);
                const currentVal = parseFloat(quarters[player.id]) || 0;
                const hasValue = quarters[player.id] !== "" && quarters[player.id] !== undefined;

                return (
                  <button
                    key={player.id}
                    onClick={() => handlePlayerTap(player.id)}
                    className="touch-optimized"
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "14px 16px",
                      borderRadius: "12px",
                      border: `2px solid ${isWinner ? "#4CAF50" : !isWinner && hasValue && currentVal < 0 ? "#EF5350" : theme.colors.border}`,
                      background: isWinner
                        ? "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)"
                        : !isWinner && hasValue && currentVal < 0
                          ? "linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%)"
                          : theme.colors.paper,
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                      textAlign: "left",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ fontSize: "20px" }}>
                        {isWinner ? "\uD83C\uDFC6" : "\uD83D\uDC64"}
                      </span>
                      <div>
                        <div style={{ fontWeight: "bold", fontSize: "16px", color: theme.colors.textPrimary }}>
                          {player.name}
                        </div>
                        {scores[player.id] > 0 && (
                          <div style={{ fontSize: "11px", color: theme.colors.textSecondary }}>
                            {scores[player.id]} strokes
                          </div>
                        )}
                      </div>
                    </div>
                    <div
                      style={{
                        fontSize: "22px",
                        fontWeight: "bold",
                        minWidth: "60px",
                        textAlign: "right",
                        color: hasValue
                          ? currentVal > 0 ? "#2E7D32" : currentVal < 0 ? "#C62828" : theme.colors.textSecondary
                          : theme.colors.textSecondary,
                      }}
                    >
                      {hasValue
                        ? (currentVal > 0 ? `+${currentVal}` : currentVal)
                        : "\u2014"}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      ) : (
        /* Manual mode — inline inputs for each player */
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "12px" }}>
          {players.map((player) => {
            const currentVal = parseFloat(quarters[player.id]) || 0;
            const adjustQuarters = (delta) => {
              const base = parseFloat(quarters[player.id]) || 0;
              setQuarters({ ...quarters, [player.id]: (base + delta).toString() });
            };

            return (
              <div
                key={player.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "8px 12px",
                  background: theme.colors.paper,
                  borderRadius: "12px",
                  border: `1px solid ${theme.colors.border}`,
                }}
              >
                <div style={{ flex: 1, fontWeight: "bold", fontSize: "14px" }}>
                  {player.name}
                </div>
                <button
                  onClick={() => adjustQuarters(-1)}
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
                    const val = e.target.value;
                    if (val === "" || val === "-" || /^-?\d*\.?\d*$/.test(val)) {
                      setQuarters({ ...quarters, [player.id]: val });
                    }
                  }}
                  placeholder="0"
                  style={{
                    width: "64px", padding: "8px", fontSize: "18px", fontWeight: "bold",
                    border: `2px solid ${currentVal > 0 ? "#4CAF50" : currentVal < 0 ? "#f44336" : theme.colors.border}`,
                    borderRadius: "10px", textAlign: "center", outline: "none",
                    color: currentVal > 0 ? "#4CAF50" : currentVal < 0 ? "#f44336" : theme.colors.textPrimary,
                  }}
                />
                <button
                  onClick={() => adjustQuarters(1)}
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
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
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
};

export default QuartersPanel;
