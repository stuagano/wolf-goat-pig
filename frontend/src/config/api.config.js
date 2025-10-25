/**
 * Smart API Configuration with Runtime Detection
 *
 * Handles multiple deployment scenarios:
 * - Local development (localhost:8000)
 * - Local production testing (Podman/Docker)
 * - Vercel production (Render backend)
 *
 * Priority:
 * 1. REACT_APP_API_URL environment variable (set in Vercel dashboard)
 * 2. Runtime detection from window.location
 * 3. Default fallback URLs
 */

/**
 * Detect the appropriate API URL based on environment
 */
function detectApiUrl() {
  // 1. Check build-time environment variable (preferred)
  const envApiUrl = process.env.REACT_APP_API_URL;
  if (envApiUrl && envApiUrl.trim() !== '') {
    console.log('[API Config] Using REACT_APP_API_URL:', envApiUrl);
    return envApiUrl.trim();
  }

  // 2. Runtime detection based on hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;

    // Local development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      const devUrl = 'http://localhost:8000';
      console.log('[API Config] Detected local development, using:', devUrl);
      return devUrl;
    }

    // Vercel production
    if (hostname.includes('vercel.app')) {
      const prodUrl = 'https://wolf-goat-pig.onrender.com';
      console.warn('[API Config] Detected Vercel deployment but REACT_APP_API_URL not set!');
      console.warn('[API Config] Using default production URL:', prodUrl);
      console.warn('[API Config] Please set REACT_APP_API_URL in Vercel dashboard');
      return prodUrl;
    }
  }

  // 3. Final fallback - assume production
  const fallbackUrl = 'https://wolf-goat-pig.onrender.com';
  console.warn('[API Config] No environment variable or hostname match');
  console.warn('[API Config] Using fallback URL:', fallbackUrl);
  return fallbackUrl;
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
  } catch (error) {
    console.error('[API Config] Invalid API URL:', url, error.message);
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

// Log configuration on startup
console.log('[API Config] Configuration:', {
  baseUrl: apiConfig.baseUrl,
  isDevelopment: apiConfig.isDevelopment,
  isProduction: apiConfig.isProduction,
  platform: apiConfig.platform,
});

export default apiConfig;
