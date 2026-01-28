/**
 * Fetch wrapper with standard error handling for JSON APIs
 *
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<any>} - Parsed JSON response
 * @throws {Error} - On HTTP errors or invalid JSON
 */
export const fetchJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    // Try to get error detail from response body
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Ignore JSON parse errors for error response
    }
    throw new Error(errorMessage);
  }

  const data = await response.json();
  return data;
};

/**
 * Validate that response data is a non-null object
 * @param {any} data - Response data to validate
 * @param {string} context - Context for error message
 * @throws {Error} - If data is null or not an object
 */
export const validateObject = (data, context = "response") => {
  if (!data || typeof data !== "object") {
    throw new Error(`Invalid ${context}: expected object`);
  }
  return data;
};

export default fetchJson;
