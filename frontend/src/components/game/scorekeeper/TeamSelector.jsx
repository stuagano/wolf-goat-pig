// frontend/src/components/game/scorekeeper/TeamSelector.jsx
// Extracted from SimpleScorekeeper.jsx — Team mode selection, team picks, aardvark controls
import React from "react";
import PropTypes from "prop-types";

/**
 * Helper component to display player name with authentication indicator
 */
const PlayerName = ({ name, isAuthenticated }) => (
  <>
    {name}
    {isAuthenticated && (
      <span style={{ marginLeft: "4px", fontSize: "12px" }}>&#x1F512;</span>
    )}
  </>
);

PlayerName.propTypes = {
  name: PropTypes.string.isRequired,
  isAuthenticated: PropTypes.bool,
};

/**
 * TeamSelector — team mode buttons, team picks, aardvark controls
 */
const TeamSelector = ({
  players,
  teamMode,
  team1,
  captain,
  theme,
  duncanInvoked,
  setDuncanInvoked,
  setTeamMode,
  togglePlayerTeam,
  toggleCaptain,
  announceAction,
  showTeamSelection,
  setShowTeamSelection,
  aardvarkRequestedTeam,
  setAardvarkRequestedTeam,
  aardvarkTossed,
  setAardvarkTossed,
  aardvarkSolo,
  setAardvarkSolo,
  invisibleAardvarkTossed,
  setInvisibleAardvarkTossed,
}) => {
  return (
    <>
      {/* Team Mode Selection - Enhanced Style */}
      <div
        style={{
          background: theme.colors.paper,
          padding: "16px",
          borderRadius: "8px",
          marginBottom: "20px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
          border: `1px solid ${theme.colors.border}`,
          transition: "box-shadow 0.2s ease",
          borderLeft: `4px solid ${theme.colors.primary}`,
        }}
      >
        <h3
          style={{
            margin: "0 0 16px",
            textTransform: "uppercase",
            letterSpacing: "0.5px",
            fontSize: "12px",
            fontWeight: "bold",
            color: theme.colors.textPrimary,
          }}
        >
          Team Mode
        </h3>
        <div style={{ display: "flex", gap: "12px" }}>
          <button
            onClick={() => setTeamMode("partners")}
            className="touch-optimized"
            style={{
              flex: 1,
              padding: "12px 20px",
              fontSize: "16px",
              fontWeight: "bold",
              border:
                teamMode === "partners"
                  ? `2px solid ${theme.colors.primary}`
                  : `1px solid ${theme.colors.border}`,
              borderRadius: "8px",
              background:
                teamMode === "partners" ? theme.colors.primary : "white",
              color:
                teamMode === "partners" ? "white" : theme.colors.textPrimary,
              cursor: "pointer",
              transition: "all 0.15s ease",
              boxShadow:
                teamMode === "partners" ? "0 2px 4px rgba(0,0,0,0.1)" : "none",
            }}
          >
            Partners
          </button>
          <button
            data-testid="go-solo-button"
            onClick={() => setTeamMode("solo")}
            className="touch-optimized"
            style={{
              flex: 1,
              padding: "12px 20px",
              fontSize: "16px",
              fontWeight: "bold",
              border:
                teamMode === "solo"
                  ? `2px solid ${theme.colors.primary}`
                  : `1px solid ${theme.colors.border}`,
              borderRadius: "8px",
              background: teamMode === "solo" ? theme.colors.primary : "white",
              color: teamMode === "solo" ? "white" : theme.colors.textPrimary,
              cursor: "pointer",
              transition: "all 0.15s ease",
              boxShadow:
                teamMode === "solo" ? "0 2px 4px rgba(0,0,0,0.1)" : "none",
            }}
          >
            Solo
          </button>
        </div>

        {/* The Duncan - Announcement button (only shown in Solo mode) */}
        {teamMode === "solo" && (
          <div
            style={{
              marginTop: "12px",
              padding: "12px",
              background: duncanInvoked ? "#E1BEE7" : "#F3E5F5",
              borderRadius: "8px",
              border: `2px solid ${duncanInvoked ? "#7B1FA2" : "#9C27B0"}`,
            }}
          >
            <button
              onClick={() => {
                const newValue = !duncanInvoked;
                setDuncanInvoked(newValue);
                if (newValue && captain) {
                  announceAction("duncan", captain);
                }
              }}
              className="touch-optimized"
              style={{
                width: "100%",
                padding: "12px",
                borderRadius: "8px",
                background: duncanInvoked
                  ? "linear-gradient(135deg, #7B1FA2, #6A1B9A)"
                  : "linear-gradient(135deg, #9C27B0, #7B1FA2)",
                border: "none",
                fontSize: "14px",
                fontWeight: "bold",
                color: "white",
                cursor: "pointer",
                boxShadow: "0 2px 8px rgba(156, 39, 176, 0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
              }}
            >
              {duncanInvoked ? (
                <>{"\u2713"} Duncan Called - 3-for-2 Payout</>
              ) : (
                <>{"\uD83C\uDFC6"} Call The Duncan (Solo before hitting)</>
              )}
            </button>
            {duncanInvoked && (
              <div
                style={{
                  marginTop: "8px",
                  fontSize: "12px",
                  color: "#6A1B9A",
                  textAlign: "center",
                }}
              >
                Captain goes solo before hitting. Click again to cancel.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Team Selection - Collapsible */}
      <div
        style={{
          background: theme.colors.paper,
          padding: "16px",
          borderRadius: "8px",
          marginBottom: "20px",
        }}
      >
        <h3
          onClick={() => setShowTeamSelection(!showTeamSelection)}
          style={{
            margin: "0 0 8px",
            cursor: "pointer",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>
            {teamMode === "partners" ? "Teams" : "Captain Selection"}
            {/* Show summary when collapsed */}
            {!showTeamSelection && (
              <span
                style={{
                  fontWeight: "normal",
                  fontSize: "14px",
                  color: theme.colors.textSecondary,
                  marginLeft: "8px",
                }}
              >
                {teamMode === "partners"
                  ? team1.length > 0
                    ? `(Team 1: ${team1.map((id) => players.find((p) => p.id === id)?.name?.split(" ")[0]).join(", ")} vs Team 2)`
                    : "(tap to select)"
                  : captain
                    ? `(\u2B50 ${players.find((p) => p.id === captain)?.name?.split(" ")[0]} vs all)`
                    : "(tap to select)"}
              </span>
            )}
          </span>
          <span style={{ fontSize: "14px", color: theme.colors.textSecondary }}>
            {showTeamSelection ? "\u25BC" : "\u25B6"}
          </span>
        </h3>
        {showTeamSelection && teamMode === "partners" && (
          <p
            style={{
              margin: "0 0 12px",
              fontSize: "14px",
              color: theme.colors.textSecondary,
              fontStyle: "italic",
            }}
          >
            {players.length === 5
              ? "Click to select 2 or 3 players for Team 1. The rest will be Team 2."
              : "Click players to add them to Team 1. Remaining players will automatically be Team 2."}
          </p>
        )}

        {showTeamSelection &&
          (teamMode === "partners" ? (
            <>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: `repeat(${Math.min(3, Math.ceil(players.length / 2))}, 1fr)`,
                  gap: "12px",
                }}
              >
                {players.map((player) => {
                  const inTeam1 = team1.includes(player.id);
                  return (
                    <button
                      key={player.id}
                      data-testid={`partner-${player.id}`}
                      onClick={() => togglePlayerTeam(player.id)}
                      style={{
                        padding: "12px",
                        fontSize: "16px",
                        border: inTeam1
                          ? `3px solid #00bcd4`
                          : `2px solid ${theme.colors.border}`,
                        borderRadius: "8px",
                        background: inTeam1
                          ? "rgba(0, 188, 212, 0.15)"
                          : "white",
                        cursor: "pointer",
                        fontWeight: inTeam1 ? 600 : 400,
                      }}
                    >
                      <PlayerName
                        name={player.name}
                        isAuthenticated={player.is_authenticated}
                      />
                      {inTeam1 && " (Team 1)"}
                    </button>
                  );
                })}
              </div>

              {/* 5-Man and 6-Man Aardvark - Compact */}
              {(players.length === 5 || players.length === 6) &&
                team1.length >= 2 && (
                  <div
                    style={{
                      marginTop: "12px",
                      padding: "10px",
                      background: "#E3F2FD",
                      borderRadius: "8px",
                      border: "1px solid #90CAF9",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "13px",
                        fontWeight: "bold",
                        color: "#1565C0",
                        marginBottom: "8px",
                      }}
                    >
                      Aardvark:{" "}
                      {players[players.length === 5 ? 4 : 5]?.name?.split(
                        " ",
                      )[0] || "Player " + players.length}
                    </div>
                    <div
                      style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}
                    >
                      <button
                        onClick={() => {
                          setAardvarkRequestedTeam("team1");
                          setAardvarkTossed(false);
                          setAardvarkSolo(false);
                        }}
                        style={{
                          padding: "6px 10px",
                          fontSize: "12px",
                          border:
                            aardvarkRequestedTeam === "team1" &&
                            !aardvarkTossed &&
                            !aardvarkSolo
                              ? "2px solid #00bcd4"
                              : "1px solid #90CAF9",
                          borderRadius: "6px",
                          background:
                            aardvarkRequestedTeam === "team1" &&
                            !aardvarkTossed &&
                            !aardvarkSolo
                              ? "#B2EBF2"
                              : "white",
                          cursor: "pointer",
                        }}
                      >
                        {"\u2192"} T1
                      </button>
                      <button
                        onClick={() => {
                          setAardvarkRequestedTeam("team2");
                          setAardvarkTossed(false);
                          setAardvarkSolo(false);
                        }}
                        style={{
                          padding: "6px 10px",
                          fontSize: "12px",
                          border:
                            aardvarkRequestedTeam === "team2" &&
                            !aardvarkTossed &&
                            !aardvarkSolo
                              ? "2px solid #ff9800"
                              : "1px solid #90CAF9",
                          borderRadius: "6px",
                          background:
                            aardvarkRequestedTeam === "team2" &&
                            !aardvarkTossed &&
                            !aardvarkSolo
                              ? "#FFE0B2"
                              : "white",
                          cursor: "pointer",
                        }}
                      >
                        {"\u2192"} T2
                      </button>
                      <button
                        onClick={() => {
                          setAardvarkTossed(!aardvarkTossed);
                        }}
                        disabled={!aardvarkRequestedTeam || aardvarkSolo}
                        style={{
                          padding: "6px 10px",
                          fontSize: "12px",
                          border: aardvarkTossed
                            ? "2px solid #d32f2f"
                            : "1px solid #90CAF9",
                          borderRadius: "6px",
                          background: aardvarkTossed ? "#FFCDD2" : "white",
                          cursor:
                            !aardvarkRequestedTeam || aardvarkSolo
                              ? "not-allowed"
                              : "pointer",
                          opacity:
                            !aardvarkRequestedTeam || aardvarkSolo ? 0.5 : 1,
                        }}
                      >
                        Tossed
                      </button>
                      <button
                        onClick={() => {
                          setAardvarkSolo(!aardvarkSolo);
                          setAardvarkTossed(false);
                        }}
                        style={{
                          padding: "6px 10px",
                          fontSize: "12px",
                          border: aardvarkSolo
                            ? "2px solid #7B1FA2"
                            : "1px solid #90CAF9",
                          borderRadius: "6px",
                          background: aardvarkSolo ? "#E1BEE7" : "white",
                          cursor: "pointer",
                        }}
                      >
                        Solo
                      </button>
                    </div>
                  </div>
                )}

              {/* 4-Man Invisible Aardvark - Compact */}
              {players.length === 4 && team1.length === 2 && (
                <div
                  style={{
                    marginTop: "12px",
                    padding: "8px 10px",
                    background: "#FFF8E1",
                    borderRadius: "6px",
                    border: "1px dashed #FFB74D",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <label
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      cursor: "pointer",
                      fontSize: "13px",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={invisibleAardvarkTossed}
                      onChange={(e) =>
                        setInvisibleAardvarkTossed(e.target.checked)
                      }
                      style={{ width: "16px", height: "16px" }}
                    />
                    <span
                      style={{
                        color: invisibleAardvarkTossed ? "#d32f2f" : "#795548",
                        fontWeight: invisibleAardvarkTossed ? "bold" : "normal",
                      }}
                    >
                      Invisible Aardvark tossed
                      {invisibleAardvarkTossed && " (3:2)"}
                    </span>
                  </label>
                </div>
              )}
            </>
          ) : (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: `repeat(${Math.min(3, Math.ceil(players.length / 2))}, 1fr)`,
                gap: "12px",
              }}
            >
              {players.map((player) => {
                const isCaptain = captain === player.id;
                return (
                  <button
                    key={player.id}
                    data-testid={`partner-${player.id}`}
                    onClick={() => toggleCaptain(player.id)}
                    style={{
                      padding: "12px",
                      fontSize: "16px",
                      border: isCaptain
                        ? `3px solid #ffc107`
                        : `2px solid ${theme.colors.border}`,
                      borderRadius: "8px",
                      background: isCaptain
                        ? "rgba(255, 193, 7, 0.1)"
                        : "white",
                      cursor: "pointer",
                    }}
                  >
                    {isCaptain && "\u2B50 "}
                    {player.name}
                  </button>
                );
              })}
            </div>
          ))}
      </div>
    </>
  );
};

TeamSelector.propTypes = {
  players: PropTypes.array.isRequired,
  teamMode: PropTypes.string.isRequired,
  team1: PropTypes.array.isRequired,
  captain: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  theme: PropTypes.object.isRequired,
  duncanInvoked: PropTypes.bool,
  setDuncanInvoked: PropTypes.func.isRequired,
  setTeamMode: PropTypes.func.isRequired,
  togglePlayerTeam: PropTypes.func.isRequired,
  toggleCaptain: PropTypes.func.isRequired,
  announceAction: PropTypes.func.isRequired,
  showTeamSelection: PropTypes.bool.isRequired,
  setShowTeamSelection: PropTypes.func.isRequired,
  aardvarkRequestedTeam: PropTypes.string,
  setAardvarkRequestedTeam: PropTypes.func.isRequired,
  aardvarkTossed: PropTypes.bool,
  setAardvarkTossed: PropTypes.func.isRequired,
  aardvarkSolo: PropTypes.bool,
  setAardvarkSolo: PropTypes.func.isRequired,
  invisibleAardvarkTossed: PropTypes.bool,
  setInvisibleAardvarkTossed: PropTypes.func.isRequired,
};

export default TeamSelector;
