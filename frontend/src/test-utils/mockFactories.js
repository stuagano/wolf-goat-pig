/**
 * Mock Factory Functions for Wolf Goat Pig Testing
 *
 * Provides reusable factory functions to create common test mocks
 * with sensible defaults and customization options.
 *
 * Usage:
 *   const theme = createMockTheme();
 *   const auth = createMockAuthContext({ isAuthenticated: true });
 *   const players = createMockPlayers(4);
 */

// ============================================================================
// Theme Mocks
// ============================================================================

/**
 * Create a mock theme object
 * @param {Object} overrides - Optional theme overrides
 * @returns {Object} Mock theme with colors, spacing, etc.
 */
export const createMockTheme = (overrides = {}) => ({
  colors: {
    primary: '#2196F3',
    secondary: '#757575',
    success: '#4CAF50',
    error: '#f44336',
    warning: '#ff9800',
    info: '#2196f3',
    accent: '#FFD700',
    textPrimary: '#333',
    textSecondary: '#666',
    background: '#ffffff',
    backgroundSecondary: '#f5f5f5',
    backgroundTertiary: '#e0e0e0',
    border: '#e0e0e0',
    shadow: 'rgba(0, 0, 0, 0.1)',
    ...overrides.colors
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    ...overrides.spacing
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    ...overrides.borderRadius
  },
  typography: {
    fontSize: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 24
    },
    fontWeight: {
      light: 300,
      regular: 400,
      medium: 500,
      bold: 700
    },
    ...overrides.typography
  },
  shadows: {
    sm: '0 1px 3px rgba(0, 0, 0, 0.1)',
    md: '0 2px 6px rgba(0, 0, 0, 0.15)',
    lg: '0 4px 12px rgba(0, 0, 0, 0.2)',
    ...overrides.shadows
  },
  ...overrides
});

/**
 * Mock the useTheme hook
 * @param {Object} themeOverrides - Optional theme overrides
 * @returns {Function} Mock hook function
 */
export const createMockUseTheme = (themeOverrides = {}) => {
  return () => createMockTheme(themeOverrides);
};

// ============================================================================
// Authentication Mocks
// ============================================================================

/**
 * Create a mock authentication context
 * @param {Object} config - Auth configuration
 * @param {boolean} config.isAuthenticated - Whether user is authenticated
 * @param {Object} config.user - User object
 * @param {Function} config.login - Login function
 * @param {Function} config.logout - Logout function
 * @returns {Object} Mock auth context
 */
export const createMockAuthContext = ({
  isAuthenticated = false,
  user = null,
  login = jest.fn(),
  logout = jest.fn(),
  loading = false,
  error = null
} = {}) => ({
  isAuthenticated,
  user: user || (isAuthenticated ? createMockUser() : null),
  login,
  logout,
  loading,
  error,
  checkAuth: jest.fn()
});

/**
 * Create a mock user object
 * @param {Object} overrides - User property overrides
 * @returns {Object} Mock user
 */
export const createMockUser = (overrides = {}) => ({
  id: 'user_123',
  email: 'test@example.com',
  name: 'Test User',
  avatar_url: 'https://example.com/avatar.jpg',
  created_at: '2024-01-01T00:00:00Z',
  ...overrides
});

// ============================================================================
// Game State Mocks
// ============================================================================

/**
 * Create mock players
 * @param {number} count - Number of players to create
 * @param {Object} baseOverrides - Base overrides applied to all players
 * @returns {Array} Array of mock players
 */
export const createMockPlayers = (count = 4, baseOverrides = {}) => {
  const names = ['Alice', 'Bob', 'Carol', 'David', 'Eve', 'Frank'];
  const handicaps = [8, 12, 15, 18, 20, 25];

  return Array.from({ length: count }, (_, i) => ({
    id: `player_${i + 1}`,
    name: names[i] || `Player ${i + 1}`,
    handicap: handicaps[i] || 15,
    is_human: i === 0, // First player is human by default
    avatar_url: i === 0 ? 'https://example.com/avatar.jpg' : null,
    current_score: 0,
    shots_taken: 0,
    distance_to_pin: 385,
    lie_type: 'tee',
    is_captain: false,
    team_id: null,
    hole_scores: [],
    ...baseOverrides
  }));
};

/**
 * Create a mock game state
 * @param {string} scenario - Scenario type: 'initial', 'mid_game', 'final_hole', 'completed'
 * @param {Object} overrides - Property overrides
 * @returns {Object} Mock game state
 */
export const createMockGameState = (scenario = 'initial', overrides = {}) => {
  const scenarios = {
    initial: {
      game_id: 'game_001',
      status: 'active',
      created_at: new Date().toISOString(),
      current_hole: 1,
      current_hole_par: 4,
      hole_difficulty: 3.2,
      course_id: 'test_course',
      players: createMockPlayers(4),
      teams: {
        type: 'pending',
        formation: null,
        captain: null
      },
      current_wager: 2.0,
      is_doubled: false,
      line_of_scrimmage_passed: false,
      betting: {
        currentPot: 8.0,
        opportunities: [],
        history: []
      },
      weather: {
        condition: 'clear',
        wind_speed: 5,
        wind_direction: 'NE',
        temperature: 72
      }
    },
    mid_game: {
      game_id: 'game_002',
      status: 'active',
      created_at: new Date().toISOString(),
      current_hole: 8,
      current_hole_par: 4,
      hole_difficulty: 3.8,
      course_id: 'test_course',
      players: createMockPlayers(4, {
        current_score: 32,
        shots_taken: 1,
        distance_to_pin: 150,
        lie_type: 'fairway',
        hole_scores: [4, 3, 5, 4, 6, 3, 4]
      }),
      teams: {
        type: 'partnerships',
        formation: {
          team_1: ['player_1', 'player_2'],
          team_2: ['player_3', 'player_4']
        },
        captain: 'player_1'
      },
      current_wager: 4.0,
      is_doubled: true,
      line_of_scrimmage_passed: true,
      betting: {
        currentPot: 48.50,
        opportunities: [],
        history: []
      }
    },
    final_hole: {
      game_id: 'game_003',
      status: 'active',
      current_hole: 18,
      current_hole_par: 5,
      hole_difficulty: 4.5,
      course_id: 'test_course',
      players: createMockPlayers(4, {
        current_score: 74,
        shots_taken: 2
      }),
      teams: {
        type: 'head_to_head',
        captain: 'player_1'
      },
      current_wager: 8.0,
      betting: {
        currentPot: 156.75,
        opportunities: [],
        history: []
      }
    },
    completed: {
      game_id: 'game_004',
      status: 'completed',
      completed_at: new Date().toISOString(),
      current_hole: 18,
      final_results: {
        winner: 'player_1',
        final_scores: [
          { player_id: 'player_1', total_score: 74, earnings: 45.50 },
          { player_id: 'player_2', total_score: 89, earnings: -15.25 }
        ]
      }
    }
  };

  return {
    ...scenarios[scenario],
    ...overrides
  };
};

/**
 * Create mock hole history
 * @param {number} holesCompleted - Number of completed holes
 * @param {Array} playerIds - Array of player IDs
 * @returns {Array} Array of hole history objects
 */
export const createMockHoleHistory = (holesCompleted = 2, playerIds = ['player_1', 'player_2', 'player_3', 'player_4']) => {
  return Array.from({ length: holesCompleted }, (_, i) => ({
    hole: i + 1,
    points_delta: Object.fromEntries(
      playerIds.map(id => [id, Math.floor(Math.random() * 5) - 2])
    ),
    gross_scores: Object.fromEntries(
      playerIds.map(id => [id, Math.floor(Math.random() * 3) + 4])
    )
  }));
};

/**
 * Create mock course holes
 * @param {number} numHoles - Number of holes (default 18)
 * @returns {Array} Array of course hole objects
 */
export const createMockCourseHoles = (numHoles = 18) => {
  const parSequence = [4, 5, 3, 4, 4, 5, 4, 3, 4, 4, 3, 5, 4, 4, 3, 5, 4, 4];

  return Array.from({ length: numHoles }, (_, i) => ({
    hole: i + 1,
    par: parSequence[i % 18],
    handicap: i + 1,
    yards: 350 + (i * 15),
    description: `Hole ${i + 1} description`
  }));
};

/**
 * Create mock stroke allocation
 * @param {Array} playerIds - Array of player IDs
 * @param {number} numHoles - Number of holes
 * @returns {Object} Stroke allocation map
 */
export const createMockStrokeAllocation = (playerIds, numHoles = 18) => {
  return Object.fromEntries(
    playerIds.map(id => [
      id,
      Object.fromEntries(
        Array.from({ length: numHoles }, (_, i) => [i + 1, Math.random() > 0.5 ? 1 : 0])
      )
    ])
  );
};

// ============================================================================
// Betting and Odds Mocks
// ============================================================================

/**
 * Create mock odds response
 * @param {Object} overrides - Property overrides
 * @returns {Object} Mock odds calculation response
 */
export const createMockOddsResponse = (overrides = {}) => ({
  timestamp: new Date().toISOString(),
  calculation_time_ms: 145.2,
  confidence_level: 0.87,
  monte_carlo_used: true,
  player_probabilities: {
    player_1: {
      name: 'Alice',
      win_probability: 0.65,
      expected_score: 4.2,
      confidence_interval: [0.58, 0.72],
      risk_factors: ['weather', 'lie']
    },
    player_2: {
      name: 'Bob',
      win_probability: 0.35,
      expected_score: 4.8,
      confidence_interval: [0.28, 0.42],
      risk_factors: ['distance', 'lie']
    }
  },
  team_probabilities: {
    team_1: 0.58,
    team_2: 0.42
  },
  optimal_strategy: 'conservative_play',
  betting_scenarios: [
    createMockBettingScenario('double_down'),
    createMockBettingScenario('side_bet')
  ],
  risk_assessment: {
    volatility: 0.23,
    weather_factor: 1.0,
    course_difficulty: 3.5,
    player_fatigue: 0.15
  },
  educational_insights: [
    'Current hole difficulty suggests moderate challenge',
    'Team partnerships favor balanced risk-taking approach'
  ],
  simulation_details: {
    num_simulations_run: 5000,
    convergence_achieved: true,
    monte_carlo_variance: 0.012
  },
  ...overrides
});

/**
 * Create a mock betting scenario
 * @param {string} type - Scenario type
 * @param {Object} overrides - Property overrides
 * @returns {Object} Mock betting scenario
 */
export const createMockBettingScenario = (type = 'double_down', overrides = {}) => {
  const scenarios = {
    double_down: {
      scenario_type: 'double_down',
      win_probability: 0.62,
      expected_value: 1.25,
      risk_level: 'medium',
      reasoning: 'Favorable position with good lie and manageable distance',
      confidence_interval: [0.55, 0.69],
      payout_matrix: {
        win: 4.00,
        loss: -2.00,
        push: 0.00
      },
      recommendation: 'offer'
    },
    side_bet: {
      scenario_type: 'side_bet',
      win_probability: 0.45,
      expected_value: -0.15,
      risk_level: 'high',
      reasoning: 'Challenging lie with increased distance',
      confidence_interval: [0.38, 0.52],
      payout_matrix: {
        win: 2.50,
        loss: -1.50
      },
      recommendation: 'decline'
    },
    press_bet: {
      scenario_type: 'press_bet',
      win_probability: 0.55,
      expected_value: 0.85,
      risk_level: 'medium',
      reasoning: 'Opportunity to press after losing streak',
      confidence_interval: [0.48, 0.62],
      payout_matrix: {
        win: 6.00,
        loss: -3.00
      },
      recommendation: 'consider'
    }
  };

  return {
    ...(scenarios[type] || scenarios.double_down),
    ...overrides
  };
};

// ============================================================================
// UI Component Mocks
// ============================================================================

/**
 * Create mock UI components for testing
 * @returns {Object} Mock UI component implementations
 */
export const createMockUIComponents = () => ({
  Card: jest.fn(({ children, className, style }) => (
    <div data-testid="card" className={className} style={style}>
      {children}
    </div>
  )),
  Button: jest.fn(({ children, onClick, variant, disabled, style }) => (
    <button
      onClick={onClick}
      data-variant={variant}
      disabled={disabled}
      style={style}
      data-testid="button"
    >
      {children}
    </button>
  )),
  Input: jest.fn(({ type, value, onChange, placeholder, disabled }) => (
    <input
      type={type}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      data-testid="input"
    />
  )),
  Modal: jest.fn(({ isOpen, onClose, title, children }) =>
    isOpen ? (
      <div data-testid="modal">
        <div data-testid="modal-title">{title}</div>
        <div data-testid="modal-content">{children}</div>
        <button onClick={onClose} data-testid="modal-close">
          Close
        </button>
      </div>
    ) : null
  )
});

// ============================================================================
// Event and Handler Mocks
// ============================================================================

/**
 * Create a set of common event handler mocks
 * @returns {Object} Mock event handlers
 */
export const createMockEventHandlers = () => ({
  onClick: jest.fn(),
  onChange: jest.fn(),
  onSubmit: jest.fn(),
  onClose: jest.fn(),
  onSave: jest.fn(),
  onCancel: jest.fn(),
  onEdit: jest.fn(),
  onDelete: jest.fn(),
  onBettingAction: jest.fn(),
  onEditHole: jest.fn(),
  onPlayerNameChange: jest.fn()
});

/**
 * Create a mock DOM event
 * @param {string} type - Event type
 * @param {Object} properties - Event properties
 * @returns {Object} Mock event object
 */
export const createMockEvent = (type = 'click', properties = {}) => ({
  type,
  preventDefault: jest.fn(),
  stopPropagation: jest.fn(),
  target: {
    value: '',
    name: '',
    checked: false,
    ...properties.target
  },
  currentTarget: properties.currentTarget || properties.target,
  ...properties
});

// ============================================================================
// API Response Mocks
// ============================================================================

/**
 * Create a successful fetch response
 * @param {*} data - Response data
 * @param {Object} options - Response options
 * @returns {Promise} Mock fetch response
 */
export const createMockFetchResponse = (data, options = {}) => {
  return Promise.resolve({
    ok: true,
    status: 200,
    statusText: 'OK',
    json: async () => data,
    text: async () => JSON.stringify(data),
    headers: new Headers(options.headers || {}),
    ...options
  });
};

/**
 * Create a fetch error response
 * @param {number} status - HTTP status code
 * @param {string} message - Error message
 * @returns {Promise} Mock fetch error response
 */
export const createMockFetchError = (status = 500, message = 'Internal Server Error') => {
  return Promise.resolve({
    ok: false,
    status,
    statusText: message,
    json: async () => ({ error: message }),
    text: async () => message
  });
};

/**
 * Create a network error (rejected promise)
 * @param {string} message - Error message
 * @returns {Promise} Rejected promise
 */
export const createMockNetworkError = (message = 'Network error') => {
  return Promise.reject(new Error(message));
};

// ============================================================================
// Tutorial Context Mocks
// ============================================================================

/**
 * Create a mock tutorial context
 * @param {Object} overrides - Context overrides
 * @returns {Object} Mock tutorial context
 */
export const createMockTutorialContext = (overrides = {}) => ({
  isActive: false,
  currentModule: null,
  currentStep: 0,
  startTutorial: jest.fn(),
  nextStep: jest.fn(),
  prevStep: jest.fn(),
  completeTutorial: jest.fn(),
  skipTutorial: jest.fn(),
  ...overrides
});

// ============================================================================
// Utility Exports
// ============================================================================

const mockFactories = {
  // Theme
  createMockTheme,
  createMockUseTheme,

  // Auth
  createMockAuthContext,
  createMockUser,

  // Game State
  createMockPlayers,
  createMockGameState,
  createMockHoleHistory,
  createMockCourseHoles,
  createMockStrokeAllocation,

  // Betting
  createMockOddsResponse,
  createMockBettingScenario,

  // UI
  createMockUIComponents,
  createMockEventHandlers,
  createMockEvent,

  // API
  createMockFetchResponse,
  createMockFetchError,
  createMockNetworkError,

  // Tutorial
  createMockTutorialContext
};

export default mockFactories;
