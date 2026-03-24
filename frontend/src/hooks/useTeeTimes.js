import { useState, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || '';

const useTeeTimes = () => {
  const { getAccessTokenSilently } = useAuth0();
  const [teeTimes, setTeeTimes] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState(null);
  const [credentialsStatus, setCredentialsStatus] = useState(null);

  const clearError = useCallback(() => setError(null), []);
  const clearBookingError = useCallback(() => setBookingError(null), []);

  const authFetch = useCallback(async (url, options = {}) => {
    const token = await getAccessTokenSilently();
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
    return fetch(fullUrl, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      },
    });
  }, [getAccessTokenSilently]);

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

  const bookTeeTime = useCallback(async (ttdata, transportMode = 'WLK', date = null, time = null) => {
    setBookingLoading(true);
    setBookingError(null);
    try {
      const resp = await authFetch('/api/foretees/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ttdata, transport_mode: transportMode, date, time }),
      });
      const json = await resp.json();
      if (!resp.ok) {
        setBookingError(json?.detail || json?.message || 'Booking failed');
      }
      return json;
    } catch (err) {
      setBookingError(err.message);
      return null;
    } finally {
      setBookingLoading(false);
    }
  }, [authFetch]);

  return {
    teeTimes,
    bookings,
    loading,
    error,
    clearError,
    fetchTeeTimes,
    fetchBookings,
    bookTeeTime,
    bookingLoading,
    bookingError,
    clearBookingError,
    credentialsStatus,
    fetchCredentialsStatus,
    saveCredentials,
    removeCredentials,
  };
};

export default useTeeTimes;
