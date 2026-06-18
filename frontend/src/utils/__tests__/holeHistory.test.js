// frontend/src/utils/__tests__/holeHistory.test.js
import { upsertHole, allHolesPlayed } from '../holeHistory';

const hole = (n, extra = {}) => ({ hole: n, points_delta: {}, ...extra });

describe('upsertHole', () => {
  test('appends a brand-new hole', () => {
    const result = upsertHole([hole(1)], hole(2));
    expect(result.map((h) => h.hole)).toEqual([1, 2]);
  });

  test('replaces an existing hole instead of appending (no duplicates)', () => {
    const result = upsertHole([hole(1, { wager: 1 })], hole(1, { wager: 5 }));
    expect(result).toHaveLength(1);
    expect(result[0].wager).toBe(5);
  });

  test('does not mutate the input array', () => {
    const input = [hole(1)];
    upsertHole(input, hole(2));
    expect(input).toHaveLength(1);
  });
});

describe('allHolesPlayed', () => {
  test('true when all 18 distinct holes are present', () => {
    const history = Array.from({ length: 18 }, (_, i) => hole(i + 1));
    expect(allHolesPlayed(history)).toBe(true);
  });

  test('false when a real hole is missing even if length is 18', () => {
    // Holes 1..17 plus a duplicate of hole 1 → 18 entries, hole 18 missing.
    const history = [
      ...Array.from({ length: 17 }, (_, i) => hole(i + 1)),
      hole(1),
    ];
    expect(history).toHaveLength(18);
    expect(allHolesPlayed(history)).toBe(false);
  });

  test('false when a middle hole is skipped', () => {
    const history = Array.from({ length: 18 }, (_, i) => i + 1)
      .filter((n) => n !== 9)
      .map((n) => hole(n))
      .concat(hole(19));
    expect(allHolesPlayed(history)).toBe(false);
  });

  test('respects a custom round length', () => {
    const history = Array.from({ length: 9 }, (_, i) => hole(i + 1));
    expect(allHolesPlayed(history, 9)).toBe(true);
  });
});
