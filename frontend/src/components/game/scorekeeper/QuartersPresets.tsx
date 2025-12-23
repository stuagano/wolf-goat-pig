// =============================================================================
// QuartersPresets Component - Quick Preset Buttons
// One-tap buttons for common scoring scenarios
// =============================================================================

import React from 'react';
import { useTheme } from '../../../theme/Provider';

interface QuartersPresetsProps {
  teamMode: 'partners' | 'solo';
  wager: number;
  onApplyPreset: (presetId: string) => void;
  disabled?: boolean;
}

interface Preset {
  id: string;
  label: string;
  shortLabel: string;
  description: string;
}

const PARTNERS_PRESETS: Preset[] = [
  {
    id: 'team1-win',
    label: 'Team 1 Wins',
    shortLabel: 'T1 Win',
    description: 'Team 1 wins the hole',
  },
  {
    id: 'team1-lose',
    label: 'Team 2 Wins',
    shortLabel: 'T2 Win',
    description: 'Team 2 wins the hole',
  },
  {
    id: 'push',
    label: 'Push',
    shortLabel: 'Push',
    description: 'Hole is tied',
  },
];

const SOLO_PRESETS: Preset[] = [
  {
    id: 'captain-win',
    label: 'Captain Wins',
    shortLabel: 'Cap Win',
    description: 'Captain beats opponents',
  },
  {
    id: 'captain-lose',
    label: 'Opponents Win',
    shortLabel: 'Opp Win',
    description: 'Opponents beat captain',
  },
  {
    id: 'push',
    label: 'Push',
    shortLabel: 'Push',
    description: 'Hole is tied',
  },
];

const QuartersPresets: React.FC<QuartersPresetsProps> = ({
  teamMode,
  wager,
  onApplyPreset,
  disabled = false,
}) => {
  const theme = useTheme();
  const presets = teamMode === 'partners' ? PARTNERS_PRESETS : SOLO_PRESETS;

  const styles = {
    container: {
      marginBottom: theme.spacing[4],
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing[2],
    },
    title: {
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      color: theme.colors.textSecondary,
    },
    wagerBadge: {
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      color: theme.colors.primary,
      backgroundColor: theme.isDark ? 'rgba(16, 185, 129, 0.2)' : 'rgba(16, 185, 129, 0.1)',
      padding: `2px ${theme.spacing[2]}`,
      borderRadius: '12px',
    },
    buttonContainer: {
      display: 'flex',
      gap: theme.spacing[2],
    },
    button: {
      flex: 1,
      padding: `${theme.spacing[3]} ${theme.spacing[2]}`,
      backgroundColor: theme.colors.paper,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.borderRadius.base,
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1,
      transition: 'all 0.15s ease',
    },
    buttonHover: {
      backgroundColor: theme.colors.gray100,
      borderColor: theme.colors.primary,
    },
    buttonLabel: {
      display: 'block',
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
      color: theme.colors.textPrimary,
      marginBottom: '2px',
    },
    buttonDescription: {
      display: 'block',
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
    },
    winButton: {
      borderColor: theme.colors.primary,
      backgroundColor: theme.isDark ? 'rgba(16, 185, 129, 0.1)' : 'rgba(16, 185, 129, 0.05)',
    },
    loseButton: {
      borderColor: theme.colors.error,
      backgroundColor: theme.isDark ? 'rgba(220, 38, 38, 0.1)' : 'rgba(220, 38, 38, 0.05)',
    },
    pushButton: {
      borderColor: theme.colors.gray400,
    },
  };

  const getButtonStyle = (presetId: string) => {
    const base = styles.button;
    if (presetId.includes('win') && presetId.includes('team1') || presetId.includes('captain-win')) {
      return { ...base, ...styles.winButton };
    }
    if (presetId.includes('lose') || presetId.includes('team1-lose')) {
      return { ...base, ...styles.loseButton };
    }
    if (presetId === 'push') {
      return { ...base, ...styles.pushButton };
    }
    return base;
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.title}>Quick Presets</span>
        <span style={styles.wagerBadge}>{wager}Q</span>
      </div>
      <div style={styles.buttonContainer}>
        {presets.map((preset) => (
          <button
            key={preset.id}
            style={getButtonStyle(preset.id)}
            onClick={() => !disabled && onApplyPreset(preset.id)}
            disabled={disabled}
            title={preset.description}
          >
            <span style={styles.buttonLabel}>{preset.shortLabel}</span>
            <span style={styles.buttonDescription}>{preset.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuartersPresets;
