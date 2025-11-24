// frontend/src/components/game/Scorecard.jsx
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Card, Button, Input } from '../ui';
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

  // Debug logging with safe array/object access
  useEffect(() => {
    console.log('[Scorecard] Received data:', {
      players: Array.isArray(players) ? players.map(p => p && p.id ? ({ id: p.id, name: p.name || 'Unknown' }) : null).filter(Boolean) : [],
      holeHistoryLength: Array.isArray(holeHistory) ? holeHistory.length : 0,
      currentHole: typeof currentHole === 'number' ? currentHole : 1,
      courseHolesLength: Array.isArray(courseHoles) ? courseHoles.length : 0,
      hasStrokeAllocation: strokeAllocation && typeof strokeAllocation === 'object' ? Object.keys(strokeAllocation).length > 0 : false,
      holeHistory: Array.isArray(holeHistory) ? holeHistory : [],
      courseHoles: Array.isArray(courseHoles) ? courseHoles : [],
      strokeAllocation: strokeAllocation && typeof strokeAllocation === 'object' ? strokeAllocation : {}
    });
  }, [players, holeHistory, currentHole, courseHoles, strokeAllocation]);

  // Create a scorecard data structure
  const holes = Array.from({ length: 18 }, (_, i) => i + 1);

  // Get course hole info (par, handicap, yards)
  const getCourseHoleInfo = (holeNumber) => {
    if (!Array.isArray(courseHoles) || courseHoles.length === 0) return null;
    if (typeof holeNumber !== 'number' || holeNumber < 1 || holeNumber > 18) return null;
    const holeInfo = courseHoles.find(h => h && typeof h.hole === 'number' && h.hole === holeNumber);
    return holeInfo || null;
  };

  // Get stroke allocation for a player on a hole
  const getStrokesReceived = (playerId, holeNumber) => {
    if (!strokeAllocation || typeof strokeAllocation !== 'object') return 0;
    if (!playerId || typeof holeNumber !== 'number') return 0;
    const playerAllocation = strokeAllocation[playerId];
    if (!playerAllocation || typeof playerAllocation !== 'object') return 0;
    const strokes = playerAllocation[holeNumber];
    return typeof strokes === 'number' ? strokes : 0;
  };

  // Get hole data for a player
  const getHoleData = (holeNumber, playerId) => {
    if (!Array.isArray(holeHistory)) return { quarters: null, strokes: null };
    if (typeof holeNumber !== 'number' || !playerId) return { quarters: null, strokes: null };

    const holeData = holeHistory.find(h => h && typeof h.hole === 'number' && h.hole === holeNumber);
    if (!holeData) return { quarters: null, strokes: null };

    const pointsDelta = (holeData.points_delta && typeof holeData.points_delta === 'object')
      ? holeData.points_delta
      : {};
    const grossScores = (holeData.gross_scores && typeof holeData.gross_scores === 'object')
      ? holeData.gross_scores
      : {};

    const quarters = pointsDelta[playerId];
    const strokes = grossScores[playerId];

    return {
      quarters: typeof quarters === 'number' ? quarters : null,
      strokes: typeof strokes === 'number' ? strokes : null
    };
  };

  // Calculate front 9, back 9, and total
  const calculateTotals = (playerId) => {
    if (!playerId) return { front9: 0, back9: 0, total: 0 };

    const front9 = holes.slice(0, 9).reduce((sum, hole) => {
      const { quarters } = getHoleData(hole, playerId);
      const quarterValue = typeof quarters === 'number' ? quarters : 0;
      return sum + quarterValue;
    }, 0);

    const back9 = holes.slice(9, 18).reduce((sum, hole) => {
      const { quarters } = getHoleData(hole, playerId);
      const quarterValue = typeof quarters === 'number' ? quarters : 0;
      return sum + quarterValue;
    }, 0);

    return { front9, back9, total: front9 + back9 };
  };

  // Handle clicking on a hole cell to edit
  const handleCellClick = (hole, playerId) => {
    if (typeof hole !== 'number' || !playerId) return;

    const isCurrentHole = hole === currentHole;
    const isCompleted = hole < currentHole || (Array.isArray(holeHistory) && holeHistory.find(h => h && h.hole === hole));

    if (!isCurrentHole && !isCompleted) {
      return; // Don't allow editing future holes
    }

    const { strokes, quarters } = getHoleData(hole, playerId);
    setEditingHole(hole);
    setEditingPlayer(playerId);
    setEditStrokes(typeof strokes === 'number' ? strokes.toString() : '');
    setEditQuarters(typeof quarters === 'number' ? quarters.toString() : '0');
  };

  // Handle saving the edit
  const handleSaveEdit = () => {
    if (!onEditHole || !editingHole || !editingPlayer) return;

    // Validate and parse strokes
    const parsedStrokes = editStrokes ? parseInt(editStrokes, 10) : null;
    if (parsedStrokes !== null && (isNaN(parsedStrokes) || parsedStrokes < 0 || parsedStrokes > 15)) {
      console.error('Invalid strokes value:', editStrokes);
      alert('Strokes must be a number between 0 and 15');
      return;
    }

    // Validate and parse quarters
    const parsedQuarters = editQuarters ? parseFloat(editQuarters) : 0;
    if (isNaN(parsedQuarters) || parsedQuarters < -10 || parsedQuarters > 10) {
      console.error('Invalid quarters value:', editQuarters);
      alert('Quarters must be a number between -10 and 10');
      return;
    }

    onEditHole({
      hole: editingHole,
      playerId: editingPlayer,
      strokes: parsedStrokes,
      quarters: parsedQuarters
    });

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
    if (!playerId || typeof currentName !== 'string') return;
    setEditingPlayerName(playerId);
    setEditPlayerNameValue(currentName);
  };

  // Handle saving the player name edit
  const handleSavePlayerName = async () => {
    if (!editingPlayerName || !onPlayerNameChange) return;

    const trimmedName = editPlayerNameValue?.trim();
    if (!trimmedName || trimmedName.length === 0) {
      alert('Player name cannot be empty');
      return;
    }

    if (trimmedName.length > 50) {
      alert('Player name must be 50 characters or less');
      return;
    }

    try {
      await onPlayerNameChange(editingPlayerName, trimmedName);
      setEditingPlayerName(null);
      setEditPlayerNameValue('');
    } catch (error) {
      console.error('Failed to update player name:', error);
      alert('Failed to update player name. Please try again.');
    }
  };

  // Handle canceling the player name edit
  const handleCancelPlayerNameEdit = () => {
    setEditingPlayerName(null);
    setEditPlayerNameValue('');
  };

  // Standings View Component (for simulations)
  const StandingsView = () => {
    if (!Array.isArray(players) || players.length === 0) {
      return <div style={{ padding: '20px', textAlign: 'center', color: theme.colors.textSecondary }}>No players available</div>;
    }

    return (
      <div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          {players.map(player => {
            if (!player || !player.id) return null;

            const totals = calculateTotals(player.id);
            const isCaptain = player.id === captainId;
            const isHuman = player.is_human || player.id === 'human';
            const playerName = typeof player.name === 'string' ? player.name : 'Unknown';
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
            {Array.isArray(courseHoles) && courseHoles.length > 0 && (
              <>
                <tr style={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                  <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '10px' }}>PAR</td>
                  {holes.map(hole => {
                    const holeInfo = getCourseHoleInfo(hole);
                    const par = holeInfo && typeof holeInfo.par === 'number' ? holeInfo.par : '-';
                    return (
                      <td key={`par-${hole}`} style={{ ...cellStyle, fontSize: '10px', textAlign: 'center' }}>
                        {par}
                      </td>
                    );
                  })}
                  <td style={{ ...totalCellStyle, fontSize: '10px' }}>
                    {courseHoles.slice(0, 9).reduce((sum, h) => sum + (h && typeof h.par === 'number' ? h.par : 0), 0)}
                  </td>
                  <td style={{ ...totalCellStyle, fontSize: '10px' }}>
                    {courseHoles.slice(9, 18).reduce((sum, h) => sum + (h && typeof h.par === 'number' ? h.par : 0), 0)}
                  </td>
                  <td style={{ ...totalCellStyle, fontWeight: 'bold', fontSize: '10px' }}>
                    {courseHoles.reduce((sum, h) => sum + (h && typeof h.par === 'number' ? h.par : 0), 0)}
                  </td>
                </tr>
                <tr style={{ backgroundColor: 'rgba(0, 0, 0, 0.04)' }}>
                  <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '9px' }}>HDCP</td>
                  {holes.map(hole => {
                    const holeInfo = getCourseHoleInfo(hole);
                    const handicap = holeInfo && typeof holeInfo.handicap === 'number' ? holeInfo.handicap : '-';
                    return (
                      <td key={`hdcp-${hole}`} style={{ ...cellStyle, fontSize: '9px', textAlign: 'center' }}>
                        {handicap}
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
            {Array.isArray(players) && players.map((player, idx) => {
              if (!player || !player.id) return null;

              const totals = calculateTotals(player.id);
              const isHuman = player.is_human || player.id === 'human';
              const playerName = typeof player.name === 'string' ? player.name : 'Unknown';

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
                    {playerName}
                    {onPlayerNameChange && <span style={{ fontSize: '10px', marginLeft: '4px', opacity: 0.5 }}>✏️</span>}
                  </td>
                  {holes.map(hole => {
                    const { quarters, strokes } = getHoleData(hole, player.id);
                    const isCurrentHole = hole === currentHole;
                    const isCompleted = hole < currentHole || (Array.isArray(holeHistory) && holeHistory.find(h => h && h.hole === hole));
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
              Edit Hole {editingHole} - {Array.isArray(players) && players.find(p => p && p.id === editingPlayer)?.name || 'Unknown'}
            </h3>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                Strokes (Gross Score):
              </label>
              <Input
                type="number"
                value={editStrokes}
                onChange={(e) => setEditStrokes(e.target.value)}
                min="0"
                max="15"
                variant="inline"
                inputStyle={{
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
              <Input
                type="number"
                value={editQuarters}
                onChange={(e) => setEditQuarters(e.target.value)}
                min="-10"
                max="10"
                step="0.5"
                variant="inline"
                inputStyle={{
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
              <Input
                type="text"
                value={editPlayerNameValue}
                onChange={(e) => setEditPlayerNameValue(e.target.value)}
                placeholder="Enter player name"
                maxLength="50"
                autoFocus
                variant="inline"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSavePlayerName();
                  }
                }}
                inputStyle={{
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
  // Array of player objects
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    points: PropTypes.number,
    handicap: PropTypes.number,
    is_human: PropTypes.bool
  })).isRequired,

  // Array of completed hole data
  holeHistory: PropTypes.arrayOf(PropTypes.shape({
    hole: PropTypes.number.isRequired,
    // Object mapping playerId -> quarters won/lost
    points_delta: PropTypes.objectOf(PropTypes.number),
    // Object mapping playerId -> gross score
    gross_scores: PropTypes.objectOf(PropTypes.number)
  })).isRequired,

  // Current hole number (1-18)
  currentHole: PropTypes.number,

  // Callback when user edits a hole: (data: {hole, playerId, strokes, quarters}) => void
  onEditHole: PropTypes.func,

  // Optional: Callback for player name changes in simulation mode
  onPlayerNameChange: PropTypes.func,

  // Optional: Captain ID for highlighting in standings view
  captainId: PropTypes.string,

  // Course hole information (par, handicap, yards)
  courseHoles: PropTypes.arrayOf(PropTypes.shape({
    hole: PropTypes.number.isRequired,
    par: PropTypes.number,
    handicap: PropTypes.number, // Stroke index (1-18)
    yards: PropTypes.number
  })).isRequired,

  // Stroke allocation: { playerId: { holeNumber: strokes } }
  // e.g., { "player1": { 1: 1, 2: 0, 3: 0.5, ... } }
  strokeAllocation: PropTypes.objectOf(
    PropTypes.objectOf(PropTypes.number)
  ).isRequired
};

// Default props to ensure we never work with undefined arrays
Scorecard.defaultProps = {
  players: [],
  holeHistory: [],
  courseHoles: [],
  strokeAllocation: {},
  currentHole: 1
};

export default Scorecard;
