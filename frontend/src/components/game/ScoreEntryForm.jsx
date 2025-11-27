/**
 * ScoreEntryForm - Score entry section extracted from SimpleScorekeeper
 *
 * Handles the score input section for all players on a hole.
 * Uses the new useScoreInput hook and ScoreInputField component.
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';
import ScoreInputField from './ScoreInputField';

/**
 * ScoreEntryForm Component
 *
 * @param {Object} props
 * @param {Array} props.players - Array of player objects
 * @param {Object} props.scores - Current scores object { playerId: score }
 * @param {Function} props.onScoreChange - Callback when score changes (playerId, value)
 * @param {Function} props.onClearScore - Callback to clear a score (playerId)
 * @param {number} props.holePar - Par for the current hole
 * @param {boolean} props.showQuickButtons - Show par-relative quick selection buttons
 * @param {boolean} props.compact - Use compact layout (grid instead of stacked)
 * @param {boolean} props.disabled - Disable all inputs
 */
const ScoreEntryForm = ({
  players,
  scores,
  onScoreChange,
  onClearScore,
  holePar = null,
  showQuickButtons = false,
  compact = false,
  disabled = false
}) => {
  const theme = useTheme();

  if (compact) {
    return (
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 12px' }}>Enter Scores</h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '12px'
        }}>
          {players.map(player => (
            <ScoreInputField
              key={player.id}
              player={player}
              value={scores[player.id]}
              onChange={onScoreChange}
              onClear={onClearScore}
              holePar={holePar}
              compact={true}
              disabled={disabled}
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: theme.colors.paper,
      padding: '20px',
      borderRadius: '16px',
      marginBottom: '20px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <h2 style={{
          margin: 0,
          fontSize: '26px',
          color: theme.colors.primary,
          fontWeight: 'bold'
        }}>
          Enter Scores
        </h2>
        {holePar && (
          <div style={{
            padding: '10px 16px',
            background: theme.colors.accent,
            color: 'white',
            borderRadius: '12px',
            fontSize: '18px',
            fontWeight: 'bold',
            minHeight: '50px',
            display: 'flex',
            alignItems: 'center'
          }}>
            Par {holePar}
          </div>
        )}
      </div>

      {players.map(player => (
        <ScoreInputField
          key={player.id}
          player={player}
          value={scores[player.id]}
          onChange={onScoreChange}
          onClear={onClearScore}
          holePar={holePar}
          showQuickButtons={showQuickButtons}
          disabled={disabled}
        />
      ))}
    </div>
  );
};

ScoreEntryForm.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    handicap: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
  })).isRequired,
  scores: PropTypes.object.isRequired,
  onScoreChange: PropTypes.func.isRequired,
  onClearScore: PropTypes.func,
  holePar: PropTypes.number,
  showQuickButtons: PropTypes.bool,
  compact: PropTypes.bool,
  disabled: PropTypes.bool
};

export default ScoreEntryForm;
