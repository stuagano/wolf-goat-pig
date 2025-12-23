// =============================================================================
// useGameState Hook - Core State Management
// Manages team assignments, scores, quarters, hole history, and navigation
// =============================================================================

import { useState, useCallback } from 'react';
import {
  GameState,
  Game,
  Player,
  Course,
  Hole,
  CurrentHole,
  RotationState,
  AardvarkState,
  BettingState,
  StrokeAllocationState,
  UseGameStateReturn,
} from '../types';

// =============================================================================
// Initial State Factories
// =============================================================================

const createInitialRotation = (holeNumber: number): RotationState => ({
  holeNumber,
  rotationOrder: [],
  captainIndex: 0,
  isHoepfingerPhase: false,
  hoepfingerStartHole: 17,
  goatPlayerIndex: null,
});

const createInitialAardvark = (): AardvarkState => ({
  mode: 'none',
  aardvarkPlayerId: null,
  aardvarkRotation: [],
  aardvarkIndex: 0,
  invisibleAardvarkHandicap: 0,
  invisibleAardvarkScore: null,
  tunkarriActive: false,
});

const createInitialBetting = (baseWager: number): BettingState => ({
  playerUsage: {},
  currentWager: baseWager,
  baseWager,
  wagerMultiplier: 1,
  pendingOffers: [],
  duncanActive: false,
  duncanPlayerId: null,
  vinniesActive: false,
  vinniesMultiplier: 1,
});

const createInitialStrokes = (): StrokeAllocationState => ({
  allocations: {},
  creecherEnabled: true,
  displayMode: 'gross',
});

const createInitialCurrentHole = (holeNumber: number, par: number, wager: number): CurrentHole => ({
  hole: holeNumber,
  par,
  teamMode: 'partners',
  team1: [],
  team2: [],
  captain: null,
  opponents: [],
  grossScores: {},
  quarters: {},
  wager,
  bets: [],
  notes: '',
});

// =============================================================================
// Quarters Presets
// =============================================================================

const QUARTERS_PRESETS = {
  // 2v2 Partners scenarios
  'partners-win': (team1: string[], team2: string[], wager: number) => {
    const result: Record<string, number> = {};
    team1.forEach(id => { result[id] = wager; });
    team2.forEach(id => { result[id] = -wager; });
    return result;
  },
  'partners-lose': (team1: string[], team2: string[], wager: number) => {
    const result: Record<string, number> = {};
    team1.forEach(id => { result[id] = -wager; });
    team2.forEach(id => { result[id] = wager; });
    return result;
  },
  'partners-push': (team1: string[], team2: string[]) => {
    const result: Record<string, number> = {};
    [...team1, ...team2].forEach(id => { result[id] = 0; });
    return result;
  },
  // Solo scenarios
  'solo-win': (captain: string | null, opponents: string[], wager: number) => {
    if (!captain) return {};
    const result: Record<string, number> = {};
    const totalWin = wager * opponents.length;
    result[captain] = totalWin;
    opponents.forEach(id => { result[id] = -wager; });
    return result;
  },
  'solo-lose': (captain: string | null, opponents: string[], wager: number) => {
    if (!captain) return {};
    const result: Record<string, number> = {};
    const totalLoss = wager * opponents.length;
    result[captain] = -totalLoss;
    opponents.forEach(id => { result[id] = wager; });
    return result;
  },
  'solo-push': (captain: string | null, opponents: string[]) => {
    if (!captain) return {};
    const result: Record<string, number> = {};
    result[captain] = 0;
    opponents.forEach(id => { result[id] = 0; });
    return result;
  },
};

// =============================================================================
// Hook Implementation
// =============================================================================

interface UseGameStateOptions {
  game: Game;
  players: Player[];
  course: Course;
  initialHoleHistory?: Hole[];
}

export function useGameState({
  game,
  players,
  course,
  initialHoleHistory = [],
}: UseGameStateOptions): UseGameStateReturn {
  // Get par for a hole
  const getHolePar = useCallback((holeNumber: number): number => {
    const hole = course.holes.find(h => h.holeNumber === holeNumber);
    return hole?.par || 4;
  }, [course.holes]);

  // Initialize state
  const [state, setState] = useState<GameState>(() => ({
    game,
    players,
    course,
    holeHistory: initialHoleHistory,
    currentHole: createInitialCurrentHole(
      game.currentHole,
      getHolePar(game.currentHole),
      game.baseWager
    ),
    rotation: createInitialRotation(game.currentHole),
    aardvark: createInitialAardvark(),
    betting: createInitialBetting(game.baseWager),
    strokes: createInitialStrokes(),
    isLoading: false,
    error: null,
    lastSavedAt: null,
  }));

  // =============================================================================
  // Team Actions
  // =============================================================================

  const toggleTeam1 = useCallback((playerId: string) => {
    setState(prev => {
      const { currentHole } = prev;
      if (currentHole.teamMode !== 'partners') return prev;

      const isInTeam1 = currentHole.team1.includes(playerId);
      const isInTeam2 = currentHole.team2.includes(playerId);

      let newTeam1 = [...currentHole.team1];
      let newTeam2 = [...currentHole.team2];

      if (isInTeam1) {
        // Move from team1 to team2
        newTeam1 = newTeam1.filter(id => id !== playerId);
        newTeam2.push(playerId);
      } else if (isInTeam2) {
        // Move from team2 to team1
        newTeam2 = newTeam2.filter(id => id !== playerId);
        newTeam1.push(playerId);
      } else {
        // Not assigned - add to team1
        newTeam1.push(playerId);
      }

      return {
        ...prev,
        currentHole: {
          ...currentHole,
          team1: newTeam1,
          team2: newTeam2,
        },
      };
    });
  }, []);

  const selectCaptain = useCallback((playerId: string) => {
    setState(prev => {
      const { currentHole, players } = prev;
      if (currentHole.teamMode !== 'solo') return prev;

      // If already captain, deselect
      if (currentHole.captain === playerId) {
        return {
          ...prev,
          currentHole: {
            ...currentHole,
            captain: null,
            opponents: [],
          },
        };
      }

      // Set as captain, everyone else becomes opponent
      const opponents = players
        .filter(p => p.id !== playerId)
        .map(p => p.id);

      return {
        ...prev,
        currentHole: {
          ...currentHole,
          captain: playerId,
          opponents,
        },
      };
    });
  }, []);

  const setTeamMode = useCallback((mode: 'partners' | 'solo') => {
    setState(prev => ({
      ...prev,
      currentHole: {
        ...prev.currentHole,
        teamMode: mode,
        // Reset team assignments when switching modes
        team1: [],
        team2: [],
        captain: null,
        opponents: [],
      },
    }));
  }, []);

  // =============================================================================
  // Score Actions
  // =============================================================================

  const setScore = useCallback((playerId: string, score: number) => {
    setState(prev => ({
      ...prev,
      currentHole: {
        ...prev.currentHole,
        grossScores: {
          ...prev.currentHole.grossScores,
          [playerId]: score,
        },
      },
    }));
  }, []);

  const setQuarters = useCallback((playerId: string, quarters: number) => {
    setState(prev => ({
      ...prev,
      currentHole: {
        ...prev.currentHole,
        quarters: {
          ...prev.currentHole.quarters,
          [playerId]: quarters,
        },
      },
    }));
  }, []);

  const applyQuartersPreset = useCallback((presetId: string) => {
    setState(prev => {
      const { currentHole, betting } = prev;
      const wager = betting.currentWager;

      let newQuarters: Record<string, number> = {};

      if (currentHole.teamMode === 'partners') {
        switch (presetId) {
          case 'team1-win':
            newQuarters = QUARTERS_PRESETS['partners-win'](
              currentHole.team1, currentHole.team2, wager
            );
            break;
          case 'team1-lose':
            newQuarters = QUARTERS_PRESETS['partners-lose'](
              currentHole.team1, currentHole.team2, wager
            );
            break;
          case 'push':
            newQuarters = QUARTERS_PRESETS['partners-push'](
              currentHole.team1, currentHole.team2
            );
            break;
        }
      } else {
        switch (presetId) {
          case 'captain-win':
            newQuarters = QUARTERS_PRESETS['solo-win'](
              currentHole.captain, currentHole.opponents, wager
            );
            break;
          case 'captain-lose':
            newQuarters = QUARTERS_PRESETS['solo-lose'](
              currentHole.captain, currentHole.opponents, wager
            );
            break;
          case 'push':
            newQuarters = QUARTERS_PRESETS['solo-push'](
              currentHole.captain, currentHole.opponents
            );
            break;
        }
      }

      return {
        ...prev,
        currentHole: {
          ...currentHole,
          quarters: newQuarters,
        },
      };
    });
  }, []);

  // =============================================================================
  // Navigation
  // =============================================================================

  const goToHole = useCallback((holeNumber: number) => {
    setState(prev => {
      // Find if we have history for this hole
      const existingHole = prev.holeHistory.find(h => h.hole === holeNumber);

      if (existingHole) {
        // Load from history (edit mode)
        return {
          ...prev,
          currentHole: {
            hole: existingHole.hole,
            par: existingHole.par,
            teamMode: existingHole.teams.type,
            team1: existingHole.teams.type === 'partners' ? existingHole.teams.team1 : [],
            team2: existingHole.teams.type === 'partners' ? existingHole.teams.team2 : [],
            captain: existingHole.teams.type === 'solo' ? existingHole.teams.captain : null,
            opponents: existingHole.teams.type === 'solo' ? existingHole.teams.opponents : [],
            grossScores: existingHole.grossScores,
            quarters: existingHole.pointsDelta,
            wager: existingHole.wager,
            bets: existingHole.bets,
            notes: existingHole.notes,
          },
        };
      }

      // New hole
      const par = getHolePar(holeNumber);
      return {
        ...prev,
        currentHole: createInitialCurrentHole(holeNumber, par, prev.betting.baseWager),
        rotation: createInitialRotation(holeNumber),
      };
    });
  }, [getHolePar]);

  const undoLastHole = useCallback(() => {
    setState(prev => {
      if (prev.holeHistory.length === 0) return prev;

      const lastHole = prev.holeHistory[prev.holeHistory.length - 1];
      const newHistory = prev.holeHistory.slice(0, -1);

      // Recalculate standings by removing last hole's quarters
      const updatedPlayers = prev.players.map(player => {
        const quartersToRemove = lastHole.pointsDelta[player.id] || 0;
        return {
          ...player,
          standings: {
            ...player.standings,
            quarters: player.standings.quarters - quartersToRemove,
          },
        };
      });

      return {
        ...prev,
        players: updatedPlayers,
        holeHistory: newHistory,
        currentHole: {
          hole: lastHole.hole,
          par: lastHole.par,
          teamMode: lastHole.teams.type,
          team1: lastHole.teams.type === 'partners' ? lastHole.teams.team1 : [],
          team2: lastHole.teams.type === 'partners' ? lastHole.teams.team2 : [],
          captain: lastHole.teams.type === 'solo' ? lastHole.teams.captain : null,
          opponents: lastHole.teams.type === 'solo' ? lastHole.teams.opponents : [],
          grossScores: lastHole.grossScores,
          quarters: lastHole.pointsDelta,
          wager: lastHole.wager,
          bets: lastHole.bets,
          notes: lastHole.notes,
        },
      };
    });
  }, []);

  // =============================================================================
  // Notes
  // =============================================================================

  const setNotes = useCallback((notes: string) => {
    setState(prev => ({
      ...prev,
      currentHole: {
        ...prev.currentHole,
        notes,
      },
    }));
  }, []);

  // =============================================================================
  // Player Management
  // =============================================================================

  const editPlayerName = useCallback((playerId: string, newName: string) => {
    setState(prev => ({
      ...prev,
      players: prev.players.map(p =>
        p.id === playerId ? { ...p, name: newName } : p
      ),
    }));
  }, []);

  // =============================================================================
  // Validation
  // =============================================================================

  const validateCurrentHole = useCallback(() => {
    const errors: string[] = [];
    const { currentHole, players } = state;

    // Check all scores entered
    const missingScores = players.filter(
      p => currentHole.grossScores[p.id] === undefined || currentHole.grossScores[p.id] <= 0
    );
    if (missingScores.length > 0) {
      errors.push(`Missing scores for: ${missingScores.map(p => p.name).join(', ')}`);
    }

    // Check quarters sum to zero
    const quartersSum = Object.values(currentHole.quarters).reduce(
      (sum, q) => sum + (q || 0),
      0
    );
    if (quartersSum !== 0) {
      errors.push(`Quarters must sum to zero (currently ${quartersSum > 0 ? '+' : ''}${quartersSum})`);
    }

    // Check team formation
    if (currentHole.teamMode === 'partners') {
      if (currentHole.team1.length === 0 || currentHole.team2.length === 0) {
        errors.push('Both teams must have at least one player');
      }
    } else {
      if (!currentHole.captain) {
        errors.push('A captain must be selected');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }, [state]);

  // =============================================================================
  // Return Hook API
  // =============================================================================

  return {
    state,
    toggleTeam1,
    selectCaptain,
    setTeamMode,
    setScore,
    setQuarters,
    applyQuartersPreset,
    goToHole,
    undoLastHole,
    setNotes,
    editPlayerName,
    validateCurrentHole,
  };
}

export default useGameState;
