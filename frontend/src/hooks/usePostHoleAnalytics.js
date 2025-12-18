import { useState, useEffect, useCallback } from 'react';
import useFetchAsync from './useFetchAsync';

/**
 * Hook for fetching and managing post-hole analytics
 */
const usePostHoleAnalytics = (holeNumber, isHoleComplete) => {
  const [analytics, setAnalytics] = useState(null);
  const { loading, error, get, clearError } = useFetchAsync({ throwOnError: false });

  const fetchAnalytics = useCallback(async () => {
    if (!holeNumber || !isHoleComplete) {
      return;
    }

    try {
      const data = await get(
        `/api/simulation/post-hole-analytics/${holeNumber}`,
        'Fetch post-hole analytics'
      );
      if (data) {
        setAnalytics(data);
      }
    } catch (err) {
      console.error('Error fetching post-hole analytics:', err);
    }
  }, [holeNumber, isHoleComplete, get]);

  useEffect(() => {
    if (isHoleComplete) {
      fetchAnalytics();
    }
  }, [isHoleComplete, fetchAnalytics]);

  const clearAnalytics = useCallback(() => {
    setAnalytics(null);
    clearError();
  }, [clearError]);

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