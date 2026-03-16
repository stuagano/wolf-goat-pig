// =============================================================================
// TeamSelector Component - Live Scorekeeper
// Mode toggle and team formation UI
// =============================================================================

import React from 'react';

interface TeamSelectorProps {
  teamMode: 'partners' | 'solo';
  onSetTeamMode: (mode: 'partners' | 'solo') => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
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
  chevron: {
    fontSize: '12px',
    color: 'var(--color-text-secondary, #757575)',
    transition: 'transform 0.2s ease',
  },
  content: {
    padding: '16px',
  },
  modeToggle: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
  },
  modeButton: {
    flex: 1,
    padding: '12px 16px',
    fontSize: '14px',
    fontWeight: 600,
    border: '2px solid transparent',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  modeButtonActive: {
    backgroundColor: '#047857', // emerald
    color: '#ffffff',
    borderColor: '#047857',
  },
  modeButtonInactive: {
    backgroundColor: 'var(--color-gray-100, #f5f5f5)',
    color: 'var(--color-text-primary, #212121)',
    borderColor: 'var(--color-border, #e0e0e0)',
  },
  hint: {
    fontSize: '13px',
    color: 'var(--color-text-secondary, #757575)',
    textAlign: 'center' as const,
    padding: '8px 12px',
    backgroundColor: 'var(--color-gray-50, #fafafa)',
    borderRadius: '8px',
  },
  teamLabels: {
    display: 'flex',
    justifyContent: 'space-between',
    marginTop: '16px',
    padding: '0 8px',
  },
  teamLabel: {
    fontSize: '12px',
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  team1Label: {
    color: '#047857', // emerald
  },
  team2Label: {
    color: '#0369A1', // sky
  },
  captainLabel: {
    color: '#B45309', // gold
  },
  opponentsLabel: {
    color: '#0369A1', // sky
  },
};

const TeamSelector: React.FC<TeamSelectorProps> = ({
  teamMode,
  onSetTeamMode,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  return (
    <div style={styles.container}>
      {/* Collapsible Header */}
      <div style={styles.header} onClick={onToggleCollapse}>
        <span style={styles.headerTitle}>
          ⚔️ Team Formation
          {!isCollapsed && (
            <span style={{
              fontSize: '12px',
              fontWeight: 400,
              color: 'var(--color-text-secondary, #757575)'
            }}>
              ({teamMode === 'partners' ? 'Partners' : 'Solo Captain'})
            </span>
          )}
        </span>
        <span style={{
          ...styles.chevron,
          transform: isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)'
        }}>
          ▼
        </span>
      </div>

      {/* Collapsible Content */}
      {!isCollapsed && (
        <div style={styles.content}>
          {/* Mode Toggle */}
          <div style={styles.modeToggle}>
            <button
              style={{
                ...styles.modeButton,
                ...(teamMode === 'partners'
                  ? styles.modeButtonActive
                  : styles.modeButtonInactive),
              }}
              onClick={() => onSetTeamMode('partners')}
            >
              👥 Partners
            </button>
            <button
              style={{
                ...styles.modeButton,
                ...(teamMode === 'solo'
                  ? styles.modeButtonActive
                  : styles.modeButtonInactive),
              }}
              onClick={() => onSetTeamMode('solo')}
            >
              👑 Solo Captain
            </button>
          </div>

          {/* Mode Hint */}
          <div style={styles.hint}>
            {teamMode === 'partners'
              ? 'Tap players below to assign them to Team 1 (others go to Team 2)'
              : 'Tap a player below to make them the Solo Captain'}
          </div>

          {/* Team Labels */}
          <div style={styles.teamLabels}>
            {teamMode === 'partners' ? (
              <>
                <span style={{ ...styles.teamLabel, ...styles.team1Label }}>
                  Team 1
                </span>
                <span style={{ ...styles.teamLabel, ...styles.team2Label }}>
                  Team 2
                </span>
              </>
            ) : (
              <>
                <span style={{ ...styles.teamLabel, ...styles.captainLabel }}>
                  Captain
                </span>
                <span style={{ ...styles.teamLabel, ...styles.opponentsLabel }}>
                  Opponents
                </span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamSelector;
