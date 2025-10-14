import React, { createContext, useContext, useReducer, useCallback } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

// Game Context
const GameContext = createContext();

// Initial game state
const initialGameState = {
  // Core game state
  gameState: null,
  shotState: null,
  holeState: null,
  
  // UI state
  loading: false,
  error: null,
  
  // Game configuration
  players: [],
  currentHole: 1,
  currentPlayer: null,
  
  // Game history and tracking
  gameHistory: [],
  playerStrokes: {},
  bettingTips: [],
  
  // Simulation state
  isGameActive: false,
  interactionNeeded: null,
  pendingDecision: {},
  
  // Shot analysis
  shotProbabilities: null,
  hasNextShot: true,
  
  // Feedback and educational content
  feedback: [],
  rules: [],
  ruleIdx: 0,
};

// Action types
const GameActions = {
  // Core game actions
  SET_GAME_STATE: 'SET_GAME_STATE',
  SET_SHOT_STATE: 'SET_SHOT_STATE',
  SET_HOLE_STATE: 'SET_HOLE_STATE',
  
  // Loading and error states
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  
  // Game configuration
  SET_PLAYERS: 'SET_PLAYERS',
  SET_CURRENT_HOLE: 'SET_CURRENT_HOLE',
  SET_CURRENT_PLAYER: 'SET_CURRENT_PLAYER',
  
  // Game actions
  START_GAME: 'START_GAME',
  END_GAME: 'END_GAME',
  NEXT_HOLE: 'NEXT_HOLE',
  PREVIOUS_HOLE: 'PREVIOUS_HOLE',
  
  // Player actions
  UPDATE_PLAYER_STROKES: 'UPDATE_PLAYER_STROKES',
  ADD_FEEDBACK: 'ADD_FEEDBACK',
  CLEAR_FEEDBACK: 'CLEAR_FEEDBACK',
  
  // Betting and tips
  SET_BETTING_TIPS: 'SET_BETTING_TIPS',
  
  // Simulation state
  SET_INTERACTION_NEEDED: 'SET_INTERACTION_NEEDED',
  SET_PENDING_DECISION: 'SET_PENDING_DECISION',
  
  // Shot analysis
  SET_SHOT_PROBABILITIES: 'SET_SHOT_PROBABILITIES',
  SET_HAS_NEXT_SHOT: 'SET_HAS_NEXT_SHOT',
  
  // Educational content
  SET_RULES: 'SET_RULES',
  SET_RULE_INDEX: 'SET_RULE_INDEX',
  
  // Reset and cleanup
  RESET_GAME: 'RESET_GAME',
};

// Game reducer
const gameReducer = (state, action) => {
  switch (action.type) {
    case GameActions.SET_GAME_STATE:
      return { ...state, gameState: action.payload };
      
    case GameActions.SET_SHOT_STATE:
      return { ...state, shotState: action.payload };
      
    case GameActions.SET_HOLE_STATE:
      return { ...state, holeState: action.payload };
      
    case GameActions.SET_LOADING:
      return { ...state, loading: action.payload };
      
    case GameActions.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
      
    case GameActions.CLEAR_ERROR:
      return { ...state, error: null };
      
    case GameActions.SET_PLAYERS:
      return { ...state, players: action.payload };
      
    case GameActions.SET_CURRENT_HOLE:
      return { ...state, currentHole: action.payload };
      
    case GameActions.SET_CURRENT_PLAYER:
      return { ...state, currentPlayer: action.payload };
      
    case GameActions.START_GAME:
      return { 
        ...state, 
        isGameActive: true, 
        gameState: action.payload,
        error: null 
      };
      
    case GameActions.END_GAME:
      return { 
        ...state, 
        isGameActive: false, 
        gameState: null,
        currentHole: 1,
        interactionNeeded: null,
        pendingDecision: {}
      };
      
    case GameActions.NEXT_HOLE:
      return { 
        ...state, 
        currentHole: Math.min(state.currentHole + 1, 18),
        interactionNeeded: null,
        pendingDecision: {}
      };
      
    case GameActions.PREVIOUS_HOLE:
      return { 
        ...state, 
        currentHole: Math.max(state.currentHole - 1, 1) 
      };
      
    case GameActions.UPDATE_PLAYER_STROKES:
      return { 
        ...state, 
        playerStrokes: { 
          ...state.playerStrokes, 
          ...action.payload 
        } 
      };
      
    case GameActions.ADD_FEEDBACK:
      return { 
        ...state, 
        feedback: [...state.feedback, action.payload] 
      };
      
    case GameActions.CLEAR_FEEDBACK:
      return { ...state, feedback: [] };
      
    case GameActions.SET_BETTING_TIPS:
      return { ...state, bettingTips: action.payload };
      
    case GameActions.SET_INTERACTION_NEEDED:
      return { ...state, interactionNeeded: action.payload };
      
    case GameActions.SET_PENDING_DECISION:
      return { ...state, pendingDecision: action.payload };
      
    case GameActions.SET_SHOT_PROBABILITIES:
      return { ...state, shotProbabilities: action.payload };
      
    case GameActions.SET_HAS_NEXT_SHOT:
      return { ...state, hasNextShot: action.payload };
      
    case GameActions.SET_RULES:
      return { ...state, rules: action.payload };
      
    case GameActions.SET_RULE_INDEX:
      return { ...state, ruleIdx: action.payload };
      
    case GameActions.RESET_GAME:
      return { 
        ...initialGameState,
        rules: state.rules // Preserve rules
      };
      
    default:
      return state;
  }
};

// Game Provider Component
export const GameProvider = ({ children, initialState = {} }) => {
  const [state, dispatch] = useReducer(gameReducer, { ...initialGameState, ...initialState });

  // API Actions
  const fetchGameState = useCallback(async () => {
    dispatch({ type: GameActions.SET_LOADING, payload: true });
    try {
      const response = await fetch(`${API_URL}/game/state`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      dispatch({ type: GameActions.SET_GAME_STATE, payload: data });
    } catch (error) {
      const message = error?.message && error.message.startsWith('HTTP error!')
        ? error.message
        : 'Failed to fetch game state';
      dispatch({ type: GameActions.SET_ERROR, payload: message });
    } finally {
      dispatch({ type: GameActions.SET_LOADING, payload: false });
    }
  }, []);

  const createGame = useCallback(async (gameConfig) => {
    dispatch({ type: GameActions.SET_LOADING, payload: true });
    try {
      const response = await fetch(`${API_URL}/game/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(gameConfig),
      });
      if (!response.ok) throw new Error('Failed to create game');
      const data = await response.json();
      dispatch({ type: GameActions.START_GAME, payload: data });
      return data;
    } catch (error) {
      dispatch({ type: GameActions.SET_ERROR, payload: error.message });
      throw error;
    } finally {
      dispatch({ type: GameActions.SET_LOADING, payload: false });
    }
  }, []);

  const makeGameAction = useCallback(async (action, payload = {}) => {
    dispatch({ type: GameActions.SET_LOADING, payload: true });
    try {
      const response = await fetch(`${API_URL}/game/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, payload }),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      const nextState = data?.gameState ?? data;
      dispatch({ type: GameActions.SET_GAME_STATE, payload: nextState });
      return data;
    } catch (error) {
      dispatch({ type: GameActions.SET_ERROR, payload: error?.message || 'Failed to execute game action' });
      return undefined;
    } finally {
      dispatch({ type: GameActions.SET_LOADING, payload: false });
    }
  }, []);

  const submitShot = useCallback(async (shotData) => {
    dispatch({ type: GameActions.SET_LOADING, payload: true });
    try {
      const response = await fetch(`${API_URL}/game/shot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(shotData),
      });
      if (!response.ok) throw new Error('Failed to submit shot');
      const data = await response.json();
      dispatch({ type: GameActions.SET_GAME_STATE, payload: data });
      return data;
    } catch (error) {
      dispatch({ type: GameActions.SET_ERROR, payload: error.message });
      throw error;
    } finally {
      dispatch({ type: GameActions.SET_LOADING, payload: false });
    }
  }, []);

  const fetchBettingTips = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/game/tips`);
      if (!response.ok) throw new Error('Failed to fetch betting tips');
      const data = await response.json();
      dispatch({ type: GameActions.SET_BETTING_TIPS, payload: data });
      return data;
    } catch (error) {
      dispatch({ type: GameActions.SET_ERROR, payload: error.message });
    }
  }, []);

  const fetchPlayerStrokes = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/game/player_strokes`);
      if (!response.ok) throw new Error('Failed to fetch player strokes');
      const data = await response.json();
      dispatch({ type: GameActions.UPDATE_PLAYER_STROKES, payload: data });
      return data;
    } catch (error) {
      dispatch({ type: GameActions.SET_ERROR, payload: error.message });
    }
  }, []);

  const fetchRules = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/rules`);
      if (!response.ok) throw new Error('Failed to fetch rules');
      const data = await response.json();
      dispatch({ type: GameActions.SET_RULES, payload: data });
      return data;
    } catch (error) {
      dispatch({ type: GameActions.SET_ERROR, payload: error.message });
    }
  }, []);

  // Action creators
  const actions = {
    // Direct state updates
    setGameState: (gameState) => dispatch({ type: GameActions.SET_GAME_STATE, payload: gameState }),
    setShotState: (shotState) => dispatch({ type: GameActions.SET_SHOT_STATE, payload: shotState }),
    setHoleState: (holeState) => dispatch({ type: GameActions.SET_HOLE_STATE, payload: holeState }),
    setLoading: (loading) => dispatch({ type: GameActions.SET_LOADING, payload: loading }),
    setError: (error) => dispatch({ type: GameActions.SET_ERROR, payload: error }),
    clearError: () => dispatch({ type: GameActions.CLEAR_ERROR }),
    
    // Game flow
    startGame: (gameState) => dispatch({ type: GameActions.START_GAME, payload: gameState }),
    endGame: () => dispatch({ type: GameActions.END_GAME }),
    nextHole: () => dispatch({ type: GameActions.NEXT_HOLE }),
    previousHole: () => dispatch({ type: GameActions.PREVIOUS_HOLE }),
    resetGame: () => dispatch({ type: GameActions.RESET_GAME }),
    
    // Player management
    setPlayers: (players) => dispatch({ type: GameActions.SET_PLAYERS, payload: players }),
    setCurrentPlayer: (player) => dispatch({ type: GameActions.SET_CURRENT_PLAYER, payload: player }),
    setCurrentHole: (hole) => dispatch({ type: GameActions.SET_CURRENT_HOLE, payload: hole }),
    updatePlayerStrokes: (strokes) => dispatch({ type: GameActions.UPDATE_PLAYER_STROKES, payload: strokes }),
    
    // Feedback and education
    addFeedback: (feedback) => dispatch({ type: GameActions.ADD_FEEDBACK, payload: feedback }),
    clearFeedback: () => dispatch({ type: GameActions.CLEAR_FEEDBACK }),
    setRuleIndex: (index) => dispatch({ type: GameActions.SET_RULE_INDEX, payload: index }),
    setBettingTips: (tips) => dispatch({ type: GameActions.SET_BETTING_TIPS, payload: tips }),
    
    // Simulation state
    setInteractionNeeded: (interaction) => dispatch({ type: GameActions.SET_INTERACTION_NEEDED, payload: interaction }),
    setPendingDecision: (decision) => dispatch({ type: GameActions.SET_PENDING_DECISION, payload: decision }),
    
    // Shot analysis
    setShotProbabilities: (probabilities) => {
      const previousProbabilities =
        state.shotProbabilities && typeof state.shotProbabilities === 'object'
          ? { ...state.shotProbabilities }
          : null;

      const resolvedProbabilities =
        typeof probabilities === 'function'
          ? probabilities(previousProbabilities)
          : probabilities;

      if (
        resolvedProbabilities !== null &&
        (typeof resolvedProbabilities !== 'object' || Array.isArray(resolvedProbabilities))
      ) {
        console.warn('setShotProbabilities expected a plain object or null. Received:', resolvedProbabilities);
        dispatch({ type: GameActions.SET_SHOT_PROBABILITIES, payload: null });
        return;
      }

      const normalizedProbabilities =
        resolvedProbabilities && typeof resolvedProbabilities === 'object'
          ? { ...resolvedProbabilities }
          : null;

      dispatch({ type: GameActions.SET_SHOT_PROBABILITIES, payload: normalizedProbabilities });
    },
    setHasNextShot: (hasNext) => dispatch({ type: GameActions.SET_HAS_NEXT_SHOT, payload: hasNext }),
    
    // API actions
    fetchGameState,
    createGame,
    makeGameAction,
    submitShot,
    fetchBettingTips,
    fetchPlayerStrokes,
    fetchRules,
  };

  const value = {
    ...state,
    ...actions,
    dispatch, // For advanced use cases
  };

  return (
    <GameContext.Provider value={value}>
      {children}
    </GameContext.Provider>
  );
};

// Custom hook to use game context
export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};

export { GameActions };
export default GameProvider;
