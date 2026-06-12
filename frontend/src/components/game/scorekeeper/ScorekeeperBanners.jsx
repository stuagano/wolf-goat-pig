// frontend/src/components/game/scorekeeper/ScorekeeperBanners.jsx
// Status banners: course-data loading/error, rotation error, achievement-check
// warning, complete-game-edit and hole-edit modes. Plus the named ErrorBanner
// (validation errors with guidance) which renders lower in the page.
// JSX moved verbatim from SimpleScorekeeper.jsx.

import React from "react";
import PropTypes from "prop-types";

export const ErrorBanner = ({ error, setError, theme }) => {
  return (
    <>
      {/* Error Display with Helpful Guidance */}
      {error && (
        <div
          style={{
            background: error.includes("💡") ? "#FFF3E0" : theme.colors.error,
            color: error.includes("💡") ? "#E65100" : "white",
            padding: "16px",
            borderRadius: "8px",
            marginBottom: "20px",
            border: error.includes("💡") ? "2px solid #FF9800" : "none",
          }}
        >
          {error.includes("💡") ? (
            <>
              <div
                style={{
                  fontWeight: "bold",
                  marginBottom: "8px",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <span style={{ fontSize: "20px" }}>⚠️</span>
                {error.split("\n\n")[0]}
              </div>
              <div
                style={{
                  background: "rgba(255, 152, 0, 0.1)",
                  padding: "12px",
                  borderRadius: "6px",
                  fontSize: "14px",
                  lineHeight: "1.5",
                }}
              >
                {error.split("\n\n")[1]}
              </div>
              <button
                onClick={() => setError(null)}
                style={{
                  marginTop: "12px",
                  padding: "8px 16px",
                  background: "#FF9800",
                  color: "white",
                  border: "none",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontWeight: "bold",
                }}
              >
                Got it, let me fix this
              </button>
            </>
          ) : (
            <div style={{ textAlign: "center" }}>{error}</div>
          )}
        </div>
      )}
    </>
  );
};

ErrorBanner.propTypes = {
  error: PropTypes.string,
  setError: PropTypes.func.isRequired,
  theme: PropTypes.object.isRequired,
};

const ScorekeeperBanners = ({
  courseDataLoading,
  courseDataError,
  rotationError,
  achievementCheckFailed,
  setAchievementCheckFailed,
  isEditingCompleteGame,
  setIsEditingCompleteGame,
  editingHole,
  setCurrentHole,
  resetHole,
  holeHistory,
}) => {
  return (
    <>
      {/* Loading/Error/Warning Banners */}
      {courseDataLoading && (
        <div
          style={{
            background: "#e3f2fd",
            color: "#1976d2",
            padding: "10px 14px",
            borderRadius: "8px",
            marginBottom: "12px",
            fontSize: "14px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>⏳</span>
          <span>Loading course data...</span>
        </div>
      )}

      {courseDataError && (
        <div
          style={{
            background: "#f44336",
            color: "white",
            padding: "12px 16px",
            borderRadius: "8px",
            marginBottom: "12px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <span style={{ fontSize: "18px" }}>⚠️</span>
          <div>
            <strong>Course Data Error:</strong> {courseDataError}
            <div style={{ fontSize: "12px", opacity: 0.9, marginTop: "4px" }}>
              Hole par and handicap data may be unavailable
            </div>
          </div>
        </div>
      )}

      {rotationError && (
        <div
          style={{
            background: "#ff9800",
            color: "white",
            padding: "12px 16px",
            borderRadius: "8px",
            marginBottom: "12px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <span style={{ fontSize: "18px" }}>⚠️</span>
          <div>
            <strong>Rotation/Wager Error:</strong> {rotationError}
            <div style={{ fontSize: "12px", opacity: 0.9, marginTop: "4px" }}>
              Using default wager. Rotation may be incorrect.
            </div>
          </div>
        </div>
      )}

      {achievementCheckFailed && (
        <div
          style={{
            background: "#9c27b0",
            color: "white",
            padding: "10px 14px",
            borderRadius: "8px",
            marginBottom: "12px",
            fontSize: "14px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>🏆</span>
          <span>
            Achievement check failed - some badges may not have been recorded
          </span>
          <button
            onClick={() => setAchievementCheckFailed(false)}
            style={{
              marginLeft: "auto",
              background: "transparent",
              border: "none",
              color: "white",
              cursor: "pointer",
              fontSize: "16px",
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Editing Completed Game Banner */}
      {isEditingCompleteGame && (
        <div
          style={{
            background: "linear-gradient(135deg, #ff9800 0%, #f57c00 100%)",
            color: "white",
            padding: "16px 20px",
            borderRadius: "12px",
            marginBottom: "16px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            boxShadow: "0 4px 6px rgba(0,0,0,0.15)",
          }}
        >
          <div>
            <div
              style={{
                fontSize: "18px",
                fontWeight: "bold",
                marginBottom: "4px",
              }}
            >
              Editing Completed Game
            </div>
            <div style={{ fontSize: "14px", opacity: 0.9 }}>
              Click on any hole in the scorecard below to edit it
            </div>
          </div>
          <button
            onClick={() => {
              setIsEditingCompleteGame(false);
              setCurrentHole(19); // Return to completed state
            }}
            style={{
              padding: "10px 20px",
              fontSize: "16px",
              fontWeight: "bold",
              borderRadius: "8px",
              border: "2px solid white",
              background: "transparent",
              color: "white",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
            onMouseOver={(e) => {
              e.target.style.background = "rgba(255,255,255,0.2)";
            }}
            onMouseOut={(e) => {
              e.target.style.background = "transparent";
            }}
          >
            Done Editing
          </button>
        </div>
      )}

      {/* Edit Mode Banner */}
      {editingHole && (
        <div
          style={{
            background: "#FF9800",
            color: "white",
            padding: "16px 20px",
            borderRadius: "12px",
            marginBottom: "16px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
          }}
        >
          <div>
            <div
              style={{
                fontSize: "20px",
                fontWeight: "bold",
                marginBottom: "4px",
              }}
            >
              ✏️ Editing Hole {editingHole}
            </div>
            <div style={{ fontSize: "14px", opacity: 0.9 }}>
              Make your changes and submit to update
            </div>
          </div>
          <button
            onClick={() => {
              setCurrentHole(Math.max(...holeHistory.map((h) => h.hole)) + 1);
              resetHole();
            }}
            className="touch-optimized"
            style={{
              padding: "10px 20px",
              fontSize: "14px",
              fontWeight: "bold",
              border: "2px solid white",
              borderRadius: "8px",
              background: "transparent",
              color: "white",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            Cancel
          </button>
        </div>
      )}
    </>
  );
};

ScorekeeperBanners.propTypes = {
  courseDataLoading: PropTypes.bool.isRequired,
  courseDataError: PropTypes.string,
  rotationError: PropTypes.string,
  achievementCheckFailed: PropTypes.bool.isRequired,
  setAchievementCheckFailed: PropTypes.func.isRequired,
  isEditingCompleteGame: PropTypes.bool.isRequired,
  setIsEditingCompleteGame: PropTypes.func.isRequired,
  editingHole: PropTypes.number,
  setCurrentHole: PropTypes.func.isRequired,
  resetHole: PropTypes.func.isRequired,
  holeHistory: PropTypes.array.isRequired,
};

export default ScorekeeperBanners;
