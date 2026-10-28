import React, { useState } from "react";
import PropTypes from "prop-types";
import GameCompletionView from "./GameCompletionView";
import RoundCardReview from "./RoundCardReview";
import EditHoleModal from "./EditHoleModal";
import { SyncStatusBanner } from "../ui/SyncStatusIndicator";
import { apiConfig } from "../../config/api.config";
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
  onSaveHole,
  summary,
}) => {
  const authenticatedFetch = useAuthenticatedFetch();
  // { has_photo, can_edit, edited_by, edited_at } — null when signed out or unknown.
  const { card, refresh } = useRoundCard(gameId);
  // Bumped after an upload to remount the photo button so it re-reads the image.
  const [photoVersion, setPhotoVersion] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [reviewing, setReviewing] = useState(false);
  const [editingHole, setEditingHole] = useState(null);

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
      const res = await authenticatedFetch(`${API_URL}/games/${gameId}/complete`, {
        method: "POST",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Save failed (${res.status})`);
      }
      onMarkedComplete();
    } catch (error) {
      console.error("Error marking game complete:", error);
      alert(`Failed to save game: ${error.message}`);
    }
  };

  const scores = (
    <>
      {!summary && <SyncStatusBanner />}
      {summary && <>
        <h1>Accepted round scores</h1>
        <p>{summary.played_on || summary.raw_date || 'Date not recorded'} · {summary.course_name || 'Course not recorded'}</p>
        <p>Revision {summary.revision} · {summary.detail_coverage?.replaceAll('_', ' ') || 'Detail not recorded'}</p>
        {!summary.score_eligible && <p>Incomplete or retracted results — not included in score standings.</p>}
        <ul>{players.map(player => <li key={player.id}><span>{player.name || 'Unnamed participant'}</span>: {player.quarters == null ? 'Not recorded' : `${player.quarters > 0 ? '+' : ''}${player.quarters}`}</li>)}</ul>
        {summary.detail_coverage === 'partial' && <p>Partial recorded holes only; these do not imply a complete round.</p>}
        {holeHistory.length === 0 ? <p>Hole detail: Not recorded</p> : <table>
          <caption>Recorded hole detail (final totals above remain authoritative)</caption>
          <thead><tr><th>Hole</th>{players.map(p => <th key={p.id}>{p.name}</th>)}</tr></thead>
          <tbody>{holeHistory.map(h => <tr key={h.hole}><th>{h.hole}</th>{players.map(p => <td key={p.id}>{h.points_delta?.[p.id] ?? 'Not recorded'}</td>)}</tr>)}</tbody>
        </table>}
        {Object.entries(summary.detail_discrepancies || {}).map(([slot, value]) => <p key={slot} role="status">{players.find(p => p.id === slot)?.name || slot}: accepted {value.accepted ?? 'Not recorded'}; computed detail {value.computed_detail ?? 'Not recorded'} — requires review.</p>)}
        {card?.can_edit && <button onClick={onEditScores}>Fill in holes / edit recorded detail</button>}
        <button onClick={() => navigator.clipboard.writeText(`${window.location.origin}/game/${encodeURIComponent(gameId)}`).catch(() => setUploadError('Could not copy link'))}>Copy game link</button>
      </>}
      {!reviewing && card?.can_edit && onSaveHole && (
        <button type="button" onClick={() => setReviewing(true)} style={{ padding: '10px 16px', marginBottom: '12px', borderRadius: '8px', background: '#216b45', color: 'white' }}>Edit scores</button>
      )}
      {reviewing && card?.can_edit && onSaveHole && (
        <div>
          <p>Select a hole to correct its strokes or quarters.</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
            {holeHistory.map((hole) => (
              <button key={hole.hole} type="button" disabled={editingHole !== null} onClick={() => setEditingHole(hole)} aria-label={`Edit hole ${hole.hole}`} style={{ padding: '10px', border: '1px solid #527b63', borderRadius: '6px' }}>{hole.hole}</button>
            ))}
            <button type="button" disabled={editingHole !== null} onClick={() => setReviewing(false)}>Done editing</button>
          </div>
          <EditHoleModal embedded isOpen={editingHole !== null} holeData={editingHole} players={players} onClose={() => setEditingHole(null)} onSave={onSaveHole} />
        </div>
      )}
      {!summary && <GameCompletionView
        players={players}
        playerStandings={playerStandings}
        holeHistory={holeHistory}
        onNewGame={() => {
          // Reset to start a new game
          window.location.reload();
        }}
        onEditScores={card?.can_edit && !onSaveHole ? onEditScores : undefined}
        compact
        onMarkComplete={handleMarkComplete}
        isCompleted={isMarkedComplete}
        courseHoles={courseHoles}
        strokeAllocation={strokeAllocation}
      />}
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

  return gameId ? <RoundCardReview gameId={gameId} photoVersion={photoVersion} players={players} holeHistory={holeHistory} acceptedTotals={summary ? Object.fromEntries(players.map(p => [p.id, p.quarters])) : undefined} detailCoverage={summary?.detail_coverage} uploading={uploading}>{scores}</RoundCardReview> : scores;
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
  onEditScores: PropTypes.func,
  onSaveHole: PropTypes.func,
};

export default CompletedRoundView;
