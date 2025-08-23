/**
 * Test fixtures for Wolf Goat Pig game testing
 * 
 * Provides consistent mock data for testing components and hooks
 * that depend on game state, player profiles, and statistics.
 */

// Base player profiles for testing
export const mockPlayerProfiles = [
  {
    id: '1',
    name: 'Alice Johnson',
    handicap: 8.5,
    avatar_url: 'https://example.com/alice.jpg',
    email: 'alice@example.com',
    created_date: '2024-01-01T00:00:00Z',
    last_played: '2024-01-15T10:30:00Z',
    preferences: {
      ai_difficulty: 'medium',
      preferred_game_modes: ['wolf_goat_pig'],
      preferred_player_count: 4,
      betting_style: 'conservative',
      display_hints: true,
      auto_calculate_odds: true,
      notification_preferences: {
        email: true,
        push: false,
        sms: false
      }
    },
    statistics: {
      games_played: 25,
      total_earnings: 156.75,
      win_rate: 0.68,
      average_score: 79.2,
      best_score: 72,
      worst_score: 88,
      holes_won: 94,
      total_holes: 450,
      favorite_bet_type: 'conservative',
      most_successful_formation: 'partnerships',
      handicap_trend: 'improving'
    }
  },
  {
    id: '2',
    name: 'Bob Smith',
    handicap: 18.0,
    avatar_url: '',
    email: 'bob@example.com',
    created_date: '2024-01-05T00:00:00Z',
    last_played: null,
    preferences: {
      ai_difficulty: 'easy',
      preferred_game_modes: ['wolf_goat_pig'],
      preferred_player_count: 4,
      betting_style: 'aggressive',
      display_hints: false,
      auto_calculate_odds: false,
      notification_preferences: {
        email: false,
        push: true,
        sms: true
      }
    },
    statistics: {
      games_played: 8,
      total_earnings: -32.50,
      win_rate: 0.25,
      average_score: 92.4,
      best_score: 85,
      worst_score: 102,
      holes_won: 18,
      total_holes: 144,
      favorite_bet_type: 'aggressive',
      most_successful_formation: 'solo',
      handicap_trend: 'stable'
    }
  },
  {
    id: '3',
    name: 'Carol Davis',
    handicap: 25.5,
    avatar_url: null,
    email: 'carol@example.com',
    created_date: '2024-01-10T00:00:00Z',
    last_played: '2024-01-14T15:45:00Z',
    preferences: {
      ai_difficulty: 'hard',
      preferred_game_modes: ['wolf_goat_pig'],
      preferred_player_count: 6,
      betting_style: 'moderate',
      display_hints: true,
      auto_calculate_odds: true,
      notification_preferences: {
        email: true,
        push: true,
        sms: false
      }
    },
    statistics: {
      games_played: 12,
      total_earnings: 45.25,
      win_rate: 0.42,
      average_score: 98.8,
      best_score: 89,
      worst_score: 115,
      holes_won: 31,
      total_holes: 216,
      favorite_bet_type: 'moderate',
      most_successful_formation: 'wolf_pack',
      handicap_trend: 'improving'
    }
  },
  {
    id: '4',
    name: 'David Wilson',
    handicap: 12.0,
    avatar_url: 'https://example.com/david.jpg',
    email: 'david@example.com',
    created_date: '2024-01-08T00:00:00Z',
    last_played: '2024-01-16T09:15:00Z',
    preferences: {
      ai_difficulty: 'medium',
      preferred_game_modes: ['wolf_goat_pig'],
      preferred_player_count: 4,
      betting_style: 'conservative',
      display_hints: true,
      auto_calculate_odds: true,
      notification_preferences: {
        email: true,
        push: false,
        sms: true
      }
    },
    statistics: {
      games_played: 18,
      total_earnings: 78.90,
      win_rate: 0.56,
      average_score: 84.6,
      best_score: 76,
      worst_score: 96,
      holes_won: 58,
      total_holes: 324,
      favorite_bet_type: 'conservative',
      most_successful_formation: 'partnerships',
      handicap_trend: 'stable'
    }
  }
];

// Mock game states for different scenarios
export const mockGameStates = {
  // New game, no shots taken
  initial: {
    game_id: 'game_001',
    status: 'active',
    created_at: '2024-01-16T10:00:00Z',
    current_hole: 1,
    current_hole_par: 4,
    hole_difficulty: 3.2,
    course_id: 'test_course_18',
    players: mockPlayerProfiles.slice(0, 4).map(profile => ({
      id: profile.id,
      name: profile.name,
      handicap: profile.handicap,
      current_score: 0,
      shots_taken: 0,
      distance_to_pin: 385, // Tee shot distance
      lie_type: 'tee',
      is_captain: false,
      team_id: null,
      hole_scores: []
    })),
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

  // Mid-game state
  mid_game: {
    game_id: 'game_002',
    status: 'active',
    created_at: '2024-01-16T10:00:00Z',
    current_hole: 8,
    current_hole_par: 4,
    hole_difficulty: 3.8,
    course_id: 'test_course_18',
    players: [
      {
        id: '1',
        name: 'Alice Johnson',
        handicap: 8.5,
        current_score: 32,
        shots_taken: 1,
        distance_to_pin: 150,
        lie_type: 'fairway',
        is_captain: true,
        team_id: 'team_alice_bob',
        hole_scores: [4, 3, 5, 4, 6, 3, 4]
      },
      {
        id: '2',
        name: 'Bob Smith',
        handicap: 18.0,
        current_score: 38,
        shots_taken: 2,
        distance_to_pin: 180,
        lie_type: 'rough',
        is_captain: false,
        team_id: 'team_alice_bob',
        hole_scores: [5, 4, 6, 5, 7, 4, 5]
      },
      {
        id: '3',
        name: 'Carol Davis',
        handicap: 25.5,
        current_score: 29,
        shots_taken: 1,
        distance_to_pin: 85,
        lie_type: 'fairway',
        is_captain: false,
        team_id: 'solo',
        hole_scores: [3, 3, 4, 3, 4, 3, 4]
      },
      {
        id: '4',
        name: 'David Wilson',
        handicap: 12.0,
        current_score: 35,
        shots_taken: 1,
        distance_to_pin: 120,
        lie_type: 'bunker',
        is_captain: false,
        team_id: 'solo',
        hole_scores: [4, 4, 5, 4, 5, 4, 5]
      }
    ],
    teams: {
      type: 'partnerships',
      formation: {
        team_alice_bob: ['1', '2'],
        solo: ['3', '4']
      },
      captain: '1'
    },
    current_wager: 4.0,
    is_doubled: true,
    line_of_scrimmage_passed: true,
    betting: {
      currentPot: 48.50,
      opportunities: [
        {
          id: 'bet_001',
          description: 'Carol to win hole 8',
          type: 'hole_winner',
          odds: '2:1',
          potential_payout: 12.00,
          risk_level: 'medium',
          expires_at: '2024-01-16T11:00:00Z'
        },
        {
          id: 'bet_002',
          description: 'Alice & Bob vs Field',
          type: 'team_vs_field',
          odds: '3:2',
          potential_payout: 18.00,
          risk_level: 'low',
          expires_at: '2024-01-16T11:00:00Z'
        }
      ],
      history: [
        {
          id: 'hist_001',
          hole: 7,
          player_id: '1',
          action: 'Double Down',
          amount: 4.00,
          result: 'won',
          payout: 8.00,
          timestamp: '2024-01-16T10:45:00Z'
        },
        {
          id: 'hist_002',
          hole: 6,
          player_id: '2',
          action: 'Side Bet',
          amount: 2.00,
          result: 'lost',
          payout: 0.00,
          timestamp: '2024-01-16T10:30:00Z'
        }
      ]
    },
    weather: {
      condition: 'partly_cloudy',
      wind_speed: 12,
      wind_direction: 'W',
      temperature: 75
    }
  },

  // Final hole state
  final_hole: {
    game_id: 'game_003',
    status: 'active',
    created_at: '2024-01-16T10:00:00Z',
    current_hole: 18,
    current_hole_par: 5,
    hole_difficulty: 4.5,
    course_id: 'test_course_18',
    players: [
      {
        id: '1',
        name: 'Alice Johnson',
        handicap: 8.5,
        current_score: 74,
        shots_taken: 2,
        distance_to_pin: 220,
        lie_type: 'fairway',
        is_captain: false,
        team_id: 'solo',
        hole_scores: [4, 3, 5, 4, 6, 3, 4, 3, 4, 5, 3, 4, 6, 4, 3, 5, 4]
      },
      {
        id: '3',
        name: 'Carol Davis',
        handicap: 25.5,
        current_score: 76,
        shots_taken: 1,
        distance_to_pin: 185,
        lie_type: 'rough',
        is_captain: true,
        team_id: 'team_carol_david',
        hole_scores: [3, 3, 4, 3, 4, 3, 4, 5, 4, 4, 5, 4, 5, 4, 4, 4, 5]
      }
    ],
    teams: {
      type: 'head_to_head',
      formation: {
        alice_solo: ['1'],
        team_carol_david: ['3', '4']
      },
      captain: '3'
    },
    current_wager: 8.0,
    is_doubled: false,
    line_of_scrimmage_passed: true,
    betting: {
      currentPot: 156.75,
      opportunities: [
        {
          id: 'bet_final',
          description: 'Championship Playoff - Winner Takes All',
          type: 'winner_takes_all',
          odds: 'even',
          potential_payout: 156.75,
          risk_level: 'high',
          expires_at: '2024-01-16T12:00:00Z'
        }
      ],
      history: [] // Many betting events throughout the game
    }
  },

  // Completed game state
  completed: {
    game_id: 'game_004',
    status: 'completed',
    created_at: '2024-01-15T10:00:00Z',
    completed_at: '2024-01-15T14:30:00Z',
    duration_minutes: 270,
    current_hole: 18,
    course_id: 'test_course_18',
    final_results: {
      winner: '1',
      final_scores: [
        { player_id: '1', total_score: 74, earnings: 45.50, holes_won: 8 },
        { player_id: '2', total_score: 89, earnings: -15.25, holes_won: 3 },
        { player_id: '3', total_score: 78, earnings: 22.75, holes_won: 6 },
        { player_id: '4', total_score: 82, earnings: -8.00, holes_won: 1 }
      ],
      total_pot: 156.00,
      betting_volume: 328.50,
      longest_drive: { player_id: '2', distance: 285, hole: 12 },
      most_birdies: { player_id: '1', count: 4 },
      best_comeback: { player_id: '3', deficit: 8, hole: 14 }
    },
    game_events: [
      {
        type: 'hole_in_one',
        player_id: '1',
        hole: 7,
        timestamp: '2024-01-15T12:15:00Z'
      },
      {
        type: 'eagle',
        player_id: '3',
        hole: 15,
        timestamp: '2024-01-15T13:45:00Z'
      }
    ]
  }
};

// Mock odds calculation responses
export const mockOddsResponses = {
  basic: {
    timestamp: '2024-01-16T10:30:00Z',
    calculation_time_ms: 145.2,
    confidence_level: 0.87,
    monte_carlo_used: true,
    player_probabilities: {
      '1': {
        name: 'Alice Johnson',
        win_probability: 0.65,
        expected_score: 4.2,
        confidence_interval: [0.58, 0.72]
      },
      '2': {
        name: 'Bob Smith',
        win_probability: 0.15,
        expected_score: 5.1,
        confidence_interval: [0.10, 0.22]
      },
      '3': {
        name: 'Carol Davis',
        win_probability: 0.12,
        expected_score: 5.5,
        confidence_interval: [0.08, 0.18]
      },
      '4': {
        name: 'David Wilson',
        win_probability: 0.08,
        expected_score: 5.8,
        confidence_interval: [0.05, 0.13]
      }
    },
    team_probabilities: {
      team_alice_bob: 0.58,
      solo_carol: 0.25,
      solo_david: 0.17
    },
    optimal_strategy: 'conservative_play',
    betting_scenarios: [
      {
        scenario_type: 'double_down',
        win_probability: 0.62,
        expected_value: 1.25,
        risk_level: 'medium',
        reasoning: 'Alice has favorable position with good lie and manageable distance',
        confidence_interval: [0.55, 0.69],
        payout_matrix: {
          win: 4.00,
          loss: -2.00,
          push: 0.00
        },
        recommendation: 'offer'
      },
      {
        scenario_type: 'side_bet',
        win_probability: 0.45,
        expected_value: -0.15,
        risk_level: 'high',
        reasoning: 'Bob faces challenging rough lie with increased distance',
        confidence_interval: [0.38, 0.52],
        payout_matrix: {
          win: 2.50,
          loss: -1.50
        },
        recommendation: 'decline'
      }
    ],
    risk_assessment: {
      volatility: 0.23,
      weather_factor: 1.0,
      course_difficulty: 3.5,
      player_fatigue: 0.15
    },
    educational_insights: [
      'Alice\'s fairway lie provides significant advantage over rough',
      'Current hole difficulty (3.5/5) suggests moderate challenge',
      'Team partnerships favor balanced risk-taking approach'
    ],
    simulation_details: {
      num_simulations_run: 5000,
      convergence_achieved: true,
      monte_carlo_variance: 0.012
    }
  },

  complex: {
    timestamp: '2024-01-16T11:15:00Z',
    calculation_time_ms: 342.8,
    confidence_level: 0.76,
    monte_carlo_used: true,
    player_probabilities: {
      '1': { win_probability: 0.35, expected_score: 4.8 },
      '2': { win_probability: 0.28, expected_score: 5.2 },
      '3': { win_probability: 0.25, expected_score: 5.4 },
      '4': { win_probability: 0.12, expected_score: 6.1 }
    },
    team_probabilities: {
      partnerships: 0.42,
      wolf_pack: 0.35,
      solo_players: 0.23
    },
    optimal_strategy: 'aggressive_betting',
    betting_scenarios: [
      {
        scenario_type: 'press_bet',
        win_probability: 0.48,
        expected_value: 0.85,
        risk_level: 'high',
        recommendation: 'consider'
      },
      {
        scenario_type: 'wolf_declaration',
        win_probability: 0.32,
        expected_value: 2.15,
        risk_level: 'very_high',
        recommendation: 'offer'
      }
    ],
    simulation_details: {
      num_simulations_run: 10000,
      convergence_achieved: true
    }
  }
};

// Mock shot analysis responses
export const mockShotAnalysisResponses = {
  fairway_approach: {
    timestamp: '2024-01-16T10:30:00Z',
    calculation_time_ms: 85.4,
    recommended_shot: {
      type: 'standard_approach',
      club: '7_iron',
      target_area: 'center_pin',
      success_rate: '78%',
      risk_level: 'low',
      expected_distance: 155,
      expected_accuracy: 0.82
    },
    all_ranges: [
      {
        type: 'conservative_approach',
        club: '8_iron',
        success_rate: '85%',
        risk_level: 'very_low',
        expected_value: 0.15,
        description: 'Safe play to center of green'
      },
      {
        type: 'standard_approach',
        club: '7_iron',
        success_rate: '78%',
        risk_level: 'low',
        expected_value: 0.25,
        description: 'Direct approach to pin'
      },
      {
        type: 'aggressive_approach',
        club: '6_iron',
        success_rate: '65%',
        risk_level: 'medium',
        expected_value: 0.35,
        description: 'Attack the pin for birdie chance'
      }
    ],
    strategic_advice: {
      primary: 'Favorable lie and distance suggest standard approach',
      considerations: [
        'Wind direction favors slightly longer club',
        'Pin position allows for aggressive play',
        'Current score differential supports risk-taking'
      ],
      course_management: 'Consider team dynamics in shot selection'
    },
    player_style: {
      profile: 'balanced',
      description: 'Adapts strategy based on situation',
      confidence_modifier: 1.0
    }
  },

  rough_recovery: {
    timestamp: '2024-01-16T10:35:00Z',
    calculation_time_ms: 125.7,
    recommended_shot: {
      type: 'recovery_shot',
      club: '9_iron',
      target_area: 'safe_area',
      success_rate: '65%',
      risk_level: 'medium',
      expected_distance: 120,
      expected_accuracy: 0.68
    },
    all_ranges: [
      {
        type: 'conservative_layup',
        club: 'wedge',
        success_rate: '88%',
        risk_level: 'low',
        expected_value: -0.05,
        description: 'Safe recovery to fairway'
      },
      {
        type: 'recovery_shot',
        club: '9_iron',
        success_rate: '65%',
        risk_level: 'medium',
        expected_value: 0.10,
        description: 'Advance toward green'
      },
      {
        type: 'hero_shot',
        club: '7_iron',
        success_rate: '35%',
        risk_level: 'very_high',
        expected_value: -0.15,
        description: 'Risky attempt to reach green'
      }
    ],
    strategic_advice: {
      primary: 'Rough lie limits options - prioritize position',
      considerations: [
        'Thick rough reduces club selection',
        'Risk/reward doesn\'t favor aggressive play',
        'Team situation allows for conservative approach'
      ]
    }
  }
};

// Mock course data
export const mockCourseData = {
  id: 'test_course_18',
  name: 'Test Golf Course',
  par: 72,
  yardage: 6842,
  difficulty_rating: 72.1,
  slope_rating: 134,
  holes: Array.from({ length: 18 }, (_, i) => ({
    number: i + 1,
    par: i % 3 === 0 ? 3 : i % 5 === 0 ? 5 : 4,
    yardage: 150 + Math.floor(Math.random() * 400),
    difficulty: 2.5 + Math.random() * 2,
    hazards: ['water', 'bunker', 'trees'].filter(() => Math.random() > 0.6)
  }))
};

// Utility functions for test data manipulation
export const testUtils = {
  // Create a player with custom properties
  createPlayer: (overrides = {}) => ({
    ...mockPlayerProfiles[0],
    id: Math.random().toString(36).substr(2, 9),
    ...overrides
  }),

  // Create a game state with custom properties
  createGameState: (scenario = 'initial', overrides = {}) => ({
    ...mockGameStates[scenario],
    game_id: Math.random().toString(36).substr(2, 9),
    ...overrides
  }),

  // Generate random score for testing
  generateRandomScore: (par, handicap) => {
    const base = par + (handicap / 18);
    return Math.max(1, Math.round(base + (Math.random() - 0.5) * 2));
  },

  // Generate realistic betting opportunity
  generateBettingOpportunity: (type = 'hole_winner') => ({
    id: Math.random().toString(36).substr(2, 9),
    description: `Test ${type} opportunity`,
    type,
    odds: '2:1',
    potential_payout: Math.round(Math.random() * 20 + 5),
    risk_level: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)],
    expires_at: new Date(Date.now() + 300000).toISOString() // 5 minutes from now
  }),

  // Deep clone object for mutation testing
  deepClone: (obj) => JSON.parse(JSON.stringify(obj)),

  // Wait for async operations in tests
  waitFor: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  // Generate time series data for charts
  generateTimeSeriesData: (days, baseValue, variance = 0.1) => {
    const data = [];
    let currentValue = baseValue;
    
    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));
      
      currentValue += (Math.random() - 0.5) * variance * baseValue;
      currentValue = Math.max(0, currentValue);
      
      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.round(currentValue * 100) / 100
      });
    }
    
    return data;
  }
};

// Test cases for fixtures
describe('Game Fixtures Test Suite', () => {
  test('mockPlayerProfiles structure is valid', () => {
    expect(mockPlayerProfiles).toHaveLength(4);
    mockPlayerProfiles.forEach(profile => {
      expect(profile).toHaveProperty('id');
      expect(profile).toHaveProperty('name');
      expect(profile).toHaveProperty('handicap');
      expect(profile).toHaveProperty('preferences');
      expect(profile).toHaveProperty('statistics');
    });
  });

  test('mockGameStates contains expected scenarios', () => {
    const expectedScenarios = ['initial', 'mid_game', 'final_hole', 'completed'];
    expectedScenarios.forEach(scenario => {
      expect(mockGameStates).toHaveProperty(scenario);
      expect(mockGameStates[scenario]).toHaveProperty('game_id');
      expect(mockGameStates[scenario]).toHaveProperty('status');
    });
  });

  test('testUtils functions work correctly', () => {
    const customPlayer = testUtils.createPlayer({ name: 'Custom Player' });
    expect(customPlayer.name).toBe('Custom Player');
    expect(customPlayer).toHaveProperty('id');

    const gameState = testUtils.createGameState('initial', { current_hole: 5 });
    expect(gameState.current_hole).toBe(5);

    const score = testUtils.generateRandomScore(4, 18);
    expect(typeof score).toBe('number');
    expect(score).toBeGreaterThanOrEqual(1);

    const opportunity = testUtils.generateBettingOpportunity('hole_winner');
    expect(opportunity.type).toBe('hole_winner');
    expect(opportunity).toHaveProperty('potential_payout');
  });

  test('mockOddsResponses contain valid probability data', () => {
    expect(mockOddsResponses.basic).toHaveProperty('player_probabilities');
    expect(mockOddsResponses.basic).toHaveProperty('team_probabilities');
    expect(mockOddsResponses.basic).toHaveProperty('optimal_strategy');
    
    // Check probabilities sum approximately to 1
    const playerProbs = Object.values(mockOddsResponses.basic.player_probabilities);
    const totalProb = playerProbs.reduce((sum, p) => sum + p.win_probability, 0);
    expect(totalProb).toBeCloseTo(1, 1);
  });

  test('mockShotAnalysisResponses provide valid shot options', () => {
    expect(mockShotAnalysisResponses.fairway_approach).toHaveProperty('recommended_shot');
    expect(mockShotAnalysisResponses.fairway_approach).toHaveProperty('all_ranges');
    expect(mockShotAnalysisResponses.fairway_approach.all_ranges).toBeInstanceOf(Array);
    
    mockShotAnalysisResponses.fairway_approach.all_ranges.forEach(range => {
      expect(range).toHaveProperty('club');
      expect(range).toHaveProperty('success_rate');
      expect(range).toHaveProperty('risk_level');
    });
  });

  test('time series data generation works', () => {
    const data = testUtils.generateTimeSeriesData(7, 100, 0.1);
    expect(data).toHaveLength(7);
    data.forEach(point => {
      expect(point).toHaveProperty('date');
      expect(point).toHaveProperty('value');
      expect(typeof point.value).toBe('number');
    });
  });
});

export default {
  mockPlayerProfiles,
  mockGameStates,
  mockOddsResponses,
  mockShotAnalysisResponses,
  mockCourseData,
  testUtils
};