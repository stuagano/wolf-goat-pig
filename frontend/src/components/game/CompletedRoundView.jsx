import React, { useState } from "react";
import PropTypes from "prop-types";
import GameCompletionView from "./GameCompletionView";
import ScorecardPhotoButton from "./ScorecardPhotoButton";
import { apiConfig } from "../../config/api.config";
import { fetchJson } from "../../services/fetchJson";
import { useAuthenticatedFetch } from "../../hooks/useAuthenticatedFetch";
import useRoundCard from "../../hooks/useRoundCard";

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
  const { card, refresh } = useRoundCard(gameId);
  // Bumped after an upload to remount the photo button so it re-reads the image.
  const [photoVersion, setPhotoVersion] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const handleCardPhoto = async (event) => {
    const input = event.target;
    const file = input.files?.[0];
    // Reset so picking the same file again (a retry) still fires change.
    input.value = "";
    if (!file) return;
    const body = new FormData();
    body.append("file", file);
    setUploadError(null);
    setUploading(true);
    try {
      const res = await authenticatedFetch(`${API_URL}/games/${gameId}/scorecard-photo`, { method: "PUT", body });
      if (!res.ok) {
        const data = (await res.json?.().catch(() => ({}))) || {};
        throw new Error(data.detail || `Upload failed (${res.status})`);
      }
      setPhotoVersion((v) => v + 1);
      refresh();
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setUploading(false);
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
      {card?.can_edit && (
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
          {uploading ? "Uploading…" : card.has_photo ? "📷 Replace card photo" : "📷 Add the card photo"}
          <input type="file" accept="image/*" hidden disabled={uploading} onChange={handleCardPhoto} />
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
