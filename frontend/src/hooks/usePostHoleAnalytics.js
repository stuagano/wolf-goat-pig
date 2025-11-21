import { useState, useEffect, useCallback } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Hook for fetching and managing post-hole analytics
 */
const usePostHoleAnalytics = (holeNumber, isHoleComplete) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    if (!holeNumber || !isHoleComplete) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/simulation/post-hole-analytics/${holeNumber}`);
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch analytics');
      }

      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Error fetching post-hole analytics:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [holeNumber, isHoleComplete]);

  useEffect(() => {
    if (isHoleComplete) {
      fetchAnalytics();
    }
  }, [isHoleComplete, fetchAnalytics]);

  const clearAnalytics = useCallback(() => {
    setAnalytics(null);
    setError(null);
  }, []);

  const retryFetch = useCallback(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return {
    analytics,
    loading,
    error,
    clearAnalytics,
    retryFetch
  };
};

export default usePostHoleAnalytics;