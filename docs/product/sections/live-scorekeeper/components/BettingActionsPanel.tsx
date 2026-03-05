// =============================================================================
// BettingActionsPanel Component - Live Scorekeeper
// Betting action buttons (Float, Option, Duncan, Vinnies)
// =============================================================================

import React, { useState } from 'react';
import { BettingAction, Bet, Player, BetType } from '../types';

interface BettingActionsPanelProps {
  bettingActions: BettingAction[];
  currentBets: Bet[];
  players: Player[];
  currentWager: number;
  onInvokeBet?: (betType: BetType, playerId: string) => void;
  isExpanded?: boolean;
  onToggleExpanded?: () => void;
}

const styles = {
  container: {
    backgroundColor: 'var(--color-paper, #ffffff)',
    borderRadius: '12px',
    border: '1px solid var(--color-border, #e0e0e0)',
    marginBottom: '16px',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    backgroundColor: 'var(--color-gray-100, #f5f5f5)',
    cursor: 'pointer',
  },
  headerTitle: {
    fontWeight: 600,
    fontSize: '14px',
    color: 'var(--color-text-primary, #212121)',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  wagerDisplay: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  wagerBadge: {
    backgroundColor: '#047857',
    color: '#ffffff',
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '13px',
    fontWeight: 600,
  },
  wagerMultiplier: {
    backgroundColor: '#dc2626',
    color: '#ffffff',
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '13px',
    fontWeight: 600,
  },
  content: {
    padding: '16px',
  },
  actionsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '8px',
    marginBottom: '16px',
  },
  actionButton: {
    padding: '12px',
    fontSize: '14px',
    fontWeight: 600,
    border: '2px solid var(--color-border, #e0e0e0)',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    backgroundColor: 'var(--color-paper, #ffffff)',
    color: 'var(--color-text-primary, #212121)',
    textAlign: 'center' as const,
  },
  actionButtonFloat: {
    borderColor: '#dc2626',
    color: '#dc2626',
  },
  actionButtonOption: {
    borderColor: '#B45309',
    color: '#B45309',
  },
  actionButtonDuncan: {
    borderColor: '#9b59b6',
    color: '#9b59b6',
  },
  actionButtonVinnies: {
    borderColor: '#795548',
    color: '#795548',
  },
  actionButtonActive: {
    backgroundColor: '#047857',
    borderColor: '#047857',
    color: '#ffffff',
  },
  actionLabel: {
    display: 'block',
    fontSize: '14px',
    fontWeight: 600,
    marginBottom: '2px',
  },
  actionDesc: {
    display: 'block',
    fontSize: '11px',
    fontWeight: 400,
    opacity: 0.8,
  },
  playerSelectModal: {
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
    backgroundColor: 'var(--color-paper, #ffffff)',
    borderRadius: '16px',
    padding: '24px',
    maxWidth: '320px',
    width: '90%',
  },
  modalTitle: {
    fontSize: '18px',
    fontWeight: 600,
    marginBottom: '16px',
    textAlign: 'center' as const,
  },
  playerButton: {
    width: '100%',
    padding: '12px 16px',
    marginBottom: '8px',
    fontSize: '16px',
    fontWeight: 500,
    border: '1px solid var(--color-border, #e0e0e0)',
    borderRadius: '8px',
    backgroundColor: 'var(--color-paper, #ffffff)',
    cursor: 'pointer',
    textAlign: 'left' as const,
    transition: 'all 0.2s ease',
  },
  cancelButton: {
    width: '100%',
    padding: '12px 16px',
    marginTop: '8px',
    fontSize: '14px',
    fontWeight: 500,
    border: 'none',
    borderRadius: '8px',
    backgroundColor: 'var(--color-gray-200, #eeeeee)',
    cursor: 'pointer',
  },
  bettingHistory: {
    borderTop: '1px solid var(--color-border, #e0e0e0)',
    paddingTop: '12px',
  },
  historyTitle: {
    fontSize: '12px',
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    color: 'var(--color-text-secondary, #757575)',
    marginBottom: '8px',
  },
  historyItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 12px',
    backgroundColor: 'var(--color-gray-50, #fafafa)',
    borderRadius: '6px',
    marginBottom: '4px',
    fontSize: '13px',
  },
};

const getActionStyle = (actionId: string) => {
  switch (actionId) {
    case 'float':
      return styles.actionButtonFloat;
    case 'option':
      return styles.actionButtonOption;
    case 'duncan':
      return styles.actionButtonDuncan;
    case 'vinnies':
      return styles.actionButtonVinnies;
    default:
      return {};
  }
};

const BettingActionsPanel: React.FC<BettingActionsPanelProps> = ({
  bettingActions,
  currentBets,
  players,
  currentWager,
  onInvokeBet,
  isExpanded = false,
  onToggleExpanded,
}) => {
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

  return (
    <>
      <div style={styles.container}>
        <div style={styles.header} onClick={onToggleExpanded}>
          <span style={styles.headerTitle}>
            \u{1F3B2} Betting Actions
          </span>
          <div style={styles.wagerDisplay}>
            <span style={currentWager > 1 ? styles.wagerMultiplier : styles.wagerBadge}>
              {currentWager}Q {currentWager > 1 && '\u{1F525}'}
            </span>
          </div>
        </div>

        {isExpanded && (
          <div style={styles.content}>
            <div style={styles.actionsGrid}>
              {bettingActions.map((action) => (
                <button
                  key={action.id}
                  style={{
                    ...styles.actionButton,
                    ...getActionStyle(action.id),
                    ...(isActionUsed(action.id) ? styles.actionButtonActive : {}),
                  }}
                  onClick={() => handleActionClick(action.id)}
                  disabled={isActionUsed(action.id)}
                >
                  <span style={styles.actionLabel}>{action.label}</span>
                  <span style={styles.actionDesc}>{action.description}</span>
                </button>
              ))}
            </div>

            {currentBets.length > 0 && (
              <div style={styles.bettingHistory}>
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
        <div style={styles.playerSelectModal}>
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
