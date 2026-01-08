/**
 * useGameState - Main hook combining reducer with custom hooks
 * 
 * This is the primary hook for SimpleScorekeeper state management.
 * It combines:
 * - gameReducer for core game state
 * - useBettingState for betting logic
 * - useUIState for UI toggles
 */
import { useReducer, useEffect, useCallback, useMemo } from 'react';
import { gameReducer, createInitialState, gameActions } from '../components/game/gameReducer';
import { useBettingState } from './useBettingState';
import { useUIState } from './useUIState';
import syncManager from '../services/syncManager';

/**
 * useGameState - Combined state management hook
 * 
 * @param {Object} props
 * @param {string} props.gameId - Game ID
 * @param {Array} props.players - Array of player objects
 * @param {number} props.baseWager - Base wager amount
 * @param {Array} props.initialHoleHistory - Initial hole history from server
 * @param {number} props.initialCurrentHole - Initial current hole from server
 * @returns {Object} Combined state and actions
 */
export function useGameState({
  gameId,
  players,
  baseWager = 1,
  initialHoleHistory = [],
  initialCurrentHole = 1,
}) {
  // Try to restore from local storage first
  const restoredState = useMemo(() => {
    const localState = syncManager.loadLocalGameState(gameId);
    if (localState?.holeHistory && localState.holeHistory.length > initialHoleHistory.length) {
      console.log('[useGameState] Restored from local storage:', localState.holeHistory.length, 'holes');
      return localState;
    }
    return null;
  }, [gameId, initialHoleHistory.length]);

  // Initialize reducer with props
  const [state, dispatch] = useReducer(
    gameReducer,
    { baseWager, initialCurrentHole, initialHoleHistory, players, restoredState },
    createInitialState
  );

  // Extract state for convenience
  const { hole, teams, betting, rotation, aardvark, history, editing } = state;

  // Wrapper for setCurrentWager that dispatches to reducer
  const setCurrentWager = useCallback((wager) => {
    dispatch(gameActions.setCurrentWager(wager));
  }, []);

  // Initialize betting state hook
  const bettingState = useBettingState({
    currentHole: hole.currentHole,
    currentWager: betting.currentWager,
    setCurrentWager,
    players,
  });

  // Initialize UI state hook
  const uiState = useUIState();

  // Save game state locally whenever history changes
  useEffect(() => {
    if (gameId && history.holes.length > 0) {
      syncManager.saveLocalGameState(gameId, {
        holeHistory: history.holes,
        currentHole: hole.currentHole,
        playerStandings: history.playerStandings,
      });
    }
  }, [gameId, history.holes, hole.currentHole, history.playerStandings]);

  // Initialize player standings from hole history
  useEffect(() => {
    const standings = {};
    players.forEach(player => {
      standings[player.id] = {
        quarters: 0,
        name: player.name,
        soloCount: 0,
        floatCount: 0,
        optionCount: 0
      };
    });

    // Recalculate from history
    history.holes.forEach(holeData => {
      if (holeData.points_delta) {
        Object.entries(holeData.points_delta).forEach(([playerId, points]) => {
          if (standings[playerId]) {
            standings[playerId].quarters += points;
          }
        });
      }
      if (holeData.teams?.type === 'solo' && holeData.teams?.captain) {
        if (standings[holeData.teams.captain]) {
          standings[holeData.teams.captain].soloCount += 1;
        }
      }
      if (holeData.float_invoked_by && standings[holeData.float_invoked_by]) {
        standings[holeData.float_invoked_by].floatCount += 1;
      }
      if (holeData.option_invoked_by && standings[holeData.option_invoked_by]) {
        standings[holeData.option_invoked_by].optionCount += 1;
      }
    });

    dispatch(gameActions.setPlayerStandings(standings));
  }, [players, history.holes]);

  // ===========================================
  // Action creators with dispatch
  // ===========================================
  
  // Hole actions
  const setCurrentHole = useCallback((h) => dispatch(gameActions.setCurrentHole(h)), []);
  const updateScore = useCallback((playerId, score) => dispatch(gameActions.updateScore(playerId, score)), []);
  const setScores = useCallback((scores) => dispatch(gameActions.setScores(scores)), []);
  const updateQuarters = useCallback((playerId, q) => dispatch(gameActions.updateQuarters(playerId, q)), []);
  const setQuarters = useCallback((q) => dispatch(gameActions.setQuarters(q)), []);
  const setHoleNotes = useCallback((notes) => dispatch(gameActions.setHoleNotes(notes)), []);
  const setWinner = useCallback((w) => dispatch(gameActions.setWinner(w)), []);
  
  // Team actions
  const setTeamMode = useCallback((mode) => dispatch(gameActions.setTeamMode(mode)), []);
  const setTeam1 = useCallback((team) => dispatch(gameActions.setTeam1(team)), []);
  const setTeam2 = useCallback((team) => dispatch(gameActions.setTeam2(team)), []);
  const togglePlayerTeam = useCallback((playerId) => dispatch(gameActions.togglePlayerTeam(playerId)), []);
  const setCaptain = useCallback((c) => dispatch(gameActions.setCaptain(c)), []);
  const toggleCaptain = useCallback((playerId) => {
    dispatch(gameActions.toggleCaptain(playerId, players.map(p => p.id)));
  }, [players]);
  const setOpponents = useCallback((o) => dispatch(gameActions.setOpponents(o)), []);
  
  // Betting actions
  const setNextHoleWager = useCallback((w) => dispatch(gameActions.setNextHoleWager(w)), []);
  const setFloatInvokedBy = useCallback((p) => dispatch(gameActions.setFloatInvokedBy(p)), []);
  const setOptionInvokedBy = useCallback((p) => dispatch(gameActions.setOptionInvokedBy(p)), []);
  const setOptionActive = useCallback((a) => dispatch(gameActions.setOptionActive(a)), []);
  const setOptionTurnedOff = useCallback((o) => dispatch(gameActions.setOptionTurnedOff(o)), []);
  const setDuncanInvoked = useCallback((d) => dispatch(gameActions.setDuncanInvoked(d)), []);
  const setCarryOver = useCallback((c) => dispatch(gameActions.setCarryOver(c)), []);
  const setVinniesVariation = useCallback((v) => dispatch(gameActions.setVinniesVariation(v)), []);
  const setJoesSpecialWager = useCallback((w) => dispatch(gameActions.setJoesSpecialWager(w)), []);
  
  // Rotation actions
  const setRotationOrder = useCallback((o) => dispatch(gameActions.setRotationOrder(o)), []);
  const setCaptainIndex = useCallback((i) => dispatch(gameActions.setCaptainIndex(i)), []);
  const setIsHoepfinger = useCallback((h) => dispatch(gameActions.setIsHoepfinger(h)), []);
  const setGoatId = useCallback((id) => dispatch(gameActions.setGoatId(id)), []);
  const setPhase = useCallback((p) => dispatch(gameActions.setPhase(p)), []);
  
  // Aardvark actions
  const setAardvarkRequestedTeam = useCallback((t) => dispatch(gameActions.setAardvarkRequestedTeam(t)), []);
  const setAardvarkTossed = useCallback((t) => dispatch(gameActions.setAardvarkTossed(t)), []);
  const setAardvarkSolo = useCallback((s) => dispatch(gameActions.setAardvarkSolo(s)), []);
  const setInvisibleAardvarkTossed = useCallback((t) => dispatch(gameActions.setInvisibleAardvarkTossed(t)), []);
  
  // History actions
  const setHoleHistory = useCallback((h) => dispatch(gameActions.setHoleHistory(h)), []);
  const addHoleToHistory = useCallback((h) => dispatch(gameActions.addHoleToHistory(h)), []);
  const updateHoleInHistory = useCallback((num, data) => dispatch(gameActions.updateHoleInHistory(num, data)), []);
  
  // Batch actions
  const loadHoleForEdit = useCallback((holeData) => {
    dispatch(gameActions.loadHoleForEdit(holeData));
    bettingState.loadEventsForEdit(holeData.betting_events);
    uiState.setEditingHole(holeData.hole);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [bettingState, uiState]);
  
  const resetHole = useCallback(() => {
    dispatch(gameActions.resetHole({ baseWager }));
    bettingState.resetForNewHole();
    uiState.resetForNewHole();
  }, [baseWager, bettingState, uiState]);
  
  const setRotationAndWager = useCallback((data) => {
    dispatch(gameActions.setRotationAndWager(data));
  }, []);

  // ===========================================
  // Return combined state and actions
  // ===========================================
  return {
    // Raw state access
    state,
    dispatch,
    
    // Hole state
    currentHole: hole.currentHole,
    scores: hole.scores,
    quarters: hole.quarters,
    holeNotes: hole.notes,
    winner: hole.winner,
    
    // Team state
    teamMode: teams.mode,
    team1: teams.team1,
    team2: teams.team2,
    captain: teams.captain,
    opponents: teams.opponents,
    
    // Betting state (from reducer)
    currentWager: betting.currentWager,
    nextHoleWager: betting.nextHoleWager,
    floatInvokedBy: betting.floatInvokedBy,
    optionInvokedBy: betting.optionInvokedBy,
    optionActive: betting.optionActive,
    optionTurnedOff: betting.optionTurnedOff,
    duncanInvoked: betting.duncanInvoked,
    carryOver: betting.carryOver,
    vinniesVariation: betting.vinniesVariation,
    joesSpecialWager: betting.joesSpecialWager,
    
    // Rotation state
    rotationOrder: rotation.order,
    captainIndex: rotation.captainIndex,
    isHoepfinger: rotation.isHoepfinger,
    goatId: rotation.goatId,
    phase: rotation.phase,
    
    // Aardvark state
    aardvarkRequestedTeam: aardvark.requestedTeam,
    aardvarkTossed: aardvark.tossed,
    aardvarkSolo: aardvark.solo,
    invisibleAardvarkTossed: aardvark.invisibleTossed,
    
    // History state
    holeHistory: history.holes,
    playerStandings: history.playerStandings,
    
    // Editing state
    editingHole: editing.holeNumber,
    
    // Hole actions
    setCurrentHole,
    updateScore,
    setScores,
    updateQuarters,
    setQuarters,
    setHoleNotes,
    setWinner,
    resetHole,
    
    // Team actions
    setTeamMode,
    setTeam1,
    setTeam2,
    togglePlayerTeam,
    setCaptain,
    toggleCaptain,
    setOpponents,
    
    // Betting actions
    setCurrentWager,
    setNextHoleWager,
    setFloatInvokedBy,
    setOptionInvokedBy,
    setOptionActive,
    setOptionTurnedOff,
    setDuncanInvoked,
    setCarryOver,
    setVinniesVariation,
    setJoesSpecialWager,
    
    // Rotation actions
    setRotationOrder,
    setCaptainIndex,
    setIsHoepfinger,
    setGoatId,
    setPhase,
    setRotationAndWager,
    
    // Aardvark actions
    setAardvarkRequestedTeam,
    setAardvarkTossed,
    setAardvarkSolo,
    setInvisibleAardvarkTossed,
    
    // History actions
    setHoleHistory,
    addHoleToHistory,
    updateHoleInHistory,
    loadHoleForEdit,
    
    // Betting hook (interactive betting)
    betting: bettingState,
    
    // UI hook
    ui: uiState,
  };
}

export default useGameState;
