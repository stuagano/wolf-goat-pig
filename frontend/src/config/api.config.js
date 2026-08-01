/**
 * API configuration for local development and Firebase Hosting → Cloud Run.
 *
 * Priority:
 * 1. VITE_API_URL build-time override (preferred for previews/production builds)
 * 2. localhost → local backend
 * 3. Cloud Run production fallback
 */

/**
 * Detect the appropriate API URL based on environment
 */
function detectApiUrl() {
  const envApiUrl = import.meta.env.VITE_API_URL;
  if (envApiUrl && envApiUrl.trim() !== '') {
    return envApiUrl.trim();
  }

  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
  }

  return 'https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app';
}

/**
 * Validate API URL format
 */
function validateApiUrl(url) {
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      throw new Error(`Invalid protocol: ${parsed.protocol}`);
    }
    return true;
  } catch {
    return false;
  }
}

/**
 * Detect deployment platform from the browser hostname.
 */
function detectPlatform() {
  if (typeof window === 'undefined') return 'local';
  const host = window.location.hostname;
  if (host.endsWith('.web.app') || host.endsWith('.firebaseapp.com')) {
    return 'firebase';
  }
  return 'local';
}

// Detect and validate API URL
const API_URL = detectApiUrl();

if (!validateApiUrl(API_URL)) {
  throw new Error(`Invalid API_URL detected: ${API_URL}`);
}

// Export configuration
export const apiConfig = {
  baseUrl: API_URL,
  timeout: 30000,
  retries: 3,

  // Health check endpoint
  healthEndpoint: '/health',

  // Environment detection
  isDevelopment: API_URL.includes('localhost'),
  isProduction: !API_URL.includes('localhost'),

  platform: detectPlatform(),
};

export default apiConfig;
