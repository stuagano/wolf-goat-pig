/**
 * Smart API URL detection for simulation mode
 * Uses the same logic as api.config.js
 */
function detectApiUrl() {
  // 1. Check build-time environment variable (preferred)
  const envApiUrl = process.env.REACT_APP_API_URL;
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

export const simulationConfig = {
  apiUrl: detectApiUrl(),
};

const environmentConfig = {
  simulation: simulationConfig,
};

export default environmentConfig;
