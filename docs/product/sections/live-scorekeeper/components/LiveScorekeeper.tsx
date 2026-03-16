// =============================================================================
// LiveScorekeeper Component - Main Composite
// Core hole-by-hole interface for tracking a Wolf Goat Pig round
// =============================================================================

import React, { useState, useMemo } from 'react';
import {
  LiveScorekeeperProps,
  Player,
  Hole,
  BetType,
} from '../types';

import HoleHeader from './HoleHeader';
import TeamSelector from './TeamSelector';
import PlayerCard from './PlayerCard';
import BettingActionsPanel from './BettingActionsPanel';
import StandingsSidebar from './StandingsSidebar';
import NotesPanel from './NotesPanel';
import SubmitButton from './SubmitButton';

const styles = {
  container: {
    maxWidth: '480px',
    margin: '0 auto',
    padding: '16px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    backgroundColor: 'var(--color-background, #f9fafe)',
    minHeight: '100vh',
  },
  playersSection: {
    marginBottom: '16px',
  },
  sectionTitle: {
    fontSize: '12px',
    fontWeight: 600,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    color: 'var(--color-text-secondary, #757575)',
    marginBottom: '8px',
    paddingLeft: '4px',
  },
  divider: {
    height: '1px',
    backgroundColor: 'var(--color-border, #e0e0e0)',
    margin: '16px 0',
  },
  editModeHeader: {
    backgroundColor: '#B45309',
    color: '#ffffff',
    padding: '12px 16px',
    borderRadius: '8px',
    marginBottom: '16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  editModeText: {
    fontWeight: 600,
    fontSize: '14px',
  },
  editModeActions: {
    display: 'flex',
    gap: '8px',
  },
  editButton: {
    padding: '6px 12px',
    fontSize: '12px',
    fontWeight: 600,
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  saveButton: {
    backgroundColor: '#ffffff',
    color: '#B45309',
  },
  cancelButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    color: '#ffffff',
  },
};

const LiveScorekeeper: React.FC<LiveScorekeeperProps> = ({
  game,
  players,
  course,
  holeHistory,
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
  onSaveHoleEdit,
  onCancelEdit,
  onSetNotes,
  onEditPlayerName,
  onCompleteGame,
}) => {
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
    // Check all players have scores
    const allScoresEntered = players.every(
      (p) => currentHole.grossScores[p.id] !== undefined && currentHole.grossScores[p.id] > 0
    );

    // Check quarters sum to zero
    const quartersSum = Object.values(currentHole.quarters).reduce(
      (sum, q) => sum + (q || 0),
      0
    );
    const quartersValid = quartersSum === 0;

    // Check teams are formed
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

  // Determine if a player is on team 1 or is captain
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

  // Handle editing a previous hole
  const handleEditHole = (holeNumber: number) => {
    setEditingHoleNumber(holeNumber);
    onEditHole?.(holeNumber);
  };

  const handleSaveEdit = () => {
    // In a real implementation, we'd get the edited hole data
    // For now, just clear the editing state
    setEditingHoleNumber(null);
    // onSaveHoleEdit would be called with the edited data
  };

  const handleCancelEdit = () => {
    setEditingHoleNumber(null);
    onCancelEdit?.();
  };

  return (
    <div style={styles.container}>
      {/* Edit Mode Header */}
      {editingHoleNumber && (
        <div style={styles.editModeHeader}>
          <span style={styles.editModeText}>
            Editing Hole {editingHoleNumber}
          </span>
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

      {/* Hole Header */}
      <HoleHeader
        holeNumber={currentHole.hole}
        par={currentHoleData?.par || currentHole.par}
        courseName={game.courseName}
        wager={currentHole.wager}
        onNavigateHole={handleEditHole}
      />

      {/* Standings (Minimized by default, floating) */}
      <StandingsSidebar
        players={players}
        isMinimized={standingsMinimized}
        onToggleMinimize={() => setStandingsMinimized(!standingsMinimized)}
      />

      {/* Team Selection */}
      <TeamSelector
        teamMode={currentHole.teamMode}
        onSetTeamMode={onSetTeamMode || (() => {})}
        isCollapsed={!showTeamSelection}
        onToggleCollapse={() => setShowTeamSelection(!showTeamSelection)}
      />

      {/* Players Section */}
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

      {/* Betting Actions */}
      <BettingActionsPanel
        bettingActions={bettingActions}
        currentBets={currentHole.bets}
        players={players}
        currentWager={currentHole.wager}
        onInvokeBet={onInvokeBet}
        isExpanded={showBettingActions}
        onToggleExpanded={() => setShowBettingActions(!showBettingActions)}
      />

      {/* Notes */}
      <NotesPanel
        notes={currentHole.notes}
        onSetNotes={onSetNotes}
        isCollapsed={!showNotes}
        onToggleCollapse={() => setShowNotes(!showNotes)}
        isEditable={!editingHoleNumber}
      />

      {/* Submit Button */}
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
