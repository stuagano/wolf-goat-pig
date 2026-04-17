// frontend/src/utils/__tests__/stuartModeInsights.test.js
import { computeThreatScore, generateInsights } from '../stuartModeInsights';

describe('computeThreatScore', () => {
  test('returns handicap minus full stroke', () => {
    expect(computeThreatScore(8, 1)).toBe(7);
  });

  test('returns handicap minus half stroke (Creecher)', () => {
    expect(computeThreatScore(8, 0.5)).toBe(7.5);
  });

  test('returns handicap when no strokes', () => {
    expect(computeThreatScore(1, 0)).toBe(1);
  });

  test('handles double stroke', () => {
    expect(computeThreatScore(20, 2)).toBe(18);
  });
});

describe('generateInsights', () => {
  const stuart = { id: 'p1', name: 'Stuart', handicap: 15, is_authenticated: true };
  const steve  = { id: 'p2', name: 'Steve',  handicap: 1,  is_authenticated: false };
  const dan    = { id: 'p3', name: 'Dan',    handicap: 12, is_authenticated: false };
  const mike   = { id: 'p4', name: 'Mike',   handicap: 14, is_authenticated: false };

  const baseParams = {
    players: [stuart, steve, dan, mike],
    currentHole: 5,
    strokeAllocation: {
      p1: { 5: 1 },
      p2: { 5: 0 },
      p3: { 5: 0 },
      p4: { 5: 0 },
    },
    playerStandings: {
      p1: { quarters: 0 },
      p2: { quarters: 0 },
      p3: { quarters: 0 },
      p4: { quarters: 0 },
    },
    courseData: { holes: [{ hole_number: 5, handicap: 4 }] },
    currentWager: 2,
  };

  test('returns required fields', () => {
    const result = generateInsights(baseParams);
    expect(result).toHaveProperty('headline');
    expect(result).toHaveProperty('detail');
    expect(result).toHaveProperty('threats');
    expect(result).toHaveProperty('soloRecommendation');
  });

  test('soloRecommendation is go when Stuart has full stroke and no high-threat opponents', () => {
    const params = {
      ...baseParams,
      players: [
        stuart,
        { id: 'p2', name: 'Bob', handicap: 18, is_authenticated: false },
        { id: 'p3', name: 'Ted', handicap: 16, is_authenticated: false },
      ],
      strokeAllocation: { p1: { 5: 1 }, p2: { 5: 0 }, p3: { 5: 0 } },
      playerStandings: {
        p1: { quarters: 0 },
        p2: { quarters: 0 },
        p3: { quarters: 0 },
      },
    };
    const result = generateInsights(params);
    expect(result.soloRecommendation).toBe('go');
  });

  test('soloRecommendation is caution when Stuart has full stroke but Steve (1 hdcp) is high threat', () => {
    const result = generateInsights(baseParams);
    expect(result.soloRecommendation).toBe('caution');
  });

  test('soloRecommendation is avoid when Stuart has no stroke and high-threat opponent exists', () => {
    const params = {
      ...baseParams,
      strokeAllocation: { p1: { 5: 0 }, p2: { 5: 0 }, p3: { 5: 0 }, p4: { 5: 0 } },
    };
    const result = generateInsights(params);
    expect(result.soloRecommendation).toBe('avoid');
  });

  test('being down > 3q bumps soloRecommendation up one level (caution → go)', () => {
    const params = {
      ...baseParams,
      playerStandings: {
        p1: { quarters: -4 },
        p2: { quarters: 2 },
        p3: { quarters: 1 },
        p4: { quarters: 1 },
      },
    };
    const result = generateInsights(params);
    expect(result.soloRecommendation).toBe('go');
  });

  test('threats array sorted lowest threatScore first', () => {
    const result = generateInsights(baseParams);
    const scores = result.threats.map(t => t.threatScore);
    expect(scores).toEqual([...scores].sort((a, b) => a - b));
  });

  test('Creecher (0.5 stroke) is reflected in threatScore', () => {
    const params = {
      ...baseParams,
      strokeAllocation: {
        p1: { 5: 0.5 },
        p2: { 5: 0 },
        p3: { 5: 0 },
        p4: { 5: 0 },
      },
    };
    const result = generateInsights(params);
    const stuartThreat = result.threats.find(t => t.player.id === 'p1');
    expect(stuartThreat.threatScore).toBe(14.5);
  });

  test('headline mentions high-threat opponent by name', () => {
    const result = generateInsights(baseParams);
    expect(result.headline).toMatch(/Steve/);
  });

  test('hungry flag set for player who is down and is high threat', () => {
    const params = {
      ...baseParams,
      playerStandings: {
        p1: { quarters: 5 },
        p2: { quarters: -5 },
        p3: { quarters: 0 },
        p4: { quarters: 0 },
      },
    };
    const result = generateInsights(params);
    const steveThreat = result.threats.find(t => t.player.id === 'p2');
    expect(steveThreat.hungry).toBe(true);
  });

  test('soloRecommendation is caution when Stuart has Creecher and high-threat opponent exists', () => {
    const params = {
      ...baseParams,
      strokeAllocation: { p1: { 5: 0.5 }, p2: { 5: 0 }, p3: { 5: 0 }, p4: { 5: 0 } },
    };
    const result = generateInsights(params);
    expect(result.soloRecommendation).toBe('caution');
  });

  test('being down > 3q bumps soloRecommendation up one level (avoid → caution)', () => {
    const params = {
      ...baseParams,
      strokeAllocation: { p1: { 5: 0 }, p2: { 5: 0 }, p3: { 5: 0 }, p4: { 5: 0 } },
      playerStandings: {
        p1: { quarters: -4 },
        p2: { quarters: 0 },
        p3: { quarters: 0 },
        p4: { quarters: 0 },
      },
    };
    const result = generateInsights(params);
    expect(result.soloRecommendation).toBe('caution');
  });

  test('returns fallback when no authenticated player found', () => {
    const params = {
      players: [{ id: 'p1', name: 'Bob', handicap: 10, is_authenticated: false }],
      currentHole: 1,
      strokeAllocation: {},
      playerStandings: {},
      courseData: { holes: [] },
      currentWager: 1,
    };
    const result = generateInsights(params);
    expect(result.headline).toBe('No authenticated player found');
    expect(result.threats).toEqual([]);
    expect(result.soloRecommendation).toBe('caution');
  });
});
