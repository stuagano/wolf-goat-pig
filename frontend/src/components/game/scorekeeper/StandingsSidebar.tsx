// =============================================================================
// StandingsSidebar Component - Live Scorekeeper
// Player standings display (quarters, solo/float/option counts)
// =============================================================================

import React from 'react';
import { useTheme } from '../../../theme/Provider';
import { Player } from './types';

interface StandingsSidebarProps {
  players: Player[];
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
}

const StandingsSidebar: React.FC<StandingsSidebarProps> = ({
  players,
  isMinimized = false,
  onToggleMinimize,
}) => {
  const theme = useTheme();

  const sortedPlayers = [...players].sort(
    (a, b) => b.standings.quarters - a.standings.quarters
  );

  const getQuartersStyle = (quarters: number) => {
    if (quarters > 0) return { color: theme.colors.primary, fontWeight: theme.typography.bold };
    if (quarters < 0) return { color: theme.colors.error, fontWeight: theme.typography.bold };
    return { color: theme.colors.textSecondary, fontWeight: theme.typography.semibold };
  };

  const formatQuarters = (q: number) => {
    if (q > 0) return `+${q}`;
    return q.toString();
  };

  const styles = {
    container: {
      backgroundColor: theme.colors.paper,
      borderRadius: theme.borderRadius.md,
      border: `1px solid ${theme.colors.border}`,
      overflow: 'hidden',
      marginBottom: theme.spacing[4],
      ...(isMinimized ? {
        position: 'fixed' as const,
        bottom: '80px',
        right: theme.spacing[4],
        width: 'auto',
        zIndex: 100,
        boxShadow: theme.shadows.lg,
      } : {}),
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      backgroundColor: theme.colors.primary,
      color: '#ffffff',
      cursor: 'pointer',
    },
    headerTitle: {
      fontWeight: theme.typography.semibold,
      fontSize: theme.typography.sm,
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing[2],
    },
    toggleButton: {
      backgroundColor: 'rgba(255, 255, 255, 0.2)',
      border: 'none',
      color: '#ffffff',
      padding: `4px ${theme.spacing[2]}`,
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: theme.typography.xs,
    },
    table: {
      width: '100%',
      borderCollapse: 'collapse' as const,
    },
    th: {
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      color: theme.colors.textSecondary,
      textAlign: 'left' as const,
      borderBottom: `1px solid ${theme.colors.border}`,
      backgroundColor: theme.colors.gray100,
    },
    td: {
      padding: `10px ${theme.spacing[3]}`,
      fontSize: theme.typography.sm,
      color: theme.colors.textPrimary,
      borderBottom: `1px solid ${theme.colors.border}`,
    },
    playerName: {
      fontWeight: theme.typography.semibold,
    },
    badge: {
      display: 'inline-block',
      minWidth: '20px',
      padding: '2px 6px',
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      textAlign: 'center' as const,
      borderRadius: '10px',
      backgroundColor: theme.colors.gray200,
      color: theme.colors.textPrimary,
    },
    badgeActive: {
      backgroundColor: theme.colors.primary,
      color: '#ffffff',
    },
    minimizedContent: {
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      display: 'flex',
      gap: theme.spacing[4],
      flexWrap: 'wrap' as const,
    },
    minimizedPlayer: {
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing[2],
      fontSize: theme.typography.sm,
      color: theme.colors.textPrimary,
    },
  };

  if (isMinimized) {
    return (
      <div style={styles.container}>
        <div style={styles.header} onClick={onToggleMinimize}>
          <span style={styles.headerTitle}>🏆 Standings</span>
          <button style={styles.toggleButton}>Expand</button>
        </div>
        <div style={styles.minimizedContent}>
          {sortedPlayers.map((player) => (
            <div key={player.id} style={styles.minimizedPlayer}>
              <span style={{ fontWeight: theme.typography.medium }}>{player.name}:</span>
              <span style={getQuartersStyle(player.standings.quarters)}>
                {formatQuarters(player.standings.quarters)}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header} onClick={onToggleMinimize}>
        <span style={styles.headerTitle}>🏆 Standings</span>
        <button style={styles.toggleButton}>Minimize</button>
      </div>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Player</th>
            <th style={{ ...styles.th, textAlign: 'right' }}>Q</th>
            <th style={{ ...styles.th, textAlign: 'center' }}>Solo</th>
            <th style={{ ...styles.th, textAlign: 'center' }}>Float</th>
            <th style={{ ...styles.th, textAlign: 'center' }}>Opt</th>
          </tr>
        </thead>
        <tbody>
          {sortedPlayers.map((player) => (
            <tr key={player.id}>
              <td style={styles.td}>
                <span style={styles.playerName}>{player.name}</span>
              </td>
              <td style={{ ...styles.td, textAlign: 'right' }}>
                <span style={{ ...getQuartersStyle(player.standings.quarters), fontSize: theme.typography.base }}>
                  {formatQuarters(player.standings.quarters)}
                </span>
              </td>
              <td style={{ ...styles.td, textAlign: 'center' }}>
                <span style={{
                  ...styles.badge,
                  ...(player.standings.soloCount > 0 ? styles.badgeActive : {}),
                }}>
                  {player.standings.soloCount}
                </span>
              </td>
              <td style={{ ...styles.td, textAlign: 'center' }}>
                <span style={{
                  ...styles.badge,
                  ...(player.standings.floatCount > 0 ? styles.badgeActive : {}),
                }}>
                  {player.standings.floatCount}
                </span>
              </td>
              <td style={{ ...styles.td, textAlign: 'center' }}>
                <span style={{
                  ...styles.badge,
                  ...(player.standings.optionCount > 0 ? styles.badgeActive : {}),
                }}>
                  {player.standings.optionCount}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default StandingsSidebar;
