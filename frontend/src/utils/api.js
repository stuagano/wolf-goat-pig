/**
 * API Utility with Cold Start Handling
 * Handles Render's free tier cold start delays gracefully
 */

import { useState } from 'react';

const API_URL = process.env.REACT_APP_API_URL || "";

class ApiError extends Error {
  constructor(message, status, isColdStart = false) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.isColdStart = isColdStart;
  }
}

/**
 * Enhanced fetch with cold start detection and retry logic
 */
export const apiCall = async (endpoint, options = {}, retries = 3) => {
  const url = `${API_URL}${endpoint}`;
  const startTime = Date.now();
  
  // Default options
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  };

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeout = attempt === 0 ? 30000 : 60000; // First attempt: 30s, retries: 60s
      const timeoutId = setTimeout(() => controller.abort(), timeout);
      
      const response = await fetch(url, {
        ...defaultOptions,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const elapsed = Date.now() - startTime;
        const isColdStart = elapsed > 10000 && (response.status === 503 || response.status === 502);
        
        throw new ApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          isColdStart
        );
      }
      
      return response;
      
    } catch (error) {
      const elapsed = Date.now() - startTime;
      
      // Check if this looks like a cold start
      const isColdStart = error.name === 'AbortError' || elapsed > 10000;
      
      if (attempt === retries) {
        // Last attempt failed
        if (isColdStart) {
          throw new ApiError(
            'Backend is taking longer than expected to respond. This usually happens when the free hosting service needs to wake up.',
            503,
            true
          );
        } else {
          throw new ApiError(
            error.message || 'Network error occurred',
            error.status || 0,
            false
          );
        }
      }
      
      // Wait before retry (exponential backoff for cold starts)
      const waitTime = isColdStart ? Math.min(10000 * (attempt + 1), 30000) : 1000 * (attempt + 1);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
  }
};

/**
 * GET request with cold start handling
 */
export const apiGet = async (endpoint, retries = 3) => {
  const response = await apiCall(endpoint, { method: 'GET' }, retries);
  return response.json();
};

/**
 * POST request with cold start handling
 */
export const apiPost = async (endpoint, data, retries = 3) => {
  const response = await apiCall(endpoint, {
    method: 'POST',
    body: JSON.stringify(data)
  }, retries);
  return response.json();
};

/**
 * PUT request with cold start handling
 */
export const apiPut = async (endpoint, data, retries = 3) => {
  const response = await apiCall(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data)
  }, retries);
  return response.json();
};

/**
 * DELETE request with cold start handling
 */
export const apiDelete = async (endpoint, retries = 3) => {
  const response = await apiCall(endpoint, { method: 'DELETE' }, retries);
  return response.json();
};

/**
 * Health check with specific cold start messaging
 */
export const checkBackendHealth = async () => {
  try {
    const response = await apiCall('/health', { method: 'GET' }, 5); // More retries for health
    const data = await response.json();
    return { healthy: true, data };
  } catch (error) {
    return { 
      healthy: false, 
      error: error.message,
      isColdStart: error.isColdStart 
    };
  }
};

/**
 * Hook for components to handle API calls with loading states
 */
export const useApiCall = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isColdStart, setIsColdStart] = useState(false);

  const makeApiCall = async (apiFunction, ...args) => {
    setLoading(true);
    setError(null);
    setIsColdStart(false);
    
    try {
      const result = await apiFunction(...args);
      setLoading(false);
      return result;
    } catch (error) {
      setLoading(false);
      setError(error.message);
      setIsColdStart(error.isColdStart || false);
      throw error;
    }
  };

  return { makeApiCall, loading, error, isColdStart };
};

const apiUtilities = {
  get: apiGet,
  post: apiPost,
  put: apiPut,
  delete: apiDelete,
  call: apiCall,
  checkHealth: checkBackendHealth,
  useApiCall
};

export default apiUtilities;
