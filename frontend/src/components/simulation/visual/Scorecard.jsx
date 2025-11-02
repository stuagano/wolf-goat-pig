// frontend/src/components/simulation/visual/Scorecard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Card } from '../../ui';
import { useTheme } from '../../../theme/Provider';

const Scorecard = ({ players = [], holeHistory = [], currentHole = 1 }) => {
  const theme = useTheme();

  // Create a scorecard data structure
  const holes = Array.from({ length: 18 }, (_, i) => i + 1);

  // Get quarters won per hole for each player
  const getHoleQuarters = (holeNumber, playerId) => {
    const holeData = holeHistory.find(h => h.hole === holeNumber);
    if (!holeData) return null;

    const pointsDelta = holeData.points_delta || {};
    return pointsDelta[playerId] || 0;
  };

  // Calculate front 9, back 9, and total
  const calculateTotals = (playerId) => {
    const front9 = holes.slice(0, 9).reduce((sum, hole) => {
      const quarters = getHoleQuarters(hole, playerId);
      return sum + (quarters || 0);
    }, 0);

    const back9 = holes.slice(9, 18).reduce((sum, hole) => {
      const quarters = getHoleQuarters(hole, playerId);
      return sum + (quarters || 0);
    }, 0);

    return { front9, back9, total: front9 + back9 };
  };

  return (
    <Card style={{ height: '100%', overflow: 'auto' }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
        📊 SCORECARD
      </h3>

      <div style={{ overflowX: 'auto' }}>
        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: '12px',
          minWidth: '500px'
        }}>
          <thead>
            <tr style={{ backgroundColor: theme.colors.backgroundSecondary }}>
              <th style={headerCellStyle}>HOLE</th>
              {holes.map(hole => (
                <th
                  key={hole}
                  style={{
                    ...headerCellStyle,
                    backgroundColor: hole === currentHole ? 'rgba(255, 215, 0, 0.2)' : 'transparent',
                    fontWeight: hole === currentHole ? 'bold' : 'normal',
                    color: hole === currentHole ? '#FFD700' : 'inherit'
                  }}
                >
                  {hole}
                </th>
              ))}
              <th style={headerCellStyle}>OUT</th>
              <th style={headerCellStyle}>IN</th>
              <th style={headerCellStyle}>TOT</th>
            </tr>
          </thead>
          <tbody>
            {players.map((player, idx) => {
              const totals = calculateTotals(player.id);
              const isHuman = player.is_human || player.id === 'human';

              return (
                <tr key={player.id} style={{
                  backgroundColor: idx % 2 === 0 ? 'rgba(0, 0, 0, 0.02)' : 'transparent',
                  borderLeft: isHuman ? '3px solid rgba(33, 150, 243, 0.5)' : 'none'
                }}>
                  <td style={{
                    ...cellStyle,
                    fontWeight: 'bold',
                    maxWidth: '100px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {isHuman ? '👤 ' : '🤖 '}
                    {player.name}
                  </td>
                  {holes.map(hole => {
                    const quarters = getHoleQuarters(hole, player.id);
                    const isCurrentHole = hole === currentHole;
                    const isCompleted = hole < currentHole || (holeHistory.find(h => h.hole === hole));

                    return (
                      <td
                        key={hole}
                        style={{
                          ...cellStyle,
                          backgroundColor: isCurrentHole ? 'rgba(255, 215, 0, 0.1)' : 'transparent',
                          fontWeight: quarters && quarters !== 0 ? 'bold' : 'normal',
                          color: quarters > 0 ? '#4CAF50' : quarters < 0 ? '#f44336' : theme.colors.textSecondary
                        }}
                      >
                        {isCompleted ? (
                          quarters !== null && quarters !== 0 ? (
                            quarters > 0 ? `+${quarters}` : quarters
                          ) : '-'
                        ) : ''}
                      </td>
                    );
                  })}
                  <td style={{ ...totalCellStyle, fontWeight: 'bold' }}>
                    {totals.front9 !== 0 ? (totals.front9 > 0 ? `+${totals.front9}` : totals.front9) : '-'}
                  </td>
                  <td style={{ ...totalCellStyle, fontWeight: 'bold' }}>
                    {totals.back9 !== 0 ? (totals.back9 > 0 ? `+${totals.back9}` : totals.back9) : '-'}
                  </td>
                  <td style={{ ...totalCellStyle, fontWeight: 'bold', fontSize: '14px' }}>
                    {totals.total !== 0 ? (totals.total > 0 ? `+${totals.total}` : totals.total) : '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};

const headerCellStyle = {
  padding: '8px 4px',
  textAlign: 'center',
  borderBottom: '2px solid rgba(0, 0, 0, 0.1)',
  fontSize: '11px',
  fontWeight: 'bold'
};

const cellStyle = {
  padding: '6px 4px',
  textAlign: 'center',
  borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
  fontSize: '12px'
};

const totalCellStyle = {
  ...cellStyle,
  borderLeft: '2px solid rgba(0, 0, 0, 0.1)',
  backgroundColor: 'rgba(0, 0, 0, 0.03)'
};

Scorecard.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    points: PropTypes.number,
    is_human: PropTypes.bool
  })),
  holeHistory: PropTypes.arrayOf(PropTypes.shape({
    hole: PropTypes.number.isRequired,
    points_delta: PropTypes.object
  })),
  currentHole: PropTypes.number
};

export default Scorecard;
