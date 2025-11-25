/**
 * useFetchAsync - Centralized async fetch hook
 *
 * Eliminates duplicate loading/error/fetch patterns across API hooks.
 * Provides consistent error handling, loading states, and response processing.
 *
 * Features:
 * - Automatic loading state management
 * - Consistent error handling
 * - Response validation
 * - Request cancellation support
 * - Retry logic (optional)
 *
 * @example
 * const { loading, error, execute, clearError } = useFetchAsync();
 *
 * const fetchData = useCallback(async () => {
 *   return execute(
 *     () => fetch(`${API_URL}/data`),
 *     'Fetch data'
 *   );
 * }, [execute]);
 */

import { useState, useCallback, useRef } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Custom hook for async fetch operations with standardized error handling
 *
 * @param {Object} options - Configuration options
 * @param {boolean} options.throwOnError - Whether to throw errors (default: true)
 * @param {number} options.retryCount - Number of retries on failure (default: 0)
 * @param {number} options.retryDelay - Delay between retries in ms (default: 1000)
 * @returns {Object} Hook state and methods
 */
const useFetchAsync = (options = {}) => {
  const {
    throwOnError = true,
    retryCount = 0,
    retryDelay = 1000
  } = options;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  /**
   * Clear the current error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Cancel any in-flight request
   */
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  /**
   * Execute a fetch operation with automatic loading/error handling
   *
   * @param {Function} fetchFn - Function that returns a fetch Promise
   * @param {string} operationName - Name for error messages (default: 'Operation')
   * @param {Object} fetchOptions - Additional options
   * @param {boolean} fetchOptions.skipLoadingState - Don't update loading state
   * @param {Function} fetchOptions.onSuccess - Callback on success
   * @param {Function} fetchOptions.onError - Callback on error
   * @returns {Promise<any>} The parsed response data
   */
  const execute = useCallback(async (fetchFn, operationName = 'Operation', fetchOptions = {}) => {
    const { skipLoadingState = false, onSuccess, onError } = fetchOptions;

    // Cancel any previous request
    cancel();

    // Create new abort controller
    abortControllerRef.current = new AbortController();

    if (!skipLoadingState) {
      setLoading(true);
    }
    setError(null);

    let lastError = null;
    const attempts = retryCount + 1;

    for (let attempt = 1; attempt <= attempts; attempt++) {
      try {
        const response = await fetchFn(abortControllerRef.current.signal);

        // Handle non-Response objects (for custom fetch implementations)
        if (!(response instanceof Response)) {
          if (!skipLoadingState) {
            setLoading(false);
          }
          if (onSuccess) {
            onSuccess(response);
          }
          return response;
        }

        // Check for HTTP errors
        if (!response.ok) {
          let errorMessage = `${operationName} failed`;
          let errorDetails = {};

          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.message || errorMessage;
            errorDetails = errorData;
          } catch {
            // Response wasn't JSON, use status text
            errorMessage = `${operationName} failed: ${response.status} ${response.statusText}`;
          }

          throw new FetchError(errorMessage, response.status, errorDetails);
        }

        // Parse successful response
        const data = await response.json();

        if (!skipLoadingState) {
          setLoading(false);
        }

        if (onSuccess) {
          onSuccess(data);
        }

        return data;

      } catch (err) {
        lastError = err;

        // Don't retry on abort
        if (err.name === 'AbortError') {
          break;
        }

        // Don't retry on client errors (4xx)
        if (err instanceof FetchError && err.status >= 400 && err.status < 500) {
          break;
        }

        // Wait before retry (if not last attempt)
        if (attempt < attempts) {
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
      }
    }

    // All attempts failed
    if (!skipLoadingState) {
      setLoading(false);
    }

    const errorMessage = lastError?.message || `${operationName} failed`;
    setError(errorMessage);

    if (onError) {
      onError(lastError);
    }

    if (throwOnError) {
      throw lastError;
    }

    return null;
  }, [cancel, retryCount, retryDelay, throwOnError]);

  /**
   * Execute a GET request
   *
   * @param {string} url - URL to fetch (can be relative)
   * @param {string} operationName - Name for error messages
   * @param {Object} options - Fetch options
   * @returns {Promise<any>} The parsed response data
   */
  const get = useCallback(async (url, operationName = 'Fetch', options = {}) => {
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
    return execute(
      (signal) => fetch(fullUrl, { signal, ...options }),
      operationName
    );
  }, [execute]);

  /**
   * Execute a POST request
   *
   * @param {string} url - URL to post to (can be relative)
   * @param {any} data - Data to send in body
   * @param {string} operationName - Name for error messages
   * @param {Object} options - Additional fetch options
   * @returns {Promise<any>} The parsed response data
   */
  const post = useCallback(async (url, data, operationName = 'Create', options = {}) => {
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
    return execute(
      (signal) => fetch(fullUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...options.headers },
        body: JSON.stringify(data),
        signal,
        ...options
      }),
      operationName
    );
  }, [execute]);

  /**
   * Execute a PUT request
   *
   * @param {string} url - URL to put to (can be relative)
   * @param {any} data - Data to send in body
   * @param {string} operationName - Name for error messages
   * @param {Object} options - Additional fetch options
   * @returns {Promise<any>} The parsed response data
   */
  const put = useCallback(async (url, data, operationName = 'Update', options = {}) => {
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
    return execute(
      (signal) => fetch(fullUrl, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...options.headers },
        body: JSON.stringify(data),
        signal,
        ...options
      }),
      operationName
    );
  }, [execute]);

  /**
   * Execute a PATCH request
   *
   * @param {string} url - URL to patch
   * @param {any} data - Data to send in body
   * @param {string} operationName - Name for error messages
   * @param {Object} options - Additional fetch options
   * @returns {Promise<any>} The parsed response data
   */
  const patch = useCallback(async (url, data, operationName = 'Update', options = {}) => {
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
    return execute(
      (signal) => fetch(fullUrl, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...options.headers },
        body: JSON.stringify(data),
        signal,
        ...options
      }),
      operationName
    );
  }, [execute]);

  /**
   * Execute a DELETE request
   *
   * @param {string} url - URL to delete
   * @param {string} operationName - Name for error messages
   * @param {Object} options - Additional fetch options
   * @returns {Promise<any>} The parsed response data
   */
  const del = useCallback(async (url, operationName = 'Delete', options = {}) => {
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
    return execute(
      (signal) => fetch(fullUrl, {
        method: 'DELETE',
        signal,
        ...options
      }),
      operationName
    );
  }, [execute]);

  return {
    loading,
    error,
    execute,
    clearError,
    cancel,
    // Convenience methods
    get,
    post,
    put,
    patch,
    del
  };
};

/**
 * Custom error class for fetch errors with status code
 */
class FetchError extends Error {
  constructor(message, status, details = {}) {
    super(message);
    this.name = 'FetchError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Helper to create a fetch function with automatic API_URL prefixing
 *
 * @param {string} endpoint - API endpoint (will be prefixed with API_URL)
 * @param {Object} options - Fetch options
 * @returns {Function} Fetch function for use with execute()
 */
export const createFetchFn = (endpoint, options = {}) => {
  return (signal) => fetch(`${API_URL}${endpoint}`, { signal, ...options });
};

/**
 * Helper to create a POST fetch function
 *
 * @param {string} endpoint - API endpoint
 * @param {any} data - Data to send
 * @param {Object} options - Additional options
 * @returns {Function} Fetch function for use with execute()
 */
export const createPostFn = (endpoint, data, options = {}) => {
  return (signal) => fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    body: JSON.stringify(data),
    signal,
    ...options
  });
};

export { FetchError };
export default useFetchAsync;
