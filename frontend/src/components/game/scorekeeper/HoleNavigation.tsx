// =============================================================================
// HoleNavigation Component - Thumb Zone Sticky Navigation
// Previous/Next hole navigation with undo support
// =============================================================================

import React from 'react';
import { useTheme } from '../../../theme/Provider';

interface HoleNavigationProps {
  currentHole: number;
  totalHoles?: number;
  completedHoles: number;
  canUndo: boolean;
  onPreviousHole: () => void;
  onNextHole: () => void;
  onUndoLastHole: () => void;
  onGoToHole: (holeNumber: number) => void;
}

const HoleNavigation: React.FC<HoleNavigationProps> = ({
  currentHole,
  totalHoles = 18,
  completedHoles,
  canUndo,
  onPreviousHole,
  onNextHole,
  onUndoLastHole,
  onGoToHole,
}) => {
  const theme = useTheme();

  const canGoPrevious = currentHole > 1;
  const canGoNext = currentHole < totalHoles;
  const isAtLatestHole = currentHole === completedHoles + 1;

  const styles = {
    container: {
      position: 'fixed' as const,
      bottom: 0,
      left: 0,
      right: 0,
      backgroundColor: theme.colors.paper,
      borderTop: `1px solid ${theme.colors.border}`,
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      zIndex: 100,
      boxShadow: theme.shadows.lg,
    },
    navButton: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      width: '48px',
      height: '48px',
      backgroundColor: theme.colors.gray100,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.borderRadius.md,
      cursor: 'pointer',
      fontSize: theme.typography.lg,
      color: theme.colors.textPrimary,
      transition: 'all 0.15s ease',
    },
    navButtonDisabled: {
      opacity: 0.3,
      cursor: 'not-allowed',
    },
    centerSection: {
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
      gap: theme.spacing[1],
    },
    holeIndicator: {
      fontSize: theme.typography.lg,
      fontWeight: theme.typography.bold,
      color: theme.colors.textPrimary,
    },
    progressBar: {
      display: 'flex',
      gap: '3px',
    },
    progressDot: {
      width: '8px',
      height: '8px',
      borderRadius: '50%',
      backgroundColor: theme.colors.gray300,
      transition: 'all 0.15s ease',
    },
    progressDotCompleted: {
      backgroundColor: theme.colors.primary,
    },
    progressDotCurrent: {
      backgroundColor: theme.colors.gold,
      transform: 'scale(1.2)',
    },
    undoButton: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      backgroundColor: 'transparent',
      border: `1px solid ${theme.colors.error}`,
      borderRadius: theme.borderRadius.base,
      cursor: 'pointer',
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      color: theme.colors.error,
      transition: 'all 0.15s ease',
    },
    undoButtonDisabled: {
      opacity: 0.3,
      cursor: 'not-allowed',
    },
    jumpButton: {
      fontSize: theme.typography.xs,
      color: theme.colors.primary,
      backgroundColor: 'transparent',
      border: 'none',
      cursor: 'pointer',
      textDecoration: 'underline',
      padding: '4px',
    },
  };

  // Generate hole dots for progress (max 9 visible at a time)
  const getVisibleHoles = () => {
    const start = Math.max(1, currentHole - 4);
    const end = Math.min(totalHoles, start + 8);
    return Array.from({ length: end - start + 1 }, (_, i) => start + i);
  };

  return (
    <div style={styles.container}>
      {/* Previous Button */}
      <button
        style={{
          ...styles.navButton,
          ...(canGoPrevious ? {} : styles.navButtonDisabled),
        }}
        onClick={onPreviousHole}
        disabled={!canGoPrevious}
        aria-label="Previous hole"
      >
        ←
      </button>

      {/* Center Section */}
      <div style={styles.centerSection}>
        <div style={styles.holeIndicator}>
          Hole {currentHole} of {totalHoles}
        </div>

        {/* Progress Dots */}
        <div style={styles.progressBar}>
          {getVisibleHoles().map((hole) => (
            <button
              key={hole}
              style={{
                ...styles.progressDot,
                ...(hole <= completedHoles ? styles.progressDotCompleted : {}),
                ...(hole === currentHole ? styles.progressDotCurrent : {}),
                cursor: hole <= completedHoles + 1 ? 'pointer' : 'default',
              }}
              onClick={() => hole <= completedHoles + 1 && onGoToHole(hole)}
              aria-label={`Go to hole ${hole}`}
            />
          ))}
        </div>

        {/* Undo Button (only when at latest hole) */}
        {isAtLatestHole && canUndo && (
          <button
            style={styles.undoButton}
            onClick={onUndoLastHole}
            aria-label="Undo last hole"
          >
            ↩ Undo Hole {completedHoles}
          </button>
        )}

        {/* Jump to latest (when editing previous holes) */}
        {!isAtLatestHole && (
          <button
            style={styles.jumpButton}
            onClick={() => onGoToHole(completedHoles + 1)}
          >
            Jump to current →
          </button>
        )}
      </div>

      {/* Next Button */}
      <button
        style={{
          ...styles.navButton,
          ...(canGoNext ? {} : styles.navButtonDisabled),
        }}
        onClick={onNextHole}
        disabled={!canGoNext}
        aria-label="Next hole"
      >
        →
      </button>
    </div>
  );
};

export default HoleNavigation;
