// frontend/src/components/game/scorekeeper/HoleHeader.jsx
// Extracted from SimpleScorekeeper.jsx — Enhanced Hole Title Section
import React from "react";
import PropTypes from "prop-types";

/**
 * Reusable styles for hitting order arrow buttons
 */
const ARROW_BUTTON_STYLE = {
  background: "rgba(255,255,255,0.3)",
  border: "none",
  borderRadius: "50%",
  width: "22px",
  height: "22px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  cursor: "pointer",
  fontSize: "12px",
  padding: "0",
};

/**
 * Create an object keyed by player ID from a list of players
 */
const createPlayerMap = (players, getValue) =>
  Object.fromEntries(players.map((p) => [p.id, getValue(p)]));

/**
 * HoleHeader — hole number selector, par display, wager, and hitting order row
 */
const HoleHeader = ({
  currentHole,
  courseData,
  players,
  rotationOrder,
  captainIndex,
  currentWager,
  phase,
  strokeAllocation,
  isHoepfinger,
  theme,
  holeHistory,
  holePar,
  editingHole,
  editingOrder,
  setEditingOrder,
  jumpToHole,
  movePlayerInOrder,
}) => {
  const strokeIndex = courseData?.holes?.find(
    (h) => h.hole_number === currentHole,
  )?.handicap;

  // Use the already-calculated strokeAllocation which has correct Creecher Feature logic
  const playerStrokesMap = createPlayerMap(
    players,
    (p) => strokeAllocation?.[p.id]?.[currentHole] || 0,
  );

  return (
    <div
      style={{
        background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.accent})`,
        color: "white",
        borderRadius: "16px",
        marginBottom: "16px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        overflow: "hidden",
      }}
    >
      {/* Main Header Row */}
      <div
        style={{
          padding: "16px 20px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid rgba(255,255,255,0.2)",
        }}
      >
        {/* Left: Hole Number with Selector */}
        <div
          style={{ display: "flex", alignItems: "center", gap: "8px" }}
        >
          <select
            data-testid="hole-selector"
            value={currentHole}
            onChange={(e) => jumpToHole(parseInt(e.target.value, 10))}
            style={{
              fontSize: "36px",
              fontWeight: "bold",
              background: "rgba(255,255,255,0.15)",
              border: "2px solid rgba(255,255,255,0.3)",
              borderRadius: "8px",
              color: "white",
              padding: "4px 8px",
              cursor: "pointer",
              appearance: "none",
              WebkitAppearance: "none",
              width: "70px",
              textAlign: "center",
            }}
          >
            {Array.from({ length: 18 }, (_, i) => i + 1).map((hole) => {
              const hasData = holeHistory.some((h) => h.hole === hole);
              return (
                <option
                  key={hole}
                  value={hole}
                  style={{ color: "black" }}
                >
                  {hole}
                  {hasData ? " \u2713" : ""}
                </option>
              );
            })}
          </select>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start",
            }}
          >
            <div
              style={{
                fontSize: "12px",
                opacity: 0.9,
                textTransform: "uppercase",
              }}
            >
              Hole
            </div>
            {editingHole && (
              <div
                style={{
                  fontSize: "10px",
                  background: "rgba(255,152,0,0.8)",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  marginTop: "2px",
                }}
              >
                Editing
              </div>
            )}
          </div>
        </div>

        {/* Center: Par & Stroke Index */}
        <div
          style={{ display: "flex", gap: "16px", alignItems: "center" }}
        >
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                fontSize: "11px",
                opacity: 0.8,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
              }}
            >
              Par
            </div>
            <div style={{ fontSize: "24px", fontWeight: "bold" }}>
              {holePar || "-"}
            </div>
          </div>
          {strokeIndex && (
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  fontSize: "11px",
                  opacity: 0.8,
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                }}
              >
                SI
              </div>
              <div style={{ fontSize: "24px", fontWeight: "bold" }}>
                {strokeIndex}
              </div>
            </div>
          )}
        </div>

        {/* Right: Wager */}
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              fontSize: "11px",
              opacity: 0.8,
              textTransform: "uppercase",
              letterSpacing: "0.5px",
            }}
          >
            Wager
          </div>
          <div style={{ fontSize: "20px", fontWeight: "bold" }}>
            {currentWager}q
          </div>
        </div>
      </div>

      {/* Hitting Order Row with Stroke Indicators */}
      {!isHoepfinger && rotationOrder.length > 0 && (
        <div
          style={{
            padding: "12px 16px",
            background: "rgba(0,0,0,0.15)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "8px",
            }}
          >
            <div
              style={{
                fontSize: "10px",
                textTransform: "uppercase",
                letterSpacing: "1px",
                opacity: 0.8,
              }}
            >
              Hitting Order
            </div>
            <button
              onClick={() => setEditingOrder(!editingOrder)}
              style={{
                background: editingOrder
                  ? theme.colors.primary
                  : "rgba(255,255,255,0.2)",
                color: "white",
                border: "none",
                borderRadius: "12px",
                padding: "4px 10px",
                fontSize: "11px",
                fontWeight: "bold",
                cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              {editingOrder ? "\u2713 Done" : "\u270F\uFE0F Edit"}
            </button>
          </div>
          <div
            style={{
              display: "flex",
              gap: "6px",
              flexWrap: "wrap",
              alignItems: "center",
            }}
          >
            {rotationOrder.map((playerId, index) => {
              const player = players.find((p) => p.id === playerId);
              const isCaptain = index === captainIndex;
              const playerStrokes = playerStrokesMap[playerId] || 0;
              const hasFullStroke = playerStrokes >= 1;
              const hasHalfStroke = playerStrokes % 1 >= 0.4;
              const fullStrokeCount = Math.floor(playerStrokes);

              return (
                <div
                  key={playerId}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "4px",
                    padding: "6px 10px",
                    borderRadius: "20px",
                    background: isCaptain
                      ? "rgba(33, 150, 243, 0.9)"
                      : "rgba(255,255,255,0.2)",
                    fontSize: "13px",
                    fontWeight: isCaptain ? "bold" : "500",
                    border: isCaptain
                      ? "2px solid rgba(255,255,255,0.5)"
                      : "1px solid rgba(255,255,255,0.15)",
                  }}
                >
                  {editingOrder && index > 0 && (
                    <button
                      onClick={() => movePlayerInOrder(index, -1)}
                      style={ARROW_BUTTON_STYLE}
                    >
                      &#x25B2;
                    </button>
                  )}
                  <span
                    style={{
                      fontSize: "11px",
                      opacity: 0.8,
                      fontWeight: "bold",
                      minWidth: "14px",
                    }}
                  >
                    {index + 1}.
                  </span>
                  <span>{player?.name || playerId}</span>
                  {isCaptain && <span>&#x1F451;</span>}
                  {/* Stroke indicators inline */}
                  {hasFullStroke && (
                    <span
                      style={{
                        background: "#4CAF50",
                        color: "white",
                        padding: "2px 6px",
                        borderRadius: "10px",
                        fontSize: "10px",
                        fontWeight: "bold",
                        marginLeft: "2px",
                      }}
                    >
                      {fullStrokeCount > 1 ? `\u25CF${fullStrokeCount}` : "\u25CF"}
                    </span>
                  )}
                  {hasHalfStroke && (
                    <span
                      style={{
                        background: "#FF9800",
                        color: "white",
                        padding: "2px 6px",
                        borderRadius: "10px",
                        fontSize: "10px",
                        fontWeight: "bold",
                        marginLeft: "2px",
                      }}
                    >
                      &#x25D0;
                    </span>
                  )}
                  {editingOrder && index < rotationOrder.length - 1 && (
                    <button
                      onClick={() => movePlayerInOrder(index, 1)}
                      style={ARROW_BUTTON_STYLE}
                    >
                      &#x25BC;
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Strokes Legend (compact, only if someone gets strokes) */}
      {!isHoepfinger &&
        strokeIndex &&
        Object.values(playerStrokesMap).some((s) => s > 0) && (
          <div
            style={{
              padding: "8px 16px",
              background: "rgba(0,0,0,0.1)",
              fontSize: "11px",
              opacity: 0.9,
              display: "flex",
              alignItems: "center",
              gap: "12px",
              flexWrap: "wrap",
            }}
          >
            <span
              style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <span
                style={{
                  background: "#4CAF50",
                  color: "white",
                  padding: "1px 5px",
                  borderRadius: "8px",
                  fontSize: "9px",
                }}
              >
                &#x25CF;
              </span>
              Full stroke
            </span>
            <span
              style={{
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <span
                style={{
                  background: "#FF9800",
                  color: "white",
                  padding: "1px 5px",
                  borderRadius: "8px",
                  fontSize: "9px",
                }}
              >
                &#x25D0;
              </span>
              Half stroke (Creecher)
            </span>
          </div>
        )}
    </div>
  );
};

HoleHeader.propTypes = {
  currentHole: PropTypes.number.isRequired,
  courseData: PropTypes.object,
  players: PropTypes.array.isRequired,
  rotationOrder: PropTypes.array.isRequired,
  captainIndex: PropTypes.number,
  currentWager: PropTypes.number.isRequired,
  phase: PropTypes.string,
  strokeAllocation: PropTypes.object,
  isHoepfinger: PropTypes.bool,
  theme: PropTypes.object.isRequired,
  holeHistory: PropTypes.array.isRequired,
  holePar: PropTypes.number,
  editingHole: PropTypes.number,
  editingOrder: PropTypes.bool.isRequired,
  setEditingOrder: PropTypes.func.isRequired,
  jumpToHole: PropTypes.func.isRequired,
  movePlayerInOrder: PropTypes.func.isRequired,
};

export default HoleHeader;
