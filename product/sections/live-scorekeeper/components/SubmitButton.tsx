// =============================================================================
// SubmitButton Component - Live Scorekeeper
// Submit hole / Complete game button with validation
// =============================================================================

import React from 'react';

interface SubmitButtonProps {
  holeNumber: number;
  totalHoles?: number;
  canSubmit: boolean;
  isSubmitting?: boolean;
  validationError?: string;
  onSubmitHole?: () => void;
  onCompleteGame?: () => void;
}

const styles = {
  container: {
    padding: '16px 0',
    marginTop: '8px',
  },
  button: {
    width: '100%',
    padding: '16px 24px',
    fontSize: '16px',
    fontWeight: 600,
    border: 'none',
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
  },
  buttonPrimary: {
    backgroundColor: '#047857',
    color: '#ffffff',
  },
  buttonComplete: {
    backgroundColor: '#B45309',
    color: '#ffffff',
  },
  buttonDisabled: {
    backgroundColor: 'var(--color-gray-300, #e0e0e0)',
    color: 'var(--color-text-secondary, #757575)',
    cursor: 'not-allowed',
  },
  buttonLoading: {
    backgroundColor: '#047857',
    color: '#ffffff',
    opacity: 0.7,
  },
  error: {
    marginTop: '8px',
    padding: '12px',
    backgroundColor: 'rgba(220, 38, 38, 0.1)',
    borderRadius: '8px',
    fontSize: '13px',
    color: '#dc2626',
    textAlign: 'center' as const,
  },
  hint: {
    marginTop: '8px',
    fontSize: '12px',
    color: 'var(--color-text-secondary, #757575)',
    textAlign: 'center' as const,
  },
};

const SubmitButton: React.FC<SubmitButtonProps> = ({
  holeNumber,
  totalHoles = 18,
  canSubmit,
  isSubmitting = false,
  validationError,
  onSubmitHole,
  onCompleteGame,
}) => {
  const isLastHole = holeNumber >= totalHoles;
  const isGameComplete = holeNumber > totalHoles;

  const getButtonStyle = () => {
    if (isSubmitting) return { ...styles.button, ...styles.buttonLoading };
    if (!canSubmit) return { ...styles.button, ...styles.buttonDisabled };
    if (isLastHole) return { ...styles.button, ...styles.buttonComplete };
    return { ...styles.button, ...styles.buttonPrimary };
  };

  const getButtonText = () => {
    if (isSubmitting) return 'Saving...';
    if (isGameComplete) return '\u{1F3C6} Complete Game';
    if (isLastHole) return '\u{1F3C6} Submit Hole 18 & Finish';
    return `Submit Hole ${holeNumber} \u2192`;
  };

  const handleClick = () => {
    if (!canSubmit || isSubmitting) return;
    if (isGameComplete) {
      onCompleteGame?.();
    } else {
      onSubmitHole?.();
    }
  };

  return (
    <div style={styles.container}>
      <button
        style={getButtonStyle()}
        onClick={handleClick}
        disabled={!canSubmit || isSubmitting}
      >
        {isSubmitting && (
          <span style={{ animation: 'spin 1s linear infinite' }}>\u{23F3}</span>
        )}
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
