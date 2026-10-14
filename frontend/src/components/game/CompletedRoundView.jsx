import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import GameCompletionView from "./GameCompletionView";
import ScorecardPhotoButton from "./ScorecardPhotoButton";
import { apiConfig } from "../../config/api.config";
import { fetchJson } from "../../services/fetchJson";
import { useAuthenticatedFetch } from "../../hooks/useAuthenticatedFetch";

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
  const authenticatedFetch = useAuthenticatedFetch();
  // { has_photo, can_edit, edited_by, edited_at } — null when signed out or unknown.
  const [card, setCard] = useState(null);
  // Bumped after an upload: re-reads /card and remounts the photo button.
  const [photoVersion, setPhotoVersion] = useState(0);
  const [uploadError, setUploadError] = useState(null);

  useEffect(() => {
    if (!gameId) return;
    authenticatedFetch(`${API_URL}/games/${gameId}/card`)
      .then((res) => (res.ok ? res.json() : null))
      .then(setCard)
      .catch(() => setCard(null)); // signed out: view-only
  }, [gameId, authenticatedFetch, photoVersion]);

  const handleCardPhoto = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const body = new FormData();
    body.append("file", file);
    setUploadError(null);
    try {
      const res = await authenticatedFetch(`${API_URL}/games/${gameId}/scorecard-photo`, { method: "PUT", body });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      setPhotoVersion((v) => v + 1);
    } catch (error) {
      setUploadError(error.message);
    }
  };

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
      {gameId && <ScorecardPhotoButton key={photoVersion} gameId={gameId} />}
      {card?.can_edit && !card.has_photo && (
        <label
          style={{
            display: "inline-block",
            padding: "12px 24px",
            fontSize: "16px",
            fontWeight: "bold",
            borderRadius: "8px",
            border: "2px solid #1976d2",
            background: "white",
            color: "#1976d2",
            cursor: "pointer",
          }}
        >
          📷 Add the card photo
          <input type="file" accept="image/*" hidden onChange={handleCardPhoto} />
        </label>
      )}
      {uploadError && (
        <p role="alert" style={{ color: "#b91c1c" }}>
          {uploadError}
        </p>
      )}
      {card?.edited_by && (
        <p style={{ color: "#6b7280", fontSize: "14px" }}>
          Card edited by {card.edited_by} · {new Date(card.edited_at).toLocaleDateString()}
        </p>
      )}
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
