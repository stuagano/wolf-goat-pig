import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { clearAllCaches } from '../cacheManager';

// A Storage that, unlike the global setup mock, exposes stored keys via
// Object.keys (like real localStorage) — needed because cacheManager iterates
// Object.keys(localStorage).
function makeStorage(initial = {}) {
  const store = { ...initial };
  const api = {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => {
      store[k] = String(v);
    },
    removeItem: (k) => {
      delete store[k];
    },
    clear: () => {
      Object.keys(store).forEach((k) => delete store[k]);
    },
  };
  return new Proxy(store, {
    get(target, prop) {
      return prop in api ? api[prop] : target[prop];
    },
  });
}

describe('cacheManager.clearAllCaches — preserves auth & linkage', () => {
  let original;
  beforeEach(() => {
    original = global.localStorage;
  });
  afterEach(() => {
    global.localStorage = original;
  });

  // Regression: clearAllCaches used to wipe everything except the game-state
  // keys, which nuked the Auth0 session (stored in localStorage) and the
  // legacy-name onboarding choice on every deploy — forcing users to re-link.
  test('keeps Auth0 session, onboarding choice, game + app state; drops foreign keys', async () => {
    global.localStorage = makeStorage({
      '@@auth0spajs@@::abc::https://api::openid profile email': 'session-token',
      legacy_name_skipped: 'true',
      wgp_current_game: 'game-123',
      'wgp-sync:game-state': '{}',
      'wolf-goat-pig-game-state': '{}',
      some_third_party_cache: 'junk',
    });

    await clearAllCaches();

    // Preserved
    expect(
      localStorage.getItem('@@auth0spajs@@::abc::https://api::openid profile email'),
    ).toBe('session-token');
    expect(localStorage.getItem('legacy_name_skipped')).toBe('true');
    expect(localStorage.getItem('wgp_current_game')).toBe('game-123');
    expect(localStorage.getItem('wgp-sync:game-state')).toBe('{}');
    expect(localStorage.getItem('wolf-goat-pig-game-state')).toBe('{}');

    // Cleared
    expect(localStorage.getItem('some_third_party_cache')).toBeNull();
  });
});

describe('cacheManager.initCacheManager — a new build does not log users out', () => {
  let originalLS;
  let originalFetch;
  beforeEach(() => {
    originalLS = global.localStorage;
    originalFetch = global.fetch;
    vi.useFakeTimers();
  });
  afterEach(() => {
    global.localStorage = originalLS;
    global.fetch = originalFetch;
    vi.useRealTimers();
  });

  // The core fix: the per-deploy auto path must bust SW caches only, never
  // localStorage, so the Auth0 session and profile linkage survive every build.
  test('version bump keeps Auth0 session + onboarding choice, only updates version', async () => {
    vi.resetModules();
    global.localStorage = makeStorage({
      wgp_app_version: '0.0.1-old',
      '@@auth0spajs@@::x': 'session-token',
      legacy_name_skipped: 'true',
    });
    global.fetch = vi.fn(async () => ({
      ok: true,
      json: async () => ({ version: '9.9.9-new' }),
    }));

    const mod = await import('../cacheManager');
    await mod.initCacheManager();

    expect(localStorage.getItem('@@auth0spajs@@::x')).toBe('session-token');
    expect(localStorage.getItem('legacy_name_skipped')).toBe('true');
    expect(localStorage.getItem('wgp_app_version')).toBe('9.9.9-new');
  });
});
