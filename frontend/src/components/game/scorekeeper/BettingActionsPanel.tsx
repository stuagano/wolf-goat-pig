// =============================================================================
// BettingActionsPanel Component - Live Scorekeeper
// Betting action buttons (Float, Option, Duncan, Vinnies)
// =============================================================================

import React, { useState } from 'react';
import { useTheme } from '../../../theme/Provider';
import { BettingAction, Bet, Player, BetType } from './types';

interface BettingActionsPanelProps {
  bettingActions: BettingAction[];
  currentBets: Bet[];
  players: Player[];
  currentWager: number;
  onInvokeBet?: (betType: BetType, playerId: string) => void;
  isExpanded?: boolean;
  onToggleExpanded?: () => void;
}

const BettingActionsPanel: React.FC<BettingActionsPanelProps> = ({
  bettingActions,
  currentBets,
  players,
  currentWager,
  onInvokeBet,
  isExpanded = false,
  onToggleExpanded,
}) => {
  const theme = useTheme();
  const [selectingPlayerFor, setSelectingPlayerFor] = useState<BetType | null>(null);

  const handleActionClick = (actionId: BetType) => {
    setSelectingPlayerFor(actionId);
  };

  const handlePlayerSelect = (playerId: string) => {
    if (selectingPlayerFor && onInvokeBet) {
      onInvokeBet(selectingPlayerFor, playerId);
    }
    setSelectingPlayerFor(null);
  };

  const getPlayerName = (playerId: string) => {
    return players.find((p) => p.id === playerId)?.name || 'Unknown';
  };

  const isActionUsed = (actionId: string) => {
    return currentBets.some((bet) => bet.type === actionId);
  };

  const getActionColor = (actionId: string) => {
    switch (actionId) {
      case 'float': return theme.colors.error;
      case 'option': return theme.colors.gold;
      case 'duncan': return theme.colors.purple || '#9b59b6';
      case 'vinnies': return theme.colors.vinnie || '#795548';
      default: return theme.colors.primary;
    }
  };

  const styles = {
    container: {
      backgroundColor: theme.colors.paper,
      borderRadius: theme.borderRadius.md,
      border: `1px solid ${theme.colors.border}`,
      marginBottom: theme.spacing[4],
      overflow: 'hidden',
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      backgroundColor: theme.colors.gray100,
      cursor: 'pointer',
    },
    headerTitle: {
      fontWeight: theme.typography.semibold,
      fontSize: theme.typography.sm,
      color: theme.colors.textPrimary,
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing[2],
    },
    wagerBadge: {
      backgroundColor: currentWager > 1 ? theme.colors.error : theme.colors.primary,
      color: '#ffffff',
      padding: `4px 10px`,
      borderRadius: theme.borderRadius.full,
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
    },
    content: {
      padding: theme.spacing[4],
    },
    actionsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(2, 1fr)',
      gap: theme.spacing[2],
      marginBottom: theme.spacing[4],
    },
    actionButton: {
      padding: theme.spacing[3],
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
      borderRadius: '10px',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      backgroundColor: theme.colors.paper,
      textAlign: 'center' as const,
    },
    actionLabel: {
      display: 'block',
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
      marginBottom: '2px',
    },
    actionDesc: {
      display: 'block',
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.normal,
      opacity: 0.8,
    },
    modal: {
      position: 'fixed' as const,
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    },
    modalContent: {
      backgroundColor: theme.colors.paper,
      borderRadius: theme.borderRadius.lg,
      padding: theme.spacing[6],
      maxWidth: '320px',
      width: '90%',
    },
    modalTitle: {
      fontSize: theme.typography.lg,
      fontWeight: theme.typography.semibold,
      marginBottom: theme.spacing[4],
      textAlign: 'center' as const,
      color: theme.colors.textPrimary,
    },
    playerButton: {
      width: '100%',
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      marginBottom: theme.spacing[2],
      fontSize: theme.typography.base,
      fontWeight: theme.typography.medium,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.borderRadius.base,
      backgroundColor: theme.colors.paper,
      color: theme.colors.textPrimary,
      cursor: 'pointer',
      textAlign: 'left' as const,
      transition: 'all 0.2s ease',
    },
    cancelButton: {
      width: '100%',
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      marginTop: theme.spacing[2],
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.medium,
      border: 'none',
      borderRadius: theme.borderRadius.base,
      backgroundColor: theme.colors.gray200,
      color: theme.colors.textPrimary,
      cursor: 'pointer',
    },
    historySection: {
      borderTop: `1px solid ${theme.colors.border}`,
      paddingTop: theme.spacing[3],
    },
    historyTitle: {
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      color: theme.colors.textSecondary,
      marginBottom: theme.spacing[2],
    },
    historyItem: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      backgroundColor: theme.colors.gray50,
      borderRadius: '6px',
      marginBottom: '4px',
      fontSize: theme.typography.sm,
      color: theme.colors.textPrimary,
    },
  };

  return (
    <>
      <div style={styles.container}>
        <div style={styles.header} onClick={onToggleExpanded}>
          <span style={styles.headerTitle}>🎲 Betting Actions</span>
          <span style={styles.wagerBadge}>
            {currentWager}Q {currentWager > 1 && '🔥'}
          </span>
        </div>

        {isExpanded && (
          <div style={styles.content}>
            <div style={styles.actionsGrid}>
              {bettingActions.map((action) => {
                const actionColor = getActionColor(action.id);
                const used = isActionUsed(action.id);
                return (
                  <button
                    key={action.id}
                    style={{
                      ...styles.actionButton,
                      border: `2px solid ${actionColor}`,
                      color: used ? '#ffffff' : actionColor,
                      backgroundColor: used ? theme.colors.primary : theme.colors.paper,
                      opacity: used ? 0.6 : 1,
                    }}
                    onClick={() => !used && handleActionClick(action.id)}
                    disabled={used}
                  >
                    <span style={styles.actionLabel}>{action.label}</span>
                    <span style={styles.actionDesc}>{action.description}</span>
                  </button>
                );
              })}
            </div>

            {currentBets.length > 0 && (
              <div style={styles.historySection}>
                <div style={styles.historyTitle}>This Hole</div>
                {currentBets.map((bet) => (
                  <div key={bet.id} style={styles.historyItem}>
                    <span>{bet.type.toUpperCase()}</span>
                    <span>{getPlayerName(bet.invokedBy)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {selectingPlayerFor && (
        <div style={styles.modal}>
          <div style={styles.modalContent}>
            <div style={styles.modalTitle}>
              Who invoked {selectingPlayerFor.toUpperCase()}?
            </div>
            {players.map((player) => (
              <button
                key={player.id}
                style={styles.playerButton}
                onClick={() => handlePlayerSelect(player.id)}
              >
                {player.name}
              </button>
            ))}
            <button
              style={styles.cancelButton}
              onClick={() => setSelectingPlayerFor(null)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default BettingActionsPanel;
