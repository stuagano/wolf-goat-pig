/**
 * Smart API Configuration with Runtime Detection
 *
 * Handles multiple deployment scenarios:
 * - Local development (localhost:8000)
 * - Local production testing (Podman/Docker)
 * - Vercel production (Render backend)
 *
 * Priority:
 * 1. VITE_API_URL environment variable (set in Vercel dashboard)
 * 2. Runtime detection from window.location
 * 3. Default fallback URLs
 */

/**
 * Detect the appropriate API URL based on environment
 */
function detectApiUrl() {
  // 1. Check build-time environment variable (preferred)
  const envApiUrl = import.meta.env.VITE_API_URL;
  if (envApiUrl && envApiUrl.trim() !== '') {
    return envApiUrl.trim();
  }

  // 2. Runtime detection based on hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;

    // Local development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }

    // Vercel production
    if (hostname.includes('vercel.app')) {
      return 'https://wolf-goat-pig.onrender.com';
    }
  }

  // 3. Final fallback - assume production
  return 'https://wolf-goat-pig.onrender.com';
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

  // Deployment platform
  platform: typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')
    ? 'vercel'
    : 'local',
};

export default apiConfig;
