// frontend/src/components/game/scorecardParts/StandingsView.jsx
// Standings view for the Scorecard (simulation mode, when captainId is provided).
import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../../theme/Provider';
import { calculateTotals, displayName, isHumanPlayer } from './scorecardUtils';

const StandingsView = ({ players, holeHistory, captainId }) => {
  const theme = useTheme();

  if (!Array.isArray(players) || players.length === 0) {
    return <div style={{ padding: '20px', textAlign: 'center', color: theme.colors.textSecondary }}>No players available</div>;
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
        {players.map(player => {
          if (!player || !player.id) return null;

          const totals = calculateTotals(holeHistory, player.id);
          const isCaptain = player.id === captainId;
          const isHuman = isHumanPlayer(player);
          const playerName = displayName(player);
          const playerHandicap = typeof player.handicap === 'number' ? player.handicap : '-';

          return (
            <div key={player.id} style={{
              padding: '12px',
              background: 'white',
              borderRadius: '8px',
              border: `2px solid ${isCaptain ? theme.colors.primary : theme.colors.border}`
            }}>
              <div style={{ fontWeight: 'bold', fontSize: 16, marginBottom: 4 }}>
                {isHuman ? '👤 ' : '🤖 '}
                {playerName} {isCaptain && '⭐'}
              </div>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: totals.total >= 0 ? theme.colors.success : theme.colors.error }}>
                {totals.total > 0 ? '+' : ''}{totals.total}q
              </div>
              <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                Hdcp: {playerHandicap}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

StandingsView.propTypes = {
  players: PropTypes.array,
  holeHistory: PropTypes.array,
  captainId: PropTypes.string
};

export default StandingsView;
