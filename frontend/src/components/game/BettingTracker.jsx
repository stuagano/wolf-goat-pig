// frontend/src/components/game/BettingTracker.jsx
import React, { useState, useEffect } from 'react';
import { useTheme } from '../../theme/Provider';
import useBettingState from '../../hooks/useBettingState';
import CurrentBetStatus from './CurrentBetStatus';
import BettingControls from './BettingControls';
import BettingHistory from './BettingHistory';

/**
 * BettingTracker - Main betting action tracker component
 *
 * Displays current bet status, betting controls, and event history.
 * Manages client-side state with event sourcing and batch syncs to backend.
 *
 * @param {Object} gameState - Current game state from GamePage
 * @param {string} currentPlayer - ID of current player for action context
 *
 * Features:
 * - Expandable panel (collapsed by default)
 * - Real-time betting actions (double, press, teams)
 * - Event history with tabs (current hole, last hole, game)
 * - Mobile responsive (bottom sheet)
 * - Auto-sync (every 5 events or hole completion)
 */
const BettingTracker = ({ gameState, currentPlayer = 'Player1' }) => {
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);
  const { state, eventHistory, actions } = useBettingState(
    gameState.id,
    gameState.current_hole
  );

  // Detect mobile viewport
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const hasPendingAction = state.pendingAction !== null;

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
    cursor: 'default',
    border: `2px solid ${theme.colors.primary}`
  };

  // Mobile bottom sheet styles
  const mobileExpandedStyle = {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    background: theme.colors.paper,
    borderTopLeftRadius: theme.borderRadius.lg,
    borderTopRightRadius: theme.borderRadius.lg,
    boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.15)',
    maxHeight: '80vh',
    overflowY: 'auto',
    padding: theme.spacing[4],
    zIndex: 1000,
    animation: 'slideUp 0.3s ease-out',
    border: 'none',
    borderTop: `2px solid ${theme.colors.primary}`
  };

  // Use mobile styles on small screens
  const finalExpandedStyle = isMobile ? mobileExpandedStyle : expandedContainerStyle;

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
              fontSize: theme.typography.xs,
              animation: 'pulse 2s infinite'
            }}
          >
            Action Required
          </span>
        )}
      </div>
    );
  }

  return (
    <>
      {/* Backdrop overlay for mobile */}
      {isMobile && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            zIndex: 999
          }}
          onClick={() => setIsExpanded(false)}
        />
      )}

      <div style={finalExpandedStyle}>
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
          <h3 style={{ margin: 0, fontSize: theme.typography.xl }}>Betting Tracker</h3>
          <button style={{
            ...theme.buttonStyle,
            padding: theme.spacing[1],
            background: 'transparent',
            color: theme.colors.textSecondary
          }}>
            ▼ Collapse
          </button>
        </div>

        <CurrentBetStatus state={state} />
        <BettingControls state={state} actions={actions} currentPlayer={currentPlayer} />
        <BettingHistory eventHistory={eventHistory} />
      </div>
    </>
  );
};

// Add CSS animations to document head
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement("style");
  styleSheet.textContent = `
    @keyframes slideUp {
      from {
        transform: translateY(100%);
      }
      to {
        transform: translateY(0);
      }
    }

    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.5;
      }
    }
  `;
  if (!document.head.querySelector('style[data-betting-tracker-animations]')) {
    styleSheet.setAttribute('data-betting-tracker-animations', 'true');
    document.head.appendChild(styleSheet);
  }
}

export default BettingTracker;
