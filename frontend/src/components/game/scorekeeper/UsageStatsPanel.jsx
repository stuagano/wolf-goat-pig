// frontend/src/components/game/scorekeeper/UsageStatsPanel.jsx
// Usage statistics (solo/float/option counts, rule compliance) and the
// hole 13-16 solo-requirement warning banner.
// JSX moved verbatim from SimpleScorekeeper.jsx (outer guards included).

import React from "react";
import PropTypes from "prop-types";

const UsageStatsPanel = ({
  theme,
  players,
  playerStandings,
  currentHole,
  holeHistory,
  showUsageStats,
  setShowUsageStats,
}) => {
  return (
    <>
      {/* Usage Statistics - Collapsible */}
      {holeHistory.length > 0 && (
        <div
          style={{
            background: theme.colors.paper,
            borderRadius: "8px",
            overflow: "hidden",
            marginBottom: "12px",
            border: `1px solid ${theme.colors.border}`,
          }}
        >
          <div
            onClick={() => setShowUsageStats(!showUsageStats)}
            style={{
              padding: "10px 12px",
              background: theme.colors.backgroundSecondary,
              fontSize: "13px",
              fontWeight: "bold",
              color: theme.colors.textPrimary,
              cursor: "pointer",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>Rule Compliance & Usage</span>
            <span style={{ fontSize: "16px" }}>
              {showUsageStats ? "▼" : "▶"}
            </span>
          </div>

          {showUsageStats && (
            <div style={{ padding: "12px" }}>
              {Object.values(playerStandings).map((player, idx) => {
                const soloCount = player.soloCount || 0;
                const floatCount = player.floatCount || 0;
                const optionCount = player.optionCount || 0;

                // Rule requirements
                const soloRequired = 1; // Everyone must go solo at least once
                const floatAvailable = 1; // One float per player per round
                const soloMet = soloCount >= soloRequired;
                const floatUsed = floatCount >= floatAvailable;

                return (
                  <div
                    key={idx}
                    style={{
                      padding: "12px",
                      borderBottom:
                        idx < Object.values(playerStandings).length - 1
                          ? `1px solid ${theme.colors.border}`
                          : "none",
                      background:
                        idx % 2 === 0 ? "white" : theme.colors.background,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "8px",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "16px",
                          fontWeight: "bold",
                          color: theme.colors.textPrimary,
                          flex: 1,
                        }}
                      >
                        {player.name}
                      </div>
                      <div
                        style={{
                          display: "flex",
                          gap: "16px",
                          fontSize: "14px",
                          color: theme.colors.textSecondary,
                        }}
                      >
                        {/* Solo Count */}
                        <div style={{ textAlign: "center" }}>
                          <div
                            style={{
                              fontSize: "20px",
                              fontWeight: "bold",
                              color: soloMet ? "#4CAF50" : "#f44336",
                            }}
                          >
                            {soloCount}/{soloRequired}
                          </div>
                          <div style={{ fontSize: "11px" }}>Solo</div>
                          {!soloMet && (
                            <div
                              style={{
                                fontSize: "9px",
                                color: "#f44336",
                                fontWeight: "bold",
                                marginTop: "2px",
                              }}
                            >
                              Required
                            </div>
                          )}
                        </div>

                        {/* Float Count */}
                        <div style={{ textAlign: "center" }}>
                          <div
                            style={{
                              fontSize: "20px",
                              fontWeight: "bold",
                              color: floatUsed
                                ? "#9E9E9E"
                                : theme.colors.primary,
                            }}
                          >
                            {floatCount}/{floatAvailable}
                          </div>
                          <div style={{ fontSize: "11px" }}>Float</div>
                          {floatUsed && (
                            <div
                              style={{
                                fontSize: "9px",
                                color: "#9E9E9E",
                                marginTop: "2px",
                              }}
                            >
                              Used
                            </div>
                          )}
                        </div>

                        {/* Option Count (informational) */}
                        <div style={{ textAlign: "center" }}>
                          <div
                            style={{
                              fontSize: "20px",
                              fontWeight: "bold",
                              color: theme.colors.warning,
                            }}
                          >
                            {optionCount}
                          </div>
                          <div style={{ fontSize: "11px" }}>Option</div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Rule Summary */}
              <div
                style={{
                  padding: "8px 12px",
                  background: "#f9fafb",
                  borderTop: `1px solid ${theme.colors.border}`,
                  fontSize: "10px",
                  color: theme.colors.textSecondary,
                }}
              >
                <div>• Solo: Must go solo once (by hole 16)</div>
                <div>• Float: One-time use per player</div>
                <div>• Option: Auto when captain furthest down</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Solo Requirement Warning Banner - Phase 3 */}
      {players.length === 4 &&
        currentHole >= 13 &&
        currentHole <= 16 &&
        (() => {
          const playersNeedingSolo = Object.values(playerStandings).filter(
            (p) => (p.soloCount || 0) === 0,
          );
          if (playersNeedingSolo.length > 0) {
            return (
              <div
                style={{
                  background:
                    "linear-gradient(135deg, #FF6B6B 0%, #FFB347 100%)",
                  padding: "20px",
                  borderRadius: "16px",
                  marginBottom: "20px",
                  boxShadow: "0 4px 12px rgba(255, 107, 107, 0.3)",
                  border: "3px solid #FF4757",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    marginBottom: "12px",
                  }}
                >
                  <div style={{ fontSize: "32px" }}>⚠️</div>
                  <div>
                    <div
                      style={{
                        fontSize: "20px",
                        fontWeight: "bold",
                        color: "white",
                        marginBottom: "4px",
                      }}
                    >
                      Solo Requirement Alert!
                    </div>
                    <div
                      style={{
                        fontSize: "14px",
                        color: "rgba(255, 255, 255, 0.95)",
                      }}
                    >
                      {currentHole === 16
                        ? "🚨 LAST CHANCE - Hoepfinger starts next hole!"
                        : `Only ${17 - currentHole} hole${17 - currentHole === 1 ? "" : "s"} until Hoepfinger`}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    background: "rgba(255, 255, 255, 0.95)",
                    padding: "12px",
                    borderRadius: "8px",
                    marginBottom: "8px",
                  }}
                >
                  <div
                    style={{
                      fontSize: "14px",
                      fontWeight: "bold",
                      color: "#d32f2f",
                      marginBottom: "8px",
                    }}
                  >
                    Players who MUST go solo:
                  </div>
                  <div
                    style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}
                  >
                    {playersNeedingSolo.map((player, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "#FF4757",
                          color: "white",
                          padding: "6px 12px",
                          borderRadius: "20px",
                          fontSize: "14px",
                          fontWeight: "bold",
                          boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
                        }}
                      >
                        {player.name}
                      </div>
                    ))}
                  </div>
                </div>

                <div
                  style={{
                    fontSize: "12px",
                    color: "white",
                    fontWeight: "bold",
                    opacity: 0.9,
                  }}
                >
                  📖 Rule: Each player must go solo at least once in the first
                  16 holes
                </div>
              </div>
            );
          }
          return null;
        })()}
    </>
  );
};

UsageStatsPanel.propTypes = {
  theme: PropTypes.object.isRequired,
  players: PropTypes.array.isRequired,
  playerStandings: PropTypes.object.isRequired,
  currentHole: PropTypes.number.isRequired,
  holeHistory: PropTypes.array.isRequired,
  showUsageStats: PropTypes.bool.isRequired,
  setShowUsageStats: PropTypes.func.isRequired,
};

export default UsageStatsPanel;
