// frontend/src/components/game/BettingTracker.jsx
import React, { useState } from 'react';
import { useTheme } from '../../theme/Provider';
import useBettingState from '../../hooks/useBettingState';

const BettingTracker = ({ gameState, hasPendingAction = false }) => {
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);
  const { state, eventHistory, actions } = useBettingState(
    gameState.id,
    gameState.current_hole
  );

  const collapsedStyle = {
    padding: theme.spacing[3],
    background: theme.colors.paper,
    borderRadius: theme.borderRadius.md,
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing[3],
    border: `2px solid ${theme.colors.border}`,
  };

  const expandedContainerStyle = {
    ...collapsedStyle,
    flexDirection: 'column',
    cursor: 'default'
  };

  if (!isExpanded) {
    return (
      <div style={collapsedStyle} onClick={() => setIsExpanded(true)}>
        <span>
          Bet: ${state.currentBet.toFixed(2)} ({state.currentMultiplier}x)
        </span>
        {hasPendingAction && (
          <span
            data-testid="pending-indicator"
            style={{
              background: theme.colors.error,
              color: 'white',
              borderRadius: theme.borderRadius.full,
              padding: `${theme.spacing[1]} ${theme.spacing[2]}`,
              fontSize: theme.typography.xs
            }}
          >
            Action Required
          </span>
        )}
      </div>
    );
  }

  return (
    <div style={expandedContainerStyle}>
      <div
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: theme.spacing[3],
          cursor: 'pointer'
        }}
        onClick={() => setIsExpanded(false)}
      >
        <h3 style={{ margin: 0 }}>Current Bet Status</h3>
        <button style={{ ...theme.buttonStyle, padding: theme.spacing[1] }}>
          Collapse
        </button>
      </div>

      <div style={{ width: '100%' }}>
        <p>Multiplier: {state.currentMultiplier}x</p>
        <p>Base Amount: ${state.baseAmount.toFixed(2)}</p>
        <p>Current Bet: ${state.currentBet.toFixed(2)}</p>
      </div>
    </div>
  );
};

export default BettingTracker;
