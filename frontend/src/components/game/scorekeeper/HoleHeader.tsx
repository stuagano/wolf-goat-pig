// =============================================================================
// HoleHeader Component - Live Scorekeeper
// Displays current hole number, par, and navigation
// =============================================================================

import React from 'react';
import { useTheme } from '../../../theme/Provider';

interface HoleHeaderProps {
  holeNumber: number;
  par: number;
  courseName: string;
  wager: number;
  totalHoles?: number;
  onNavigateHole?: (holeNumber: number) => void;
}

const HoleHeader: React.FC<HoleHeaderProps> = ({
  holeNumber,
  par,
  courseName,
  wager,
  totalHoles = 18,
  onNavigateHole,
}) => {
  const theme = useTheme();
  const progressPercent = ((holeNumber - 1) / totalHoles) * 100;

  const styles = {
    container: {
      backgroundColor: theme.colors.primary,
      color: '#ffffff',
      padding: theme.spacing[4],
      borderRadius: theme.borderRadius.md,
      marginBottom: theme.spacing[4],
    },
    topRow: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing[2],
    },
    courseName: {
      fontSize: theme.typography.sm,
      opacity: 0.9,
      fontWeight: theme.typography.medium,
    },
    wagerBadge: {
      backgroundColor: 'rgba(255, 255, 255, 0.2)',
      padding: `${theme.spacing[1]} ${theme.spacing[3]}`,
      borderRadius: theme.borderRadius.full,
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
    },
    mainRow: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    holeInfo: {
      display: 'flex',
      alignItems: 'baseline',
      gap: theme.spacing[2],
    },
    holeLabel: {
      fontSize: theme.typography.sm,
      opacity: 0.8,
      fontWeight: theme.typography.medium,
    },
    holeNumber: {
      fontSize: theme.typography['4xl'],
      fontWeight: theme.typography.bold,
      lineHeight: 1,
    },
    parInfo: {
      textAlign: 'right' as const,
    },
    parLabel: {
      fontSize: theme.typography.xs,
      opacity: 0.8,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
    },
    parValue: {
      fontSize: theme.typography['3xl'],
      fontWeight: theme.typography.bold,
      lineHeight: 1,
    },
    navRow: {
      display: 'flex',
      justifyContent: 'center',
      gap: theme.spacing[2],
      marginTop: theme.spacing[3],
    },
    navButton: {
      backgroundColor: 'rgba(255, 255, 255, 0.2)',
      border: 'none',
      color: '#ffffff',
      padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
      borderRadius: theme.borderRadius.base,
      cursor: 'pointer',
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
      transition: 'all 0.2s ease',
    },
    navButtonDisabled: {
      opacity: 0.4,
      cursor: 'not-allowed',
    },
    progress: {
      marginTop: theme.spacing[3],
      height: '4px',
      backgroundColor: 'rgba(255, 255, 255, 0.2)',
      borderRadius: '2px',
      overflow: 'hidden',
    },
    progressBar: {
      height: '100%',
      backgroundColor: '#ffffff',
      borderRadius: '2px',
      transition: 'width 0.3s ease',
      width: `${progressPercent}%`,
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.topRow}>
        <span style={styles.courseName}>{courseName}</span>
        <span style={styles.wagerBadge}>
          {wager}Q {wager > 1 && '🔥'}
        </span>
      </div>

      <div style={styles.mainRow}>
        <div style={styles.holeInfo}>
          <span style={styles.holeLabel}>Hole</span>
          <span style={styles.holeNumber}>{holeNumber}</span>
        </div>
        <div style={styles.parInfo}>
          <div style={styles.parLabel}>Par</div>
          <div style={styles.parValue}>{par}</div>
        </div>
      </div>

      <div style={styles.progress}>
        <div style={styles.progressBar} />
      </div>

      <div style={styles.navRow}>
        <button
          style={{
            ...styles.navButton,
            ...(holeNumber <= 1 ? styles.navButtonDisabled : {}),
          }}
          onClick={() => holeNumber > 1 && onNavigateHole?.(holeNumber - 1)}
          disabled={holeNumber <= 1}
        >
          ← Prev
        </button>
        <button
          style={{
            ...styles.navButton,
            ...(holeNumber >= totalHoles ? styles.navButtonDisabled : {}),
          }}
          onClick={() => holeNumber < totalHoles && onNavigateHole?.(holeNumber + 1)}
          disabled={holeNumber >= totalHoles}
        >
          Next →
        </button>
      </div>
    </div>
  );
};

export default HoleHeader;
