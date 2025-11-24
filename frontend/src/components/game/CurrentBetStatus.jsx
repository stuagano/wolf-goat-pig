// frontend/src/components/game/CurrentBetStatus.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';

const CurrentBetStatus = ({ state }) => {
  const theme = useTheme();

  const containerStyle = {
    background: '#f0f7ff',
    padding: theme.spacing[4],
    borderRadius: theme.borderRadius.md,
    marginBottom: theme.spacing[3]
  };

  const multiplierBadgeStyle = {
    display: 'inline-block',
    background: theme.colors.primary,
    color: 'white',
    padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
    borderRadius: theme.borderRadius.full,
    fontSize: theme.typography.xl,
    fontWeight: theme.typography.bold,
    marginRight: theme.spacing[2]
  };

  const teamContainerStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: theme.spacing[3],
    marginTop: theme.spacing[3]
  };

  const teamCardStyle = {
    background: 'white',
    padding: theme.spacing[3],
    borderRadius: theme.borderRadius.md,
    border: `2px solid ${theme.colors.border}`
  };

  // Display quarters (Q) instead of dollars
  // Backend stores base_wager as integer quarters (1 = 1 quarter)
  // Only convert to dollars in final summary (quarters * $0.25)

  return (
    <div style={containerStyle}>
      <div style={{ marginBottom: theme.spacing[3] }}>
        <span style={multiplierBadgeStyle}>{state.currentMultiplier}x</span>
        <span style={{ fontSize: theme.typography.lg }}>
          Base: {state.baseAmount}Q = Total: {state.currentBet}Q
        </span>
      </div>

      {state.teams && state.teams.length > 0 && (
        <div style={teamContainerStyle}>
          {state.teams.map((team, idx) => (
            <div key={idx} style={teamCardStyle}>
              <div style={{ fontWeight: theme.typography.bold, marginBottom: theme.spacing[2] }}>
                Team {idx + 1}
              </div>
              <div>
                {team.players.map((player, pIdx) => (
                  <div key={pIdx}>{player}</div>
                ))}
              </div>
              <div style={{ marginTop: theme.spacing[2], fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Bet: {team.betAmount}Q
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

CurrentBetStatus.propTypes = {
  state: PropTypes.shape({
    wager: PropTypes.number,
    multiplier: PropTypes.number,
    doubleHistory: PropTypes.arrayOf(PropTypes.shape({
      from: PropTypes.string,
      accepted: PropTypes.bool,
    })),
  }).isRequired,
};

export default CurrentBetStatus;
