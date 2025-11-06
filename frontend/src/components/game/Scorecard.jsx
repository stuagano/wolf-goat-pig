// frontend/src/components/game/Scorecard.jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Card, Button } from '../ui';
import { useTheme } from '../../theme/Provider';

/**
 * Scorecard component for real game mode
 * Displays all 18 holes with strokes and quarters, with click-to-edit functionality
 */
const Scorecard = ({ players = [], holeHistory = [], currentHole = 1, onEditHole }) => {
  const theme = useTheme();
  const [editingHole, setEditingHole] = useState(null);
  const [editingPlayer, setEditingPlayer] = useState(null);
  const [editStrokes, setEditStrokes] = useState('');
  const [editQuarters, setEditQuarters] = useState('');

  // Create a scorecard data structure
  const holes = Array.from({ length: 18 }, (_, i) => i + 1);

  // Get hole data for a player
  const getHoleData = (holeNumber, playerId) => {
    const holeData = holeHistory.find(h => h.hole === holeNumber);
    if (!holeData) return { quarters: null, strokes: null };

    const pointsDelta = holeData.points_delta || {};
    const grossScores = holeData.gross_scores || {};

    return {
      quarters: pointsDelta[playerId] || 0,
      strokes: grossScores[playerId] || null
    };
  };

  // Calculate front 9, back 9, and total
  const calculateTotals = (playerId) => {
    const front9 = holes.slice(0, 9).reduce((sum, hole) => {
      const { quarters } = getHoleData(hole, playerId);
      return sum + (quarters || 0);
    }, 0);

    const back9 = holes.slice(9, 18).reduce((sum, hole) => {
      const { quarters } = getHoleData(hole, playerId);
      return sum + (quarters || 0);
    }, 0);

    return { front9, back9, total: front9 + back9 };
  };

  // Handle clicking on a hole cell to edit
  const handleCellClick = (hole, playerId) => {
    const isCurrentHole = hole === currentHole;
    const isCompleted = hole < currentHole || (holeHistory.find(h => h.hole === hole));

    if (!isCurrentHole && !isCompleted) {
      return; // Don't allow editing future holes
    }

    const { strokes, quarters } = getHoleData(hole, playerId);
    setEditingHole(hole);
    setEditingPlayer(playerId);
    setEditStrokes(strokes?.toString() || '');
    setEditQuarters(quarters?.toString() || '0');
  };

  // Handle saving the edit
  const handleSaveEdit = () => {
    if (onEditHole && editingHole && editingPlayer) {
      onEditHole({
        hole: editingHole,
        playerId: editingPlayer,
        strokes: editStrokes ? parseInt(editStrokes, 10) : null,
        quarters: editQuarters ? parseInt(editQuarters, 10) : 0
      });
    }
    setEditingHole(null);
    setEditingPlayer(null);
    setEditStrokes('');
    setEditQuarters('');
  };

  // Handle canceling the edit
  const handleCancelEdit = () => {
    setEditingHole(null);
    setEditingPlayer(null);
    setEditStrokes('');
    setEditQuarters('');
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
                    const { quarters, strokes } = getHoleData(hole, player.id);
                    const isCurrentHole = hole === currentHole;
                    const isCompleted = hole < currentHole || (holeHistory.find(h => h.hole === hole));

                    return (
                      <td
                        key={hole}
                        style={{
                          ...cellStyle,
                          backgroundColor: isCurrentHole ? 'rgba(255, 215, 0, 0.1)' : 'transparent',
                          fontWeight: (quarters && quarters !== 0) || strokes ? 'bold' : 'normal',
                          color: quarters > 0 ? '#4CAF50' : quarters < 0 ? '#f44336' : theme.colors.textSecondary,
                          cursor: isCurrentHole || isCompleted ? 'pointer' : 'default'
                        }}
                        title={isCurrentHole || isCompleted ? 'Click to edit' : ''}
                        onClick={() => handleCellClick(hole, player.id)}
                      >
                        {isCompleted ? (
                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight: '1.2' }}>
                            <div style={{ fontSize: '11px', fontWeight: 'bold' }}>
                              {strokes || '-'}
                            </div>
                            <div style={{ fontSize: '9px', marginTop: '2px' }}>
                              {quarters !== null && quarters !== 0 ? (
                                quarters > 0 ? `+${quarters}` : quarters
                              ) : '·'}
                            </div>
                          </div>
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

      {/* Edit Modal */}
      {editingHole && editingPlayer && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <Card style={{
            maxWidth: '400px',
            width: '90%',
            padding: '24px'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '16px' }}>
              Edit Hole {editingHole} - {players.find(p => p.id === editingPlayer)?.name}
            </h3>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                Strokes:
              </label>
              <input
                type="number"
                value={editStrokes}
                onChange={(e) => setEditStrokes(e.target.value)}
                min="0"
                max="15"
                style={{
                  width: '100%',
                  padding: '8px',
                  fontSize: '16px',
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: '4px'
                }}
              />
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                Quarters (points):
              </label>
              <input
                type="number"
                value={editQuarters}
                onChange={(e) => setEditQuarters(e.target.value)}
                min="-10"
                max="10"
                style={{
                  width: '100%',
                  padding: '8px',
                  fontSize: '16px',
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: '4px'
                }}
              />
              <p style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '4px' }}>
                Positive for winning, negative for losing
              </p>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <Button variant="secondary" onClick={handleCancelEdit}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSaveEdit}>
                Save
              </Button>
            </div>
          </Card>
        </div>
      )}
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
    points_delta: PropTypes.object,
    gross_scores: PropTypes.object
  })),
  currentHole: PropTypes.number,
  onEditHole: PropTypes.func
};

export default Scorecard;
