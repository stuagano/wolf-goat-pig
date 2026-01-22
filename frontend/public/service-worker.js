/**
 * Service Worker for Wolf Goat Pig PWA
 * Provides offline capability for golf course use where cell signal is poor
 *
 * Cache busting strategy:
 * - Version-based cache naming
 * - Automatic cleanup of old caches
 * - Network-first for version.json to detect updates
 * - Stale-while-revalidate for static assets
 */

// IMPORTANT: Update this version with each release to trigger cache refresh
const SW_VERSION = '0.1.1.22025';
const CACHE_NAME = `wgp-cache-v${SW_VERSION}`;

const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json'
];

// Files that should always be fetched from network first
const NETWORK_FIRST_PATTERNS = [
  '/version.json',
  '/api/',
];

// Files that should never be cached
const NO_CACHE_PATTERNS = [
  '/sockjs-node/',
  'hot-update',
];

/**
 * Check if URL matches any pattern in the list
 */
function matchesPattern(url, patterns) {
  return patterns.some(pattern => url.includes(pattern));
}

// Install event - cache core resources
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker v' + SW_VERSION);
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching app shell');
        return cache.addAll(urlsToCache).catch((err) => {
          console.warn('[SW] Some resources failed to cache:', err);
          // Don't fail installation if some resources can't be cached
          return Promise.resolve();
        });
      })
  );
  // Activate immediately
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker v' + SW_VERSION);
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Delete any cache that doesn't match current version
          if (cacheName.startsWith('wgp-cache-') && cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Take control immediately
  return self.clients.claim();
});

// Fetch event - intelligent caching strategy
self.addEventListener('fetch', (event) => {
  const url = event.request.url;

  // Skip cross-origin requests
  if (!url.startsWith(self.location.origin)) {
    return;
  }

  // Skip requests that shouldn't be cached
  if (matchesPattern(url, NO_CACHE_PATTERNS)) {
    return;
  }

  // Network-first strategy for version checks and API calls
  if (matchesPattern(url, NETWORK_FIRST_PATTERNS)) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  // Stale-while-revalidate for static assets
  if (url.includes('/static/')) {
    event.respondWith(staleWhileRevalidate(event.request));
    return;
  }

  // Cache-first with network fallback for everything else
  event.respondWith(cacheFirst(event.request));
});

/**
 * Cache-first strategy
 * Try cache, fallback to network
 */
async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) {
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok && response.type === 'basic' && request.method === 'GET') {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    // For navigation, return cached index.html
    if (request.mode === 'navigate') {
      const cached = await caches.match('/index.html');
      if (cached) return cached;
    }
    return new Response('Offline', { status: 503 });
  }
}

/**
 * Network-first strategy
 * Try network, fallback to cache
 */
async function networkFirst(request) {
  try {
    const response = await fetch(request, {
      cache: 'no-store',
    });
    if (response.ok && response.type === 'basic' && request.method === 'GET') {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response('Network error', { status: 408 });
  }
}

/**
 * Stale-while-revalidate strategy
 * Return cached version immediately, update cache in background
 */
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  // Fetch fresh version in background
  const fetchPromise = fetch(request).then((response) => {
    if (response.ok && response.type === 'basic' && request.method === 'GET') {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => null);

  // Return cached version immediately if available
  if (cached) {
    return cached;
  }

  // Otherwise wait for network
  const response = await fetchPromise;
  if (response) return response;

  return new Response('Asset not available', { status: 404 });
}

// Background sync event
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  if (event.tag === 'sync-game-state') {
    event.waitUntil(syncGameState());
  }
});

// Sync game state function
async function syncGameState() {
  try {
    console.log('[SW] Syncing game state...');
    // This would typically POST any pending game data to the server
    return Promise.resolve();
  } catch (error) {
    console.error('[SW] Sync failed:', error);
    return Promise.reject(error);
  }
}

// Message event - handle messages from clients
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      }).then(() => {
        // Notify clients that cache was cleared
        self.clients.matchAll().then((clients) => {
          clients.forEach((client) => {
            client.postMessage({ type: 'CACHE_CLEARED' });
          });
        });
      })
    );
  }

  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: SW_VERSION });
  }
});
