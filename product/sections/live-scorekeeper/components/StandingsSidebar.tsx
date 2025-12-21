// =============================================================================
// StandingsSidebar Component - Live Scorekeeper
// Player standings display (quarters, solo/float/option counts)
// =============================================================================

import React from 'react';
import { Player } from '../types';

interface StandingsSidebarProps {
  players: Player[];
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
}

const styles = {
  container: {
    backgroundColor: 'var(--color-paper, #ffffff)',
    borderRadius: '12px',
    border: '1px solid var(--color-border, #e0e0e0)',
    overflow: 'hidden',
    marginBottom: '16px',
  },
  containerMinimized: {
    position: 'fixed' as const,
    bottom: '80px',
    right: '16px',
    width: 'auto',
    zIndex: 100,
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    backgroundColor: '#047857',
    color: '#ffffff',
    cursor: 'pointer',
  },
  headerTitle: {
    fontWeight: 600,
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  toggleButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    color: '#ffffff',
    padding: '4px 8px',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  content: {
    padding: '0',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
  },
  tableHeader: {
    backgroundColor: 'var(--color-gray-100, #f5f5f5)',
  },
  th: {
    padding: '8px 12px',
    fontSize: '11px',
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    color: 'var(--color-text-secondary, #757575)',
    textAlign: 'left' as const,
    borderBottom: '1px solid var(--color-border, #e0e0e0)',
  },
  thRight: {
    textAlign: 'right' as const,
  },
  thCenter: {
    textAlign: 'center' as const,
  },
  tr: {
    borderBottom: '1px solid var(--color-border, #e0e0e0)',
  },
  trLast: {
    borderBottom: 'none',
  },
  td: {
    padding: '10px 12px',
    fontSize: '14px',
    color: 'var(--color-text-primary, #212121)',
  },
  tdRight: {
    textAlign: 'right' as const,
  },
  tdCenter: {
    textAlign: 'center' as const,
  },
  playerName: {
    fontWeight: 600,
  },
  quartersPositive: {
    color: '#047857',
    fontWeight: 700,
    fontSize: '16px',
  },
  quartersNegative: {
    color: '#dc2626',
    fontWeight: 700,
    fontSize: '16px',
  },
  quartersNeutral: {
    color: 'var(--color-text-secondary, #757575)',
    fontWeight: 600,
    fontSize: '16px',
  },
  badge: {
    display: 'inline-block',
    minWidth: '20px',
    padding: '2px 6px',
    fontSize: '11px',
    fontWeight: 600,
    textAlign: 'center' as const,
    borderRadius: '10px',
    backgroundColor: 'var(--color-gray-200, #eeeeee)',
    color: 'var(--color-text-primary, #212121)',
  },
  badgeActive: {
    backgroundColor: '#047857',
    color: '#ffffff',
  },
  minimizedContent: {
    padding: '12px 16px',
    display: 'flex',
    gap: '16px',
    flexWrap: 'wrap' as const,
  },
  minimizedPlayer: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
  },
};

const StandingsSidebar: React.FC<StandingsSidebarProps> = ({
  players,
  isMinimized = false,
  onToggleMinimize,
}) => {
  const sortedPlayers = [...players].sort(
    (a, b) => b.standings.quarters - a.standings.quarters
  );

  const getQuartersStyle = (quarters: number) => {
    if (quarters > 0) return styles.quartersPositive;
    if (quarters < 0) return styles.quartersNegative;
    return styles.quartersNeutral;
  };

  const formatQuarters = (q: number) => {
    if (q > 0) return `+${q}`;
    return q.toString();
  };

  if (isMinimized) {
    return (
      <div style={{ ...styles.container, ...styles.containerMinimized }}>
        <div style={styles.header} onClick={onToggleMinimize}>
          <span style={styles.headerTitle}>\u{1F3C6} Standings</span>
          <button style={styles.toggleButton}>Expand</button>
        </div>
        <div style={styles.minimizedContent}>
          {sortedPlayers.map((player) => (
            <div key={player.id} style={styles.minimizedPlayer}>
              <span style={{ fontWeight: 500 }}>{player.name}:</span>
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
        <span style={styles.headerTitle}>\u{1F3C6} Standings</span>
        <button style={styles.toggleButton}>Minimize</button>
      </div>
      <div style={styles.content}>
        <table style={styles.table}>
          <thead style={styles.tableHeader}>
            <tr>
              <th style={styles.th}>Player</th>
              <th style={{ ...styles.th, ...styles.thRight }}>Q</th>
              <th style={{ ...styles.th, ...styles.thCenter }}>Solo</th>
              <th style={{ ...styles.th, ...styles.thCenter }}>Float</th>
              <th style={{ ...styles.th, ...styles.thCenter }}>Opt</th>
            </tr>
          </thead>
          <tbody>
            {sortedPlayers.map((player, index) => (
              <tr
                key={player.id}
                style={
                  index === sortedPlayers.length - 1 ? styles.trLast : styles.tr
                }
              >
                <td style={styles.td}>
                  <span style={styles.playerName}>{player.name}</span>
                </td>
                <td style={{ ...styles.td, ...styles.tdRight }}>
                  <span style={getQuartersStyle(player.standings.quarters)}>
                    {formatQuarters(player.standings.quarters)}
                  </span>
                </td>
                <td style={{ ...styles.td, ...styles.tdCenter }}>
                  <span
                    style={{
                      ...styles.badge,
                      ...(player.standings.soloCount > 0 ? styles.badgeActive : {}),
                    }}
                  >
                    {player.standings.soloCount}
                  </span>
                </td>
                <td style={{ ...styles.td, ...styles.tdCenter }}>
                  <span
                    style={{
                      ...styles.badge,
                      ...(player.standings.floatCount > 0 ? styles.badgeActive : {}),
                    }}
                  >
                    {player.standings.floatCount}
                  </span>
                </td>
                <td style={{ ...styles.td, ...styles.tdCenter }}>
                  <span
                    style={{
                      ...styles.badge,
                      ...(player.standings.optionCount > 0 ? styles.badgeActive : {}),
                    }}
                  >
                    {player.standings.optionCount}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default StandingsSidebar;
