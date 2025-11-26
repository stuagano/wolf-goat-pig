/**
 * ScoreInputField - Reusable score input component
 *
 * A consolidated score input field with built-in validation and styling.
 * Supports both simple text input and button-based quick selection.
 *
 * Replaces scattered score input implementations across:
 * - SimpleScorekeeper.jsx
 * - LargeScoringButtons.jsx
 * - Scorecard.jsx
 */

import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';
import { Input } from '../ui';
import { SCORE_CONSTRAINTS } from '../../hooks/useScoreValidation';
import '../../styles/mobile-touch.css';

/**
 * Get score label and color based on difference from par
 */
const getScoreStyle = (score, par) => {
  if (!par || !score) return { label: '', color: '#616161' };

  const diff = score - par;

  if (diff <= -3) return { label: 'Albatross', color: '#2e7d32' };
  if (diff === -2) return { label: 'Eagle', color: '#2e7d32' };
  if (diff === -1) return { label: 'Birdie', color: '#1976d2' };
  if (diff === 0) return { label: 'Par', color: '#616161' };
  if (diff === 1) return { label: 'Bogey', color: '#f57c00' };
  if (diff === 2) return { label: 'Double', color: '#d32f2f' };
  return { label: `+${diff}`, color: '#d32f2f' };
};

/**
 * ScoreInputField Component
 *
 * @param {Object} props
 * @param {Object} props.player - Player object with id, name, handicap
 * @param {number} props.value - Current score value
 * @param {Function} props.onChange - Callback when score changes (playerId, value)
 * @param {Function} props.onClear - Callback to clear the score
 * @param {number} props.holePar - Par for the current hole (enables quick buttons)
 * @param {boolean} props.showQuickButtons - Show par-relative quick selection buttons
 * @param {boolean} props.compact - Use compact styling
 * @param {boolean} props.disabled - Disable the input
 * @param {string} props.error - Error message to display
 */
const ScoreInputField = ({
  player,
  value,
  onChange,
  onClear,
  holePar = null,
  showQuickButtons = false,
  compact = false,
  disabled = false,
  error = null
}) => {
  const theme = useTheme();
  const [pressedButton, setPressedButton] = useState(null);

  // Generate quick score options based on par
  const quickScores = holePar
    ? [holePar - 2, holePar - 1, holePar, holePar + 1, holePar + 2]
    : [];

  const handleInputChange = useCallback((e) => {
    const inputValue = e.target.value;
    if (inputValue === '') {
      onChange(player.id, '');
    } else {
      const numValue = parseInt(inputValue, 10);
      if (!isNaN(numValue) && numValue >= SCORE_CONSTRAINTS.MIN_STROKES && numValue <= SCORE_CONSTRAINTS.MAX_STROKES) {
        onChange(player.id, numValue);
      }
    }
  }, [player.id, onChange]);

  const handleQuickSelect = useCallback((score) => {
    onChange(player.id, score);
  }, [player.id, onChange]);

  const handleClear = useCallback(() => {
    if (onClear) {
      onClear(player.id);
    } else {
      onChange(player.id, '');
    }
  }, [player.id, onChange, onClear]);

  const hasValue = value !== undefined && value !== null && value !== '' && value !== 0;
  const scoreStyle = holePar && hasValue ? getScoreStyle(value, holePar) : null;

  // Compact mode - just the input field
  if (compact) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <label style={{ flex: 1, fontWeight: 'bold', fontSize: '14px' }}>
          {player.name}:
        </label>
        <Input
          type="number"
          min={SCORE_CONSTRAINTS.MIN_STROKES}
          max={SCORE_CONSTRAINTS.MAX_STROKES}
          value={value || ''}
          onChange={handleInputChange}
          disabled={disabled}
          variant="inline"
          inputStyle={{
            width: '60px',
            padding: '8px',
            fontSize: '16px',
            border: `2px solid ${error ? theme.colors.error : theme.colors.border}`,
            borderRadius: '4px',
            textAlign: 'center'
          }}
        />
        {error && (
          <span style={{ color: theme.colors.error, fontSize: '12px' }}>{error}</span>
        )}
      </div>
    );
  }

  // Full mode with optional quick buttons
  return (
    <div
      className="touch-optimized"
      style={{
        background: theme.colors.paper,
        borderRadius: '16px',
        padding: '20px',
        marginBottom: '16px',
        border: `3px solid ${hasValue ? theme.colors.success : theme.colors.border}`
      }}
    >
      {/* Player Header */}
      <h3 style={{
        margin: '0 0 16px 0',
        fontSize: '24px',
        color: theme.colors.primary,
        fontWeight: 'bold'
      }}>
        {player.name}
        {player.handicap !== undefined && (
          <span style={{
            fontSize: '16px',
            color: theme.colors.textSecondary,
            fontWeight: 'normal',
            marginLeft: '10px'
          }}>
            (Hdcp {player.handicap})
          </span>
        )}
      </h3>

      {/* Quick Score Buttons */}
      {showQuickButtons && quickScores.length > 0 && (
        <div
          className="score-grid-mobile"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(5, 1fr)',
            gap: '12px',
            marginBottom: '12px'
          }}
        >
          {quickScores.map(score => {
            const style = getScoreStyle(score, holePar);
            const isSelected = value === score;
            const buttonId = `score-${player.id}-${score}`;
            const isPressedScore = pressedButton === buttonId;

            return (
              <button
                key={score}
                onClick={() => handleQuickSelect(score)}
                disabled={disabled}
                className="touch-optimized"
                style={{
                  minHeight: '90px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  padding: '12px',
                  border: isSelected ? `4px solid ${style.color}` : '3px solid #e0e0e0',
                  borderRadius: '12px',
                  background: isSelected ? `${style.color}25` : 'white',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                  transition: 'all 0.15s ease',
                  fontWeight: isSelected ? 'bold' : 'normal',
                  transform: isPressedScore ? 'scale(0.95)' : 'scale(1)',
                  touchAction: 'manipulation',
                  opacity: disabled ? 0.5 : 1
                }}
                onTouchStart={() => !disabled && setPressedButton(buttonId)}
                onTouchEnd={() => !disabled && setPressedButton(null)}
                onTouchCancel={() => !disabled && setPressedButton(null)}
                onMouseDown={() => !disabled && setPressedButton(buttonId)}
                onMouseUp={() => !disabled && setPressedButton(null)}
                onMouseLeave={() => !disabled && setPressedButton(null)}
              >
                <span style={{
                  fontSize: '28px',
                  fontWeight: 'bold',
                  color: style.color
                }}>
                  {score}
                </span>
                <span style={{
                  fontSize: '13px',
                  color: style.color,
                  fontWeight: 'bold',
                  textTransform: 'uppercase'
                }}>
                  {style.label}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Custom Score Input */}
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <Input
          type="number"
          placeholder={showQuickButtons ? "Other score..." : "Enter score"}
          value={hasValue && (!showQuickButtons || !quickScores.includes(value)) ? value : ''}
          onChange={handleInputChange}
          disabled={disabled}
          min={SCORE_CONSTRAINTS.MIN_STROKES}
          max={SCORE_CONSTRAINTS.MAX_STROKES}
          variant="inline"
          inputStyle={{
            flex: 1,
            padding: '16px',
            fontSize: '20px',
            border: `3px solid ${error ? theme.colors.error : theme.colors.border}`,
            borderRadius: '12px',
            background: theme.colors.background,
            minHeight: '60px'
          }}
        />
        {hasValue && (
          <button
            onClick={handleClear}
            disabled={disabled}
            className="touch-optimized"
            style={{
              padding: '16px 20px',
              fontSize: '20px',
              border: 'none',
              borderRadius: '12px',
              background: theme.colors.error,
              color: 'white',
              cursor: disabled ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              minHeight: '60px',
              touchAction: 'manipulation',
              opacity: disabled ? 0.5 : 1
            }}
          >
            Clear
          </button>
        )}
      </div>

      {/* Score Confirmation Badge */}
      {hasValue && (
        <div style={{
          marginTop: '12px',
          padding: '8px',
          background: scoreStyle ? scoreStyle.color : theme.colors.success,
          color: 'white',
          borderRadius: '8px',
          textAlign: 'center',
          fontWeight: 'bold',
          fontSize: '16px'
        }}>
          Score: {value} {scoreStyle && `(${scoreStyle.label})`}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{
          marginTop: '8px',
          padding: '8px',
          background: '#ffebee',
          color: theme.colors.error,
          borderRadius: '4px',
          fontSize: '14px'
        }}>
          {error}
        </div>
      )}
    </div>
  );
};

ScoreInputField.propTypes = {
  player: PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    handicap: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
  }).isRequired,
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  onChange: PropTypes.func.isRequired,
  onClear: PropTypes.func,
  holePar: PropTypes.number,
  showQuickButtons: PropTypes.bool,
  compact: PropTypes.bool,
  disabled: PropTypes.bool,
  error: PropTypes.string
};

export default ScoreInputField;
