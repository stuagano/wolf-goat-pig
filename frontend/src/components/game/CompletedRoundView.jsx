import React from "react";
import PropTypes from "prop-types";
import GameCompletionView from "./GameCompletionView";
import ScorecardPhotoButton from "./ScorecardPhotoButton";
import { apiConfig } from "../../config/api.config";
import { fetchJson } from "../../services/fetchJson";

const API_URL = apiConfig.baseUrl;

/**
 * Read-only view of a finished round: final standings, the "mark complete"
 * save, and the scorecard photo. SimpleScorekeeper decides when to show it
 * (a live round can finish in-session), so standings come in as props.
 */
const CompletedRoundView = ({
  gameId,
  players,
  playerStandings,
  holeHistory,
  courseHoles,
  strokeAllocation,
  isMarkedComplete,
  onMarkedComplete,
  onEditScores,
}) => {
  // Mark the game complete in the database
  const handleMarkComplete = async () => {
    if (!gameId) {
      console.error("No game ID available");
      return;
    }

    try {
      await fetchJson(`${API_URL}/games/${gameId}/complete`, {
        method: "POST",
      });
      onMarkedComplete();
    } catch (error) {
      console.error("Error marking game complete:", error);
      alert(`Failed to save game: ${error.message}`);
    }
  };

  return (
    <>
      <GameCompletionView
        players={players}
        playerStandings={playerStandings}
        holeHistory={holeHistory}
        onNewGame={() => {
          // Reset to start a new game
          window.location.reload();
        }}
        onEditScores={onEditScores}
        onMarkComplete={handleMarkComplete}
        isCompleted={isMarkedComplete}
        courseHoles={courseHoles}
        strokeAllocation={strokeAllocation}
      />
      {gameId && <ScorecardPhotoButton gameId={gameId} />}
    </>
  );
};

CompletedRoundView.propTypes = {
  gameId: PropTypes.string,
  players: PropTypes.array.isRequired,
  playerStandings: PropTypes.object,
  holeHistory: PropTypes.array,
  courseHoles: PropTypes.array,
  strokeAllocation: PropTypes.object,
  isMarkedComplete: PropTypes.bool,
  onMarkedComplete: PropTypes.func.isRequired,
  onEditScores: PropTypes.func.isRequired,
};

export default CompletedRoundView;
