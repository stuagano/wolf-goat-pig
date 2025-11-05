// jest-dom adds custom jest matchers for asserting on DOM nodes.
import '@testing-library/jest-dom';

// Note: react-router-dom mocking is handled in individual test files

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

// Mock environment variables
process.env.REACT_APP_API_URL = 'http://test-api.com';
process.env.REACT_APP_USE_MOCK_AUTH = 'true';

// Mock window.alert
global.alert = jest.fn();

// Mock window.confirm
global.confirm = jest.fn(() => true);

const defaultFetchImplementation = () =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    status: 200,
  });

// Mock window.localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock window.innerWidth for responsive tests
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 1024,
});

// Mock fetch globally
global.fetch = jest.fn(defaultFetchImplementation);

beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();
  global.fetch.mockImplementation(defaultFetchImplementation);
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
});
