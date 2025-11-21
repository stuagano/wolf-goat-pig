// frontend/src/components/game/Scorecard.jsx
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Card, Button } from '../ui';
import { useTheme } from '../../theme/Provider';

/**
 * Unified Scorecard component for both real games and simulations
 * Displays all 18 holes with strokes and quarters, with click-to-edit functionality
 *
 * Optional features (enabled via props):
 * - Player name editing (onPlayerNameChange)
 * - Standings view toggle (captainId)
 */
const Scorecard = ({
  players = [],
  holeHistory = [],
  currentHole = 1,
  onEditHole,
  onPlayerNameChange, // Optional: enables player name editing in simulations
  captainId, // Optional: enables standings view and captain highlighting
  courseHoles = [],
  strokeAllocation = {}
}) => {
  const theme = useTheme();
  const [editingHole, setEditingHole] = useState(null);
  const [editingPlayer, setEditingPlayer] = useState(null);
  const [editStrokes, setEditStrokes] = useState('');
  const [editQuarters, setEditQuarters] = useState('');
  const [viewMode, setViewMode] = useState('scorecard'); // 'scorecard' or 'standings'
  const [editingPlayerName, setEditingPlayerName] = useState(null);
  const [editPlayerNameValue, setEditPlayerNameValue] = useState('');

  // Debug logging
  useEffect(() => {
    console.log('[Scorecard] Received data:', {
      players: players.map(p => ({ id: p.id, name: p.name })),
      holeHistoryLength: holeHistory.length,
      currentHole,
      courseHolesLength: courseHoles.length,
      hasStrokeAllocation: Object.keys(strokeAllocation).length > 0,
      holeHistory: holeHistory,
      courseHoles: courseHoles,
      strokeAllocation: strokeAllocation
    });
  }, [players, holeHistory, currentHole, courseHoles, strokeAllocation]);

  // Create a scorecard data structure
  const holes = Array.from({ length: 18 }, (_, i) => i + 1);

  // Get course hole info (par, handicap, yards)
  const getCourseHoleInfo = (holeNumber) => {
    if (!courseHoles || courseHoles.length === 0) return null;
    return courseHoles.find(h => h.hole === holeNumber);
  };

  // Get stroke allocation for a player on a hole
  const getStrokesReceived = (playerId, holeNumber) => {
    if (!strokeAllocation || !strokeAllocation[playerId]) return 0;
    return strokeAllocation[playerId][holeNumber] || 0;
  };

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

  // Handle clicking on a player name to edit it (simulation mode only)
  const handlePlayerNameClick = (playerId, currentName) => {
    setEditingPlayerName(playerId);
    setEditPlayerNameValue(currentName);
  };

  // Handle saving the player name edit
  const handleSavePlayerName = async () => {
    if (editingPlayerName && editPlayerNameValue.trim() && onPlayerNameChange) {
      try {
        await onPlayerNameChange(editingPlayerName, editPlayerNameValue.trim());
      } catch (error) {
        console.error('Failed to update player name:', error);
        alert('Failed to update player name. Please try again.');
      }
    }
    setEditingPlayerName(null);
    setEditPlayerNameValue('');
  };

  // Handle canceling the player name edit
  const handleCancelPlayerNameEdit = () => {
    setEditingPlayerName(null);
    setEditPlayerNameValue('');
  };

  // Standings View Component (for simulations)
  const StandingsView = () => (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
        {players.map(player => {
          const totals = calculateTotals(player.id);
          const isCaptain = player.id === captainId;
          const isHuman = player.is_human || player.id === 'human';

          return (
            <div key={player.id} style={{
              padding: '12px',
              background: 'white',
              borderRadius: '8px',
              border: `2px solid ${isCaptain ? theme.colors.primary : theme.colors.border}`
            }}>
              <div style={{ fontWeight: 'bold', fontSize: 16, marginBottom: 4 }}>
                {isHuman ? '👤 ' : '🤖 '}
                {player.name} {isCaptain && '⭐'}
              </div>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: totals.total >= 0 ? theme.colors.success : theme.colors.error }}>
                {totals.total > 0 ? '+' : ''}{totals.total}q
              </div>
              <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                Hdcp: {player.handicap}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <Card style={{ height: '100%', overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 'bold' }}>
          📊 SCORECARD
        </h3>
        {/* View toggle button - only show in simulation mode (when captainId is provided) */}
        {captainId && (
          <Button
            variant="secondary"
            onClick={() => setViewMode(viewMode === 'scorecard' ? 'standings' : 'scorecard')}
            style={{ padding: '6px 12px', fontSize: '12px' }}
          >
            {viewMode === 'scorecard' ? '📊 Standings' : '📋 Scorecard'}
          </Button>
        )}
      </div>

      {viewMode === 'standings' ? (
        <StandingsView />
      ) : (
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
            {courseHoles && courseHoles.length > 0 && (
              <>
                <tr style={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '10px' }}>PAR</td>
                  {holes.map(hole => {
                    const holeInfo = getCourseHoleInfo(hole);
                    return (
                      <td key={`par-${hole}`} style={{ ...cellStyle, fontSize: '10px', textAlign: 'center' }}>
                        {holeInfo?.par || '-'}
                      </td>
                    );
                  })}
                  <td style={{ ...totalCellStyle, fontSize: '10px' }}>
                    {courseHoles.slice(0, 9).reduce((sum, h) => sum + (h.par || 0), 0)}
                  </td>
                  <td style={{ ...totalCellStyle, fontSize: '10px' }}>
                    {courseHoles.slice(9, 18).reduce((sum, h) => sum + (h.par || 0), 0)}
                  </td>
                  <td style={{ ...totalCellStyle, fontWeight: 'bold', fontSize: '10px' }}>
                    {courseHoles.reduce((sum, h) => sum + (h.par || 0), 0)}
                  </td>
                </tr>
                <tr style={{ backgroundColor: 'rgba(0, 0, 0, 0.04)' }}>
                  <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '9px' }}>HDCP</td>
                  {holes.map(hole => {
                    const holeInfo = getCourseHoleInfo(hole);
                    return (
                      <td key={`hdcp-${hole}`} style={{ ...cellStyle, fontSize: '9px', textAlign: 'center' }}>
                        {holeInfo?.handicap || '-'}
                      </td>
                    );
                  })}
                  <td style={{ ...totalCellStyle, fontSize: '9px' }}>-</td>
                  <td style={{ ...totalCellStyle, fontSize: '9px' }}>-</td>
                  <td style={{ ...totalCellStyle, fontSize: '9px' }}>-</td>
                </tr>
              </>
            )}
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
                  <td
                    style={{
                      ...cellStyle,
                      fontWeight: 'bold',
                      maxWidth: '100px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      cursor: onPlayerNameChange ? 'pointer' : 'default',
                      position: 'relative'
                    }}
                    onClick={() => onPlayerNameChange && handlePlayerNameClick(player.id, player.name)}
                    title={onPlayerNameChange ? 'Click to edit name' : ''}
                  >
                    {isHuman ? '👤 ' : '🤖 '}
                    {player.name}
                    {onPlayerNameChange && <span style={{ fontSize: '10px', marginLeft: '4px', opacity: 0.5 }}>✏️</span>}
                  </td>
                  {holes.map(hole => {
                    const { quarters, strokes } = getHoleData(hole, player.id);
                    const isCurrentHole = hole === currentHole;
                    const isCompleted = hole < currentHole || (holeHistory.find(h => h.hole === hole));
                    const strokesReceived = getStrokesReceived(player.id, hole);

                    return (
                      <td
                        key={hole}
                        style={{
                          ...cellStyle,
                          backgroundColor: isCurrentHole ? 'rgba(255, 215, 0, 0.1)' : 'transparent',
                          fontWeight: (quarters && quarters !== 0) || strokes ? 'bold' : 'normal',
                          color: quarters > 0 ? '#4CAF50' : quarters < 0 ? '#f44336' : theme.colors.textSecondary,
                          cursor: isCurrentHole || isCompleted ? 'pointer' : 'default',
                          position: 'relative'
                        }}
                        title={isCurrentHole || isCompleted ? 'Click to edit' : ''}
                        onClick={() => handleCellClick(hole, player.id)}
                      >
                        {isCompleted ? (
                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight: '1.2' }}>
                            <div style={{ fontSize: '11px', fontWeight: 'bold' }}>
                              {strokes || '-'}
                              {strokesReceived === 1 && (
                                <span style={{ color: theme.colors.accent, marginLeft: '2px' }} title="Gets 1 stroke">●</span>
                              )}
                              {strokesReceived === 0.5 && (
                                <span style={{ color: theme.colors.warning, marginLeft: '2px' }} title="Gets 0.5 stroke">◐</span>
                              )}
                              {strokesReceived > 1 && (
                                <span style={{ color: theme.colors.accent, marginLeft: '2px', fontSize: '8px' }} title={`Gets ${strokesReceived} strokes`}>●{strokesReceived}</span>
                              )}
                            </div>
                            <div style={{ fontSize: '9px', marginTop: '2px' }}>
                              {quarters !== null && quarters !== 0 ? (
                                quarters > 0 ? `+${quarters}` : quarters
                              ) : '·'}
                            </div>
                          </div>
                        ) : (
                          strokesReceived > 0 && (
                            <div style={{ fontSize: '10px', color: theme.colors.textSecondary }}>
                              {strokesReceived === 1 && <span title="Gets 1 stroke">●</span>}
                              {strokesReceived === 0.5 && <span title="Gets 0.5 stroke">◐</span>}
                              {strokesReceived > 1 && <span title={`Gets ${strokesReceived} strokes`}>●{strokesReceived}</span>}
                            </div>
                          )
                        )}
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
      )}

      {/* Edit Hole Modal */}
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
                Strokes (Gross Score):
              </label>
              <input
                type="number"
                value={editStrokes}
                onChange={(e) => setEditStrokes(e.target.value)}
                min="0"
                max="15"
                autoComplete="off"
                data-lpignore="true"
                data-form-type="other"
                data-1p-ignore="true"
                style={{
                  width: '100%',
                  padding: '8px',
                  fontSize: '16px',
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: '4px'
                }}
              />
              <p style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '4px' }}>
                Actual number of strokes taken on this hole
              </p>
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                Quarters (Manual Override):
              </label>
              <input
                type="number"
                value={editQuarters}
                onChange={(e) => setEditQuarters(e.target.value)}
                min="-10"
                max="10"
                step="0.5"
                autoComplete="off"
                data-lpignore="true"
                data-form-type="other"
                data-1p-ignore="true"
                style={{
                  width: '100%',
                  padding: '8px',
                  fontSize: '16px',
                  border: `2px solid ${theme.colors.warning || '#ff9800'}`,
                  borderRadius: '4px',
                  backgroundColor: 'rgba(255, 152, 0, 0.05)'
                }}
              />
              <p style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '4px' }}>
                ⚠️ Override automatic quarter calculation. Use when scores are correct but quarters are wrong.
                <br />
                Positive for winning (+), negative for losing (-)
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

      {/* Edit Player Name Modal (simulation mode only) */}
      {editingPlayerName && onPlayerNameChange && (
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
          zIndex: 1001
        }}>
          <Card style={{
            maxWidth: '400px',
            width: '90%',
            padding: '24px'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '16px' }}>
              Edit Player Name
            </h3>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                Player Name:
              </label>
              <input
                type="text"
                value={editPlayerNameValue}
                onChange={(e) => setEditPlayerNameValue(e.target.value)}
                placeholder="Enter player name"
                maxLength="50"
                autoFocus
                autoComplete="off"
                data-lpignore="true"
                data-form-type="other"
                data-1p-ignore="true"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSavePlayerName();
                  }
                }}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '16px',
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: '4px'
                }}
              />
              <p style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '4px' }}>
                Press Enter to save, or click Save button
              </p>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <Button variant="secondary" onClick={handleCancelPlayerNameEdit}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handleSavePlayerName}>
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
    handicap: PropTypes.number,
    is_human: PropTypes.bool
  })),
  holeHistory: PropTypes.arrayOf(PropTypes.shape({
    hole: PropTypes.number.isRequired,
    points_delta: PropTypes.object,
    gross_scores: PropTypes.object
  })),
  currentHole: PropTypes.number,
  onEditHole: PropTypes.func,
  onPlayerNameChange: PropTypes.func, // Optional: enables player name editing
  captainId: PropTypes.string, // Optional: enables standings view
  courseHoles: PropTypes.arrayOf(PropTypes.shape({
    hole: PropTypes.number.isRequired,
    par: PropTypes.number,
    handicap: PropTypes.number,
    yards: PropTypes.number
  })),
  strokeAllocation: PropTypes.object
};

export default Scorecard;
