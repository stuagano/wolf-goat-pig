// frontend/src/components/game/scorekeeper/OptionalEntryPanels.jsx
// Optional entry sections: golf scores, Ask Commissioner, hole notes.
// JSX moved verbatim from SimpleScorekeeper.jsx — collapsible panels only;
// all state lives in the parent.

import React from "react";
import PropTypes from "prop-types";
import CommissionerChat from "../CommissionerChat";

const OptionalEntryPanels = ({
  theme,
  players,
  scores,
  handleScoreChange,
  currentHole,
  playerStandings,
  holeNotes,
  setHoleNotes,
  showGolfScores,
  setShowGolfScores,
  showCommissioner,
  setShowCommissioner,
  showNotes,
  setShowNotes,
}) => {
  return (
    <>
      {/* Scores (Optional) - Collapsible */}
      <div style={{ marginBottom: "20px" }}>
        <div
          onClick={() => setShowGolfScores(!showGolfScores)}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "12px 16px",
            background: theme.colors.paper,
            borderRadius: "8px",
            cursor: "pointer",
            border: `2px solid ${theme.colors.border}`,
            boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
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
            Golf Scores{" "}
            <span
              style={{ fontWeight: "normal", fontSize: "11px", opacity: 0.7 }}
            >
              (optional)
            </span>
          </h3>
          <button
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: theme.colors.backgroundSecondary,
              border: `1px solid ${theme.colors.border}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
            }}
          >
            <span style={{ fontSize: "16px" }}>
              {showGolfScores ? "▼" : "▶"}
            </span>
          </button>
        </div>
        {showGolfScores && (
          <div
            style={{
              marginTop: "12px",
              padding: "16px",
              background: theme.colors.paper,
              borderRadius: "8px",
              border: `2px solid ${theme.colors.border}`,
            }}
          >
            <div
              style={{
                fontSize: "12px",
                color: theme.colors.textSecondary,
                marginBottom: "12px",
              }}
            >
              Enter strokes for tracking only
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: `repeat(${Math.min(2, Math.ceil(players.length / 3))}, 1fr)`,
                gap: "12px",
              }}
            >
              {players.map((player) => (
                <div
                  key={player.id}
                  style={{ display: "flex", alignItems: "center", gap: "8px" }}
                >
                  <label style={{ flex: 1, fontWeight: "bold" }}>
                    {player.name}:
                  </label>
                  <Input
                    data-testid={`score-input-${player.id}`}
                    type="number"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    min="0"
                    max="15"
                    value={scores[player.id] || ""}
                    onChange={(e) =>
                      handleScoreChange(player.id, e.target.value)
                    }
                    variant="inline"
                    inputStyle={{
                      width: "60px",
                      padding: "8px",
                      fontSize: "16px",
                      border: `2px solid ${theme.colors.border}`,
                      borderRadius: "4px",
                      textAlign: "center",
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Ask Commissioner Section - Collapsible */}
      <div style={{ marginBottom: "20px" }}>
        <div
          onClick={() => setShowCommissioner(!showCommissioner)}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "12px 16px",
            background: theme.colors.paper,
            borderRadius: "8px",
            cursor: "pointer",
            border: `2px solid ${theme.colors.border}`,
            boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
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
            Ask Commissioner{" "}
            <span
              style={{ fontWeight: "normal", fontSize: "11px", opacity: 0.7 }}
            >
              (optional)
            </span>
          </h3>
          <button
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: theme.colors.backgroundSecondary,
              border: `1px solid ${theme.colors.border}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
            }}
          >
            <span style={{ fontSize: "16px" }}>
              {showCommissioner ? "▼" : "▶"}
            </span>
          </button>
        </div>
        {showCommissioner && (
          <div
            style={{
              marginTop: "12px",
              padding: "16px",
              background: theme.colors.paper,
              borderRadius: "8px",
              border: `2px solid ${theme.colors.border}`,
            }}
          >
            <CommissionerChat
              inline={true}
              gameState={{
                players,
                current_hole: currentHole,
                standings: playerStandings,
              }}
              onSaveToNotes={(text) => {
                // Append commissioner ruling to notes with timestamp
                const timestamp = new Date().toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                });
                const ruling = `[${timestamp}] Commissioner: ${text}`;
                setHoleNotes((prev) =>
                  prev ? `${prev}\n\n${ruling}` : ruling,
                );
              }}
            />
          </div>
        )}
      </div>

      {/* Hole Notes (Optional) - Collapsible */}
      <div style={{ marginBottom: "20px" }}>
        <div
          onClick={() => setShowNotes(!showNotes)}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "12px 16px",
            background: theme.colors.paper,
            borderRadius: "8px",
            cursor: "pointer",
            border: `2px solid ${theme.colors.border}`,
            boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
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
            Notes{" "}
            <span
              style={{ fontWeight: "normal", fontSize: "11px", opacity: 0.7 }}
            >
              (optional)
            </span>
            {!showNotes && holeNotes && (
              <span
                style={{
                  marginLeft: "8px",
                  fontSize: "11px",
                  color: theme.colors.primary,
                  fontWeight: "bold",
                }}
              >
                ●
              </span>
            )}
          </h3>
          <button
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: theme.colors.backgroundSecondary,
              border: `1px solid ${theme.colors.border}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
            }}
          >
            <span style={{ fontSize: "16px" }}>{showNotes ? "▼" : "▶"}</span>
          </button>
        </div>
        {showNotes && (
          <div
            style={{
              marginTop: "12px",
              padding: "16px",
              background: theme.colors.paper,
              borderRadius: "8px",
              border: `2px solid ${theme.colors.border}`,
            }}
          >
            <textarea
              value={holeNotes}
              onChange={(e) => setHoleNotes(e.target.value)}
              placeholder="Add notes about this hole (disputes, unusual situations, etc.)"
              style={{
                width: "100%",
                minHeight: "60px",
                padding: "10px",
                fontSize: "14px",
                border: `2px solid ${theme.colors.border}`,
                borderRadius: "6px",
                resize: "vertical",
                fontFamily: "inherit",
                backgroundColor:
                  theme.colors.inputBackground || theme.colors.paper,
                color: theme.colors.textPrimary,
              }}
            />
          </div>
        )}
      </div>
    </>
  );
};

OptionalEntryPanels.propTypes = {
  theme: PropTypes.object.isRequired,
  players: PropTypes.array.isRequired,
  scores: PropTypes.object.isRequired,
  handleScoreChange: PropTypes.func.isRequired,
  currentHole: PropTypes.number.isRequired,
  playerStandings: PropTypes.object.isRequired,
  holeNotes: PropTypes.string.isRequired,
  setHoleNotes: PropTypes.func.isRequired,
  showGolfScores: PropTypes.bool.isRequired,
  setShowGolfScores: PropTypes.func.isRequired,
  showCommissioner: PropTypes.bool.isRequired,
  setShowCommissioner: PropTypes.func.isRequired,
  showNotes: PropTypes.bool.isRequired,
  setShowNotes: PropTypes.func.isRequired,
};

export default OptionalEntryPanels;
