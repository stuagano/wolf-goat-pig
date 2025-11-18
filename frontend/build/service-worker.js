/**
 * Service Worker for Wolf-Goat-Pig PWA
 *
 * Provides offline capability for golf course use where cell signal is poor.
 * Uses Cache-First strategy for app shell and Network-First for API calls.
 */

const CACHE_NAME = 'wgp-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/js/bundle.js',
];

// Install event - cache app shell
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching app shell');
        // Don't fail install if some resources aren't available
        return cache.addAll(urlsToCache).catch((err) => {
          console.warn('[SW] Failed to cache some resources:', err);
          return Promise.resolve();
        });
      })
      .then(() => {
        console.log('[SW] Service worker installed');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Service worker activated');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // API calls - Network first, fallback to cache
  // Detect API calls: starts with /games, /sheet-integration, etc. OR different origin (backend server)
  const isApiCall = url.pathname.startsWith('/games') ||
                    url.pathname.startsWith('/sheet-integration') ||
                    url.pathname.startsWith('/simulation') ||
                    url.pathname.startsWith('/players') ||
                    url.origin !== self.location.origin;

  if (isApiCall) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone response to cache it
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // If network fails, try cache
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              console.log('[SW] Serving API from cache (offline):', url.pathname);
              return cachedResponse;
            }
            // Return offline response for API calls
            return new Response(
              JSON.stringify({ error: 'Offline', offline: true }),
              {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
              }
            );
          });
        })
    );
    return;
  }

  // Static assets - Cache first, fallback to network
  event.respondWith(
    caches.match(request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          console.log('[SW] Serving from cache:', url.pathname);
          return cachedResponse;
        }

        return fetch(request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone response to cache it
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });

            return response;
          })
          .catch((err) => {
            console.error('[SW] Fetch failed:', err);
            // Return offline page or fallback
            return new Response('Offline', { status: 503 });
          });
      })
  );
});

// Background sync for game state
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);

  if (event.tag === 'sync-game-state') {
    event.waitUntil(
      // Get pending game state from IndexedDB and sync to server
      syncGameState()
    );
  }
});

async function syncGameState() {
  console.log('[SW] Syncing game state...');

  try {
    // This would integrate with your offline game manager
    // For now, just log that sync happened
    console.log('[SW] Game state sync completed');

    // Notify clients that sync completed
    const clients = await self.clients.matchAll();
    clients.forEach((client) => {
      client.postMessage({
        type: 'SYNC_COMPLETE',
        timestamp: new Date().toISOString()
      });
    });
  } catch (error) {
    console.error('[SW] Game state sync failed:', error);
    throw error;
  }
}

// Handle messages from clients
self.addEventListener('message', (event) => {
  console.log('[SW] Received message:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

console.log('[SW] Service worker loaded');
