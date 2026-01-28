/**
 * Cache Manager Service
 *
 * Provides utilities for cache busting and version management.
 * Ensures users always have the latest version of the app.
 */

// App version - loaded from version.json at init, fallback to package version
export let APP_VERSION = "0.1.1";

// Build timestamp - auto-generated during build
export const BUILD_TIMESTAMP =
  process.env.REACT_APP_BUILD_TIME || new Date().toISOString();

// Load version from version.json (generated at build time)
let versionLoaded = false;
async function loadVersion() {
  if (versionLoaded) return;
  try {
    const response = await fetch("/version.json", { cache: "no-store" });
    if (response.ok) {
      const data = await response.json();
      APP_VERSION = data.version || APP_VERSION;
      versionLoaded = true;
      console.log("[CacheManager] Loaded version:", APP_VERSION);
    }
  } catch (e) {
    console.warn("[CacheManager] Could not load version.json:", e.message);
  }
}

// Cache keys
const CACHE_KEYS = {
  APP_VERSION: "wgp_app_version",
  LAST_UPDATE_CHECK: "wgp_last_update_check",
  UPDATE_DISMISSED: "wgp_update_dismissed",
};

// How often to check for updates (in milliseconds)
const UPDATE_CHECK_INTERVAL = 5 * 60 * 1000; // 5 minutes

/**
 * Get the stored app version from localStorage
 */
export function getStoredVersion() {
  try {
    return localStorage.getItem(CACHE_KEYS.APP_VERSION);
  } catch {
    return null;
  }
}

/**
 * Store the current app version in localStorage
 */
export function storeCurrentVersion() {
  try {
    localStorage.setItem(CACHE_KEYS.APP_VERSION, APP_VERSION);
  } catch (error) {
    console.warn("[CacheManager] Failed to store version:", error);
  }
}

/**
 * Check if the app has been updated since last visit
 */
export function hasAppUpdated() {
  const storedVersion = getStoredVersion();

  // First visit - no update
  if (!storedVersion) {
    storeCurrentVersion();
    return false;
  }

  // Compare versions
  if (storedVersion !== APP_VERSION) {
    return true;
  }

  return false;
}

/**
 * Clear all application caches
 */
export async function clearAllCaches() {
  console.log("[CacheManager] Clearing all caches...");

  const results = {
    serviceWorkerCache: false,
    localStorage: false,
    sessionStorage: false,
  };

  try {
    // Clear Service Worker caches
    if ("caches" in window) {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map((cacheName) => {
          console.log("[CacheManager] Deleting cache:", cacheName);
          return caches.delete(cacheName);
        }),
      );
      results.serviceWorkerCache = true;
    }
  } catch (error) {
    console.error("[CacheManager] Failed to clear SW caches:", error);
  }

  try {
    // Clear localStorage (except critical game data)
    const gameDataKeys = [
      "wolf-goat-pig-game-state",
      "wolf-goat-pig-game-backup",
    ];
    const keysToKeep = [...gameDataKeys];

    Object.keys(localStorage).forEach((key) => {
      if (!keysToKeep.some((k) => key.includes(k))) {
        localStorage.removeItem(key);
      }
    });
    results.localStorage = true;
  } catch (error) {
    console.error("[CacheManager] Failed to clear localStorage:", error);
  }

  try {
    // Clear sessionStorage
    sessionStorage.clear();
    results.sessionStorage = true;
  } catch (error) {
    console.error("[CacheManager] Failed to clear sessionStorage:", error);
  }

  console.log("[CacheManager] Cache clear results:", results);
  return results;
}

/**
 * Force refresh the app by clearing caches and reloading
 */
export async function forceRefresh() {
  console.log("[CacheManager] Force refreshing app...");

  // Clear all caches
  await clearAllCaches();

  // Update stored version
  storeCurrentVersion();

  // Unregister service worker and reload
  if ("serviceWorker" in navigator) {
    const registrations = await navigator.serviceWorker.getRegistrations();
    await Promise.all(registrations.map((reg) => reg.unregister()));
  }

  // Hard reload
  window.location.reload(true);
}

/**
 * Check if a new version is available from the server
 */
export async function checkForUpdates() {
  try {
    // Check rate limiting
    const lastCheck = localStorage.getItem(CACHE_KEYS.LAST_UPDATE_CHECK);
    if (lastCheck && Date.now() - parseInt(lastCheck) < UPDATE_CHECK_INTERVAL) {
      return { updateAvailable: false, cached: true };
    }

    // Fetch version file with cache-busting query string
    const response = await fetch(`/version.json?t=${Date.now()}`, {
      cache: "no-store",
      headers: {
        "Cache-Control": "no-cache",
        Pragma: "no-cache",
      },
    });

    if (!response.ok) {
      return { updateAvailable: false, error: "Version check failed" };
    }

    const serverVersion = await response.json();

    // Update last check time
    localStorage.setItem(CACHE_KEYS.LAST_UPDATE_CHECK, Date.now().toString());

    // Compare versions
    const updateAvailable = serverVersion.version !== APP_VERSION;

    return {
      updateAvailable,
      currentVersion: APP_VERSION,
      serverVersion: serverVersion.version,
      releaseNotes: serverVersion.releaseNotes || null,
    };
  } catch (error) {
    console.warn("[CacheManager] Update check failed:", error);
    return { updateAvailable: false, error: error.message };
  }
}

/**
 * Dismiss the update notification temporarily
 */
export function dismissUpdate(version) {
  try {
    localStorage.setItem(CACHE_KEYS.UPDATE_DISMISSED, version);
  } catch {
    // Ignore
  }
}

/**
 * Check if update notification was dismissed for this version
 */
export function isUpdateDismissed(version) {
  try {
    return localStorage.getItem(CACHE_KEYS.UPDATE_DISMISSED) === version;
  } catch {
    return false;
  }
}

/**
 * Send message to service worker to skip waiting
 */
export function skipWaiting() {
  if ("serviceWorker" in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({ type: "SKIP_WAITING" });
  }
}

/**
 * Get cache statistics
 */
export async function getCacheStats() {
  const stats = {
    cacheNames: [],
    totalSize: 0,
    entries: 0,
  };

  if ("caches" in window) {
    try {
      const cacheNames = await caches.keys();
      stats.cacheNames = cacheNames;

      for (const name of cacheNames) {
        const cache = await caches.open(name);
        const keys = await cache.keys();
        stats.entries += keys.length;
      }
    } catch (error) {
      console.warn("[CacheManager] Failed to get cache stats:", error);
    }
  }

  return stats;
}

/**
 * Initialize cache manager
 * Call this when the app starts
 */
export async function initCacheManager() {
  // Load version from version.json first
  await loadVersion();

  // Check for version update on app start
  if (hasAppUpdated()) {
    console.log(
      "[CacheManager] App updated from",
      getStoredVersion(),
      "to",
      APP_VERSION,
    );
    storeCurrentVersion();

    // Clear old caches on version update
    clearAllCaches().catch(console.error);
  }

  // Set up periodic update checks
  setInterval(() => {
    checkForUpdates().then((result) => {
      if (result.updateAvailable) {
        console.log(
          "[CacheManager] New version available:",
          result.serverVersion,
        );
        // Dispatch custom event for UI to handle
        window.dispatchEvent(
          new CustomEvent("appUpdateAvailable", {
            detail: result,
          }),
        );
      }
    });
  }, UPDATE_CHECK_INTERVAL);

  console.log("[CacheManager] Initialized - Version:", APP_VERSION);
}

const cacheManager = {
  APP_VERSION,
  BUILD_TIMESTAMP,
  getStoredVersion,
  storeCurrentVersion,
  hasAppUpdated,
  clearAllCaches,
  forceRefresh,
  checkForUpdates,
  dismissUpdate,
  isUpdateDismissed,
  skipWaiting,
  getCacheStats,
  initCacheManager,
};

export default cacheManager;
