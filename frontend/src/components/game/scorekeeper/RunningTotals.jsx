// frontend/src/components/game/scorekeeper/RunningTotals.jsx
// Per-player running quarter totals. JSX moved verbatim from SimpleScorekeeper.jsx.

import React from "react";
import PropTypes from "prop-types";

const RunningTotals = ({ players, playerStandings, theme }) => (
  <div
    data-testid="running-totals"
    style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
      gap: "8px",
      marginBottom: "16px",
    }}
  >
    {players.map((player) => {
      const total = playerStandings[player.id]?.quarters ?? 0;
      const formatted =
        total > 0 ? `+${total.toFixed(1)}` : total.toFixed(1);
      return (
        <div
          key={player.id}
          style={{
            padding: "10px 12px",
            borderRadius: "10px",
            background: theme.colors.paper,
            border: `1px solid ${theme.colors.border}`,
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: "11px",
              fontWeight: "bold",
              color: theme.colors.textSecondary,
              textTransform: "uppercase",
              marginBottom: "4px",
            }}
          >
            {player.name}
          </div>
          <div
            data-testid={`player-${player.id}-points`}
            style={{
              fontSize: "18px",
              fontWeight: "bold",
              color:
                total > 0
                  ? "#2E7D32"
                  : total < 0
                    ? "#C62828"
                    : theme.colors.textPrimary,
            }}
          >
            {formatted}
          </div>
        </div>
      );
    })}
  </div>
);

RunningTotals.propTypes = {
  players: PropTypes.array.isRequired,
  playerStandings: PropTypes.object.isRequired,
  theme: PropTypes.object.isRequired,
};

export default RunningTotals;
