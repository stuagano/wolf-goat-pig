// =============================================================================
// AardvarkPanel Component - 5-man and 4-man Aardvark UI
// Displays aardvark info and allows invisible aardvark score entry
// =============================================================================

import React, { useState } from 'react';
import { useTheme } from '../../../theme/Provider';
import { AardvarkState, Player } from './types';

interface AardvarkPanelProps {
  aardvark: AardvarkState;
  players: Player[];
  par: number;
  onSetInvisibleScore: (score: number) => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

const AardvarkPanel: React.FC<AardvarkPanelProps> = ({
  aardvark,
  players,
  par,
  onSetInvisibleScore,
  isCollapsed = false,
  onToggleCollapse,
}) => {
  const theme = useTheme();
  const [localScore, setLocalScore] = useState<string>(
    aardvark.invisibleAardvarkScore?.toString() || ''
  );

  if (aardvark.mode === 'none') {
    return null;
  }

  const aardvarkPlayer = aardvark.mode === 'real' && aardvark.aardvarkPlayerId
    ? players.find(p => p.id === aardvark.aardvarkPlayerId)
    : null;

  const handleScoreChange = (value: string) => {
    setLocalScore(value);
    const score = parseInt(value, 10);
    if (!isNaN(score) && score > 0) {
      onSetInvisibleScore(score);
    }
  };

  const styles = {
    container: {
      backgroundColor: theme.colors.paper,
      borderRadius: theme.borderRadius.md,
      border: `2px solid ${theme.colors.gold}`,
      overflow: 'hidden',
      marginBottom: theme.spacing[4],
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      backgroundColor: theme.colors.gold,
      color: '#ffffff',
      cursor: 'pointer',
    },
    headerTitle: {
      fontWeight: theme.typography.semibold,
      fontSize: theme.typography.sm,
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing[2],
    },
    badge: {
      fontSize: theme.typography.xs,
      backgroundColor: 'rgba(255, 255, 255, 0.2)',
      padding: `2px ${theme.spacing[2]}`,
      borderRadius: '10px',
    },
    content: {
      padding: theme.spacing[4],
    },
    realAardvarkSection: {
      textAlign: 'center' as const,
    },
    sittingOutLabel: {
      fontSize: theme.typography.xs,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      color: theme.colors.textSecondary,
      marginBottom: theme.spacing[2],
    },
    playerName: {
      fontSize: theme.typography.xl,
      fontWeight: theme.typography.bold,
      color: theme.colors.gold,
      marginBottom: theme.spacing[1],
    },
    handicap: {
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary,
    },
    rotationInfo: {
      marginTop: theme.spacing[3],
      padding: theme.spacing[3],
      backgroundColor: theme.colors.gray100,
      borderRadius: theme.borderRadius.base,
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
    },
    invisibleSection: {
      display: 'flex',
      flexDirection: 'column' as const,
      alignItems: 'center',
      gap: theme.spacing[3],
    },
    invisibleLabel: {
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary,
      textAlign: 'center' as const,
    },
    invisibleHandicap: {
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
      backgroundColor: theme.colors.gray100,
      padding: `4px ${theme.spacing[3]}`,
      borderRadius: '12px',
    },
    scoreInputContainer: {
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing[2],
    },
    scoreButton: {
      width: '44px',
      height: '44px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.colors.gray100,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.borderRadius.base,
      cursor: 'pointer',
      fontSize: theme.typography.lg,
      fontWeight: theme.typography.bold,
      color: theme.colors.textPrimary,
      transition: 'all 0.15s ease',
    },
    scoreInput: {
      width: '80px',
      height: '56px',
      textAlign: 'center' as const,
      fontSize: theme.typography.xl,
      fontWeight: theme.typography.bold,
      backgroundColor: theme.colors.background,
      border: `2px solid ${theme.colors.gold}`,
      borderRadius: theme.borderRadius.base,
      color: theme.colors.textPrimary,
    },
    parReference: {
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary,
      marginTop: theme.spacing[1],
    },
    tunkarriNote: {
      marginTop: theme.spacing[3],
      padding: theme.spacing[3],
      backgroundColor: theme.isDark ? 'rgba(234, 179, 8, 0.2)' : 'rgba(234, 179, 8, 0.1)',
      borderRadius: theme.borderRadius.base,
      fontSize: theme.typography.xs,
      color: theme.colors.gold,
      textAlign: 'center' as const,
    },
  };

  const renderRealAardvark = () => (
    <div style={styles.realAardvarkSection}>
      <div style={styles.sittingOutLabel}>Sitting Out This Hole</div>
      {aardvarkPlayer ? (
        <>
          <div style={styles.playerName}>{aardvarkPlayer.name}</div>
          <div style={styles.handicap}>Handicap: {aardvarkPlayer.handicap}</div>
        </>
      ) : (
        <div style={styles.playerName}>Unknown Player</div>
      )}
      <div style={styles.rotationInfo}>
        Rotation: {aardvark.aardvarkIndex + 1} of {aardvark.aardvarkRotation.length}
        {aardvark.aardvarkRotation.length > 0 && (
          <div style={{ marginTop: theme.spacing[1] }}>
            Next up: {players.find(p =>
              p.id === aardvark.aardvarkRotation[(aardvark.aardvarkIndex + 1) % aardvark.aardvarkRotation.length]
            )?.name || 'Unknown'}
          </div>
        )}
      </div>
    </div>
  );

  const renderInvisibleAardvark = () => (
    <div style={styles.invisibleSection}>
      <div style={styles.invisibleLabel}>
        Enter the Invisible Aardvark's score for this hole
      </div>
      <div style={styles.invisibleHandicap}>
        Virtual Handicap: {aardvark.invisibleAardvarkHandicap}
      </div>
      <div style={styles.scoreInputContainer}>
        <button
          style={styles.scoreButton}
          onClick={() => {
            const current = parseInt(localScore, 10) || par;
            if (current > 1) handleScoreChange((current - 1).toString());
          }}
        >
          −
        </button>
        <input
          type="number"
          min="1"
          max="15"
          value={localScore}
          onChange={(e) => handleScoreChange(e.target.value)}
          style={styles.scoreInput}
          placeholder={par.toString()}
        />
        <button
          style={styles.scoreButton}
          onClick={() => {
            const current = parseInt(localScore, 10) || par;
            if (current < 15) handleScoreChange((current + 1).toString());
          }}
        >
          +
        </button>
      </div>
      <div style={styles.parReference}>Par {par}</div>
    </div>
  );

  return (
    <div style={styles.container}>
      <div style={styles.header} onClick={onToggleCollapse}>
        <span style={styles.headerTitle}>
          🦡 {aardvark.mode === 'real' ? 'Aardvark' : 'Invisible Aardvark'}
          {aardvark.tunkarriActive && <span style={styles.badge}>Tunkarri</span>}
        </span>
        <span>{isCollapsed ? '▼' : '▲'}</span>
      </div>

      {!isCollapsed && (
        <div style={styles.content}>
          {aardvark.mode === 'real' && renderRealAardvark()}
          {aardvark.mode === 'invisible' && renderInvisibleAardvark()}

          {aardvark.tunkarriActive && (
            <div style={styles.tunkarriNote}>
              Tunkarri mode active - special scoring rules apply
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AardvarkPanel;
