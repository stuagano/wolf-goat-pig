import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';

const BettingControls = ({ state, actions, currentPlayer }) => {
  const theme = useTheme();

  const buttonStyle = {
    ...theme.buttonStyle,
    padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
    margin: theme.spacing[2],
    fontSize: theme.typography.base,
    minWidth: 120
  };

  const acceptButtonStyle = {
    ...buttonStyle,
    background: theme.colors.success
  };

  const declineButtonStyle = {
    ...buttonStyle,
    background: theme.colors.error
  };

  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing[2],
    padding: theme.spacing[3],
    background: theme.colors.paper,
    borderRadius: theme.borderRadius.md
  };

  const hasPendingAction = state.pendingAction !== null;
  const isPendingDouble = state.pendingAction?.type === 'DOUBLE_OFFERED';

  return (
    <div style={containerStyle}>
      {!hasPendingAction && (
        <>
          <button
            style={buttonStyle}
            onClick={() => actions.offerDouble(currentPlayer, (state.currentMultiplier || 1) * 2)}
          >
            Offer Double
          </button>
          <button
            style={buttonStyle}
            onClick={() => actions.offerPress(currentPlayer, state.baseAmount)}
          >
            Offer Press
          </button>
        </>
      )}

      {isPendingDouble && (
        <>
          <div style={{ marginBottom: theme.spacing[2], fontSize: theme.typography.base }}>
            {state.pendingAction.by} offered to double to {state.pendingAction.proposedMultiplier}x
          </div>
          <div style={{ display: 'flex', gap: theme.spacing[2] }}>
            <button
              style={acceptButtonStyle}
              onClick={() => actions.acceptDouble(currentPlayer)}
            >
              Accept Double
            </button>
            <button
              style={declineButtonStyle}
              onClick={() => actions.declineDouble(currentPlayer)}
            >
              Decline
            </button>
          </div>
        </>
      )}
    </div>
  );
};

BettingControls.propTypes = {
  state: PropTypes.shape({
    pendingAction: PropTypes.shape({
      type: PropTypes.string,
      from: PropTypes.string,
    }),
  }).isRequired,
  actions: PropTypes.shape({
    respondToDouble: PropTypes.func,
    offerDouble: PropTypes.func,
    pass: PropTypes.func,
  }).isRequired,
  currentPlayer: PropTypes.string.isRequired,
};

export default BettingControls;
