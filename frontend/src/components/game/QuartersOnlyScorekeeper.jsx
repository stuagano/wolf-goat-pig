// frontend/src/components/game/QuartersOnlyScorekeeper.jsx
// Simplified scorekeeper - just quarters per player per hole
// Only validation: each hole must sum to zero (zero-sum game)
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Zero-sum validation: all quarters for a hole must sum to zero
 */
const validateHoleSum = (holeQuarters) => {
  const values = Object.values(holeQuarters);
  if (values.length === 0) return { valid: true, sum: 0 };
  const sum = values.reduce((acc, val) => acc + (val || 0), 0);
  return { valid: sum === 0, sum };
};

/**
 * Simplified scorekeeper - just quarters per player per hole
 * No golf scores, no teams, no special rules - just the net result
 */
const QuartersOnlyScorekeeper = ({
  gameId,
  players,
  initialHoleData = {},
  initialCurrentHole = 1,
  onGameComplete,
}) => {
  const theme = useTheme();

  // Core state: quarters per hole per player
  // Shape: { 1: { playerId1: 2, playerId2: -1, playerId3: -1 }, 2: { ... }, ... }
  const [holeQuarters, setHoleQuarters] = useState(initialHoleData);
  const [currentHole, setCurrentHole] = useState(initialCurrentHole);
  const [showOptionalDetails, setShowOptionalDetails] = useState(false);

  // Optional details per hole (collapsed by default)
  // Shape: { 1: { golfScores: {...}, teams: {...}, notes: '...' }, ... }
  const [optionalDetails, setOptionalDetails] = useState({});

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [editingCell, setEditingCell] = useState(null); // { hole, playerId }
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(true);

  // Load existing game data on mount
  useEffect(() => {
    const loadGameData = async () => {
      if (!gameId) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/games/${gameId}/state`);
        if (response.ok) {
          const data = await response.json();

          // Load quarters-only data if available
          if (data.hole_quarters) {
            setHoleQuarters(data.hole_quarters);
          } else if (data.hole_history) {
            // Convert from hole_history format
            const quarters = {};
            data.hole_history.forEach(hole => {
              if (hole.points_delta) {
                quarters[hole.hole] = hole.points_delta;
              }
            });
            setHoleQuarters(quarters);
          }

          if (data.optional_details) {
            setOptionalDetails(data.optional_details);
          }

          if (data.current_hole) {
            setCurrentHole(data.current_hole);
          }
        }
      } catch (err) {
        console.error('Error loading game data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadGameData();
  }, [gameId]);

  // Calculate standings from all hole data
  const standings = useMemo(() => {
    const result = {};
    players.forEach(p => {
      result[p.id] = { name: p.name, quarters: 0 };
    });

    Object.values(holeQuarters).forEach(holeData => {
      Object.entries(holeData).forEach(([playerId, quarters]) => {
        if (result[playerId]) {
          result[playerId].quarters += quarters || 0;
        }
      });
    });

    return result;
  }, [players, holeQuarters]);

  // Validation for current hole
  const currentHoleValidation = useMemo(() => {
    const holeData = holeQuarters[currentHole] || {};
    return validateHoleSum(holeData);
  }, [holeQuarters, currentHole]);

  // Check if all holes through current have valid (zero-sum) data
  const allHolesValid = useMemo(() => {
    for (let h = 1; h <= currentHole; h++) {
      const holeData = holeQuarters[h] || {};
      const hasData = Object.keys(holeData).length > 0;
      if (hasData) {
        const validation = validateHoleSum(holeData);
        if (!validation.valid) return false;
      }
    }
    return true;
  }, [holeQuarters, currentHole]);

  // Handle quarter input for a player on a hole
  const handleQuarterChange = useCallback((hole, playerId, value) => {
    const numValue = value === '' || value === '-' ? 0 : parseInt(value, 10);
    if (isNaN(numValue)) return;

    setHoleQuarters(prev => ({
      ...prev,
      [hole]: {
        ...(prev[hole] || {}),
        [playerId]: numValue
      }
    }));
  }, []);

  // Quick buttons for common quarter values
  const quickValues = [-3, -2, -1, 0, 1, 2, 3];

  // Start editing a cell
  const startEdit = (hole, playerId) => {
    const currentValue = holeQuarters[hole]?.[playerId] || 0;
    setEditingCell({ hole, playerId });
    setInputValue(currentValue.toString());
  };

  // Finish editing
  const finishEdit = () => {
    if (editingCell) {
      handleQuarterChange(editingCell.hole, editingCell.playerId, inputValue);
    }
    setEditingCell(null);
    setInputValue('');
  };

  // Handle optional detail changes
  const handleOptionalDetailChange = (hole, field, value) => {
    setOptionalDetails(prev => ({
      ...prev,
      [hole]: {
        ...(prev[hole] || {}),
        [field]: value
      }
    }));
  };

  // Save game to backend
  const saveGame = async () => {
    if (!allHolesValid) {
      setError('All holes must sum to zero before saving');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/games/${gameId}/quarters-only`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hole_quarters: holeQuarters,
          optional_details: optionalDetails,
          current_hole: currentHole
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to save: ${response.statusText}`);
      }

      if (onGameComplete && currentHole >= 18) {
        onGameComplete(standings);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Styles
  const styles = {
    container: {
      padding: '16px',
      maxWidth: '100%',
      overflowX: 'auto',
      backgroundColor: theme.colors?.background || '#1a1a2e',
      minHeight: '100vh',
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '16px',
      flexWrap: 'wrap',
      gap: '8px',
    },
    title: {
      fontSize: '20px',
      fontWeight: 'bold',
      color: theme.colors?.text || '#fff',
    },
    standingsBar: {
      display: 'flex',
      gap: '16px',
      padding: '12px',
      backgroundColor: theme.colors?.surface || '#252542',
      borderRadius: '8px',
      marginBottom: '16px',
      flexWrap: 'wrap',
    },
    standingItem: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
    },
    playerName: {
      fontSize: '14px',
      color: theme.colors?.textSecondary || '#aaa',
    },
    quarterValue: (value) => ({
      fontSize: '20px',
      fontWeight: 'bold',
      color: value > 0 ? '#4CAF50' : value < 0 ? '#f44336' : theme.colors?.text || '#fff',
    }),
    table: {
      width: '100%',
      borderCollapse: 'collapse',
      marginBottom: '16px',
    },
    th: {
      padding: '8px',
      backgroundColor: theme.colors?.surface || '#252542',
      color: theme.colors?.text || '#fff',
      border: `1px solid ${theme.colors?.border || '#333'}`,
      fontSize: '14px',
      minWidth: '60px',
    },
    td: {
      padding: '4px',
      border: `1px solid ${theme.colors?.border || '#333'}`,
      textAlign: 'center',
      backgroundColor: theme.colors?.background || '#1a1a2e',
    },
    holeNumber: {
      fontWeight: 'bold',
      color: theme.colors?.text || '#fff',
      backgroundColor: theme.colors?.surface || '#252542',
      minWidth: '40px',
    },
    sumCell: (valid) => ({
      fontWeight: 'bold',
      color: valid ? '#4CAF50' : '#f44336',
      backgroundColor: valid ? 'rgba(76, 175, 80, 0.1)' : 'rgba(244, 67, 54, 0.1)',
    }),
    quarterCell: (value, isEditing) => ({
      cursor: 'pointer',
      backgroundColor: isEditing
        ? theme.colors?.primary || '#6366f1'
        : value > 0
          ? 'rgba(76, 175, 80, 0.2)'
          : value < 0
            ? 'rgba(244, 67, 54, 0.2)'
            : 'transparent',
      color: value > 0 ? '#4CAF50' : value < 0 ? '#f44336' : theme.colors?.text || '#fff',
      fontWeight: 'bold',
      fontSize: '16px',
      minHeight: '36px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }),
    input: {
      width: '50px',
      padding: '4px',
      textAlign: 'center',
      fontSize: '16px',
      backgroundColor: theme.colors?.surface || '#252542',
      color: theme.colors?.text || '#fff',
      border: `2px solid ${theme.colors?.primary || '#6366f1'}`,
      borderRadius: '4px',
    },
    quickButtons: {
      display: 'flex',
      gap: '4px',
      justifyContent: 'center',
      marginTop: '4px',
    },
    quickButton: (value) => ({
      padding: '4px 8px',
      fontSize: '12px',
      backgroundColor: theme.colors?.surface || '#252542',
      color: value > 0 ? '#4CAF50' : value < 0 ? '#f44336' : theme.colors?.text || '#fff',
      border: `1px solid ${theme.colors?.border || '#333'}`,
      borderRadius: '4px',
      cursor: 'pointer',
    }),
    currentHoleRow: {
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
    },
    navigationButtons: {
      display: 'flex',
      gap: '8px',
      marginBottom: '16px',
    },
    button: {
      padding: '10px 20px',
      fontSize: '14px',
      backgroundColor: theme.colors?.primary || '#6366f1',
      color: '#fff',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
    },
    buttonDisabled: {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
    error: {
      padding: '12px',
      backgroundColor: 'rgba(244, 67, 54, 0.2)',
      color: '#f44336',
      borderRadius: '8px',
      marginBottom: '16px',
    },
    validationMessage: {
      padding: '8px',
      textAlign: 'center',
      color: currentHoleValidation.valid ? '#4CAF50' : '#f44336',
      fontSize: '14px',
    },
    optionalToggle: {
      padding: '8px 16px',
      fontSize: '14px',
      backgroundColor: 'transparent',
      color: theme.colors?.textSecondary || '#aaa',
      border: `1px solid ${theme.colors?.border || '#333'}`,
      borderRadius: '8px',
      cursor: 'pointer',
    },
    optionalSection: {
      padding: '16px',
      backgroundColor: theme.colors?.surface || '#252542',
      borderRadius: '8px',
      marginBottom: '16px',
    },
    optionalTitle: {
      fontSize: '14px',
      color: theme.colors?.textSecondary || '#aaa',
      marginBottom: '8px',
    },
    optionalInput: {
      width: '100%',
      padding: '8px',
      fontSize: '14px',
      backgroundColor: theme.colors?.background || '#1a1a2e',
      color: theme.colors?.text || '#fff',
      border: `1px solid ${theme.colors?.border || '#333'}`,
      borderRadius: '4px',
    },
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={{ textAlign: 'center', padding: '40px', color: theme.colors?.text || '#fff' }}>
          Loading game data...
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.title}>Hole {currentHole} of 18</div>
        <button
          style={styles.optionalToggle}
          onClick={() => setShowOptionalDetails(!showOptionalDetails)}
        >
          {showOptionalDetails ? 'Hide Details' : 'Show Details (Optional)'}
        </button>
      </div>

      {/* Error display */}
      {error && <div style={styles.error}>{error}</div>}

      {/* Current standings */}
      <div style={styles.standingsBar}>
        {players.map(player => (
          <div key={player.id} style={styles.standingItem}>
            <span style={styles.playerName}>{player.name}</span>
            <span style={styles.quarterValue(standings[player.id]?.quarters || 0)}>
              {standings[player.id]?.quarters > 0 ? '+' : ''}{standings[player.id]?.quarters || 0}
            </span>
          </div>
        ))}
      </div>

      {/* Validation message for current hole */}
      <div style={styles.validationMessage}>
        {holeQuarters[currentHole] && Object.keys(holeQuarters[currentHole]).length > 0 ? (
          currentHoleValidation.valid
            ? '✓ Hole sums to zero'
            : `⚠ Sum: ${currentHoleValidation.sum > 0 ? '+' : ''}${currentHoleValidation.sum} (must be 0)`
        ) : (
          'Enter quarters for each player'
        )}
      </div>

      {/* Main scoring table */}
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Hole</th>
            {players.map(player => (
              <th key={player.id} style={styles.th}>{player.name}</th>
            ))}
            <th style={styles.th}>Sum</th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 18 }, (_, i) => i + 1).map(hole => {
            const holeData = holeQuarters[hole] || {};
            const validation = validateHoleSum(holeData);
            const isCurrentHole = hole === currentHole;
            const hasData = Object.keys(holeData).length > 0;

            return (
              <tr key={hole} style={isCurrentHole ? styles.currentHoleRow : {}}>
                <td style={{ ...styles.td, ...styles.holeNumber }}>{hole}</td>
                {players.map(player => {
                  const value = holeData[player.id] || 0;
                  const isEditing = editingCell?.hole === hole && editingCell?.playerId === player.id;

                  return (
                    <td
                      key={player.id}
                      style={styles.td}
                      onClick={() => !isEditing && startEdit(hole, player.id)}
                    >
                      {isEditing ? (
                        <div>
                          <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onBlur={finishEdit}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') finishEdit();
                              if (e.key === 'Escape') {
                                setEditingCell(null);
                                setInputValue('');
                              }
                            }}
                            style={styles.input}
                            autoFocus
                          />
                          <div style={styles.quickButtons}>
                            {quickValues.map(v => (
                              <button
                                key={v}
                                style={styles.quickButton(v)}
                                onMouseDown={(e) => {
                                  e.preventDefault();
                                  handleQuarterChange(hole, player.id, v);
                                  setEditingCell(null);
                                }}
                              >
                                {v > 0 ? `+${v}` : v}
                              </button>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div style={styles.quarterCell(value, isEditing)}>
                          {hasData || value !== 0 ? (value > 0 ? `+${value}` : value) : '-'}
                        </div>
                      )}
                    </td>
                  );
                })}
                <td style={{ ...styles.td, ...styles.sumCell(validation.valid) }}>
                  {hasData ? validation.sum : '-'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Optional details section */}
      {showOptionalDetails && (
        <div style={styles.optionalSection}>
          <div style={styles.optionalTitle}>
            Optional: How did hole {currentHole} play out?
          </div>
          <textarea
            style={{ ...styles.optionalInput, minHeight: '80px' }}
            placeholder="e.g., Partners mode, Team A won with birdie, Duncan invoked..."
            value={optionalDetails[currentHole]?.notes || ''}
            onChange={(e) => handleOptionalDetailChange(currentHole, 'notes', e.target.value)}
          />
        </div>
      )}

      {/* Navigation and save buttons */}
      <div style={styles.navigationButtons}>
        <button
          style={{
            ...styles.button,
            backgroundColor: theme.colors?.surface || '#252542',
            ...(currentHole <= 1 ? styles.buttonDisabled : {})
          }}
          onClick={() => setCurrentHole(Math.max(1, currentHole - 1))}
          disabled={currentHole <= 1}
        >
          ← Previous
        </button>
        <button
          style={{
            ...styles.button,
            ...(currentHole >= 18 ? styles.buttonDisabled : {})
          }}
          onClick={() => setCurrentHole(Math.min(18, currentHole + 1))}
          disabled={currentHole >= 18}
        >
          Next →
        </button>
        <button
          style={{
            ...styles.button,
            backgroundColor: '#4CAF50',
            ...(submitting || !allHolesValid ? styles.buttonDisabled : {})
          }}
          onClick={saveGame}
          disabled={submitting || !allHolesValid}
        >
          {submitting ? 'Saving...' : 'Save Game'}
        </button>
      </div>
    </div>
  );
};

QuartersOnlyScorekeeper.propTypes = {
  gameId: PropTypes.string.isRequired,
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
  })).isRequired,
  initialHoleData: PropTypes.object,
  initialCurrentHole: PropTypes.number,
  onGameComplete: PropTypes.func,
};

export default QuartersOnlyScorekeeper;
