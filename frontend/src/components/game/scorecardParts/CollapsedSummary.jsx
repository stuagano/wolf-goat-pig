// frontend/src/components/game/scorecardParts/CollapsedSummary.jsx
// Compact per-player quarters chips shown while the Scorecard is collapsed.
import React from 'react';
import PropTypes from 'prop-types';
import { calculateTotals, displayName, formatSignedQuarters, quartersColor } from './scorecardUtils';

const CollapsedSummary = ({ players, holeHistory }) => (
  <div style={{
    display: 'flex',
    flexWrap: 'nowrap',
    gap: '12px',
    overflowX: 'auto',
    padding: '8px 4px'
  }}>
    {Array.isArray(players) && players.map(player => {
      if (!player || !player.id) return null;

      const totals = calculateTotals(holeHistory, player.id);
      const playerName = displayName(player);
      // Get first name only for mobile display
      const shortName = playerName.split(' ')[0];

      return (
        <div
          key={player.id}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 10px',
            backgroundColor: totals.total > 0 ? 'rgba(76, 175, 80, 0.1)' : totals.total < 0 ? 'rgba(244, 67, 54, 0.1)' : 'rgba(0,0,0,0.05)',
            borderRadius: '8px',
            whiteSpace: 'nowrap',
            flexShrink: 0
          }}
        >
          <span style={{ fontWeight: '600', fontSize: '13px' }}>
            {shortName}
          </span>
          <span style={{
            fontWeight: 'bold',
            fontSize: '16px',
            color: quartersColor(totals.total, '#666')
          }}>
            {formatSignedQuarters(totals.total, '0')}
          </span>
        </div>
      );
    })}
  </div>
);

CollapsedSummary.propTypes = {
  players: PropTypes.array,
  holeHistory: PropTypes.array
};

export default CollapsedSummary;
