import { useState, useCallback, useRef } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { acquireAccessToken, apiTokenOptions } from '../services/authToken';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

const useTeeTimes = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [teeTimes, setTeeTimes] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState(null);
  const [credentialsStatus, setCredentialsStatus] = useState(null);
  const [pendingConfirm, setPendingConfirm] = useState(null);
  const confirmResolverRef = useRef(null);

  const clearError = useCallback(() => setError(null), []);
  const clearBookingError = useCallback(() => setBookingError(null), []);

  const authFetch = useCallback(async (url, options = {}) => {
    const token = await acquireAccessToken(getAccessTokenSilently, apiTokenOptions);
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
    return fetch(fullUrl, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      },
    });
  }, [getAccessTokenSilently]);

  const resolvePendingConfirm = useCallback((approved) => {
    const resolver = confirmResolverRef.current;
    confirmResolverRef.current = null;
    setPendingConfirm(null);
    if (resolver) resolver(approved);
  }, []);

  const waitForUserConfirm = useCallback((confirmPayload) => {
    setPendingConfirm(confirmPayload);
    setBookingLoading(false);
    return new Promise((resolve) => {
      confirmResolverRef.current = resolve;
    });
  }, []);

  const runWithConfirmLoop = useCallback(async (initialJson) => {
    let json = initialJson;
    // Computer Use agent may pause multiple times (login, then submit, plus safety).
    while (json?.data?.status === 'needs_confirmation') {
      const approved = await waitForUserConfirm(json.data);
      setBookingLoading(true);
      if (!approved) {
        setBookingError('Cancelled — confirmation denied');
        return { denied: true, data: { success: false, status: 'failed', error: 'User denied confirmation' } };
      }
      const resp = await authFetch('/api/foretees/book/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: json.data.job_id, confirm: true }),
      });
      json = await resp.json();
      if (!resp.ok && json?.data?.status !== 'needs_confirmation') {
        setBookingError(json?.detail || json?.message || 'Booking confirmation failed');
        return json;
      }
    }
    return json;
  }, [authFetch, waitForUserConfirm]);

  const fetchCredentialsStatus = useCallback(async () => {
    try {
      const resp = await authFetch('/api/foretees/credentials');
      if (resp.ok) {
        const json = await resp.json();
        setCredentialsStatus(json.data || null);
        return json.data;
      }
    } catch {
      // non-critical
    }
    return null;
  }, [authFetch]);

  const saveCredentials = useCallback(async (username, password) => {
    const resp = await authFetch('/api/foretees/credentials', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const json = await resp.json();
    if (!resp.ok) {
      throw new Error(json.detail || json.message || 'Failed to save credentials');
    }
    setCredentialsStatus(json.data || { configured: true, username });
    return json;
  }, [authFetch]);

  const removeCredentials = useCallback(async () => {
    const resp = await authFetch('/api/foretees/credentials', { method: 'DELETE' });
    const json = await resp.json();
    if (!resp.ok) {
      throw new Error(json.detail || json.message || 'Failed to remove credentials');
    }
    setCredentialsStatus({ configured: false, username: null });
    return json;
  }, [authFetch]);

  const fetchTeeTimes = useCallback(async (date) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await authFetch(`/api/foretees/tee-times?date=${date}`);
      const json = await resp.json();
      if (resp.ok && json?.data) {
        setTeeTimes(json.data);
      } else {
        setError(json?.detail || json?.message || 'Failed to fetch tee times');
      }
      return json;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [authFetch]);

  const fetchBookings = useCallback(async () => {
    try {
      const resp = await authFetch('/api/foretees/bookings');
      const json = await resp.json();
      if (resp.ok && json?.data) {
        setBookings(json.data);
      }
      return json;
    } catch {
      return null;
    }
  }, [authFetch]);

  const bookTeeTime = useCallback(async (ttdata, transportMode = 'WLK', date = null, time = null, players = null) => {
    setBookingLoading(true);
    setBookingError(null);
    setPendingConfirm(null);
    try {
      const resp = await authFetch('/api/foretees/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ttdata, transport_mode: transportMode, date, time, players }),
      });
      let json = await resp.json();
      if (!resp.ok && json?.data?.status !== 'needs_confirmation') {
        setBookingError(json?.detail || json?.message || 'Booking failed');
        return json;
      }
      json = await runWithConfirmLoop(json);
      if (!json?.denied && !(json?.data?.success || json?.success) && json?.data?.status !== 'needs_confirmation') {
        if (!json?.denied) {
          setBookingError(json?.detail || json?.message || json?.data?.error || 'Booking failed');
        }
      }
      return json;
    } catch (err) {
      setBookingError(err.message);
      return null;
    } finally {
      setBookingLoading(false);
      setPendingConfirm(null);
    }
  }, [authFetch, runWithConfirmLoop]);

  const cancelTeeTime = useCallback(async (date, time, ttdata) => {
    setBookingLoading(true);
    setBookingError(null);
    setPendingConfirm(null);
    try {
      const resp = await authFetch('/api/foretees/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, time, ttdata }),
      });
      let json = await resp.json();
      if (!resp.ok && json?.data?.status !== 'needs_confirmation') {
        setBookingError(json?.detail || json?.message || 'Cancellation failed');
        return json;
      }
      json = await runWithConfirmLoop(json);
      if (!json?.denied && !(json?.data?.success || json?.success)) {
        setBookingError(json?.detail || json?.message || json?.data?.error || 'Cancellation failed');
      }
      return json;
    } catch (err) {
      setBookingError(err.message);
      return null;
    } finally {
      setBookingLoading(false);
      setPendingConfirm(null);
    }
  }, [authFetch, runWithConfirmLoop]);

  return {
    teeTimes,
    bookings,
    loading,
    error,
    clearError,
    fetchTeeTimes,
    fetchBookings,
    bookTeeTime,
    cancelTeeTime,
    bookingLoading,
    bookingError,
    clearBookingError,
    credentialsStatus,
    fetchCredentialsStatus,
    saveCredentials,
    removeCredentials,
    pendingConfirm,
    resolvePendingConfirm,
  };
};

export default useTeeTimes;
