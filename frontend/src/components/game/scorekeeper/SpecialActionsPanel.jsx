// frontend/src/components/game/scorekeeper/SpecialActionsPanel.jsx
// Float & Option tracking — collapsible special-actions section.
// JSX moved verbatim from SimpleScorekeeper.jsx.

import React from "react";
import PropTypes from "prop-types";

const SpecialActionsPanel = ({
  theme,
  players,
  playerStandings,
  floatInvokedBy,
  setFloatInvokedBy,
  optionInvokedBy,
  setOptionInvokedBy,
  showSpecialActions,
  setShowSpecialActions,
}) => {
  return (
    <>
      {/* Float & Option Tracking - Collapsed by default */}
      <div
        style={{
          background: theme.colors.paper,
          borderRadius: "8px",
          marginBottom: "12px",
          border: `1px solid ${theme.colors.border}`,
          overflow: "hidden",
        }}
      >
        <div
          onClick={() => setShowSpecialActions(!showSpecialActions)}
          style={{
            padding: "10px 12px",
            fontSize: "13px",
            fontWeight: "bold",
            color: theme.colors.textSecondary,
            cursor: "pointer",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: theme.colors.backgroundSecondary,
          }}
        >
          <span>
            Special Actions
            {(floatInvokedBy || optionInvokedBy) && (
              <span
                style={{
                  marginLeft: "8px",
                  color: theme.colors.primary,
                  fontSize: "12px",
                }}
              >
                (active)
              </span>
            )}
          </span>
          <span style={{ fontSize: "14px" }}>
            {showSpecialActions ? "▼" : "▶"}
          </span>
        </div>

        {showSpecialActions && (
          <div style={{ padding: "12px" }}>
            {/* Float Selection */}
            <div style={{ marginBottom: "12px" }}>
              <div
                style={{
                  fontSize: "13px",
                  fontWeight: "bold",
                  marginBottom: "6px",
                }}
              >
                Float:{" "}
                <span
                  style={{
                    fontWeight: "normal",
                    color: theme.colors.textSecondary,
                  }}
                >
                  (one-time per player)
                </span>
              </div>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {players.map((player) => {
                  const hasUsedFloat =
                    playerStandings[player.id]?.floatCount >= 1;
                  return (
                    <button
                      key={player.id}
                      onClick={() =>
                        setFloatInvokedBy(
                          floatInvokedBy === player.id ? null : player.id,
                        )
                      }
                      className="touch-optimized"
                      disabled={hasUsedFloat}
                      style={{
                        padding: "6px 12px",
                        fontSize: "13px",
                        border: `2px solid ${floatInvokedBy === player.id ? theme.colors.primary : hasUsedFloat ? "#ccc" : theme.colors.border}`,
                        borderRadius: "6px",
                        background:
                          floatInvokedBy === player.id
                            ? theme.colors.primary
                            : hasUsedFloat
                              ? "#f5f5f5"
                              : "white",
                        color:
                          floatInvokedBy === player.id
                            ? "white"
                            : hasUsedFloat
                              ? "#999"
                              : theme.colors.text,
                        cursor: hasUsedFloat ? "not-allowed" : "pointer",
                        opacity: hasUsedFloat ? 0.6 : 1,
                      }}
                    >
                      {player.name.split(" ")[0]}
                      {hasUsedFloat && " ✓"}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Option Selection */}
            <div>
              <div
                style={{
                  fontSize: "13px",
                  fontWeight: "bold",
                  marginBottom: "6px",
                }}
              >
                Option Triggered:
              </div>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {players.map((player) => (
                  <button
                    key={player.id}
                    onClick={() =>
                      setOptionInvokedBy(
                        optionInvokedBy === player.id ? null : player.id,
                      )
                    }
                    className="touch-optimized"
                    style={{
                      padding: "6px 12px",
                      fontSize: "13px",
                      border: `2px solid ${optionInvokedBy === player.id ? theme.colors.warning : theme.colors.border}`,
                      borderRadius: "6px",
                      background:
                        optionInvokedBy === player.id
                          ? theme.colors.warning
                          : "white",
                      color:
                        optionInvokedBy === player.id
                          ? "white"
                          : theme.colors.text,
                      cursor: "pointer",
                    }}
                  >
                    {player.name.split(" ")[0]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

SpecialActionsPanel.propTypes = {
  theme: PropTypes.object.isRequired,
  players: PropTypes.array.isRequired,
  playerStandings: PropTypes.object.isRequired,
  floatInvokedBy: PropTypes.string,
  setFloatInvokedBy: PropTypes.func.isRequired,
  optionInvokedBy: PropTypes.string,
  setOptionInvokedBy: PropTypes.func.isRequired,
  showSpecialActions: PropTypes.bool.isRequired,
  setShowSpecialActions: PropTypes.func.isRequired,
};

export default SpecialActionsPanel;
