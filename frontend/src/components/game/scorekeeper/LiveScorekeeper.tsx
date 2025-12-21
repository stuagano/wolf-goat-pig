// =============================================================================
// LiveScorekeeper Component - Main Composite
// Core hole-by-hole interface for tracking a Wolf Goat Pig round
// =============================================================================

import React, { useState, useMemo } from 'react';
import { useTheme } from '../../../theme/Provider';
import {
  LiveScorekeeperProps,
} from './types';

import HoleHeader from './HoleHeader';
import TeamSelector from './TeamSelector';
import PlayerCard from './PlayerCard';
import BettingActionsPanel from './BettingActionsPanel';
import StandingsSidebar from './StandingsSidebar';
import NotesPanel from './NotesPanel';
import SubmitButton from './SubmitButton';

const LiveScorekeeper: React.FC<LiveScorekeeperProps> = ({
  game,
  players,
  course,
  // holeHistory - available for future use (viewing previous holes)
  currentHole,
  bettingActions,
  onToggleTeam1,
  onSelectCaptain,
  onSetTeamMode,
  onSetScore,
  onSetQuarters,
  onInvokeBet,
  onSubmitHole,
  onEditHole,
  // onSaveHoleEdit - available for future edit mode implementation
  onCancelEdit,
  onSetNotes,
  onEditPlayerName,
  onCompleteGame,
}) => {
  const theme = useTheme();

  // UI State
  const [showTeamSelection, setShowTeamSelection] = useState(true);
  const [showBettingActions, setShowBettingActions] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [standingsMinimized, setStandingsMinimized] = useState(true);
  const [editingHoleNumber, setEditingHoleNumber] = useState<number | null>(null);

  // Derive current hole data from course
  const currentHoleData = useMemo(() => {
    return course.holes.find((h) => h.holeNumber === currentHole.hole);
  }, [course.holes, currentHole.hole]);

  // Validation
  const validateHole = useMemo(() => {
    const allScoresEntered = players.every(
      (p) => currentHole.grossScores[p.id] !== undefined && currentHole.grossScores[p.id] > 0
    );

    const quartersSum = Object.values(currentHole.quarters).reduce(
      (sum, q) => sum + (q || 0),
      0
    );
    const quartersValid = quartersSum === 0;

    const teamsFormed =
      currentHole.teamMode === 'partners'
        ? currentHole.team1.length > 0
        : currentHole.captain !== null;

    return {
      canSubmit: allScoresEntered && quartersValid && teamsFormed,
      error: !teamsFormed
        ? 'Select teams before submitting'
        : !allScoresEntered
        ? 'Enter scores for all players'
        : !quartersValid
        ? `Quarters must sum to zero (currently ${quartersSum > 0 ? '+' : ''}${quartersSum})`
        : undefined,
    };
  }, [players, currentHole]);

  const getPlayerTeamStatus = (playerId: string) => {
    if (currentHole.teamMode === 'partners') {
      return {
        isTeam1: currentHole.team1.includes(playerId),
        isCaptain: false,
        isOpponent: currentHole.team2.includes(playerId),
      };
    } else {
      return {
        isTeam1: false,
        isCaptain: currentHole.captain === playerId,
        isOpponent: currentHole.opponents.includes(playerId),
      };
    }
  };

  const handleEditHole = (holeNumber: number) => {
    setEditingHoleNumber(holeNumber);
    onEditHole?.(holeNumber);
  };

  const handleSaveEdit = () => {
    setEditingHoleNumber(null);
  };

  const handleCancelEdit = () => {
    setEditingHoleNumber(null);
    onCancelEdit?.();
  };

  const styles = {
    container: {
      maxWidth: '480px',
      margin: '0 auto',
      padding: theme.spacing[4],
      fontFamily: theme.typography.fontFamily,
      backgroundColor: theme.colors.background,
      minHeight: '100vh',
    },
    playersSection: {
      marginBottom: theme.spacing[4],
    },
    sectionTitle: {
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      textTransform: 'uppercase' as const,
      letterSpacing: '0.5px',
      color: theme.colors.textSecondary,
      marginBottom: theme.spacing[2],
      paddingLeft: '4px',
    },
    editModeHeader: {
      backgroundColor: theme.colors.gold,
      color: '#ffffff',
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      borderRadius: theme.borderRadius.base,
      marginBottom: theme.spacing[4],
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    editModeText: {
      fontWeight: theme.typography.semibold,
      fontSize: theme.typography.sm,
    },
    editModeActions: {
      display: 'flex',
      gap: theme.spacing[2],
    },
    editButton: {
      padding: `6px ${theme.spacing[3]}`,
      fontSize: theme.typography.xs,
      fontWeight: theme.typography.semibold,
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer',
    },
    saveButton: {
      backgroundColor: '#ffffff',
      color: theme.colors.gold,
    },
    cancelButton: {
      backgroundColor: 'rgba(255, 255, 255, 0.2)',
      color: '#ffffff',
    },
  };

  return (
    <div style={styles.container}>
      {editingHoleNumber && (
        <div style={styles.editModeHeader}>
          <span style={styles.editModeText}>Editing Hole {editingHoleNumber}</span>
          <div style={styles.editModeActions}>
            <button
              style={{ ...styles.editButton, ...styles.cancelButton }}
              onClick={handleCancelEdit}
            >
              Cancel
            </button>
            <button
              style={{ ...styles.editButton, ...styles.saveButton }}
              onClick={handleSaveEdit}
            >
              Save
            </button>
          </div>
        </div>
      )}

      <HoleHeader
        holeNumber={currentHole.hole}
        par={currentHoleData?.par || currentHole.par}
        courseName={game.courseName}
        wager={currentHole.wager}
        onNavigateHole={handleEditHole}
      />

      <StandingsSidebar
        players={players}
        isMinimized={standingsMinimized}
        onToggleMinimize={() => setStandingsMinimized(!standingsMinimized)}
      />

      <TeamSelector
        teamMode={currentHole.teamMode}
        onSetTeamMode={onSetTeamMode || (() => {})}
        isCollapsed={!showTeamSelection}
        onToggleCollapse={() => setShowTeamSelection(!showTeamSelection)}
      />

      <div style={styles.playersSection}>
        <div style={styles.sectionTitle}>Players</div>
        {players.map((player) => {
          const teamStatus = getPlayerTeamStatus(player.id);
          return (
            <PlayerCard
              key={player.id}
              player={player}
              grossScore={currentHole.grossScores[player.id]}
              quarters={currentHole.quarters[player.id]}
              isTeam1={teamStatus.isTeam1}
              isCaptain={teamStatus.isCaptain}
              isOpponent={teamStatus.isOpponent}
              teamMode={currentHole.teamMode}
              onToggleTeam1={() => onToggleTeam1?.(player.id)}
              onSelectCaptain={() => onSelectCaptain?.(player.id)}
              onSetScore={(score) => onSetScore?.(player.id, score)}
              onSetQuarters={(quarters) => onSetQuarters?.(player.id, quarters)}
              onEditName={(newName) => onEditPlayerName?.(player.id, newName)}
              isEditable={!editingHoleNumber}
            />
          );
        })}
      </div>

      <BettingActionsPanel
        bettingActions={bettingActions}
        currentBets={currentHole.bets}
        players={players}
        currentWager={currentHole.wager}
        onInvokeBet={onInvokeBet}
        isExpanded={showBettingActions}
        onToggleExpanded={() => setShowBettingActions(!showBettingActions)}
      />

      <NotesPanel
        notes={currentHole.notes}
        onSetNotes={onSetNotes}
        isCollapsed={!showNotes}
        onToggleCollapse={() => setShowNotes(!showNotes)}
        isEditable={!editingHoleNumber}
      />

      <SubmitButton
        holeNumber={currentHole.hole}
        canSubmit={validateHole.canSubmit}
        validationError={validateHole.error}
        onSubmitHole={onSubmitHole}
        onCompleteGame={onCompleteGame}
      />
    </div>
  );
};

export default LiveScorekeeper;
