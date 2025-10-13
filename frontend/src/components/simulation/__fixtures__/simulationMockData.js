const clampProbability = (value) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 0;
  }
  if (value < 0) {
    return 0;
  }
  if (value > 1) {
    return 1;
  }
  return parseFloat(value.toFixed(2));
};

const withOverrides = (base, overrides) => ({
  ...base,
  ...(overrides || {}),
});

const basePlayers = [
  {
    id: 'human',
    name: 'Jordan Brooks',
    handicap: 9,
    is_human: true,
    status: 'awaiting_decision',
    points: 5,
  },
  {
    id: 'bot-wolf',
    name: 'Laser Lynx',
    handicap: 3,
    personality: 'Aggressive Attacker',
    status: 'tee_box',
    points: 7,
  },
  {
    id: 'bot-goat',
    name: 'Compass Caddie',
    handicap: 5,
    personality: 'Strategist',
    status: 'fairway',
    points: 6,
  },
  {
    id: 'bot-pig',
    name: 'Steady Stallion',
    handicap: 11,
    personality: 'Calm Finisher',
    status: 'green_side',
    points: 4,
  },
];

const baseBallPositions = {
  human: {
    lie: 'Fairway',
    distance_to_pin: 148,
    last_shot: {
      club: 'Driver',
      carry: 268,
      result: 'Center cut',
    },
  },
  'bot-wolf': {
    lie: 'First Cut',
    distance_to_pin: 139,
    last_shot: {
      club: 'Driver',
      carry: 274,
      result: 'Faded into rough',
    },
  },
  'bot-goat': {
    lie: 'Fairway',
    distance_to_pin: 125,
    last_shot: {
      club: '3 Wood',
      carry: 242,
      result: 'Positioned center fairway',
    },
  },
  'bot-pig': {
    lie: 'Fairway Bunker',
    distance_to_pin: 188,
    last_shot: {
      club: 'Driver',
      carry: 255,
      result: 'Caught left bunker lip',
    },
  },
};

const baseShotState = {
  player_id: 'bot-goat',
  player_name: 'Compass Caddie',
  club: '8 Iron',
  lie: 'Fairway',
  wind: {
    direction: 'Southwest',
    speed_mph: 6,
  },
  elevation_change: -4,
  recommended_shot: 'Controlled fade to front-middle pin',
  distance_to_pin: 125,
  carry_target: 132,
  green_receptiveness: 'Medium firm',
  miss_tendencies: 'Short right',
  confidence: 0.74,
};

const baseShotProbabilities = {
  birdie: 0.18,
  par: 0.57,
  bogey: 0.19,
  double_bogey: 0.06,
};

const baseBettingOptions = [
  {
    id: 'double-offer',
    label: 'Offer Double',
    description: 'Press the bet and double the stake before the approach shots.',
    action: 'offer_double',
  },
  {
    id: 'stay-put',
    label: 'Keep Wager',
    description: 'Hold the current wager and play it out.',
    action: 'keep_wager',
  },
];

const basePokerState = {
  pot: 12,
  current_wager: 2,
  pending_actions: [
    {
      player_id: 'bot-wolf',
      type: 'double',
      description: 'Laser Lynx wants to press the bet.',
    },
  ],
  betting_round: 'Pre-approach',
};

const baseTimelineEvents = [
  {
    id: 'evt-001',
    type: 'captain',
    description: 'Jordan Brooks earns the captaincy with the opening drive.',
    timestamp: '2024-05-07T10:02:00Z',
  },
  {
    id: 'evt-002',
    type: 'shot',
    description: 'Laser Lynx drives 274 yards into the first cut.',
    timestamp: '2024-05-07T10:04:00Z',
  },
  {
    id: 'evt-003',
    type: 'partnership',
    description: 'Jordan Brooks invited Compass Caddie to partner.',
    timestamp: '2024-05-07T10:05:30Z',
  },
  {
    id: 'evt-004',
    type: 'double',
    description: 'Steady Stallion challenges with a double.',
    timestamp: '2024-05-07T10:06:10Z',
  },
];

const baseFeedback = [
  {
    id: 'fb-001',
    title: 'Captaincy Earned',
    body: 'Your drive found the center cut and outpaced the bots. Take command of the hole.',
  },
  {
    id: 'fb-002',
    title: 'Partnership Intel',
    body: 'Compass Caddie is trending +0.9 strokes gained on approaches in similar conditions.',
  },
  {
    id: 'fb-003',
    title: 'Stakes Update',
    body: 'Robots are pressuring with an early double. Evaluate your approach confidence before accepting.',
  },
];

const baseInteraction = {
  type: 'captain_decision',
  captain_id: 'human',
  available_partners: ['bot-goat', 'bot-pig'],
};

const baseGameState = {
  game_id: 'mock-game-001',
  current_hole: 5,
  hole_par: 4,
  hole_distance: 412,
  captain_id: 'human',
  base_wager: 2,
  betting: {
    current_wager: 2,
    history: [
      { id: 'bet-001', team: 'human', amount: 1 },
      { id: 'bet-002', team: 'robots', amount: 2 },
    ],
  },
  players: basePlayers,
  hole_state: {
    hole_complete: false,
    next_player_to_hit: 'bot-goat',
    current_shot_number: 2,
    ball_positions: baseBallPositions,
  },
  feedback: baseFeedback,
  interactionNeeded: baseInteraction,
  hasNextShot: true,
};

const setupData = {
  personalities: [
    { id: 'aggressive-attacker', name: 'Aggressive Attacker' },
    { id: 'calm-finisher', name: 'Calm Finisher' },
    { id: 'strategist', name: 'Calculating Strategist' },
  ],
  opponents: [
    { id: 'op-laser-lynx', name: 'Laser Lynx', handicap: 3, personality: 'Aggressive Attacker' },
    { id: 'op-compass-caddie', name: 'Compass Caddie', handicap: 5, personality: 'Calculating Strategist' },
    { id: 'op-steady-stallion', name: 'Steady Stallion', handicap: 11, personality: 'Calm Finisher' },
    { id: 'op-wind-whisper', name: 'Wind Whisper', handicap: 7, personality: 'Shot Shaper' },
  ],
  courses: {
    'Mock National': {
      location: 'Austin, TX',
      par: 71,
      rating: 72.1,
      slope: 133,
    },
    'Robots Ridge': {
      location: 'Flagstaff, AZ',
      par: 72,
      rating: 73.4,
      slope: 136,
    },
  },
};

const buildMockBundle = (overrides = {}) => {
  const probabilityOverrides = overrides.shotProbabilities || overrides.shot_probabilities;
  const mergedShotProbabilities = probabilityOverrides
    ? Object.entries(withOverrides(baseShotProbabilities, probabilityOverrides)).reduce((acc, [key, value]) => {
        acc[key] = clampProbability(value);
        return acc;
      }, {})
    : { ...baseShotProbabilities };

  return {
    id: 'default',
    description: 'Default mock simulation data for local UI development.',
    setup: withOverrides(setupData, overrides.setup),
    gameState: withOverrides(baseGameState, overrides.gameState),
    shotState: withOverrides(baseShotState, overrides.shotState),
    shotProbabilities: mergedShotProbabilities,
    interactionNeeded: withOverrides(baseInteraction, overrides.interactionNeeded),
    bettingOptions: overrides.bettingOptions || [...baseBettingOptions],
    pokerState: withOverrides(basePokerState, overrides.pokerState),
    timelineEvents: overrides.timelineEvents || [...baseTimelineEvents],
    feedback: overrides.feedback || [...baseFeedback],
    hasNextShot: overrides.hasNextShot ?? baseGameState.hasNextShot,
  };
};

export const simulationMockPresets = {
  default: buildMockBundle(),
  pressureDouble: buildMockBundle({
    id: 'pressureDouble',
    description: 'High-stakes moment with double decision pending.',
    interactionNeeded: {
      type: 'double_offer',
    },
    pokerState: {
      ...basePokerState,
      pending_actions: [],
      betting_round: 'Post-approach',
    },
    shotState: {
      ...baseShotState,
      player_id: 'human',
      player_name: 'Jordan Brooks',
      club: 'Gap Wedge',
      distance_to_pin: 96,
      carry_target: 102,
      recommended_shot: 'Three-quarter wedge to backstop the ridge.',
      confidence: 0.81,
    },
    shotProbabilities: {
      birdie: 0.31,
      par: 0.54,
      bogey: 0.12,
      double_bogey: 0.03,
    },
    timelineEvents: [
      ...baseTimelineEvents,
      {
        id: 'evt-005',
        type: 'double',
        description: 'Jordan considers firing back with a counter double.',
        timestamp: '2024-05-07T10:07:05Z',
      },
    ],
  }),
};

export const getSimulationMock = (presetName = 'default') => {
  return simulationMockPresets[presetName] || simulationMockPresets.default;
};

export default simulationMockPresets;
