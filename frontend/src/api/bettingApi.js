// frontend/src/api/bettingApi.js

const API_URL = process.env.REACT_APP_API_URL || "";

/**
 * Syncs betting events to the backend API.
 *
 * @param {string} gameId - Unique identifier for the game
 * @param {number} holeNumber - Current hole number
 * @param {Array<Object>} events - Array of betting events to sync
 * @returns {Promise<Object>} Response with confirmed events
 * @throws {Error} If sync fails
 */
export const syncBettingEvents = async (gameId, holeNumber, events) => {
  const payload = {
    holeNumber,
    events,
    clientTimestamp: new Date().toISOString()
  };

  const response = await fetch(`${API_URL}/api/games/${gameId}/betting-events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Sync failed: ${response.status}`);
  }

  return await response.json();
};

/**
 * Syncs betting events with exponential backoff retry logic.
 *
 * @param {string} gameId - Unique identifier for the game
 * @param {number} holeNumber - Current hole number
 * @param {Array<Object>} events - Array of betting events to sync
 * @param {number} maxRetries - Maximum number of retry attempts (default: 3)
 * @returns {Promise<Object>} Response with confirmed events
 * @throws {Error} If sync fails after all retries
 */
export const syncWithRetry = async (gameId, holeNumber, events, maxRetries = 3) => {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await syncBettingEvents(gameId, holeNumber, events);
    } catch (error) {
      lastError = error;

      // Don't delay after the last attempt
      if (attempt < maxRetries - 1) {
        // Exponential backoff: 1s, 2s, 4s, 8s, 16s, capped at 30s
        const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
};
