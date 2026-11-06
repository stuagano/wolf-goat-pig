// frontend/src/components/game/scorekeeper/useScorekeeperGameState.js
// Game-state reducer for SimpleScorekeeper: local-cache restore, useReducer,
// flattened state fields, and the stable action dispatchers. Moved verbatim
// from SimpleScorekeeper.jsx — hook call order is unchanged.

import { useMemo, useReducer } from "react";
import { gameReducer, createInitialState } from "../gameReducer";
import syncManager from "../../../services/syncManager";
import useGameActions from "../useGameActions";

/**
 * @returns {{ game: Object, actions: Object }} `game` holds the flattened
 *   reducer state under the component's original variable names; `actions`
 *   is the useGameActions dispatcher map.
 */
const useScorekeeperGameState = ({
  gameId,
  players,
  baseWager,
  initialHoleHistory,
  initialCurrentHole,
}) => {
  // Restore the local cache only when it holds unsynced work (see
  // syncManager.chooseGameState); null falls back to initialHoleHistory.
  const restoredState = useMemo(() => {
    const server = { holeHistory: initialHoleHistory };
    const chosen = syncManager.chooseGameState(gameId, server);
    return chosen !== server && chosen?.holeHistory ? chosen : null;
  }, [gameId, initialHoleHistory]);

  // Initialize game state reducer
  const [gameState, dispatch] = useReducer(
    gameReducer,
    {
      baseWager,
      initialCurrentHole,
      initialHoleHistory,
      players,
      restoredState,
    },
    createInitialState,
  );

  const {
    hole,
    teams,
    betting: bettingState,
    rotation,
    aardvark,
    history,
  } = gameState;

  const game = {
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
    currentWager: bettingState.currentWager,
    nextHoleWager: bettingState.nextHoleWager,
    floatInvokedBy: bettingState.floatInvokedBy,
    optionInvokedBy: bettingState.optionInvokedBy,
    optionActive: bettingState.optionActive,
    optionTurnedOff: bettingState.optionTurnedOff,
    duncanInvoked: bettingState.duncanInvoked,
    carryOver: bettingState.carryOver,
    vinniesVariation: bettingState.vinniesVariation,
    joesSpecialWager: bettingState.joesSpecialWager,

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
  };

  // ACTION DISPATCHERS - moved to useGameActions (stable identities)
  const actions = useGameActions(dispatch);

  return { game, actions };
};

export default useScorekeeperGameState;
