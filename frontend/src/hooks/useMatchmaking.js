import { useState, useCallback, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { acquireAccessToken } from '../services/authToken';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

// How often to refresh matches in the background. Matchmaking is not
// latency-critical, so a short poll over plain HTTP replaces the previous
// (unwired) WebSocket channel — no long-lived connection to manage.
const POLL_INTERVAL_MS = 15000;

/**
 * Hook for the matchmaking flow: fetching matches, accepting/declining,
 * and keeping the list fresh via background polling.
 */
const useMatchmaking = (playerProfileId) => {
  const { getAccessTokenSilently } = useAuth0();
  const [myMatches, setMyMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [respondingTo, setRespondingTo] = useState(null); // match_id being responded to

  const authFetch = useCallback(async (url, options = {}) => {
    const token = await acquireAccessToken(getAccessTokenSilently);
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
    return fetch(fullUrl, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
  }, [getAccessTokenSilently]);

  // ========================================================================
  // Fetch my matches
  // ========================================================================

  // `silent` skips the loading flag so background polls don't flicker the UI.
  const fetchMyMatches = useCallback(async (status, { silent = false } = {}) => {
    if (!silent) setLoading(true);
    setError(null);
    try {
      const params = status ? `?status=${status}` : '';
      const resp = await authFetch(`/matchmaking/my-matches${params}`);
      if (resp.ok) {
        const data = await resp.json();
        setMyMatches(data);
      } else {
        const err = await resp.json();
        setError(err.detail || 'Failed to fetch matches');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      if (!silent) setLoading(false);
    }
  }, [authFetch]);

  // ========================================================================
  // Accept / Decline a match
  // ========================================================================

  const respondToMatch = useCallback(async (matchId, response) => {
    setRespondingTo(matchId);
    setError(null);
    try {
      const resp = await authFetch(`/matchmaking/matches/${matchId}/respond`, {
        method: 'POST',
        body: JSON.stringify({ response }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setError(data.detail || `Failed to ${response} match`);
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
  }, [authFetch, fetchMyMatches]);

  const acceptMatch = useCallback((matchId) => respondToMatch(matchId, 'accepted'), [respondToMatch]);
  const declineMatch = useCallback((matchId) => respondToMatch(matchId, 'declined'), [respondToMatch]);

  // ========================================================================
  // Get match details
  // ========================================================================

  const getMatchDetails = useCallback(async (matchId) => {
    try {
      const resp = await authFetch(`/matchmaking/matches/${matchId}`);
      if (resp.ok) {
        return await resp.json();
      }
      return null;
    } catch {
      return null;
    }
  }, [authFetch]);

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
