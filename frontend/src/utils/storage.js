/**
 * Shared localStorage utility for Wolf Goat Pig
 *
 * Provides a centralized, error-safe interface for localStorage operations
 * with automatic JSON serialization/deserialization and error handling.
 *
 * Features:
 * - Automatic JSON.stringify/parse
 * - Built-in error handling with console warnings
 * - Default values support
 * - Namespace support for feature isolation
 * - Type safety through JSDoc
 */

/**
 * Get a value from localStorage with automatic JSON parsing
 * @param {string} key - The localStorage key
 * @param {*} defaultValue - Default value if key doesn't exist or parsing fails
 * @returns {*} The parsed value or defaultValue
 */
export function get(key, defaultValue = null) {
  try {
    const item = localStorage.getItem(key);
    if (item === null) {
      return defaultValue;
    }
    return JSON.parse(item);
  } catch (error) {
    console.warn(`[Storage] Failed to get key "${key}":`, error);
    return defaultValue;
  }
}

/**
 * Set a value in localStorage with automatic JSON stringification
 * @param {string} key - The localStorage key
 * @param {*} value - The value to store (will be JSON.stringify'd)
 * @returns {boolean} True if successful, false otherwise
 */
export function set(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.warn(`[Storage] Failed to set key "${key}":`, error);
    return false;
  }
}

/**
 * Remove a value from localStorage
 * @param {string} key - The localStorage key to remove
 * @returns {boolean} True if successful, false otherwise
 */
export function remove(key) {
  try {
    localStorage.removeItem(key);
    return true;
  } catch (error) {
    console.warn(`[Storage] Failed to remove key "${key}":`, error);
    return false;
  }
}

/**
 * Clear all app-related keys from localStorage
 * Only removes keys with the app prefix (wgp-, wolf-goat-pig-)
 * @returns {boolean} True if successful, false otherwise
 */
export function clear() {
  try {
    const appPrefixes = ['wgp-', 'wolf-goat-pig-'];
    const keysToRemove = [];

    // Collect all app-related keys
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && appPrefixes.some(prefix => key.startsWith(prefix))) {
        keysToRemove.push(key);
      }
    }

    // Remove collected keys
    keysToRemove.forEach(key => localStorage.removeItem(key));

    console.log(`[Storage] Cleared ${keysToRemove.length} app-related keys`);
    return true;
  } catch (error) {
    console.warn('[Storage] Failed to clear app data:', error);
    return false;
  }
}

/**
 * Check if a key exists in localStorage
 * @param {string} key - The localStorage key
 * @returns {boolean} True if key exists
 */
export function has(key) {
  try {
    return localStorage.getItem(key) !== null;
  } catch (error) {
    console.warn(`[Storage] Failed to check key "${key}":`, error);
    return false;
  }
}

/**
 * Get all keys matching a prefix
 * @param {string} prefix - The prefix to filter keys
 * @returns {string[]} Array of matching keys
 */
export function getKeys(prefix = '') {
  try {
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith(prefix)) {
        keys.push(key);
      }
    }
    return keys;
  } catch (error) {
    console.warn(`[Storage] Failed to get keys with prefix "${prefix}":`, error);
    return [];
  }
}

/**
 * Default storage instance with all methods
 */
export const storage = {
  get,
  set,
  remove,
  clear,
  has,
  getKeys
};

/**
 * Create a namespaced storage instance
 * All operations will be prefixed with the namespace
 *
 * @param {string} namespace - The namespace prefix (e.g., 'game', 'profile', 'tutorial')
 * @returns {object} Namespaced storage interface
 *
 * @example
 * const gameStorage = createNamespacedStorage('game');
 * gameStorage.set('state', { score: 100 }); // stores as 'game_state'
 * gameStorage.get('state'); // retrieves from 'game_state'
 */
export function createNamespacedStorage(namespace) {
  const prefix = `${namespace}_`;

  return {
    /**
     * Get a namespaced value
     * @param {string} key - The key (will be prefixed)
     * @param {*} defaultValue - Default value if key doesn't exist
     * @returns {*} The parsed value or defaultValue
     */
    get: (key, defaultValue = null) => get(`${prefix}${key}`, defaultValue),

    /**
     * Set a namespaced value
     * @param {string} key - The key (will be prefixed)
     * @param {*} value - The value to store
     * @returns {boolean} True if successful
     */
    set: (key, value) => set(`${prefix}${key}`, value),

    /**
     * Remove a namespaced value
     * @param {string} key - The key (will be prefixed)
     * @returns {boolean} True if successful
     */
    remove: (key) => remove(`${prefix}${key}`),

    /**
     * Clear all keys in this namespace
     * @returns {boolean} True if successful
     */
    clear: () => {
      try {
        const keys = getKeys(prefix);
        keys.forEach(key => localStorage.removeItem(key));
        console.log(`[Storage:${namespace}] Cleared ${keys.length} keys`);
        return true;
      } catch (error) {
        console.warn(`[Storage:${namespace}] Failed to clear namespace:`, error);
        return false;
      }
    },

    /**
     * Check if a namespaced key exists
     * @param {string} key - The key (will be prefixed)
     * @returns {boolean} True if key exists
     */
    has: (key) => has(`${prefix}${key}`),

    /**
     * Get all keys in this namespace
     * @returns {string[]} Array of keys (without prefix)
     */
    getKeys: () => {
      const keys = getKeys(prefix);
      return keys.map(key => key.slice(prefix.length));
    },

    /**
     * Get the namespace prefix
     * @returns {string} The namespace
     */
    getNamespace: () => namespace
  };
}

export default storage;
