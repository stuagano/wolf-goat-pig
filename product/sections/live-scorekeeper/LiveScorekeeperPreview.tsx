// =============================================================================
// LiveScorekeeper Preview - Design Screen Preview Wrapper
// Imports sample data and renders the component for design review
// =============================================================================

import React, { useState, useCallback } from 'react';
import { LiveScorekeeper } from './components';
import {
  Game,
  Player,
  Course,
  Hole,
  CurrentHole,
  BettingAction,
  BetType,
} from './types';

// Import sample data (in production, this would be JSON import)
import sampleData from './data.json';

// Parse sample data with proper typing
const initialGame: Game = sampleData.game as Game;
const initialPlayers: Player[] = sampleData.players as Player[];
const initialCourse: Course = sampleData.course as Course;
const initialHoleHistory: Hole[] = sampleData.holeHistory as Hole[];
const initialCurrentHole: CurrentHole = sampleData.currentHole as CurrentHole;
const initialBettingActions: BettingAction[] = sampleData.bettingActions as BettingAction[];

/**
 * Preview wrapper that manages state for design testing
 */
const LiveScorekeeperPreview: React.FC = () => {
  // Stateful copies for interactive preview
  const [players, setPlayers] = useState<Player[]>(initialPlayers);
  const [currentHole, setCurrentHole] = useState<CurrentHole>(initialCurrentHole);
  const [holeHistory, setHoleHistory] = useState<Hole[]>(initialHoleHistory);

  // Team formation handlers
  const handleToggleTeam1 = useCallback((playerId: string) => {
    setCurrentHole((prev) => {
      const isInTeam1 = prev.team1.includes(playerId);
      if (isInTeam1) {
        return {
          ...prev,
          team1: prev.team1.filter((id) => id !== playerId),
          team2: [...prev.team2, playerId],
        };
      } else {
        return {
          ...prev,
          team1: [...prev.team1, playerId],
          team2: prev.team2.filter((id) => id !== playerId),
        };
      }
    });
  }, []);

  const handleSelectCaptain = useCallback((playerId: string) => {
    setCurrentHole((prev) => ({
      ...prev,
      captain: playerId,
      opponents: players
        .filter((p) => p.id !== playerId)
        .map((p) => p.id),
    }));
  }, [players]);

  const handleSetTeamMode = useCallback((mode: 'partners' | 'solo') => {
    setCurrentHole((prev) => ({
      ...prev,
      teamMode: mode,
      team1: mode === 'partners' ? [] : prev.team1,
      team2: mode === 'partners' ? [] : prev.team2,
      captain: mode === 'solo' ? null : prev.captain,
      opponents: mode === 'solo' ? [] : prev.opponents,
    }));
  }, []);

  // Score entry handlers
  const handleSetScore = useCallback((playerId: string, score: number) => {
    setCurrentHole((prev) => ({
      ...prev,
      grossScores: {
        ...prev.grossScores,
        [playerId]: score,
      },
    }));
  }, []);

  const handleSetQuarters = useCallback((playerId: string, quarters: number) => {
    setCurrentHole((prev) => ({
      ...prev,
      quarters: {
        ...prev.quarters,
        [playerId]: quarters,
      },
    }));
  }, []);

  // Betting handlers
  const handleInvokeBet = useCallback((betType: BetType, playerId: string) => {
    setCurrentHole((prev) => {
      const newBet = {
        id: `bet-${Date.now()}`,
        type: betType,
        invokedBy: playerId,
        timestamp: new Date().toISOString(),
      };

      let newWager = prev.wager;
      if (betType === 'float') {
        newWager = prev.wager * 2;
      }

      return {
        ...prev,
        bets: [...prev.bets, newBet],
        wager: newWager,
      };
    });
  }, []);

  // Hole management handlers
  const handleSubmitHole = useCallback(() => {
    console.log('Submitting hole:', currentHole);
    // In a real app, this would call the API
    alert(`Hole ${currentHole.hole} submitted!`);

    // Advance to next hole (simplified)
    setCurrentHole((prev) => ({
      ...prev,
      hole: prev.hole + 1,
      grossScores: {},
      quarters: {},
      team1: [],
      team2: [],
      captain: null,
      opponents: [],
      bets: [],
      notes: '',
      wager: 1,
    }));
  }, [currentHole]);

  const handleEditHole = useCallback((holeNumber: number) => {
    console.log('Editing hole:', holeNumber);
    // In a real app, this would load the hole data
  }, []);

  const handleSetNotes = useCallback((notes: string) => {
    setCurrentHole((prev) => ({
      ...prev,
      notes,
    }));
  }, []);

  const handleEditPlayerName = useCallback((playerId: string, newName: string) => {
    setPlayers((prev) =>
      prev.map((p) => (p.id === playerId ? { ...p, name: newName } : p))
    );
  }, []);

  const handleCompleteGame = useCallback(() => {
    console.log('Game complete!');
    alert('Congratulations! Game complete.');
  }, []);

  return (
    <LiveScorekeeper
      game={initialGame}
      players={players}
      course={initialCourse}
      holeHistory={holeHistory}
      currentHole={currentHole}
      bettingActions={initialBettingActions}
      onToggleTeam1={handleToggleTeam1}
      onSelectCaptain={handleSelectCaptain}
      onSetTeamMode={handleSetTeamMode}
      onSetScore={handleSetScore}
      onSetQuarters={handleSetQuarters}
      onInvokeBet={handleInvokeBet}
      onSubmitHole={handleSubmitHole}
      onEditHole={handleEditHole}
      onSetNotes={handleSetNotes}
      onEditPlayerName={handleEditPlayerName}
      onCompleteGame={handleCompleteGame}
    />
  );
};

export default LiveScorekeeperPreview;
