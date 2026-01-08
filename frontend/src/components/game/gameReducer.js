/**
 * Game State Reducer for SimpleScorekeeper
 * 
 * Consolidates 50+ useState hooks into organized state management.
 * Groups state into logical domains: hole, teams, betting, rotation, game history.
 */

// Action Types
export const GAME_ACTIONS = {
  // Hole actions
  SET_CURRENT_HOLE: 'SET_CURRENT_HOLE',
  UPDATE_SCORE: 'UPDATE_SCORE',
  SET_SCORES: 'SET_SCORES',
  UPDATE_QUARTERS: 'UPDATE_QUARTERS',
  SET_QUARTERS: 'SET_QUARTERS',
  SET_HOLE_NOTES: 'SET_HOLE_NOTES',
  SET_WINNER: 'SET_WINNER',
  RESET_HOLE: 'RESET_HOLE',
  
  // Team actions
  SET_TEAM_MODE: 'SET_TEAM_MODE',
  SET_TEAM1: 'SET_TEAM1',
  SET_TEAM2: 'SET_TEAM2',
  TOGGLE_PLAYER_TEAM: 'TOGGLE_PLAYER_TEAM',
  SET_CAPTAIN: 'SET_CAPTAIN',
  TOGGLE_CAPTAIN: 'TOGGLE_CAPTAIN',
  SET_OPPONENTS: 'SET_OPPONENTS',
  
  // Betting actions
  SET_CURRENT_WAGER: 'SET_CURRENT_WAGER',
  SET_NEXT_HOLE_WAGER: 'SET_NEXT_HOLE_WAGER',
  SET_FLOAT_INVOKED_BY: 'SET_FLOAT_INVOKED_BY',
  SET_OPTION_INVOKED_BY: 'SET_OPTION_INVOKED_BY',
  SET_OPTION_ACTIVE: 'SET_OPTION_ACTIVE',
  SET_OPTION_TURNED_OFF: 'SET_OPTION_TURNED_OFF',
  SET_DUNCAN_INVOKED: 'SET_DUNCAN_INVOKED',
  SET_CARRY_OVER: 'SET_CARRY_OVER',
  SET_VINNIES_VARIATION: 'SET_VINNIES_VARIATION',
  SET_JOES_SPECIAL_WAGER: 'SET_JOES_SPECIAL_WAGER',
  SET_PENDING_OFFER: 'SET_PENDING_OFFER',
  ADD_BETTING_EVENT: 'ADD_BETTING_EVENT',
  SET_BETTING_EVENTS: 'SET_BETTING_EVENTS',
  CLEAR_BETTING_EVENTS: 'CLEAR_BETTING_EVENTS',
  
  // Rotation actions
  SET_ROTATION_ORDER: 'SET_ROTATION_ORDER',
  SET_CAPTAIN_INDEX: 'SET_CAPTAIN_INDEX',
  SET_IS_HOEPFINGER: 'SET_IS_HOEPFINGER',
  SET_GOAT_ID: 'SET_GOAT_ID',
  SET_PHASE: 'SET_PHASE',
  
  // Aardvark actions (5-man game)
  SET_AARDVARK_REQUESTED_TEAM: 'SET_AARDVARK_REQUESTED_TEAM',
  SET_AARDVARK_TOSSED: 'SET_AARDVARK_TOSSED',
  SET_AARDVARK_SOLO: 'SET_AARDVARK_SOLO',
  SET_INVISIBLE_AARDVARK_TOSSED: 'SET_INVISIBLE_AARDVARK_TOSSED',
  
  // Game history actions
  SET_HOLE_HISTORY: 'SET_HOLE_HISTORY',
  ADD_HOLE_TO_HISTORY: 'ADD_HOLE_TO_HISTORY',
  UPDATE_HOLE_IN_HISTORY: 'UPDATE_HOLE_IN_HISTORY',
  SET_PLAYER_STANDINGS: 'SET_PLAYER_STANDINGS',
  
  // Batch actions
  LOAD_HOLE_FOR_EDIT: 'LOAD_HOLE_FOR_EDIT',
  INITIALIZE_FROM_STORAGE: 'INITIALIZE_FROM_STORAGE',
  SET_ROTATION_AND_WAGER: 'SET_ROTATION_AND_WAGER',
};

/**
 * Create initial state with defaults
 */
export const createInitialState = (props = {}) => {
  const {
    baseWager = 1,
    initialCurrentHole = 1,
    initialHoleHistory = [],
    players = [],
    restoredState = null,
  } = props;

  // Sort players by tee_order if available
  const sortedPlayers = [...players].sort((a, b) => {
    if (a.tee_order != null && b.tee_order != null) {
      return Number(a.tee_order) - Number(b.tee_order);
    }
    if (a.tee_order != null) return -1;
    if (b.tee_order != null) return 1;
    return 0;
  });

  return {
    // Hole state
    hole: {
      currentHole: restoredState?.currentHole ?? initialCurrentHole,
      scores: {},
      quarters: {},
      notes: '',
      winner: null,
    },
    
    // Team state
    teams: {
      mode: 'partners', // 'partners' or 'solo'
      team1: [],
      team2: [],
      captain: null,
      opponents: [],
    },
    
    // Betting state
    betting: {
      currentWager: baseWager,
      nextHoleWager: baseWager,
      baseWager,
      floatInvokedBy: null,
      optionInvokedBy: null,
      optionActive: false,
      optionTurnedOff: false,
      duncanInvoked: false,
      carryOver: false,
      vinniesVariation: false,
      joesSpecialWager: null,
      pendingOffer: null,
      currentHoleBettingEvents: [],
    },
    
    // Rotation state
    rotation: {
      order: sortedPlayers.map(p => p.id),
      captainIndex: 0,
      isHoepfinger: false,
      goatId: null,
      phase: 'normal', // 'normal', 'hoepfinger', etc.
    },
    
    // Aardvark state (5-man game)
    aardvark: {
      requestedTeam: null, // 'team1' or 'team2'
      tossed: false,
      solo: false,
      invisibleTossed: false,
    },
    
    // Game history
    history: {
      holes: restoredState?.holeHistory ?? initialHoleHistory,
      playerStandings: restoredState?.playerStandings ?? {},
    },
    
    // Editing state
    editing: {
      holeNumber: null,
      isEditingCompleteGame: false,
    },
  };
};

/**
 * Main game reducer
 */
export function gameReducer(state, action) {
  switch (action.type) {
    // ============ HOLE ACTIONS ============
    case GAME_ACTIONS.SET_CURRENT_HOLE:
      return {
        ...state,
        hole: { ...state.hole, currentHole: action.payload },
      };
      
    case GAME_ACTIONS.UPDATE_SCORE:
      return {
        ...state,
        hole: {
          ...state.hole,
          scores: { ...state.hole.scores, [action.payload.playerId]: action.payload.score },
        },
      };
      
    case GAME_ACTIONS.SET_SCORES:
      return {
        ...state,
        hole: { ...state.hole, scores: action.payload },
      };
      
    case GAME_ACTIONS.UPDATE_QUARTERS:
      return {
        ...state,
        hole: {
          ...state.hole,
          quarters: { ...state.hole.quarters, [action.payload.playerId]: action.payload.quarters },
        },
      };
      
    case GAME_ACTIONS.SET_QUARTERS:
      return {
        ...state,
        hole: { ...state.hole, quarters: action.payload },
      };
      
    case GAME_ACTIONS.SET_HOLE_NOTES:
      return {
        ...state,
        hole: { ...state.hole, notes: action.payload },
      };
      
    case GAME_ACTIONS.SET_WINNER:
      return {
        ...state,
        hole: { ...state.hole, winner: action.payload },
      };
      
    case GAME_ACTIONS.RESET_HOLE:
      return {
        ...state,
        hole: {
          currentHole: state.hole.currentHole,
          scores: {},
          quarters: {},
          notes: '',
          winner: null,
        },
        teams: {
          mode: 'partners',
          team1: [],
          team2: [],
          captain: null,
          opponents: [],
        },
        betting: {
          ...state.betting,
          currentWager: action.payload?.baseWager ?? state.betting.baseWager,
          floatInvokedBy: null,
          optionInvokedBy: null,
          optionTurnedOff: false,
          duncanInvoked: false,
          joesSpecialWager: null,
          pendingOffer: null,
          currentHoleBettingEvents: [],
        },
        aardvark: {
          requestedTeam: null,
          tossed: false,
          solo: false,
          invisibleTossed: false,
        },
        editing: {
          ...state.editing,
          holeNumber: null,
        },
      };

    // ============ TEAM ACTIONS ============
    case GAME_ACTIONS.SET_TEAM_MODE:
      return {
        ...state,
        teams: { ...state.teams, mode: action.payload },
      };
      
    case GAME_ACTIONS.SET_TEAM1:
      return {
        ...state,
        teams: { ...state.teams, team1: action.payload },
      };
      
    case GAME_ACTIONS.SET_TEAM2:
      return {
        ...state,
        teams: { ...state.teams, team2: action.payload },
      };
      
    case GAME_ACTIONS.TOGGLE_PLAYER_TEAM: {
      const playerId = action.payload;
      const newTeam1 = state.teams.team1.includes(playerId)
        ? state.teams.team1.filter(id => id !== playerId)
        : [...state.teams.team1, playerId];
      return {
        ...state,
        teams: { ...state.teams, team1: newTeam1 },
      };
    }
      
    case GAME_ACTIONS.SET_CAPTAIN:
      return {
        ...state,
        teams: { ...state.teams, captain: action.payload },
      };
      
    case GAME_ACTIONS.TOGGLE_CAPTAIN: {
      const { playerId, allPlayerIds } = action.payload;
      if (state.teams.captain === playerId) {
        return {
          ...state,
          teams: { ...state.teams, captain: null, opponents: [] },
        };
      }
      return {
        ...state,
        teams: {
          ...state.teams,
          captain: playerId,
          opponents: allPlayerIds.filter(id => id !== playerId),
        },
      };
    }
      
    case GAME_ACTIONS.SET_OPPONENTS:
      return {
        ...state,
        teams: { ...state.teams, opponents: action.payload },
      };

    // ============ BETTING ACTIONS ============
    case GAME_ACTIONS.SET_CURRENT_WAGER:
      return {
        ...state,
        betting: { ...state.betting, currentWager: action.payload },
      };
      
    case GAME_ACTIONS.SET_NEXT_HOLE_WAGER:
      return {
        ...state,
        betting: { ...state.betting, nextHoleWager: action.payload },
      };
      
    case GAME_ACTIONS.SET_FLOAT_INVOKED_BY:
      return {
        ...state,
        betting: { ...state.betting, floatInvokedBy: action.payload },
      };
      
    case GAME_ACTIONS.SET_OPTION_INVOKED_BY:
      return {
        ...state,
        betting: { ...state.betting, optionInvokedBy: action.payload },
      };
      
    case GAME_ACTIONS.SET_OPTION_ACTIVE:
      return {
        ...state,
        betting: { ...state.betting, optionActive: action.payload },
      };
      
    case GAME_ACTIONS.SET_OPTION_TURNED_OFF:
      return {
        ...state,
        betting: { ...state.betting, optionTurnedOff: action.payload },
      };
      
    case GAME_ACTIONS.SET_DUNCAN_INVOKED:
      return {
        ...state,
        betting: { ...state.betting, duncanInvoked: action.payload },
      };
      
    case GAME_ACTIONS.SET_CARRY_OVER:
      return {
        ...state,
        betting: { ...state.betting, carryOver: action.payload },
      };
      
    case GAME_ACTIONS.SET_VINNIES_VARIATION:
      return {
        ...state,
        betting: { ...state.betting, vinniesVariation: action.payload },
      };
      
    case GAME_ACTIONS.SET_JOES_SPECIAL_WAGER:
      return {
        ...state,
        betting: { ...state.betting, joesSpecialWager: action.payload },
      };
      
    case GAME_ACTIONS.SET_PENDING_OFFER:
      return {
        ...state,
        betting: { ...state.betting, pendingOffer: action.payload },
      };
      
    case GAME_ACTIONS.ADD_BETTING_EVENT:
      return {
        ...state,
        betting: {
          ...state.betting,
          currentHoleBettingEvents: [...state.betting.currentHoleBettingEvents, action.payload],
        },
      };
      
    case GAME_ACTIONS.SET_BETTING_EVENTS:
      return {
        ...state,
        betting: { ...state.betting, currentHoleBettingEvents: action.payload },
      };
      
    case GAME_ACTIONS.CLEAR_BETTING_EVENTS:
      return {
        ...state,
        betting: { ...state.betting, currentHoleBettingEvents: [] },
      };

    // ============ ROTATION ACTIONS ============
    case GAME_ACTIONS.SET_ROTATION_ORDER:
      return {
        ...state,
        rotation: { ...state.rotation, order: action.payload },
      };
      
    case GAME_ACTIONS.SET_CAPTAIN_INDEX:
      return {
        ...state,
        rotation: { ...state.rotation, captainIndex: action.payload },
      };
      
    case GAME_ACTIONS.SET_IS_HOEPFINGER:
      return {
        ...state,
        rotation: { ...state.rotation, isHoepfinger: action.payload },
      };
      
    case GAME_ACTIONS.SET_GOAT_ID:
      return {
        ...state,
        rotation: { ...state.rotation, goatId: action.payload },
      };
      
    case GAME_ACTIONS.SET_PHASE:
      return {
        ...state,
        rotation: { ...state.rotation, phase: action.payload },
      };

    // ============ AARDVARK ACTIONS ============
    case GAME_ACTIONS.SET_AARDVARK_REQUESTED_TEAM:
      return {
        ...state,
        aardvark: { ...state.aardvark, requestedTeam: action.payload },
      };
      
    case GAME_ACTIONS.SET_AARDVARK_TOSSED:
      return {
        ...state,
        aardvark: { ...state.aardvark, tossed: action.payload },
      };
      
    case GAME_ACTIONS.SET_AARDVARK_SOLO:
      return {
        ...state,
        aardvark: { ...state.aardvark, solo: action.payload },
      };
      
    case GAME_ACTIONS.SET_INVISIBLE_AARDVARK_TOSSED:
      return {
        ...state,
        aardvark: { ...state.aardvark, invisibleTossed: action.payload },
      };

    // ============ HISTORY ACTIONS ============
    case GAME_ACTIONS.SET_HOLE_HISTORY:
      return {
        ...state,
        history: { ...state.history, holes: action.payload },
      };
      
    case GAME_ACTIONS.ADD_HOLE_TO_HISTORY:
      return {
        ...state,
        history: {
          ...state.history,
          holes: [...state.history.holes, action.payload],
        },
      };
      
    case GAME_ACTIONS.UPDATE_HOLE_IN_HISTORY: {
      const { holeNumber, holeData } = action.payload;
      const updatedHoles = state.history.holes.map(h =>
        h.hole === holeNumber ? { ...h, ...holeData } : h
      );
      return {
        ...state,
        history: { ...state.history, holes: updatedHoles },
      };
    }
      
    case GAME_ACTIONS.SET_PLAYER_STANDINGS:
      return {
        ...state,
        history: { ...state.history, playerStandings: action.payload },
      };

    // ============ BATCH ACTIONS ============
    case GAME_ACTIONS.LOAD_HOLE_FOR_EDIT: {
      const hole = action.payload;
      return {
        ...state,
        hole: {
          currentHole: hole.hole,
          scores: hole.gross_scores || {},
          quarters: hole.points_delta || {},
          notes: hole.notes || '',
          winner: hole.winner,
        },
        teams: hole.teams?.type === 'partners'
          ? {
              mode: 'partners',
              team1: hole.teams.team1 || [],
              team2: hole.teams.team2 || [],
              captain: null,
              opponents: [],
            }
          : {
              mode: 'solo',
              team1: [],
              team2: [],
              captain: hole.teams?.captain || null,
              opponents: hole.teams?.opponents || [],
            },
        betting: {
          ...state.betting,
          currentWager: hole.wager || state.betting.baseWager,
          floatInvokedBy: hole.float_invoked_by || null,
          optionInvokedBy: hole.option_invoked_by || null,
          duncanInvoked: hole.duncan_invoked || false,
          optionTurnedOff: hole.option_turned_off || false,
          pendingOffer: null,
          currentHoleBettingEvents: hole.betting_events || [],
        },
        editing: {
          ...state.editing,
          holeNumber: hole.hole,
        },
      };
    }
    
    case GAME_ACTIONS.INITIALIZE_FROM_STORAGE: {
      const { currentHole, holeHistory, playerStandings } = action.payload;
      return {
        ...state,
        hole: { ...state.hole, currentHole },
        history: {
          holes: holeHistory,
          playerStandings: playerStandings || state.history.playerStandings,
        },
      };
    }
    
    case GAME_ACTIONS.SET_ROTATION_AND_WAGER: {
      const {
        rotationOrder,
        captainIndex,
        isHoepfinger,
        goatId,
        phase,
        baseWager,
        carryOver,
        vinniesVariation,
        optionActive,
        joesSpecialWager,
      } = action.payload;
      
      return {
        ...state,
        rotation: {
          ...state.rotation,
          order: rotationOrder ?? state.rotation.order,
          captainIndex: captainIndex ?? state.rotation.captainIndex,
          isHoepfinger: isHoepfinger ?? state.rotation.isHoepfinger,
          goatId: goatId ?? state.rotation.goatId,
          phase: phase ?? state.rotation.phase,
        },
        betting: {
          ...state.betting,
          currentWager: baseWager ?? state.betting.currentWager,
          nextHoleWager: baseWager ?? state.betting.nextHoleWager,
          carryOver: carryOver ?? state.betting.carryOver,
          vinniesVariation: vinniesVariation ?? state.betting.vinniesVariation,
          optionActive: optionActive ?? state.betting.optionActive,
          joesSpecialWager: joesSpecialWager ?? state.betting.joesSpecialWager,
        },
      };
    }

    default:
      console.warn(`Unknown action type: ${action.type}`);
      return state;
  }
}

/**
 * Action creators for cleaner dispatch calls
 */
export const gameActions = {
  // Hole
  setCurrentHole: (hole) => ({ type: GAME_ACTIONS.SET_CURRENT_HOLE, payload: hole }),
  updateScore: (playerId, score) => ({ type: GAME_ACTIONS.UPDATE_SCORE, payload: { playerId, score } }),
  setScores: (scores) => ({ type: GAME_ACTIONS.SET_SCORES, payload: scores }),
  updateQuarters: (playerId, quarters) => ({ type: GAME_ACTIONS.UPDATE_QUARTERS, payload: { playerId, quarters } }),
  setQuarters: (quarters) => ({ type: GAME_ACTIONS.SET_QUARTERS, payload: quarters }),
  setHoleNotes: (notes) => ({ type: GAME_ACTIONS.SET_HOLE_NOTES, payload: notes }),
  setWinner: (winner) => ({ type: GAME_ACTIONS.SET_WINNER, payload: winner }),
  resetHole: (options) => ({ type: GAME_ACTIONS.RESET_HOLE, payload: options }),
  
  // Teams
  setTeamMode: (mode) => ({ type: GAME_ACTIONS.SET_TEAM_MODE, payload: mode }),
  setTeam1: (team) => ({ type: GAME_ACTIONS.SET_TEAM1, payload: team }),
  setTeam2: (team) => ({ type: GAME_ACTIONS.SET_TEAM2, payload: team }),
  togglePlayerTeam: (playerId) => ({ type: GAME_ACTIONS.TOGGLE_PLAYER_TEAM, payload: playerId }),
  setCaptain: (captain) => ({ type: GAME_ACTIONS.SET_CAPTAIN, payload: captain }),
  toggleCaptain: (playerId, allPlayerIds) => ({ type: GAME_ACTIONS.TOGGLE_CAPTAIN, payload: { playerId, allPlayerIds } }),
  setOpponents: (opponents) => ({ type: GAME_ACTIONS.SET_OPPONENTS, payload: opponents }),
  
  // Betting
  setCurrentWager: (wager) => ({ type: GAME_ACTIONS.SET_CURRENT_WAGER, payload: wager }),
  setNextHoleWager: (wager) => ({ type: GAME_ACTIONS.SET_NEXT_HOLE_WAGER, payload: wager }),
  setFloatInvokedBy: (playerId) => ({ type: GAME_ACTIONS.SET_FLOAT_INVOKED_BY, payload: playerId }),
  setOptionInvokedBy: (playerId) => ({ type: GAME_ACTIONS.SET_OPTION_INVOKED_BY, payload: playerId }),
  setOptionActive: (active) => ({ type: GAME_ACTIONS.SET_OPTION_ACTIVE, payload: active }),
  setOptionTurnedOff: (off) => ({ type: GAME_ACTIONS.SET_OPTION_TURNED_OFF, payload: off }),
  setDuncanInvoked: (invoked) => ({ type: GAME_ACTIONS.SET_DUNCAN_INVOKED, payload: invoked }),
  setCarryOver: (carryOver) => ({ type: GAME_ACTIONS.SET_CARRY_OVER, payload: carryOver }),
  setVinniesVariation: (variation) => ({ type: GAME_ACTIONS.SET_VINNIES_VARIATION, payload: variation }),
  setJoesSpecialWager: (wager) => ({ type: GAME_ACTIONS.SET_JOES_SPECIAL_WAGER, payload: wager }),
  setPendingOffer: (offer) => ({ type: GAME_ACTIONS.SET_PENDING_OFFER, payload: offer }),
  addBettingEvent: (event) => ({ type: GAME_ACTIONS.ADD_BETTING_EVENT, payload: event }),
  setBettingEvents: (events) => ({ type: GAME_ACTIONS.SET_BETTING_EVENTS, payload: events }),
  clearBettingEvents: () => ({ type: GAME_ACTIONS.CLEAR_BETTING_EVENTS }),
  
  // Rotation
  setRotationOrder: (order) => ({ type: GAME_ACTIONS.SET_ROTATION_ORDER, payload: order }),
  setCaptainIndex: (index) => ({ type: GAME_ACTIONS.SET_CAPTAIN_INDEX, payload: index }),
  setIsHoepfinger: (is) => ({ type: GAME_ACTIONS.SET_IS_HOEPFINGER, payload: is }),
  setGoatId: (id) => ({ type: GAME_ACTIONS.SET_GOAT_ID, payload: id }),
  setPhase: (phase) => ({ type: GAME_ACTIONS.SET_PHASE, payload: phase }),
  
  // Aardvark
  setAardvarkRequestedTeam: (team) => ({ type: GAME_ACTIONS.SET_AARDVARK_REQUESTED_TEAM, payload: team }),
  setAardvarkTossed: (tossed) => ({ type: GAME_ACTIONS.SET_AARDVARK_TOSSED, payload: tossed }),
  setAardvarkSolo: (solo) => ({ type: GAME_ACTIONS.SET_AARDVARK_SOLO, payload: solo }),
  setInvisibleAardvarkTossed: (tossed) => ({ type: GAME_ACTIONS.SET_INVISIBLE_AARDVARK_TOSSED, payload: tossed }),
  
  // History
  setHoleHistory: (history) => ({ type: GAME_ACTIONS.SET_HOLE_HISTORY, payload: history }),
  addHoleToHistory: (hole) => ({ type: GAME_ACTIONS.ADD_HOLE_TO_HISTORY, payload: hole }),
  updateHoleInHistory: (holeNumber, holeData) => ({ type: GAME_ACTIONS.UPDATE_HOLE_IN_HISTORY, payload: { holeNumber, holeData } }),
  setPlayerStandings: (standings) => ({ type: GAME_ACTIONS.SET_PLAYER_STANDINGS, payload: standings }),
  
  // Batch
  loadHoleForEdit: (hole) => ({ type: GAME_ACTIONS.LOAD_HOLE_FOR_EDIT, payload: hole }),
  initializeFromStorage: (data) => ({ type: GAME_ACTIONS.INITIALIZE_FROM_STORAGE, payload: data }),
  setRotationAndWager: (data) => ({ type: GAME_ACTIONS.SET_ROTATION_AND_WAGER, payload: data }),
};

export default gameReducer;
