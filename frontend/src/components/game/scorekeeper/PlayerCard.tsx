// =============================================================================
// PlayerCard Component - Live Scorekeeper
// Displays player info with score entry and quarters tracking
// =============================================================================

import React from 'react';
import { useTheme } from '../../../theme/Provider';
import { Player } from './types';

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
  const theme = useTheme();

  const getCardStyle = () => {
    const base = {
      backgroundColor: theme.colors.paper,
      borderRadius: theme.borderRadius.md,
      border: `1px solid ${theme.colors.border}`,
      padding: theme.spacing[3],
      marginBottom: theme.spacing[2],
      transition: 'all 0.2s ease',
    };

    if (isCaptain) {
      return {
        ...base,
        borderLeft: `4px solid ${theme.colors.gold}`,
        backgroundColor: theme.isDark ? 'rgba(180, 83, 9, 0.15)' : 'rgba(180, 83, 9, 0.08)',
        boxShadow: '0 2px 8px rgba(180, 83, 9, 0.12)',
      };
    }
    if (isTeam1) {
      return {
        ...base,
        borderLeft: `4px solid ${theme.colors.primary}`,
        backgroundColor: theme.isDark ? 'rgba(4, 120, 87, 0.15)' : 'rgba(4, 120, 87, 0.05)',
      };
    }
    if (isOpponent || !isTeam1) {
      return {
        ...base,
        borderLeft: `4px solid ${theme.colors.accent}`,
        backgroundColor: theme.isDark ? 'rgba(3, 105, 161, 0.15)' : 'rgba(3, 105, 161, 0.05)',
      };
    }
    return base;
  };

  const getQuartersStyle = () => {
    const q = player.standings.quarters;
    if (q > 0) return { color: theme.colors.primary, fontWeight: theme.typography.semibold };
    if (q < 0) return { color: theme.colors.error, fontWeight: theme.typography.semibold };
    return {};
  };

  const formatQuarters = (q: number) => {
    if (q > 0) return `+${q}`;
    return q.toString();
  };

  const styles = {
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing[2],
    },
    name: {
      fontWeight: theme.typography.semibold,
      fontSize: theme.typography.base,
      color: theme.colors.textPrimary,
    },
    handicap: {
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary,
      backgroundColor: theme.colors.gray200,
      padding: `2px ${theme.spacing[2]}`,
      borderRadius: theme.borderRadius.full,
    },
    standings: {
      display: 'flex',
      gap: theme.spacing[3],
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
      marginBottom: theme.spacing[3],
    },
    standingItem: {
      display: 'flex',
      alignItems: 'center',
      gap: '4px',
    },
    inputRow: {
      display: 'flex',
      gap: theme.spacing[3],
      alignItems: 'center',
    },
    inputGroup: {
      flex: 1,
    },
    inputLabel: {
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
      marginBottom: '4px',
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
    },
    input: {
      width: '100%',
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      fontSize: theme.typography.lg,
      fontWeight: theme.typography.semibold,
      textAlign: 'center' as const,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.borderRadius.base,
      backgroundColor: theme.colors.inputBackground,
      color: theme.colors.textPrimary,
    },
    teamButton: {
      padding: `6px ${theme.spacing[3]}`,
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      marginBottom: theme.spacing[3],
    },
  };

  return (
    <div style={getCardStyle()}>
      <div style={styles.header}>
        <span style={styles.name}>
          {player.name}
          {isCaptain && ' 👑'}
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
        <div>
          {teamMode === 'partners' ? (
            <button
              style={{
                ...styles.teamButton,
                backgroundColor: isTeam1 ? theme.colors.primary : theme.colors.gray200,
                color: isTeam1 ? '#ffffff' : theme.colors.textPrimary,
              }}
              onClick={onToggleTeam1}
            >
              {isTeam1 ? 'Team 1' : 'Tap to join Team 1'}
            </button>
          ) : (
            <button
              style={{
                ...styles.teamButton,
                backgroundColor: isCaptain ? theme.colors.gold : theme.colors.gray200,
                color: isCaptain ? '#ffffff' : theme.colors.textPrimary,
              }}
              onClick={onSelectCaptain}
            >
              {isCaptain ? '👑 Captain' : 'Tap to go Solo'}
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
            placeholder="—"
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
