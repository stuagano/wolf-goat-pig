// frontend/src/components/game/scorekeeper/AnalysisPanels.jsx
// Collapsible analysis sections: real-time betting odds + shot recommendations.
// JSX moved verbatim from SimpleScorekeeper.jsx.

import React from "react";
import PropTypes from "prop-types";
import BettingOddsPanel from "../../betting/BettingOddsPanel";
import ShotAnalysisWidget from "../ShotAnalysisWidget";

const AnalysisPanels = ({
  theme,
  players,
  scores,
  captain,
  team1,
  teamMode,
  currentWager,
  currentHole,
  holePar,
  playerStandings,
  courseData,
  showBettingOdds,
  setShowBettingOdds,
  showShotAnalysis,
  setShowShotAnalysis,
}) => {
  return (
    <>
      {/* Betting Odds - Collapsible */}
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
          onClick={() => setShowBettingOdds(!showBettingOdds)}
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
          <span>📊 Real-Time Odds</span>
          <span style={{ fontSize: "14px" }}>
            {showBettingOdds ? "▼" : "▶"}
          </span>
        </div>
        {showBettingOdds && (
          <div style={{ padding: "12px" }}>
            <BettingOddsPanel
              gameState={{
                active: true,
                current_hole: currentHole,
                players: players.map((p) => ({
                  ...p,
                  current_score: scores[p.id] || 0,
                  shots_taken: scores[p.id] || 0, // Simplified
                  distance_to_pin: 0, // Would need manual entry or GPS
                  lie_type: "fairway",
                  is_captain: p.id === captain,
                  team_id: team1.includes(p.id)
                    ? "team1"
                    : teamMode === "partners"
                      ? "team2"
                      : null,
                })),
                teams: { type: teamMode },
                current_wager: currentWager,
                is_doubled: false, // Need to track this from betting events
                current_hole_par: holePar || 4,
              }}
              onBettingAction={() => {
                // Integration with actual betting state would go here
              }}
            />
          </div>
        )}
      </div>

      {/* Shot Analysis - Collapsible */}
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
          onClick={() => setShowShotAnalysis(!showShotAnalysis)}
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
          <span>🎯 Shot Recommendations</span>
          <span style={{ fontSize: "14px" }}>
            {showShotAnalysis ? "▼" : "▶"}
          </span>
        </div>
        {showShotAnalysis && (
          <div style={{ padding: "12px" }}>
            <ShotAnalysisWidget
              holeNumber={currentHole}
              players={players}
              captainId={captain}
              teamMode={teamMode}
              playerStandings={playerStandings}
              initialDistance={
                courseData?.holes?.find((h) => h.hole_number === currentHole)
                  ?.yards || 150
              }
            />
          </div>
        )}
      </div>
    </>
  );
};

AnalysisPanels.propTypes = {
  theme: PropTypes.object.isRequired,
  players: PropTypes.array.isRequired,
  scores: PropTypes.object.isRequired,
  captain: PropTypes.string,
  team1: PropTypes.array.isRequired,
  teamMode: PropTypes.string.isRequired,
  currentWager: PropTypes.number.isRequired,
  currentHole: PropTypes.number.isRequired,
  holePar: PropTypes.number,
  playerStandings: PropTypes.object.isRequired,
  courseData: PropTypes.object,
  showBettingOdds: PropTypes.bool.isRequired,
  setShowBettingOdds: PropTypes.func.isRequired,
  showShotAnalysis: PropTypes.bool.isRequired,
  setShowShotAnalysis: PropTypes.func.isRequired,
};

export default AnalysisPanels;
