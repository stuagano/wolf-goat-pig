/**
 * Service Worker Registration
 *
 * Registers the service worker for offline capability.
 * This is especially useful on the golf course where cell signal is poor.
 */

const isLocalhost = Boolean(
  window.location.hostname === 'localhost' ||
  window.location.hostname === '[::1]' ||
  window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/)
);

export function register(config) {
  // Enable in both production AND development for local testing
  if ('serviceWorker' in navigator) {
    const publicUrl = new URL(process.env.PUBLIC_URL || '', window.location.href);
    if (publicUrl.origin !== window.location.origin && process.env.PUBLIC_URL) {
      return;
    }

    window.addEventListener('load', () => {
      const swUrl = `${process.env.PUBLIC_URL}/service-worker.js`;

      if (isLocalhost) {
        checkValidServiceWorker(swUrl, config);
        navigator.serviceWorker.ready.then(() => {
          console.log(
            '[PWA] This web app is being served cache-first by a service worker.'
          );
        });
      } else {
        registerValidSW(swUrl, config);
      }
    });
  }
}

function registerValidSW(swUrl, config) {
  navigator.serviceWorker
    .register(swUrl)
    .then((registration) => {
      console.log('[PWA] Service Worker registered:', registration);

      registration.onupdatefound = () => {
        const installingWorker = registration.installing;
        if (installingWorker == null) {
          return;
        }

        installingWorker.onstatechange = () => {
          if (installingWorker.state === 'installed') {
            if (navigator.serviceWorker.controller) {
              console.log('[PWA] New content available; please refresh.');

              if (config && config.onUpdate) {
                config.onUpdate(registration);
              }
            } else {
              console.log('[PWA] Content cached for offline use.');

              if (config && config.onSuccess) {
                config.onSuccess(registration);
              }
            }
          }
        };
      };
    })
    .catch((error) => {
      console.error('[PWA] Error during service worker registration:', error);
    });
}

function checkValidServiceWorker(swUrl, config) {
  fetch(swUrl, {
    headers: { 'Service-Worker': 'script' },
  })
    .then((response) => {
      const contentType = response.headers.get('content-type');
      if (
        response.status === 404 ||
        (contentType != null && contentType.indexOf('javascript') === -1)
      ) {
        navigator.serviceWorker.ready.then((registration) => {
          registration.unregister().then(() => {
            window.location.reload();
          });
        });
      } else {
        registerValidSW(swUrl, config);
      }
    })
    .catch(() => {
      console.log('[PWA] No internet connection found. App is running in offline mode.');
    });
}

export function unregister() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error(error.message);
      });
  }
}

/**
 * Request background sync when game state changes
 */
export function requestBackgroundSync(tag = 'sync-game-state') {
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    navigator.serviceWorker.ready.then((registration) => {
      return registration.sync.register(tag);
    }).then(() => {
      console.log('[PWA] Background sync requested:', tag);
    }).catch((error) => {
      console.log('[PWA] Background sync failed:', error);
    });
  }
}

/**
 * Check if the app is currently offline
 */
export function isOffline() {
  return !navigator.onLine;
}

/**
 * Listen for online/offline events
 */
export function setupConnectivityListeners(onOnline, onOffline) {
  window.addEventListener('online', () => {
    console.log('[PWA] Connection restored');
    if (onOnline) onOnline();
  });

  window.addEventListener('offline', () => {
    console.log('[PWA] Connection lost');
    if (onOffline) onOffline();
  });

  // Return cleanup function
  return () => {
    window.removeEventListener('online', onOnline);
    window.removeEventListener('offline', onOffline);
  };
}
