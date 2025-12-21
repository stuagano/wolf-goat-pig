// =============================================================================
// SubmitButton Component - Live Scorekeeper
// Submit hole / Complete game button with validation
// =============================================================================

import React from 'react';
import { useTheme } from '../../../theme/Provider';

interface SubmitButtonProps {
  holeNumber: number;
  totalHoles?: number;
  canSubmit: boolean;
  isSubmitting?: boolean;
  validationError?: string;
  onSubmitHole?: () => void;
  onCompleteGame?: () => void;
}

const SubmitButton: React.FC<SubmitButtonProps> = ({
  holeNumber,
  totalHoles = 18,
  canSubmit,
  isSubmitting = false,
  validationError,
  onSubmitHole,
  onCompleteGame,
}) => {
  const theme = useTheme();

  const isLastHole = holeNumber >= totalHoles;
  const isGameComplete = holeNumber > totalHoles;

  const getButtonStyle = () => {
    const base = {
      width: '100%',
      padding: `${theme.spacing[4]} ${theme.spacing[6]}`,
      fontSize: theme.typography.base,
      fontWeight: theme.typography.semibold,
      border: 'none',
      borderRadius: theme.borderRadius.md,
      cursor: canSubmit && !isSubmitting ? 'pointer' : 'not-allowed',
      transition: 'all 0.2s ease',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: theme.spacing[2],
    };

    if (isSubmitting) {
      return {
        ...base,
        backgroundColor: theme.colors.primary,
        color: '#ffffff',
        opacity: 0.7,
      };
    }
    if (!canSubmit) {
      return {
        ...base,
        backgroundColor: theme.colors.gray300,
        color: theme.colors.textSecondary,
      };
    }
    if (isLastHole || isGameComplete) {
      return {
        ...base,
        backgroundColor: theme.colors.gold,
        color: '#ffffff',
      };
    }
    return {
      ...base,
      backgroundColor: theme.colors.primary,
      color: '#ffffff',
    };
  };

  const getButtonText = () => {
    if (isSubmitting) return 'Saving...';
    if (isGameComplete) return '🏆 Complete Game';
    if (isLastHole) return '🏆 Submit Hole 18 & Finish';
    return `Submit Hole ${holeNumber} →`;
  };

  const handleClick = () => {
    if (!canSubmit || isSubmitting) return;
    if (isGameComplete) {
      onCompleteGame?.();
    } else {
      onSubmitHole?.();
    }
  };

  const styles = {
    container: {
      padding: `${theme.spacing[4]} 0`,
      marginTop: theme.spacing[2],
    },
    error: {
      marginTop: theme.spacing[2],
      padding: theme.spacing[3],
      backgroundColor: theme.isDark ? 'rgba(220, 38, 38, 0.2)' : 'rgba(220, 38, 38, 0.1)',
      borderRadius: theme.borderRadius.base,
      fontSize: theme.typography.sm,
      color: theme.colors.error,
      textAlign: 'center' as const,
    },
    hint: {
      marginTop: theme.spacing[2],
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
      textAlign: 'center' as const,
    },
  };

  return (
    <div style={styles.container}>
      <button
        style={getButtonStyle()}
        onClick={handleClick}
        disabled={!canSubmit || isSubmitting}
      >
        {isSubmitting && <span>⏳</span>}
        {getButtonText()}
      </button>

      {validationError && (
        <div style={styles.error}>{validationError}</div>
      )}

      {!validationError && !canSubmit && !isSubmitting && (
        <div style={styles.hint}>
          Enter all scores and ensure quarters sum to zero
        </div>
      )}

      {canSubmit && !isSubmitting && isLastHole && !isGameComplete && (
        <div style={styles.hint}>
          This is the final hole! Submit to complete the round.
        </div>
      )}
    </div>
  );
};

export default SubmitButton;
