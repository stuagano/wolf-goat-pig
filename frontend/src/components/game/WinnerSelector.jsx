/**
 * WinnerSelector - Winner selection component
 *
 * Extracted from SimpleScorekeeper to handle winner selection
 * with proper options based on team mode (partners vs solo).
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';

/**
 * WinnerSelector Component
 *
 * @param {Object} props
 * @param {string} props.teamMode - Current team mode ('partners' or 'solo')
 * @param {string} props.winner - Currently selected winner
 * @param {Function} props.onWinnerChange - Callback when winner is selected
 * @param {boolean} props.disabled - Disable all inputs
 */
const WinnerSelector = ({
  teamMode,
  winner,
  onWinnerChange,
  disabled = false
}) => {
  const theme = useTheme();

  const partnersOptions = [
    { value: 'team1', label: 'Team 1', color: '#00bcd4' },
    { value: 'team2', label: 'Team 2', color: '#ff9800' },
    { value: 'push', label: 'Push', color: theme.colors.textSecondary },
    { value: 'team1_flush', label: 'Team 1 Flush', color: '#e91e63' },
    { value: 'team2_flush', label: 'Team 2 Flush', color: '#e91e63' }
  ];

  const soloOptions = [
    { value: 'captain', label: 'Captain', color: '#ffc107' },
    { value: 'opponents', label: 'Opponents', color: '#9c27b0' },
    { value: 'push', label: 'Push', color: theme.colors.textSecondary },
    { value: 'captain_flush', label: 'Captain Flush', color: '#e91e63' },
    { value: 'opponents_flush', label: 'Opponents Flush', color: '#e91e63' }
  ];

  const options = teamMode === 'partners' ? partnersOptions : soloOptions;

  const renderButton = ({ value, label, color }) => {
    const isSelected = winner === value;
    const isFlush = value.includes('flush');

    return (
      <button
        key={value}
        onClick={() => !disabled && onWinnerChange(value)}
        disabled={disabled}
        style={{
          flex: 1,
          minWidth: '120px',
          padding: '12px',
          fontSize: isFlush ? '14px' : '16px',
          fontWeight: 'bold',
          border: isSelected ? `3px solid ${color}` : `2px solid ${theme.colors.border}`,
          borderRadius: '8px',
          background: isSelected ? `${color}33` : 'white',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.5 : 1,
          transition: 'all 0.2s'
        }}
      >
        {label}
      </button>
    );
  };

  return (
    <div style={{
      background: theme.colors.paper,
      padding: '16px',
      borderRadius: '8px',
      marginBottom: '20px'
    }}>
      <h3 style={{ margin: '0 0 12px' }}>Winner</h3>
      <div style={{
        display: 'flex',
        gap: '12px',
        flexWrap: 'wrap'
      }}>
        {options.map(renderButton)}
      </div>
    </div>
  );
};

WinnerSelector.propTypes = {
  teamMode: PropTypes.oneOf(['partners', 'solo']).isRequired,
  winner: PropTypes.string,
  onWinnerChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool
};

export default WinnerSelector;
