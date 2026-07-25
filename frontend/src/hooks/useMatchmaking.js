import { useState, useCallback, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { acquireAccessToken } from '../services/authToken';
import { api } from '../api/client';

// How often to refresh matches in the background. Matchmaking is not
// latency-critical, so a short poll over plain HTTP replaces the previous
// (unwired) WebSocket channel — no long-lived connection to manage.
const POLL_INTERVAL_MS = 15000;

// FastAPI errors come back as `{ detail: string | ValidationError[] }`.
// Pull out a human-readable message, falling back for the array/500 cases.
const errorDetail = (error) => {
  const detail = error && typeof error === 'object' ? error.detail : undefined;
  return typeof detail === 'string' ? detail : undefined;
};

/**
 * Hook for the matchmaking flow: fetching matches, accepting/declining,
 * and keeping the list fresh via background polling.
 *
 * All requests go through the generated, typed API client (`src/api/client`),
 * so paths, params, bodies, and responses are checked against the backend
 * OpenAPI contract.
 */
const useMatchmaking = (playerProfileId) => {
  const { getAccessTokenSilently } = useAuth0();
  const [myMatches, setMyMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [respondingTo, setRespondingTo] = useState(null); // match_id being responded to

  // Per-request auth header — token acquired via Auth0, with transparent
  // recovery from a missing/expired refresh token (see acquireAccessToken).
  const authHeaders = useCallback(async () => {
    const token = await acquireAccessToken(getAccessTokenSilently);
    return { Authorization: `Bearer ${token}` };
  }, [getAccessTokenSilently]);

  // ========================================================================
  // Fetch my matches
  // ========================================================================

  // `silent` skips the loading flag so background polls don't flicker the UI.
  const fetchMyMatches = useCallback(async (status, { silent = false } = {}) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const { data, error: apiError } = await api.GET('/matchmaking/my-matches', {
        params: { query: status ? { status } : {} },
        headers: await authHeaders(),
      });
      if (data) {
        setMyMatches(data);
      } else {
        setError(errorDetail(apiError) || 'Failed to fetch matches');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      if (!silent) setLoading(false);
    }
  }, [authHeaders]);

  // ========================================================================
  // Accept / Decline a match
  // ========================================================================

  const respondToMatch = useCallback(async (matchId, response) => {
    setRespondingTo(matchId);
    setError(null);
    try {
      const { data, error: apiError } = await api.POST('/matchmaking/matches/{match_id}/respond', {
        params: { path: { match_id: matchId } },
        body: { response },
        headers: await authHeaders(),
      });
      if (!data) {
        setError(errorDetail(apiError) || `Failed to ${response} match`);
        return null;
      }
      // Refresh matches list after responding
      await fetchMyMatches();
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setRespondingTo(null);
    }
  }, [authHeaders, fetchMyMatches]);

  const acceptMatch = useCallback((matchId) => respondToMatch(matchId, 'accepted'), [respondToMatch]);
  const declineMatch = useCallback((matchId) => respondToMatch(matchId, 'declined'), [respondToMatch]);

  // ========================================================================
  // Get match details
  // ========================================================================

  const getMatchDetails = useCallback(async (matchId) => {
    try {
      const { data } = await api.GET('/matchmaking/matches/{match_id}', {
        params: { path: { match_id: matchId } },
        headers: await authHeaders(),
      });
      return data ?? null;
    } catch {
      return null;
    }
  }, [authHeaders]);

  // ========================================================================
  // Background polling — keeps the matches list fresh over plain HTTP
  // ========================================================================

  useEffect(() => {
    if (!playerProfileId) return undefined;

    const interval = setInterval(() => {
      fetchMyMatches(undefined, { silent: true });
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [playerProfileId, fetchMyMatches]);

  return {
    myMatches,
    loading,
    error,
    respondingTo,
    fetchMyMatches,
    acceptMatch,
    declineMatch,
    getMatchDetails,
  };
};

export default useMatchmaking;
