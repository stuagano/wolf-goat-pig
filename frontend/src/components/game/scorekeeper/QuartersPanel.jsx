// frontend/src/components/game/scorekeeper/QuartersPanel.jsx
// Extracted from SimpleScorekeeper.jsx — Per-player quarters entry with expand/collapse
import React from "react";
import PropTypes from "prop-types";

/**
 * QuartersPanel — per-player quarters with section header, sum display,
 * expand/collapse per player, and quick-adjust buttons
 */
const QuartersPanel = ({
  players,
  quarters,
  scores,
  expandedPlayers,
  setExpandedPlayers,
  setQuarters,
  theme,
}) => {
  // Auto-balance: compute which players have manual entries vs the auto-fill candidate
  const getAutoBalance = () => {
    const entered = [];
    const empty = [];
    players.forEach((p) => {
      const val = quarters[p.id];
      if (val !== undefined && val !== "" && val !== null) {
        entered.push({ id: p.id, value: parseFloat(val) || 0 });
      } else {
        empty.push(p.id);
      }
    });
    // Auto-fill when exactly one player is empty
    if (empty.length === 1 && entered.length >= 1) {
      const sum = entered.reduce((acc, e) => acc + e.value, 0);
      return { playerId: empty[0], value: -sum };
    }
    return null;
  };

  const autoBalance = getAutoBalance();

  const getDisplayValue = (playerId) => {
    const manual = quarters[playerId];
    if (manual !== undefined && manual !== "" && manual !== null) {
      return { value: parseFloat(manual) || 0, isAuto: false };
    }
    if (autoBalance && autoBalance.playerId === playerId) {
      return { value: autoBalance.value, isAuto: true };
    }
    return { value: 0, isAuto: false };
  };

  // Compute sum including auto-balance
  const totalSum = players.reduce((acc, p) => {
    const { value } = getDisplayValue(p.id);
    return acc + value;
  }, 0);

  return (
    <div style={{ marginBottom: "20px" }}>
      {/* Section Header with Sum */}
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
        <h3
          style={{
            margin: 0,
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            fontSize: "12px",
            fontWeight: "bold",
            color: theme.colors.textSecondary,
          }}
        >
          Enter Quarters
        </h3>
        <div style={{ fontSize: "14px", fontWeight: "bold" }}>
          Sum:{" "}
          {(() => {
            const color = Math.abs(totalSum) < 0.001 ? "#4CAF50" : "#f44336";
            const displaySum =
              Math.abs(totalSum) < 0.001
                ? "0 ✓"
                : (totalSum > 0 ? "+" : "") + totalSum.toFixed(1);
            return <span style={{ color }}>{displaySum}</span>;
          })()}
        </div>
      </div>

      {/* Player Cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {players.map((player, idx) => {
          const { value: currentVal, isAuto } = getDisplayValue(player.id);
          const playerStrokes = scores[player.id];
          const isExpanded = expandedPlayers[idx] || false;

          const adjustQuarters = (delta) => {
            const baseVal = isAuto ? currentVal : (parseFloat(quarters[player.id]) || 0);
            setQuarters({
              ...quarters,
              [player.id]: (baseVal + delta).toString(),
            });
          };

          // Accept auto-balanced value into the real quarters on tap
          const acceptAutoBalance = () => {
            if (isAuto) {
              setQuarters({
                ...quarters,
                [player.id]: currentVal.toString(),
              });
            }
          };

          const toggleExpanded = () => {
            setExpandedPlayers((prev) => ({
              ...prev,
              [idx]: !prev[idx],
            }));
          };

          return (
            <div
              key={player.id}
              style={{
                background: theme.colors.paper,
                borderRadius: "16px",
                border: `2px solid ${isExpanded ? theme.colors.primary : theme.colors.border}`,
                boxShadow: isExpanded
                  ? "0 4px 12px rgba(0,0,0,0.1)"
                  : "0 2px 4px rgba(0,0,0,0.05)",
                overflow: "hidden",
                transition: "all 0.2s ease",
              }}
            >
              {/* Player Header - Always Visible */}
              <div
                onClick={toggleExpanded}
                style={{
                  padding: "16px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  cursor: "pointer",
                  background: isExpanded
                    ? "rgba(0, 0, 0, 0.02)"
                    : "transparent",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                  }}
                >
                  {/* Trophy icon for expanded player */}
                  {isExpanded && (
                    <div
                      style={{
                        background: "rgba(255, 193, 7, 0.1)",
                        padding: "8px",
                        borderRadius: "10px",
                      }}
                    >
                      <span style={{ fontSize: "20px" }}>{"\uD83C\uDFC6"}</span>
                    </div>
                  )}

                  <div>
                    <h3
                      style={{
                        margin: 0,
                        fontSize: "18px",
                        fontWeight: "bold",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      {player.name}
                      {player.handicap != null && (
                        <span
                          style={{
                            background: theme.colors.backgroundSecondary,
                            color: theme.colors.textSecondary,
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "10px",
                            fontWeight: "bold",
                          }}
                        >
                          HDCP {player.handicap}
                        </span>
                      )}
                    </h3>
                    <p
                      style={{
                        margin: "4px 0 0",
                        fontSize: "12px",
                        color: theme.colors.textSecondary,
                        fontWeight: "500",
                      }}
                    >
                      Strokes on this hole: {playerStrokes || 0}
                    </p>
                  </div>
                </div>

                {/* Score Display */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                  }}
                >
                  <div
                    onClick={isAuto ? acceptAutoBalance : undefined}
                    style={{
                      background: isAuto
                        ? "rgba(33, 150, 243, 0.08)"
                        : theme.colors.backgroundSecondary,
                      border: isAuto
                        ? "2px dashed #2196F3"
                        : `1px solid ${theme.colors.border}`,
                      width: "48px",
                      height: "48px",
                      borderRadius: "12px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: isAuto ? "pointer" : "default",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "24px",
                        fontWeight: "bold",
                        fontStyle: isAuto ? "italic" : "normal",
                        color: isAuto
                          ? "#2196F3"
                          : currentVal > 0
                            ? "#4CAF50"
                            : currentVal < 0
                              ? "#f44336"
                              : theme.colors.textPrimary,
                      }}
                    >
                      {currentVal > 0 ? `+${currentVal}` : currentVal || 0}
                    </span>
                  </div>

                  <button
                    style={{
                      width: "32px",
                      height: "32px",
                      borderRadius: "50%",
                      background: theme.colors.backgroundSecondary,
                      border: `1px solid ${theme.colors.border}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      cursor: "pointer",
                    }}
                  >
                    <span style={{ fontSize: "18px" }}>
                      {isExpanded ? "\u25BC" : "\u25B6"}
                    </span>
                  </button>
                </div>
              </div>

              {/* Expanded Controls */}
              {isExpanded && (
                <div style={{ padding: "0 16px 16px" }}>
                  {/* Manual Entry */}
                  <div style={{ marginBottom: "12px" }}>
                    <label
                      style={{
                        display: "block",
                        fontSize: "11px",
                        fontWeight: "bold",
                        color: theme.colors.textSecondary,
                        textTransform: "uppercase",
                        marginBottom: "6px",
                      }}
                    >
                      Manual Entry
                    </label>
                    <input
                      data-testid={`quarters-input-${player.id}`}
                      type="text"
                      inputMode="numeric"
                      pattern="-?[0-9]*\.?[0-9]*"
                      value={quarters[player.id] ?? ""}
                      onChange={(e) => {
                        const val = e.target.value;
                        if (
                          val === "" ||
                          val === "-" ||
                          /^-?\d*\.?\d*$/.test(val)
                        ) {
                          setQuarters({ ...quarters, [player.id]: val });
                        }
                      }}
                      placeholder="0"
                      style={{
                        width: "100%",
                        padding: "14px",
                        fontSize: "24px",
                        fontWeight: "bold",
                        border: `2px solid ${currentVal > 0 ? "#4CAF50" : currentVal < 0 ? "#f44336" : theme.colors.border}`,
                        borderRadius: "12px",
                        textAlign: "center",
                        color:
                          currentVal > 0
                            ? "#4CAF50"
                            : currentVal < 0
                              ? "#f44336"
                              : theme.colors.textPrimary,
                        background:
                          currentVal !== 0
                            ? currentVal > 0
                              ? "rgba(76,175,80,0.05)"
                              : "rgba(244,67,54,0.05)"
                            : "white",
                        outline: "none",
                      }}
                    />
                  </div>

                  {/* Quick Adjust Buttons */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(6, 1fr)",
                      gap: "8px",
                    }}
                  >
                    {[-10, -5, -1, +1, +5, +10].map((delta) => (
                      <button
                        key={delta}
                        onClick={() => adjustQuarters(delta)}
                        className="touch-optimized"
                        style={{
                          padding: "12px 8px",
                          borderRadius: "10px",
                          border: `2px solid ${delta < 0 ? "#EF5350" : "#66BB6A"}`,
                          background:
                            delta < 0
                              ? "linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%)"
                              : "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)",
                          color: delta < 0 ? "#C62828" : "#2E7D32",
                          fontWeight: "bold",
                          fontSize: "14px",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                          boxShadow: "0 2px 4px rgba(0,0,0,0.08)",
                        }}
                        onMouseDown={(e) => {
                          e.target.style.transform = "scale(0.95)";
                        }}
                        onMouseUp={(e) => {
                          e.target.style.transform = "scale(1)";
                        }}
                        onMouseLeave={(e) => {
                          e.target.style.transform = "scale(1)";
                        }}
                      >
                        {delta > 0 ? `+${delta}` : delta}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div
        style={{
          marginTop: "12px",
          display: "flex",
          gap: "8px",
          flexWrap: "wrap",
        }}
      >
        <button
          onClick={() => {
            const allZero = {};
            players.forEach((p) => {
              allZero[p.id] = "0";
            });
            setQuarters(allZero);
          }}
          className="touch-optimized"
          style={{
            padding: "10px 16px",
            borderRadius: "8px",
            fontSize: "13px",
            fontWeight: "bold",
            border: `2px solid ${theme.colors.border}`,
            background: "white",
            cursor: "pointer",
            boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
          }}
        >
          Push (all 0)
        </button>
        <button
          onClick={() => {
            const cleared = {};
            players.forEach((p) => {
              cleared[p.id] = "";
            });
            setQuarters(cleared);
          }}
          className="touch-optimized"
          style={{
            padding: "10px 16px",
            borderRadius: "8px",
            fontSize: "13px",
            fontWeight: "bold",
            border: `2px solid ${theme.colors.border}`,
            background: "white",
            cursor: "pointer",
            boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
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
