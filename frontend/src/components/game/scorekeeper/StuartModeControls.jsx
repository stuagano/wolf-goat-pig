// frontend/src/components/game/scorekeeper/StuartModeControls.jsx
// Stuart Mode UI controls, rendered at three different positions in the
// scorekeeper: the fixed toggle button, the hole-phase strip, and the
// doubles offer/response control. JSX moved verbatim from SimpleScorekeeper.
// Parent keeps the {stuartMode && ...} outer guards where they existed.

import React from "react";
import PropTypes from "prop-types";

export const StuartModeToggle = ({ stuartMode, toggleStuartMode, theme }) => {
  // Inline, clearly-labeled toggle row at the top of the scorekeeper.
  // (Was a faint floating 🧠 icon that hid behind the nav bar — undiscoverable.)
  return (
    <button
      data-testid="stuart-mode-toggle"
      onClick={toggleStuartMode}
      aria-pressed={stuartMode}
      aria-label={stuartMode ? "Stuart Mode on — tap to turn off" : "Stuart Mode off — tap to turn on"}
      style={{
        width: "100%",
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "10px 14px",
        marginBottom: "12px",
        borderRadius: "12px",
        border: stuartMode ? "2px solid #F59E0B" : `1px solid ${theme.colors.border}`,
        background: stuartMode ? "rgba(245,158,11,0.10)" : (theme.colors.paper || "#fff"),
        cursor: "pointer",
        textAlign: "left",
      }}
    >
      <span style={{ fontSize: "22px", flexShrink: 0 }}>🧠</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: "14px", color: theme.colors.textPrimary }}>
          Stuart Mode is {stuartMode ? "ON" : "OFF"}
        </div>
        <div style={{ fontSize: "12px", color: theme.colors.textSecondary, lineHeight: 1.35 }}>
          {stuartMode
            ? "AI is playing the computer opponents and giving live strategy tips."
            : "Tap to let AI play the computer opponents and coach your strategy."}
        </div>
      </div>
      {/* Switch */}
      <span
        style={{
          flexShrink: 0,
          width: "46px",
          height: "26px",
          borderRadius: "13px",
          background: stuartMode ? "#F59E0B" : "#d1d5db",
          position: "relative",
          transition: "background 0.2s",
        }}
      >
        <span
          style={{
            position: "absolute",
            top: "3px",
            left: stuartMode ? "23px" : "3px",
            width: "20px",
            height: "20px",
            borderRadius: "50%",
            background: "#fff",
            transition: "left 0.2s",
            boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
          }}
        />
      </span>
    </button>
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
