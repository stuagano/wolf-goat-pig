// =============================================================================
// BettingActionsPanel Component - Live Scorekeeper
// Betting action buttons (Float, Option, Duncan, Vinnies) with offer/accept flow
// =============================================================================

import React, { useState } from 'react';
import { useTheme } from '../../../theme/Provider';
import { BettingAction, Bet, Player, BetType, BetOffer, PlayerBettingUsage } from './types';

interface BettingActionsPanelProps {
  bettingActions: BettingAction[];
  currentBets: Bet[];
  players: Player[];
  currentWager: number;
  onInvokeBet?: (betType: BetType, playerId: string) => void;
  isExpanded?: boolean;
  onToggleExpanded?: () => void;
  // New props for offer/accept flow
  pendingOffers?: BetOffer[];
  playerUsage?: Record<string, PlayerBettingUsage>;
  onOfferBet?: (betType: BetType, toPlayerIds: string[]) => void;
  onAcceptOffer?: (offerId: string) => void;
  onDeclineOffer?: (offerId: string) => void;
  canInvokeFloat?: (playerId: string) => boolean;
  canInvokeOption?: (playerId: string) => boolean;
  canInvokeDuncan?: (playerId: string) => boolean;
}

const BettingActionsPanel: React.FC<BettingActionsPanelProps> = ({
  bettingActions,
  currentBets,
  players,
  currentWager,
  onInvokeBet,
  isExpanded = false,
  onToggleExpanded,
  pendingOffers = [],
  playerUsage = {},
  onOfferBet: _onOfferBet,
  onAcceptOffer,
  onDeclineOffer,
  canInvokeFloat,
  canInvokeOption,
  canInvokeDuncan,
}) => {
  const theme = useTheme();
  const [selectingPlayerFor, setSelectingPlayerFor] = useState<BetType | null>(null);
  // Reserved for future player usage tooltip feature
  const [_showUsageFor, _setShowUsageFor] = useState<string | null>(null);

  // Suppress unused warning - reserved for future offer flow
  void _onOfferBet;

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

  const canPlayerInvoke = (playerId: string, actionId: BetType): boolean => {
    switch (actionId) {
      case 'float':
        return canInvokeFloat ? canInvokeFloat(playerId) : true;
      case 'option':
        return canInvokeOption ? canInvokeOption(playerId) : true;
      case 'duncan':
        return canInvokeDuncan ? canInvokeDuncan(playerId) : true;
      default:
        return true;
    }
  };

  const getPlayerUsageInfo = (playerId: string): string[] => {
    const usage = playerUsage[playerId];
    if (!usage) return [];
    const info: string[] = [];
    if (usage.floatUsed) info.push(`Float used (hole ${usage.floatHole})`);
    if (usage.optionUsed) info.push(`Option used (hole ${usage.optionHole})`);
    if (usage.duncanUsed) info.push(`Duncan used (hole ${usage.duncanHole})`);
    return info;
  };

  const hasPendingOffers = pendingOffers.filter(o => o.status === 'pending').length > 0;

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
    // Pending offers styles
    pendingOffersSection: {
      marginBottom: theme.spacing[4],
      padding: theme.spacing[3],
      backgroundColor: theme.isDark ? 'rgba(234, 179, 8, 0.2)' : 'rgba(234, 179, 8, 0.1)',
      borderRadius: theme.borderRadius.base,
      border: `1px solid ${theme.colors.gold}`,
    },
    pendingTitle: {
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      color: theme.colors.gold,
      marginBottom: theme.spacing[2],
    },
    offerCard: {
      backgroundColor: theme.colors.paper,
      borderRadius: theme.borderRadius.base,
      padding: theme.spacing[3],
      marginBottom: theme.spacing[2],
    },
    offerInfo: {
      marginBottom: theme.spacing[2],
      fontSize: theme.typography.sm,
      color: theme.colors.textPrimary,
    },
    offerActions: {
      display: 'flex',
      gap: theme.spacing[2],
    },
    acceptButton: {
      flex: 1,
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      backgroundColor: theme.colors.primary,
      color: '#ffffff',
      border: 'none',
      borderRadius: theme.borderRadius.base,
      cursor: 'pointer',
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
    },
    declineButton: {
      flex: 1,
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      backgroundColor: 'transparent',
      color: theme.colors.error,
      border: `1px solid ${theme.colors.error}`,
      borderRadius: theme.borderRadius.base,
      cursor: 'pointer',
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
    },
    playerButtonDisabled: {
      opacity: 0.4,
      cursor: 'not-allowed',
    },
    usageInfo: {
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
      marginTop: '4px',
    },
    playerAvailabilityIndicator: {
      display: 'inline-block',
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      marginRight: theme.spacing[2],
    },
    availableIndicator: {
      backgroundColor: theme.colors.primary,
    },
    unavailableIndicator: {
      backgroundColor: theme.colors.error,
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
            {/* Pending Offers Section */}
            {hasPendingOffers && (
              <div style={styles.pendingOffersSection}>
                <div style={styles.pendingTitle}>Pending Offers</div>
                {pendingOffers
                  .filter(o => o.status === 'pending')
                  .map((offer) => (
                    <div key={offer.id} style={styles.offerCard}>
                      <div style={styles.offerInfo}>
                        <strong>{offer.type.toUpperCase()}</strong> offered by{' '}
                        <strong>{getPlayerName(offer.offeredBy)}</strong>
                      </div>
                      <div style={styles.offerActions}>
                        <button
                          style={styles.acceptButton}
                          onClick={() => onAcceptOffer?.(offer.id)}
                        >
                          Accept
                        </button>
                        <button
                          style={styles.declineButton}
                          onClick={() => onDeclineOffer?.(offer.id)}
                        >
                          Decline
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            )}

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
            {players.map((player) => {
              const canInvoke = canPlayerInvoke(player.id, selectingPlayerFor);
              const usageInfo = getPlayerUsageInfo(player.id);
              return (
                <div key={player.id}>
                  <button
                    style={{
                      ...styles.playerButton,
                      ...(canInvoke ? {} : styles.playerButtonDisabled),
                    }}
                    onClick={() => canInvoke && handlePlayerSelect(player.id)}
                    disabled={!canInvoke}
                  >
                    <span
                      style={{
                        ...styles.playerAvailabilityIndicator,
                        ...(canInvoke ? styles.availableIndicator : styles.unavailableIndicator),
                      }}
                    />
                    {player.name}
                    {!canInvoke && ' (Already used)'}
                  </button>
                  {usageInfo.length > 0 && (
                    <div style={styles.usageInfo}>
                      {usageInfo.join(' · ')}
                    </div>
                  )}
                </div>
              );
            })}
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
