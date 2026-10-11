// frontend/src/hooks/useGameData.js
import { useCallback, useEffect, useState } from 'react';
import { apiConfig } from '../config/api.config';
import syncManager from '../services/syncManager';

const API_URL = apiConfig.baseUrl;
const DEFAULT_COURSE = 'Wing Point Golf & Country Club';
// The "hole" after 18: SimpleScorekeeper renders every hole as played and
// shows the completion view once currentHole is past the last hole.
const ROUND_COMPLETE_HOLE = 19;

/**
 * Map GET /games/{id}/state (snake_case) into the scorekeeper's view.
 * Single source of truth for completion: game_status is authoritative, and a
 * completed round without current_hole is placed past hole 18.
 */
export function normalizeGameState(data) {
  const isComplete = data.game_status === 'completed';
  return {
    players: data.players,
    currentHole: data.current_hole || (isComplete ? ROUND_COMPLETE_HOLE : 1),
    holeHistory: data.hole_history || [],
    standings: data.standings || {},
    strokeAllocation: data.stroke_allocation || null,
    courseName: data.course_name || DEFAULT_COURSE,
    baseWager: data.base_wager || 1,
    isComplete,
  };
}

/**
 * Load a game's state, reconcile the local offline cache against it, and fall
 * back to the local write-buffer when the server can't be reached.
 */
export default function useGameData(gameId) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [game, setGame] = useState(null);

  const reload = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_URL}/games/${gameId}/state`);

      if (!response.ok) {
        throw new Error('Failed to load game');
      }

      const data = await response.json();
      // Reconcile the local cache against server truth: flush unsynced edits,
      // or heal a stale/duplicated cache by overwriting it with server state.
      syncManager.reconcileOnLoad(gameId, {
        holeHistory: data.hole_history || [],
        currentHole: data.current_hole,
        playerStandings: data.standings || {},
        players: data.players || [],
        baseWager: data.base_wager || 1,
        courseName: data.course_name,
      });
      localStorage.setItem('wgp_current_game', gameId);
      setGame(normalizeGameState(data));
    } catch (err) {
      console.error('Error loading game:', err);
      // Bad course signal: open from the local write-buffer if we have a roster.
      const local = syncManager.loadLocalGameState(gameId);
      if (local?.players?.length) {
        syncManager.ensureScoresQueued(gameId, { holeHistory: [] });
        localStorage.setItem('wgp_current_game', gameId);
        setGame(normalizeGameState({
          players: local.players,
          hole_history: local.holeHistory,
          current_hole: local.currentHole,
          standings: local.playerStandings,
          course_name: local.courseName,
          base_wager: local.baseWager,
          game_status: 'in_progress',
        }));
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    if (gameId) {
      reload();
    }
  }, [gameId, reload]);

  return { loading, error, game, reload };
}
