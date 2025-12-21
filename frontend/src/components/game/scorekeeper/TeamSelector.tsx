// =============================================================================
// TeamSelector Component - Live Scorekeeper
// Mode toggle and team formation UI
// =============================================================================

import React from 'react';
import { useTheme } from '../../../theme/Provider';

interface TeamSelectorProps {
  teamMode: 'partners' | 'solo';
  onSetTeamMode: (mode: 'partners' | 'solo') => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

const TeamSelector: React.FC<TeamSelectorProps> = ({
  teamMode,
  onSetTeamMode,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const theme = useTheme();

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
    chevron: {
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
      transition: 'transform 0.2s ease',
      transform: isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)',
    },
    content: {
      padding: theme.spacing[4],
    },
    modeToggle: {
      display: 'flex',
      gap: theme.spacing[2],
      marginBottom: theme.spacing[4],
    },
    modeButton: {
      flex: 1,
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
      border: '2px solid transparent',
      borderRadius: theme.borderRadius.base,
      cursor: 'pointer',
      transition: 'all 0.2s ease',
    },
    modeButtonActive: {
      backgroundColor: theme.colors.primary,
      color: '#ffffff',
      borderColor: theme.colors.primary,
    },
    modeButtonInactive: {
      backgroundColor: theme.colors.gray100,
      color: theme.colors.textPrimary,
      borderColor: theme.colors.border,
    },
    hint: {
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary,
      textAlign: 'center' as const,
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      backgroundColor: theme.colors.gray50,
      borderRadius: theme.borderRadius.base,
    },
    teamLabels: {
      display: 'flex',
      justifyContent: 'space-between',
      marginTop: theme.spacing[4],
      padding: `0 ${theme.spacing[2]}`,
    },
    teamLabel: {
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.header} onClick={onToggleCollapse}>
        <span style={styles.headerTitle}>
          ⚔️ Team Formation
          {!isCollapsed && (
            <span style={{
              fontSize: theme.typography.xs,
              fontWeight: theme.typography.normal,
              color: theme.colors.textSecondary,
            }}>
              ({teamMode === 'partners' ? 'Partners' : 'Solo Captain'})
            </span>
          )}
        </span>
        <span style={styles.chevron}>▼</span>
      </div>

      {!isCollapsed && (
        <div style={styles.content}>
          <div style={styles.modeToggle}>
            <button
              style={{
                ...styles.modeButton,
                ...(teamMode === 'partners' ? styles.modeButtonActive : styles.modeButtonInactive),
              }}
              onClick={() => onSetTeamMode('partners')}
            >
              👥 Partners
            </button>
            <button
              style={{
                ...styles.modeButton,
                ...(teamMode === 'solo' ? styles.modeButtonActive : styles.modeButtonInactive),
              }}
              onClick={() => onSetTeamMode('solo')}
            >
              👑 Solo Captain
            </button>
          </div>

          <div style={styles.hint}>
            {teamMode === 'partners'
              ? 'Tap players below to assign them to Team 1 (others go to Team 2)'
              : 'Tap a player below to make them the Solo Captain'}
          </div>

          <div style={styles.teamLabels}>
            {teamMode === 'partners' ? (
              <>
                <span style={{ ...styles.teamLabel, color: theme.colors.primary }}>
                  Team 1
                </span>
                <span style={{ ...styles.teamLabel, color: theme.colors.accent }}>
                  Team 2
                </span>
              </>
            ) : (
              <>
                <span style={{ ...styles.teamLabel, color: theme.colors.gold }}>
                  Captain
                </span>
                <span style={{ ...styles.teamLabel, color: theme.colors.accent }}>
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
