import { useState, useCallback, useEffect, useRef } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || '';
const WS_URL = (API_URL || window.location.origin).replace(/^http/, 'ws');

/**
 * Hook for the matchmaking flow: fetching matches, accepting/declining,
 * and receiving real-time WebSocket notifications.
 */
const useMatchmaking = (playerProfileId) => {
  const { getAccessTokenSilently } = useAuth0();
  const [myMatches, setMyMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [respondingTo, setRespondingTo] = useState(null); // match_id being responded to
  const [wsConnected, setWsConnected] = useState(false);
  const [realtimeEvent, setRealtimeEvent] = useState(null);
  const wsRef = useRef(null);

  const authFetch = useCallback(async (url, options = {}) => {
    const token = await getAccessTokenSilently();
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

  const fetchMyMatches = useCallback(async (status) => {
    setLoading(true);
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
      setLoading(false);
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
  // WebSocket for real-time notifications
  // ========================================================================

  useEffect(() => {
    if (!playerProfileId) return;

    let ws;
    let reconnectTimeout;

    const connect = () => {
      try {
        ws = new WebSocket(`${WS_URL}/ws/user/${playerProfileId}`);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type && data.type !== 'pong') {
              setRealtimeEvent(data);
              // Auto-refresh matches on relevant events
              if ([
                'match_found',
                'match_accepted',
                'match_declined',
                'match_confirmed',
                'match_player_accepted',
              ].includes(data.type)) {
                fetchMyMatches();
              }
            }
          } catch {
            // ignore non-JSON messages
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          wsRef.current = null;
          // Reconnect after 5 seconds
          reconnectTimeout = setTimeout(connect, 5000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        // WebSocket not available
        reconnectTimeout = setTimeout(connect, 10000);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [playerProfileId, fetchMyMatches]);

  // Clear realtime event after 5 seconds
  useEffect(() => {
    if (realtimeEvent) {
      const t = setTimeout(() => setRealtimeEvent(null), 5000);
      return () => clearTimeout(t);
    }
  }, [realtimeEvent]);

  return {
    myMatches,
    loading,
    error,
    respondingTo,
    wsConnected,
    realtimeEvent,
    fetchMyMatches,
    acceptMatch,
    declineMatch,
    getMatchDetails,
  };
};

export default useMatchmaking;
