// frontend/src/components/game/scorekeeper/ScorecardSection.jsx
// Sticky golf-style scorecard + quick hole-navigation chips + undo-last-hole.
// JSX moved verbatim from SimpleScorekeeper.jsx (incl. the inline undo handler).

import React from "react";
import PropTypes from "prop-types";
import Scorecard from "../Scorecard";

const ScorecardSection = ({
  theme,
  players,
  localPlayers,
  holeHistory,
  setHoleHistory,
  setPlayerStandings,
  currentHole,
  setCurrentHole,
  editingHole,
  scorecardCourseHoles,
  strokeAllocation,
  isEditingCompleteGame,
  handleEditHoleFromScorecard,
  jumpToHole,
  resetHole,
}) => {
  return (
    <>
      {/* Golf-Style Scorecard at Top */}
      <div
        style={{
          marginBottom: "20px",
          position: "sticky",
          top: "0",
          zIndex: 10,
        }}
      >
        <Scorecard
          players={localPlayers}
          holeHistory={holeHistory}
          currentHole={currentHole}
          onEditHole={handleEditHoleFromScorecard}
          courseHoles={scorecardCourseHoles}
          strokeAllocation={strokeAllocation}
          isEditingCompleteGame={isEditingCompleteGame}
        />

        {/* Quick Hole Navigation - Shows completed holes as clickable chips */}
        {holeHistory.length > 0 && (
          <div
            style={{
              marginTop: "8px",
              padding: "8px",
              background: theme.colors.backgroundSecondary,
              borderRadius: "8px",
            }}
          >
            <div
              style={{
                fontSize: "11px",
                color: theme.colors.textSecondary,
                marginBottom: "6px",
              }}
            >
              Tap any hole to edit:
            </div>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
              {Array.from(
                { length: Math.max(currentHole - 1, holeHistory.length) },
                (_, i) => i + 1,
              ).map((hole) => {
                const holeData = holeHistory.find((h) => h.hole === hole);
                const isEditing = editingHole === hole;
                return (
                  <button
                    key={hole}
                    onClick={() => jumpToHole(hole)}
                    className="touch-optimized"
                    style={{
                      width: "32px",
                      height: "32px",
                      flexShrink: 0,
                      borderRadius: "6px",
                      border: isEditing
                        ? `2px solid ${theme.colors.warning}`
                        : holeData
                          ? `1px solid ${theme.colors.primary}`
                          : `1px solid ${theme.colors.border}`,
                      background: isEditing
                        ? theme.colors.warning
                        : holeData
                          ? "white"
                          : "#f5f5f5",
                      color: isEditing
                        ? "white"
                        : holeData
                          ? theme.colors.primary
                          : theme.colors.textSecondary,
                      fontSize: "13px",
                      fontWeight: "bold",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {hole}
                  </button>
                );
              })}
            </div>

            {/* Undo last hole button */}
            <button
              onClick={() => {
                if (
                  window.confirm(
                    `Undo hole ${holeHistory[holeHistory.length - 1].hole}? This will remove all data for that hole.`,
                  )
                ) {
                  const lastHole = holeHistory[holeHistory.length - 1];
                  setHoleHistory((prev) => prev.slice(0, -1));
                  setCurrentHole(lastHole.hole);
                  const newStandings = { ...playerStandings };
                  players.forEach((p) => {
                    const delta = lastHole.points_delta?.[p.id] || 0;
                    if (newStandings[p.id]) {
                      newStandings[p.id] = {
                        ...newStandings[p.id],
                        quarters: (newStandings[p.id].quarters || 0) - delta,
                      };
                    }
                  });
                  setPlayerStandings(newStandings);
                  resetHole();
                }
              }}
              className="touch-optimized"
              style={{
                marginTop: "8px",
                padding: "6px 12px",
                fontSize: "12px",
                border: "1px solid #f44336",
                borderRadius: "6px",
                background: "white",
                color: "#f44336",
                cursor: "pointer",
              }}
            >
              ↩️ Undo Last Hole
            </button>
          </div>
        )}

      </div>
    </>
  );
};

ScorecardSection.propTypes = {
  theme: PropTypes.object.isRequired,
  players: PropTypes.array.isRequired,
  localPlayers: PropTypes.array.isRequired,
  holeHistory: PropTypes.array.isRequired,
  setHoleHistory: PropTypes.func.isRequired,
  setPlayerStandings: PropTypes.func.isRequired,
  currentHole: PropTypes.number.isRequired,
  setCurrentHole: PropTypes.func.isRequired,
  editingHole: PropTypes.number,
  scorecardCourseHoles: PropTypes.array,
  strokeAllocation: PropTypes.object,
  isEditingCompleteGame: PropTypes.bool.isRequired,
  handleEditHoleFromScorecard: PropTypes.func.isRequired,
  jumpToHole: PropTypes.func.isRequired,
  resetHole: PropTypes.func.isRequired,
};

export default ScorecardSection;
