// frontend/src/components/game/scorecardParts/ScorecardHeader.jsx
// Compact Scorecard header: collapse toggle, front/back nine toggle, standings toggle.
import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../../theme/Provider';

const NineButton = ({ nine, label, activeNine, setActiveNine }) => {
  const theme = useTheme();
  const isActive = activeNine === nine;
  return (
    <button
      onClick={() => setActiveNine(nine)}
      style={{
        padding: '4px 12px',
        fontSize: '11px',
        fontWeight: isActive ? 'bold' : 'normal',
        border: 'none',
        borderRadius: '4px',
        background: isActive ? theme.colors.primary : 'transparent',
        color: isActive ? 'white' : theme.colors.textPrimary,
        cursor: 'pointer'
      }}
    >
      {label}
    </button>
  );
};

NineButton.propTypes = {
  nine: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  activeNine: PropTypes.string.isRequired,
  setActiveNine: PropTypes.func.isRequired
};

const ScorecardHeader = ({
  isCollapsed,
  setIsCollapsed,
  viewMode,
  setViewMode,
  activeNine,
  setActiveNine,
  captainId
}) => {
  const theme = useTheme();

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '8px',
      padding: '4px 0'
    }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          cursor: 'pointer',
          padding: '4px'
        }}
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <span style={{ fontSize: '12px' }}>{isCollapsed ? '▶' : '▼'}</span>
        <span style={{ fontSize: '13px', fontWeight: 'bold' }}>SCORECARD</span>
      </div>

      {/* Front/Back Nine Toggle - only show when expanded */}
      {!isCollapsed && viewMode === 'scorecard' && (
        <div style={{
          display: 'flex',
          background: theme.colors.backgroundSecondary,
          borderRadius: '6px',
          padding: '2px'
        }}>
          <NineButton nine="front" label="Front 9" activeNine={activeNine} setActiveNine={setActiveNine} />
          <NineButton nine="back" label="Back 9" activeNine={activeNine} setActiveNine={setActiveNine} />
        </div>
      )}

      <div style={{ display: 'flex', gap: '4px' }}>
        {/* View toggle button - only show in simulation mode (when captainId is provided) */}
        {captainId && (
          <button
            onClick={() => setViewMode(viewMode === 'scorecard' ? 'standings' : 'scorecard')}
            style={{
              padding: '4px 8px',
              fontSize: '11px',
              border: `1px solid ${theme.colors.border}`,
              borderRadius: '4px',
              background: 'white',
              cursor: 'pointer'
            }}
          >
            {viewMode === 'scorecard' ? 'Standings' : 'Scores'}
          </button>
        )}
      </div>
    </div>
  );
};

ScorecardHeader.propTypes = {
  isCollapsed: PropTypes.bool.isRequired,
  setIsCollapsed: PropTypes.func.isRequired,
  viewMode: PropTypes.string.isRequired,
  setViewMode: PropTypes.func.isRequired,
  activeNine: PropTypes.string.isRequired,
  setActiveNine: PropTypes.func.isRequired,
  captainId: PropTypes.string
};

export default ScorecardHeader;
