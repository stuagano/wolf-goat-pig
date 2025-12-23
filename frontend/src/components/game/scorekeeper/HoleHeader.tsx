// =============================================================================
// HoleHeader Component - Live Scorekeeper
// Displays current hole number, par, rotation order, and navigation
// =============================================================================

import React from 'react';
import { useTheme } from '../../../theme/Provider';
import { RotationPlayer } from './types';

interface HoleHeaderProps {
  holeNumber: number;
  par: number;
  courseName: string;
  wager: number;
  totalHoles?: number;
  onNavigateHole?: (holeNumber: number) => void;
  // New rotation props
  rotationOrder?: RotationPlayer[];
  captainIndex?: number;
  isHoepfingerPhase?: boolean;
  goatPlayerIndex?: number | null;
}

const HoleHeader: React.FC<HoleHeaderProps> = ({
  holeNumber,
  par,
  courseName,
  wager,
  totalHoles = 18,
  onNavigateHole,
  rotationOrder = [],
  captainIndex = 0,
  isHoepfingerPhase = false,
  goatPlayerIndex = null,
}) => {
  const theme = useTheme();
  const progressPercent = ((holeNumber - 1) / totalHoles) * 100;
  const hasRotation = rotationOrder.length > 0;

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
    // Rotation display styles
    rotationSection: {
      marginTop: theme.spacing[3],
      padding: `${theme.spacing[2]} 0`,
      borderTop: '1px solid rgba(255, 255, 255, 0.2)',
    },
    rotationLabel: {
      fontSize: theme.typography.xs,
      opacity: 0.8,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      marginBottom: theme.spacing[2],
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing[2],
    },
    hoepfingerBadge: {
      fontSize: theme.typography.xs,
      backgroundColor: theme.colors.gold,
      padding: `2px ${theme.spacing[2]}`,
      borderRadius: '10px',
      fontWeight: theme.typography.semibold,
    },
    rotationList: {
      display: 'flex',
      gap: theme.spacing[2],
      flexWrap: 'wrap' as const,
    },
    rotationPlayer: {
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      padding: `${theme.spacing[1]} ${theme.spacing[2]}`,
      backgroundColor: 'rgba(255, 255, 255, 0.15)',
      borderRadius: theme.borderRadius.base,
      fontSize: theme.typography.sm,
    },
    rotationPlayerCaptain: {
      backgroundColor: theme.colors.gold,
      color: '#000000',
      fontWeight: theme.typography.semibold,
    },
    rotationPlayerGoat: {
      backgroundColor: 'rgba(220, 38, 38, 0.8)',
      fontWeight: theme.typography.semibold,
    },
    rotationIndex: {
      fontSize: theme.typography.xs,
      opacity: 0.7,
      width: '16px',
      textAlign: 'center' as const,
    },
    strokeIndicator: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '18px',
      height: '18px',
      backgroundColor: 'rgba(0, 0, 0, 0.3)',
      borderRadius: '50%',
      fontSize: '10px',
      fontWeight: theme.typography.bold,
      marginLeft: '4px',
    },
    halfStroke: {
      backgroundColor: 'rgba(234, 179, 8, 0.6)',
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

      {/* Rotation Display */}
      {hasRotation && (
        <div style={styles.rotationSection}>
          <div style={styles.rotationLabel}>
            <span>Hitting Order</span>
            {isHoepfingerPhase && (
              <span style={styles.hoepfingerBadge}>Hoepfinger</span>
            )}
          </div>
          <div style={styles.rotationList}>
            {rotationOrder.map((player, index) => {
              const isCaptain = index === captainIndex;
              const isGoat = goatPlayerIndex !== null && index === goatPlayerIndex;
              return (
                <div
                  key={player.playerId}
                  style={{
                    ...styles.rotationPlayer,
                    ...(isCaptain ? styles.rotationPlayerCaptain : {}),
                    ...(isGoat ? styles.rotationPlayerGoat : {}),
                  }}
                >
                  <span style={styles.rotationIndex}>{index + 1}</span>
                  <span>{player.name}</span>
                  {isCaptain && <span>🐺</span>}
                  {isGoat && <span>🐐</span>}
                  {player.strokesOnHole > 0 && (
                    <span
                      style={{
                        ...styles.strokeIndicator,
                        ...(player.strokesOnHole % 1 !== 0 ? styles.halfStroke : {}),
                      }}
                    >
                      {player.strokesOnHole % 1 === 0
                        ? player.strokesOnHole
                        : player.strokesOnHole.toFixed(1)}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

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
