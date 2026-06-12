// frontend/src/components/game/scorekeeper/StuartModeControls.jsx
// Stuart Mode UI controls, rendered at three different positions in the
// scorekeeper: the fixed toggle button, the hole-phase strip, and the
// doubles offer/response control. JSX moved verbatim from SimpleScorekeeper.
// Parent keeps the {stuartMode && ...} outer guards where they existed.

import React from "react";
import PropTypes from "prop-types";

export const StuartModeToggle = ({ stuartMode, toggleStuartMode, theme }) => {
  return (
    <>
      {/* Stuart Mode toggle — small fixed-position icon, dims when off */}
      <button
        data-testid="stuart-mode-toggle"
        onClick={toggleStuartMode}
        aria-label={stuartMode ? "Stuart Mode on" : "Stuart Mode off"}
        title={stuartMode ? "Stuart Mode on (tap to turn off)" : "Stuart Mode off (tap to turn on)"}
        style={{
          position: "fixed",
          top: "12px",
          right: "12px",
          width: "40px",
          height: "40px",
          borderRadius: "50%",
          border: stuartMode ? "2px solid #F59E0B" : `1px solid ${theme.colors.border}`,
          background: stuartMode ? "#F59E0B" : "rgba(255,255,255,0.85)",
          color: stuartMode ? "white" : theme.colors.textSecondary,
          fontSize: "18px",
          cursor: "pointer",
          boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
          opacity: stuartMode ? 1 : 0.6,
          zIndex: 50,
          padding: 0,
        }}
      >
        🧠
      </button>
    </>
  );
};

StuartModeToggle.propTypes = {
  stuartMode: PropTypes.bool.isRequired,
  toggleStuartMode: PropTypes.func.isRequired,
  theme: PropTypes.object.isRequired,
};

export const HolePhaseStrip = ({ stuartMode, holePhase, setHolePhase, theme }) => {
  return (
    <>
      {/* Stuart Mode: hole phase strip — drives mid-hole AI decisions */}
      {stuartMode && (
        <div
          data-testid="hole-phase-strip"
          style={{
            display: "flex",
            gap: "6px",
            marginBottom: "12px",
            padding: "8px",
            background: theme.colors.paper,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: "8px",
          }}
        >
          {[
            { key: "tee", label: "⛳ Tee" },
            { key: "after-tee", label: "🏌️ After Tee" },
            { key: "green", label: "🏁 Green" },
          ].map((p) => {
            const isActive = holePhase === p.key;
            return (
              <button
                key={p.key}
                data-testid={`phase-${p.key}`}
                onClick={() => setHolePhase(p.key)}
                style={{
                  flex: 1,
                  padding: "8px",
                  fontSize: "13px",
                  fontWeight: isActive ? "bold" : "normal",
                  background: isActive ? "#F59E0B" : "white",
                  color: isActive ? "white" : theme.colors.textPrimary,
                  border: `1px solid ${isActive ? "#F59E0B" : theme.colors.border}`,
                  borderRadius: "6px",
                  cursor: "pointer",
                }}
              >
                {p.label}
              </button>
            );
          })}
        </div>
      )}
    </>
  );
};

HolePhaseStrip.propTypes = {
  stuartMode: PropTypes.bool.isRequired,
  holePhase: PropTypes.string.isRequired,
  setHolePhase: PropTypes.func.isRequired,
  theme: PropTypes.object.isRequired,
};

export const DoubleOfferControl = ({
  stuartMode,
  stuartTeamInfo,
  pendingOffer,
  currentWager,
  getPlayerName,
  respondToOffer,
  createOffer,
  setAiMoves,
  theme,
}) => {
  return (
    <>
      {/* Stuart Mode: doubles offer / response control */}
      {stuartMode && stuartTeamInfo?.stuart && (
        <div
          data-testid="double-offer-control"
          style={{
            background: pendingOffer ? "#FFF3E0" : theme.colors.paper,
            border: `1px solid ${pendingOffer ? "#F59E0B" : theme.colors.border}`,
            borderRadius: "8px",
            padding: "10px 14px",
            marginBottom: "12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
          }}
        >
          <div style={{ flex: 1, fontSize: "13px" }}>
            <div style={{ fontWeight: "bold", color: theme.colors.textPrimary }}>
              Wager: {currentWager}q
            </div>
            {pendingOffer && (
              <div style={{ color: "#92400E", marginTop: "2px" }}>
                Double offered by {getPlayerName(pendingOffer.offered_by)} —{" "}
                {pendingOffer.wager_before}q → {pendingOffer.wager_after}q
              </div>
            )}
          </div>
          {pendingOffer ? (
            stuartTeamInfo.isStuartResponseTurn ? (
              <div style={{ display: "flex", gap: "6px" }}>
                <button
                  data-testid="double-accept"
                  onClick={() =>
                    respondToOffer("accept", stuartTeamInfo.stuart.id)
                  }
                  style={{
                    padding: "6px 12px",
                    fontSize: "13px",
                    background: "#4CAF50",
                    color: "white",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontWeight: "bold",
                  }}
                >
                  Accept
                </button>
                <button
                  data-testid="double-decline"
                  onClick={() =>
                    respondToOffer("decline", stuartTeamInfo.stuart.id)
                  }
                  style={{
                    padding: "6px 12px",
                    fontSize: "13px",
                    background: "white",
                    color: "#92400E",
                    border: "1px solid #F59E0B",
                    borderRadius: "6px",
                    cursor: "pointer",
                  }}
                >
                  Decline
                </button>
              </div>
            ) : (
              <span style={{ fontSize: "12px", color: theme.colors.textSecondary }}>
                AI deciding…
              </span>
            )
          ) : (
            <button
              data-testid="offer-double-button"
              onClick={() => {
                createOffer("double", stuartTeamInfo.stuart.id);
                setAiMoves((prev) => [
                  ...prev,
                  {
                    type: "double-offer",
                    text: `You offer double — wager ${currentWager}q → ${currentWager * 2}q`,
                    timestamp: Date.now(),
                  },
                ]);
              }}
              style={{
                padding: "6px 12px",
                fontSize: "13px",
                background: "#F59E0B",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: "bold",
              }}
            >
              Offer Double → {currentWager * 2}q
            </button>
          )}
        </div>
      )}
    </>
  );
};

DoubleOfferControl.propTypes = {
  stuartMode: PropTypes.bool.isRequired,
  stuartTeamInfo: PropTypes.object,
  pendingOffer: PropTypes.object,
  currentWager: PropTypes.number.isRequired,
  getPlayerName: PropTypes.func.isRequired,
  respondToOffer: PropTypes.func.isRequired,
  createOffer: PropTypes.func.isRequired,
  setAiMoves: PropTypes.func.isRequired,
  theme: PropTypes.object.isRequired,
};
