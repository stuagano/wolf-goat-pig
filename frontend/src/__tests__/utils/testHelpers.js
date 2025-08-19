/**
 * Test utilities and helpers for Wolf Goat Pig testing
 * 
 * Provides common testing utilities, mock factories, and helper functions
 * to reduce test boilerplate and ensure consistent test patterns.
 */

import { render } from '@testing-library/react';
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context/GameProvider';
import { TutorialContext } from '../../context/TutorialContext';

// Common test wrapper that provides all necessary contexts
export const TestWrapper = ({ 
  children, 
  gameState = null,
  tutorialState = { isActive: false, currentModule: null },
  theme = 'default'
}) => (
  <ThemeProvider theme={theme}>
    <GameProvider initialState={gameState ? { gameState } : undefined}>
      <TutorialContext.Provider value={tutorialState}>
        {children}
      </TutorialContext.Provider>
    </GameProvider>
  </ThemeProvider>
);

// Render component with full context wrapper
export const renderWithContext = (ui, options = {}) => {
  const {
    gameState,
    tutorialState,
    theme,
    ...renderOptions
  } = options;

  return render(ui, {
    wrapper: ({ children }) => (
      <TestWrapper 
        gameState={gameState}
        tutorialState={tutorialState}
        theme={theme}
      >
        {children}
      </TestWrapper>
    ),
    ...renderOptions
  });
};

// Mock fetch with customizable responses
export const mockFetch = (responses = {}) => {
  const fetchMock = jest.fn();
  
  // Default successful response
  fetchMock.mockImplementation((url, options) => {
    const method = options?.method || 'GET';
    const key = `${method} ${url}`;
    
    if (responses[key]) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => responses[key],
        text: async () => JSON.stringify(responses[key])
      });
    }
    
    // Default response
    return Promise.resolve({
      ok: true,
      status: 200,
      json: async () => ({}),
      text: async () => '{}'
    });
  });
  
  global.fetch = fetchMock;
  return fetchMock;
};

// Mock fetch that returns errors
export const mockFetchError = (error = new Error('Network error')) => {
  const fetchMock = jest.fn().mockRejectedValue(error);
  global.fetch = fetchMock;
  return fetchMock;
};

// Mock fetch with specific HTTP errors
export const mockFetchHttpError = (status = 500, statusText = 'Internal Server Error') => {
  const fetchMock = jest.fn().mockResolvedValue({
    ok: false,
    status,
    statusText,
    json: async () => ({ error: statusText }),
    text: async () => `Error: ${statusText}`
  });
  
  global.fetch = fetchMock;
  return fetchMock;
};

// Mock localStorage with full API
export const mockLocalStorage = () => {
  const store = {};
  
  const localStorageMock = {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
    key: jest.fn((index) => Object.keys(store)[index] || null),
    get length() {
      return Object.keys(store).length;
    }
  };
  
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
    writable: true
  });
  
  return localStorageMock;
};

// Mock sessionStorage
export const mockSessionStorage = () => {
  const store = {};
  
  const sessionStorageMock = {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
    key: jest.fn((index) => Object.keys(store)[index] || null),
    get length() {
      return Object.keys(store).length;
    }
  };
  
  Object.defineProperty(window, 'sessionStorage', {
    value: sessionStorageMock,
    writable: true
  });
  
  return sessionStorageMock;
};

// Mock window.confirm and window.alert
export const mockWindowDialogs = () => {
  const confirmMock = jest.fn(() => true);
  const alertMock = jest.fn();
  const promptMock = jest.fn(() => 'test input');
  
  global.confirm = confirmMock;
  global.alert = alertMock;
  global.prompt = promptMock;
  
  return { confirmMock, alertMock, promptMock };
};

// Mock window.location methods
export const mockWindowLocation = (url = 'http://localhost:3000/') => {
  const location = new URL(url);
  
  const locationMock = {
    href: location.href,
    protocol: location.protocol,
    host: location.host,
    hostname: location.hostname,
    port: location.port,
    pathname: location.pathname,
    search: location.search,
    hash: location.hash,
    origin: location.origin,
    assign: jest.fn(),
    replace: jest.fn(),
    reload: jest.fn(),
    toString: () => location.href
  };
  
  Object.defineProperty(window, 'location', {
    value: locationMock,
    writable: true
  });
  
  return locationMock;
};

// Mock ResizeObserver
export const mockResizeObserver = () => {
  const ResizeObserverMock = jest.fn().mockImplementation((callback) => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn()
  }));
  
  global.ResizeObserver = ResizeObserverMock;
  return ResizeObserverMock;
};

// Mock IntersectionObserver
export const mockIntersectionObserver = () => {
  const IntersectionObserverMock = jest.fn().mockImplementation((callback) => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
    root: null,
    rootMargin: '',
    thresholds: []
  }));
  
  global.IntersectionObserver = IntersectionObserverMock;
  return IntersectionObserverMock;
};

// Mock URL and Blob for file operations
export const mockFileOperations = () => {
  const URLMock = {
    createObjectURL: jest.fn(() => 'mock-object-url'),
    revokeObjectURL: jest.fn()
  };
  
  const BlobMock = jest.fn().mockImplementation((content, options) => ({
    size: content[0].length,
    type: options?.type || 'application/octet-stream',
    slice: jest.fn(),
    stream: jest.fn(),
    text: jest.fn().mockResolvedValue(content[0]),
    arrayBuffer: jest.fn()
  }));
  
  global.URL = URLMock;
  global.Blob = BlobMock;
  
  const linkMock = {
    href: '',
    download: '',
    click: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn()
  };
  
  const originalCreateElement = document.createElement;
  document.createElement = jest.fn().mockImplementation((tagName) => {
    if (tagName === 'a') {
      return linkMock;
    }
    return originalCreateElement.call(document, tagName);
  });
  
  return { URLMock, BlobMock, linkMock };
};

// Mock WebSocket
export const mockWebSocket = () => {
  const WebSocketMock = jest.fn().mockImplementation((url) => {
    const ws = {
      url,
      readyState: WebSocket.OPEN,
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
      
      // Helper methods for testing
      simulateOpen: () => {
        ws.readyState = WebSocket.OPEN;
        if (ws.onopen) ws.onopen();
      },
      
      simulateMessage: (data) => {
        if (ws.onmessage) {
          ws.onmessage({ data: JSON.stringify(data) });
        }
      },
      
      simulateError: (error) => {
        if (ws.onerror) ws.onerror({ error });
      },
      
      simulateClose: () => {
        ws.readyState = WebSocket.CLOSED;
        if (ws.onclose) ws.onclose();
      }
    };
    
    return ws;
  });
  
  global.WebSocket = WebSocketMock;
  WebSocketMock.CONNECTING = 0;
  WebSocketMock.OPEN = 1;
  WebSocketMock.CLOSING = 2;
  WebSocketMock.CLOSED = 3;
  
  return WebSocketMock;
};

// Async test utilities
export const asyncUtils = {
  // Wait for a condition to be true
  waitForCondition: async (condition, timeout = 5000, interval = 100) => {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (await condition()) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, interval));
    }
    
    throw new Error(`Condition not met within ${timeout}ms`);
  },
  
  // Wait for element to appear
  waitForElement: async (selector, timeout = 5000) => {
    return asyncUtils.waitForCondition(
      () => document.querySelector(selector) !== null,
      timeout
    );
  },
  
  // Wait for specific timeout
  delay: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
  
  // Flush all pending promises
  flushPromises: () => new Promise(resolve => setImmediate(resolve))
};

// Performance testing utilities
export const performanceUtils = {
  // Measure rendering time
  measureRenderTime: async (renderFn) => {
    const start = performance.now();
    const result = await renderFn();
    const end = performance.now();
    
    return {
      result,
      duration: end - start
    };
  },
  
  // Run multiple iterations and get average
  benchmarkRender: async (renderFn, iterations = 10) => {
    const times = [];
    
    for (let i = 0; i < iterations; i++) {
      const { duration } = await performanceUtils.measureRenderTime(renderFn);
      times.push(duration);
    }
    
    return {
      average: times.reduce((sum, time) => sum + time, 0) / times.length,
      min: Math.min(...times),
      max: Math.max(...times),
      median: times.sort((a, b) => a - b)[Math.floor(times.length / 2)]
    };
  }
};

// Form testing utilities
export const formUtils = {
  // Fill form with data
  fillForm: async (form, data, user) => {
    for (const [name, value] of Object.entries(data)) {
      const field = form.querySelector(`[name="${name}"]`);
      if (field) {
        if (field.type === 'checkbox') {
          if (value && !field.checked) {
            await user.click(field);
          } else if (!value && field.checked) {
            await user.click(field);
          }
        } else if (field.type === 'select-one') {
          await user.selectOptions(field, value);
        } else {
          await user.clear(field);
          if (value) {
            await user.type(field, value.toString());
          }
        }
      }
    }
  },
  
  // Validate form errors
  expectFormErrors: (form, expectedErrors) => {
    Object.entries(expectedErrors).forEach(([fieldName, expectedError]) => {
      const errorElement = form.querySelector(`[data-testid="${fieldName}-error"]`) ||
                          form.querySelector(`#${fieldName}-error`) ||
                          form.querySelector(`.${fieldName}-error`);
      
      if (expectedError) {
        expect(errorElement).toBeInTheDocument();
        expect(errorElement).toHaveTextContent(expectedError);
      } else {
        expect(errorElement).not.toBeInTheDocument();
      }
    });
  }
};

// Accessibility testing helpers
export const a11yUtils = {
  // Check if element has proper ARIA labels
  expectProperLabels: (element) => {
    const inputs = element.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      const hasLabel = input.labels?.length > 0 ||
                     input.getAttribute('aria-label') ||
                     input.getAttribute('aria-labelledby');
      expect(hasLabel).toBeTruthy();
    });
  },
  
  // Check keyboard navigation
  expectKeyboardNavigation: (element) => {
    const interactiveElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    interactiveElements.forEach(el => {
      expect(el).not.toHaveAttribute('tabindex', '-1');
    });
  },
  
  // Check color contrast (simplified)
  expectSufficientContrast: (element) => {
    const styles = window.getComputedStyle(element);
    const backgroundColor = styles.backgroundColor;
    const color = styles.color;
    
    // This is a simplified check - in real testing you'd use a proper contrast checker
    expect(backgroundColor).not.toBe(color);
  }
};

// Animation testing utilities
export const animationUtils = {
  // Mock CSS transitions
  mockTransitions: () => {
    const originalGetComputedStyle = window.getComputedStyle;
    window.getComputedStyle = jest.fn().mockImplementation((element) => {
      const styles = originalGetComputedStyle(element);
      return {
        ...styles,
        transitionDuration: '0ms',
        animationDuration: '0ms',
        animationDelay: '0ms',
        transitionDelay: '0ms'
      };
    });
    
    return originalGetComputedStyle;
  },
  
  // Wait for CSS transition to complete
  waitForTransition: async (element, property = 'opacity') => {
    return new Promise((resolve) => {
      const handler = (event) => {
        if (event.propertyName === property) {
          element.removeEventListener('transitionend', handler);
          resolve();
        }
      };
      
      element.addEventListener('transitionend', handler);
    });
  }
};

// Error boundary testing
export class TestErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  render() {
    if (this.state.hasError) {
      return <div data-testid="error-boundary">Error caught: {this.state.error?.message}</div>;
    }
    
    return this.props.children;
  }
}

// Custom matchers for Jest
export const customMatchers = {
  // Check if element is visible (not just in DOM)
  toBeVisible: (received) => {
    const pass = received && 
                 received.offsetParent !== null && 
                 window.getComputedStyle(received).visibility !== 'hidden' &&
                 window.getComputedStyle(received).display !== 'none';
    
    return {
      message: () => `expected element to ${pass ? 'not ' : ''}be visible`,
      pass
    };
  },
  
  // Check if element has specific CSS class
  toHaveClass: (received, className) => {
    const pass = received && received.classList.contains(className);
    
    return {
      message: () => `expected element to ${pass ? 'not ' : ''}have class "${className}"`,
      pass
    };
  }
};

// Setup function for common test environment
export const setupTestEnvironment = () => {
  // Mock common browser APIs
  mockLocalStorage();
  mockWindowDialogs();
  mockResizeObserver();
  mockIntersectionObserver();
  
  // Set up common global mocks
  global.matchMedia = jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
  
  // Mock requestAnimationFrame
  global.requestAnimationFrame = jest.fn().mockImplementation((cb) => {
    setTimeout(cb, 0);
  });
  
  global.cancelAnimationFrame = jest.fn();
  
  // Set up console suppression for expected warnings
  const originalError = console.error;
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
  
  return () => {
    console.error = originalError;
  };
};

export default {
  TestWrapper,
  renderWithContext,
  mockFetch,
  mockFetchError,
  mockFetchHttpError,
  mockLocalStorage,
  mockSessionStorage,
  mockWindowDialogs,
  mockWindowLocation,
  mockResizeObserver,
  mockIntersectionObserver,
  mockFileOperations,
  mockWebSocket,
  asyncUtils,
  performanceUtils,
  formUtils,
  a11yUtils,
  animationUtils,
  TestErrorBoundary,
  customMatchers,
  setupTestEnvironment
};