// =============================================================================
// HoleHeader Component - Live Scorekeeper
// Displays current hole number, par, and navigation
// =============================================================================

import React from 'react';
import { CourseHole } from '../types';

interface HoleHeaderProps {
  holeNumber: number;
  par: number;
  courseName: string;
  wager: number;
  totalHoles?: number;
  onNavigateHole?: (holeNumber: number) => void;
}

const styles = {
  container: {
    backgroundColor: '#047857', // emerald primary
    color: '#ffffff',
    padding: '16px',
    borderRadius: '12px',
    marginBottom: '16px',
  },
  topRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  courseName: {
    fontSize: '13px',
    opacity: 0.9,
    fontWeight: 500,
  },
  wagerBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    padding: '4px 12px',
    borderRadius: '16px',
    fontSize: '13px',
    fontWeight: 600,
  },
  mainRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  holeInfo: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '8px',
  },
  holeLabel: {
    fontSize: '14px',
    opacity: 0.8,
    fontWeight: 500,
  },
  holeNumber: {
    fontSize: '36px',
    fontWeight: 700,
    lineHeight: 1,
  },
  parInfo: {
    textAlign: 'right' as const,
  },
  parLabel: {
    fontSize: '12px',
    opacity: 0.8,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  parValue: {
    fontSize: '28px',
    fontWeight: 700,
    lineHeight: 1,
  },
  navRow: {
    display: 'flex',
    justifyContent: 'center',
    gap: '8px',
    marginTop: '12px',
  },
  navButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    color: '#ffffff',
    padding: '8px 16px',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
    transition: 'all 0.2s ease',
  },
  navButtonDisabled: {
    opacity: 0.4,
    cursor: 'not-allowed',
  },
  progress: {
    marginTop: '12px',
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
  },
};

const HoleHeader: React.FC<HoleHeaderProps> = ({
  holeNumber,
  par,
  courseName,
  wager,
  totalHoles = 18,
  onNavigateHole,
}) => {
  const progressPercent = ((holeNumber - 1) / totalHoles) * 100;

  return (
    <div style={styles.container}>
      {/* Top Row: Course Name + Wager */}
      <div style={styles.topRow}>
        <span style={styles.courseName}>{courseName}</span>
        <span style={styles.wagerBadge}>
          {wager}Q {wager > 1 && '🔥'}
        </span>
      </div>

      {/* Main Row: Hole Number + Par */}
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

      {/* Progress Bar */}
      <div style={styles.progress}>
        <div
          style={{
            ...styles.progressBar,
            width: `${progressPercent}%`,
          }}
        />
      </div>

      {/* Navigation Row */}
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
