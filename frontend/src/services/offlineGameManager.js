/**
 * Offline Game Manager
 *
 * Allows the game to run entirely client-side when the backend is unavailable.
 * Useful for development, testing, or when database migrations are in progress.
 */

const generateGameId = () => {
  return `offline-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

const generateJoinCode = () => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let code = '';
  for (let i = 0; i < 6; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
};

/**
 * Create a game offline without backend
 * @param {Object} gameConfig - The game configuration
 * @param {Array<{id: string, name: string, handicap: number}>} gameConfig.players - Array of player objects
 * @param {number} [gameConfig.player_count=4] - Number of players in the game
 * @param {string} [gameConfig.course_name='Default Course'] - Name of the course
 * @returns {Object} The initial game state object
 */
export const createOfflineGame = (gameConfig) => {
  const now = new Date().toISOString();
  const gameId = generateGameId();
  const joinCode = generateJoinCode();

  // Initialize game state similar to backend
  const gameState = {
    game_id: gameId,
    join_code: joinCode,
    creator_user_id: 'offline-user',
    game_status: 'setup',
    offline_mode: true,
    created_at: now,
    updated_at: now,

    // Game configuration
    players: gameConfig.players || [],
    player_count: gameConfig.player_count || 4,
    course_name: gameConfig.course_name || 'Default Course',

    // Game state
    current_hole: 1,
    total_holes: 18,
    hole_history: [],
    player_scores: {},
    player_earnings: {},

    // Wolf Goat Pig specific
    wolf_rotation: [],
    current_wolf_index: 0,
    betting_state: {
      current_wager: 1,
      wager_history: []
    }
  };

  // Initialize player scores and earnings
  gameConfig.players?.forEach(player => {
    gameState.player_scores[player.id] = {
      total_strokes: 0,
      holes_completed: 0,
      holes_won: 0
    };
    gameState.player_earnings[player.id] = 0;
  });

  console.log('[Offline] Created offline game:', gameId);
  return gameState;
};

/**
 * Update offline game state
 * @param {Object} currentState - The current game state
 * @param {Object} update - Object containing fields to update
 * @returns {Object} The updated game state with new timestamp
 */
export const updateOfflineGame = (currentState, update) => {
  return {
    ...currentState,
    ...update,
    updated_at: new Date().toISOString()
  };
};

/**
 * Complete a hole in offline mode
 * @param {Object} currentState - The current game state
 * @param {Object} holeData - Data about the completed hole
 * @param {number} holeData.hole_number - The hole number that was completed
 * @param {Object} holeData.player_scores - Map of player IDs to their scores
 * @param {string} holeData.winner - The ID of the player who won
 * @param {number} holeData.wager - The wager amount for this hole
 * @returns {Object} The updated game state with hole completion recorded
 */
export const completeOfflineHole = (currentState, holeData) => {
  const { hole_number, player_scores, winner, wager } = holeData;

  const updatedState = { ...currentState };

  // Add to hole history
  updatedState.hole_history.push({
    hole_number,
    player_scores,
    winner,
    wager,
    completed_at: new Date().toISOString()
  });

  // Update player earnings
  if (winner && wager) {
    // Simplified earnings calculation
    // In real game, this would be more complex based on teams
    Object.keys(player_scores).forEach(playerId => {
      if (!updatedState.player_earnings[playerId]) {
        updatedState.player_earnings[playerId] = 0;
      }

      if (playerId === winner) {
        updatedState.player_earnings[playerId] += wager;
      }
    });
  }

  // Move to next hole
  updatedState.current_hole = Math.min(hole_number + 1, updatedState.total_holes);

  // Check if game is complete
  if (updatedState.current_hole > updatedState.total_holes) {
    updatedState.game_status = 'completed';
    updatedState.completed_at = new Date().toISOString();
  }

  updatedState.updated_at = new Date().toISOString();

  console.log('[Offline] Completed hole', hole_number);
  return updatedState;
};

/**
 * Check if we're in offline mode
 */
export const isOfflineGame = (gameState) => {
  return gameState?.offline_mode === true ||
         gameState?.game_id?.startsWith('offline-');
};

/**
 * Attempt to sync offline game to backend
 */
export const syncOfflineGame = async (gameState, apiUrl) => {
  if (!isOfflineGame(gameState)) {
    console.log('[Offline] Game is not an offline game, skipping sync');
    return { success: false, message: 'Not an offline game' };
  }

  try {
    // Attempt to create game on backend
    const response = await fetch(`${apiUrl}/game/import-offline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(gameState)
    });

    if (!response.ok) {
      throw new Error(`Sync failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('[Offline] Successfully synced game to backend:', data.game_id);

    return {
      success: true,
      message: 'Game synced successfully',
      backend_game_id: data.game_id
    };
  } catch (error) {
    console.error('[Offline] Failed to sync game:', error);
    return {
      success: false,
      message: error.message,
      error
    };
  }
};

const offlineGameManager = {
  createOfflineGame,
  updateOfflineGame,
  completeOfflineHole,
  isOfflineGame,
  syncOfflineGame,
  generateGameId,
  generateJoinCode
};

export default offlineGameManager;
