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
  import.meta.env.VITE_BUILD_TIME || new Date().toISOString();

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
      // Version loaded successfully
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

// localStorage keys that must SURVIVE cache busting. Wiping these on every
// deploy logged users out (Auth0 stores its session in localStorage because
// cacheLocation="localstorage") and forced the Auth0->profile linkage /
// legacy-name onboarding to redo on every build. Stale *code* lives in the
// Service Worker caches, never in localStorage — so identity, in-progress
// game, and app preferences are always preserved.
const PRESERVED_KEY_PARTS = [
  "@@auth0spajs@@", // Auth0 SDK session tokens
  "wolf-goat-pig-game-state",
  "wolf-goat-pig-game-backup",
  "legacy_name_skipped", // onboarding "I'm not on the list" choice
  "wgp_", // app state: current game, assist mode, version, sessions
  "wgp-", // namespaced stores (e.g. wgp-sync)
];

const isPreservedKey = (key) =>
  PRESERVED_KEY_PARTS.some((part) => key.includes(part));

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
 * Clear ONLY the Service Worker / asset caches. This is what actually busts
 * stale code on a new deploy. It never touches localStorage, so the Auth0
 * session and profile linkage survive a build.
 */
export async function clearServiceWorkerCaches() {
  if (!("caches" in window)) return false;
  try {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map((cacheName) => caches.delete(cacheName)));
    return true;
  } catch (error) {
    console.error("[CacheManager] Failed to clear SW caches:", error);
    return false;
  }
}

/**
 * Clear application caches. Busts the Service Worker/asset caches and clears
 * transient localStorage/sessionStorage, but PRESERVES auth session, profile
 * linkage, in-progress game, and app preferences (see PRESERVED_KEY_PARTS).
 *
 * Used by the manual "force refresh" path. The automatic per-deploy path
 * (initCacheManager) intentionally does NOT call this — it only clears SW
 * caches — so a routine deploy never disturbs localStorage at all.
 */
export async function clearAllCaches() {
  const results = {
    serviceWorkerCache: false,
    localStorage: false,
    sessionStorage: false,
  };

  results.serviceWorkerCache = await clearServiceWorkerCaches();

  try {
    // Clear transient localStorage, but keep auth/identity/game/app state.
    Object.keys(localStorage).forEach((key) => {
      if (!isPreservedKey(key)) {
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

  return results;
}

/**
 * Force refresh the app by clearing caches and reloading
 */
export async function forceRefresh() {
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
    storeCurrentVersion();

    // Bust ONLY the Service Worker/asset caches on a new version. Do NOT clear
    // localStorage here — it holds the Auth0 session and the user's profile
    // linkage, and wiping it on every deploy logged everyone out and forced the
    // name->login match / onboarding to redo on each build.
    clearServiceWorkerCaches().catch(console.error);
  }

  // Set up periodic update checks
  setInterval(() => {
    checkForUpdates().then((result) => {
      if (result.updateAvailable) {
        // Dispatch custom event for UI to handle
        window.dispatchEvent(
          new CustomEvent("appUpdateAvailable", {
            detail: result,
          }),
        );
      }
    });
  }, UPDATE_CHECK_INTERVAL);

}

const cacheManager = {
  APP_VERSION,
  BUILD_TIMESTAMP,
  getStoredVersion,
  storeCurrentVersion,
  hasAppUpdated,
  clearAllCaches,
  clearServiceWorkerCaches,
  forceRefresh,
  checkForUpdates,
  dismissUpdate,
  isUpdateDismissed,
  skipWaiting,
  getCacheStats,
  initCacheManager,
};

export default cacheManager;
