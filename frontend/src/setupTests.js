/* global globalThis */
// jest-dom adds custom jest matchers for asserting on DOM nodes.
import '@testing-library/jest-dom';

// Note: react-router-dom mocking is handled in individual test files

// Polyfill TextEncoder/TextDecoder for Auth0 SDK (required in JSDOM environment)
import { TextEncoder, TextDecoder } from 'util';
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// Mock crypto.getRandomValues for uuid in tests
if (typeof globalThis.crypto === 'undefined') {
  globalThis.crypto = {
    getRandomValues: (arr) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }
  };
}

// Mock environment variables for Vitest
// Use vi.stubEnv for Vite-style env vars
vi.stubEnv('VITE_API_URL', 'http://test-api.com');
vi.stubEnv('VITE_USE_MOCK_AUTH', 'true');

// Mock window.alert
global.alert = vi.fn();

// Provide jest compatibility shim
global.jest = vi;

// Mock window.confirm
global.confirm = vi.fn(() => true);

const defaultFetchImplementation = () =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    status: 200,
  });

// Mock window.localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();
global.localStorage = localStorageMock;

// Mock window.innerWidth for responsive tests
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 1024,
});

// Mock fetch globally
global.fetch = vi.fn(defaultFetchImplementation);

beforeEach(() => {
  // Clear all mocks before each test
  vi.clearAllMocks();
  global.fetch.mockImplementation(defaultFetchImplementation);
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
});
