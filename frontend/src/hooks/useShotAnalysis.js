import { useState, useCallback } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Hook for performing shot range analysis
 */
export const useShotAnalysis = () => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeShot = useCallback(async (formData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/wgp/shot-range-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      setAnalysis(data.analysis);
      return data.analysis;
    } catch (err) {
      console.error('Error analyzing shot:', err);
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearAnalysis = useCallback(() => {
    setAnalysis(null);
    setError(null);
  }, []);

  return {
    analysis,
    loading,
    error,
    analyzeShot,
    clearAnalysis
  };
};

export default useShotAnalysis;
