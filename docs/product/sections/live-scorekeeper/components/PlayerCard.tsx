// =============================================================================
// PlayerCard Component - Live Scorekeeper
// Displays player info with score entry and quarters tracking
// =============================================================================

import React from 'react';
import { Player } from '../types';

interface PlayerCardProps {
  player: Player;
  grossScore?: number;
  quarters?: number;
  isTeam1?: boolean;
  isCaptain?: boolean;
  isOpponent?: boolean;
  teamMode: 'partners' | 'solo';
  onToggleTeam1?: () => void;
  onSelectCaptain?: () => void;
  onSetScore?: (score: number) => void;
  onSetQuarters?: (quarters: number) => void;
  onEditName?: (newName: string) => void;
  isEditable?: boolean;
}

const styles = {
  card: {
    backgroundColor: 'var(--color-paper, #ffffff)',
    borderRadius: '12px',
    border: '1px solid var(--color-border, #e0e0e0)',
    padding: '12px',
    marginBottom: '8px',
    transition: 'all 0.2s ease',
  },
  cardTeam1: {
    borderLeft: '4px solid #047857',
    backgroundColor: 'rgba(4, 120, 87, 0.05)',
  },
  cardTeam2: {
    borderLeft: '4px solid #0369A1',
    backgroundColor: 'rgba(3, 105, 161, 0.05)',
  },
  cardCaptain: {
    borderLeft: '4px solid #B45309',
    backgroundColor: 'rgba(180, 83, 9, 0.08)',
    boxShadow: '0 2px 8px rgba(180, 83, 9, 0.12)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  name: {
    fontWeight: 600,
    fontSize: '16px',
    color: 'var(--color-text-primary, #212121)',
  },
  handicap: {
    fontSize: '13px',
    color: 'var(--color-text-secondary, #757575)',
    backgroundColor: 'var(--color-gray-200, #eeeeee)',
    padding: '2px 8px',
    borderRadius: '12px',
  },
  standings: {
    display: 'flex',
    gap: '12px',
    fontSize: '12px',
    color: 'var(--color-text-secondary, #757575)',
    marginBottom: '12px',
  },
  standingItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  quartersPositive: {
    color: '#047857',
    fontWeight: 600,
  },
  quartersNegative: {
    color: '#dc2626',
    fontWeight: 600,
  },
  inputRow: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  inputGroup: {
    flex: 1,
  },
  inputLabel: {
    fontSize: '11px',
    color: 'var(--color-text-secondary, #757575)',
    marginBottom: '4px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  input: {
    width: '100%',
    padding: '8px 12px',
    fontSize: '18px',
    fontWeight: 600,
    textAlign: 'center' as const,
    border: '1px solid var(--color-border, #e0e0e0)',
    borderRadius: '8px',
    backgroundColor: 'var(--color-input-bg, #ffffff)',
    color: 'var(--color-text-primary, #212121)',
  },
  teamButton: {
    padding: '6px 12px',
    fontSize: '12px',
    fontWeight: 600,
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  team1Button: {
    backgroundColor: '#047857',
    color: '#ffffff',
  },
  team2Button: {
    backgroundColor: '#0369A1',
    color: '#ffffff',
  },
  captainButton: {
    backgroundColor: '#B45309',
    color: '#ffffff',
  },
  unselectedButton: {
    backgroundColor: 'var(--color-gray-200, #eeeeee)',
    color: 'var(--color-text-primary, #212121)',
  },
};

const PlayerCard: React.FC<PlayerCardProps> = ({
  player,
  grossScore,
  quarters,
  isTeam1 = false,
  isCaptain = false,
  isOpponent = false,
  teamMode,
  onToggleTeam1,
  onSelectCaptain,
  onSetScore,
  onSetQuarters,
  isEditable = true,
}) => {
  const getCardStyle = () => {
    const base = { ...styles.card };
    if (isCaptain) return { ...base, ...styles.cardCaptain };
    if (isTeam1) return { ...base, ...styles.cardTeam1 };
    if (isOpponent || !isTeam1) return { ...base, ...styles.cardTeam2 };
    return base;
  };

  const getQuartersStyle = () => {
    const q = player.standings.quarters;
    if (q > 0) return styles.quartersPositive;
    if (q < 0) return styles.quartersNegative;
    return {};
  };

  const formatQuarters = (q: number) => {
    if (q > 0) return `+${q}`;
    return q.toString();
  };

  return (
    <div style={getCardStyle()}>
      <div style={styles.header}>
        <span style={styles.name}>
          {player.name}
          {isCaptain && ' \u{1F451}'}
        </span>
        <span style={styles.handicap}>HCP {player.handicap}</span>
      </div>

      <div style={styles.standings}>
        <div style={styles.standingItem}>
          <span>Q:</span>
          <span style={getQuartersStyle()}>
            {formatQuarters(player.standings.quarters)}
          </span>
        </div>
        <div style={styles.standingItem}>
          <span>Solo:</span>
          <span>{player.standings.soloCount}</span>
        </div>
        <div style={styles.standingItem}>
          <span>Float:</span>
          <span>{player.standings.floatCount}</span>
        </div>
        <div style={styles.standingItem}>
          <span>Opt:</span>
          <span>{player.standings.optionCount}</span>
        </div>
      </div>

      {isEditable && (
        <div style={{ marginBottom: '12px' }}>
          {teamMode === 'partners' ? (
            <button
              style={{
                ...styles.teamButton,
                ...(isTeam1 ? styles.team1Button : styles.unselectedButton),
              }}
              onClick={onToggleTeam1}
            >
              {isTeam1 ? 'Team 1' : 'Tap to join Team 1'}
            </button>
          ) : (
            <button
              style={{
                ...styles.teamButton,
                ...(isCaptain ? styles.captainButton : styles.unselectedButton),
              }}
              onClick={onSelectCaptain}
            >
              {isCaptain ? '\u{1F451} Captain' : 'Tap to go Solo'}
            </button>
          )}
        </div>
      )}

      <div style={styles.inputRow}>
        <div style={styles.inputGroup}>
          <div style={styles.inputLabel}>Gross Score</div>
          <input
            type="number"
            style={styles.input}
            value={grossScore ?? ''}
            onChange={(e) => onSetScore?.(parseInt(e.target.value) || 0)}
            placeholder="\u2014"
            min={1}
            max={20}
            disabled={!isEditable}
          />
        </div>
        <div style={styles.inputGroup}>
          <div style={styles.inputLabel}>Quarters</div>
          <input
            type="number"
            style={styles.input}
            value={quarters ?? ''}
            onChange={(e) => onSetQuarters?.(parseInt(e.target.value) || 0)}
            placeholder="0"
            disabled={!isEditable}
          />
        </div>
      </div>
    </div>
  );
};

export default PlayerCard;
