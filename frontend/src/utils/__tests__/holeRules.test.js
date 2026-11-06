import { describe, test, expect } from 'vitest';
import {
  isHolePush,
  resolveCarryOverForHole,
  blocksHole18Push,
  validateHoleQuarters,
  netScoresAndWinner,
} from '../holeRules';

const push = (hole, wager = 1) => ({
  hole,
  wager,
  winner: 'push',
  points_delta: { p1: 0, p2: 0, p3: 0, p4: 0 },
});

const win = (hole, wager = 1) => ({
  hole,
  wager,
  points_delta: { p1: wager, p2: wager, p3: -wager, p4: -wager },
});

describe('isHolePush', () => {
  test('detects all-zero quarters', () => {
    expect(isHolePush({ points_delta: { p1: 0, p2: 0, p3: 0, p4: 0 } })).toBe(true);
  });

  test('detects explicit winner=push', () => {
    expect(isHolePush({ winner: 'push', points_delta: { p1: 1 } })).toBe(true);
  });

  test('rejects a decided hole', () => {
    expect(isHolePush(win(1))).toBe(false);
  });
});

describe('resolveCarryOverForHole', () => {
  test('fresh push doubles the next hole wager and arms the badge', () => {
    expect(
      resolveCarryOverForHole({
        holeHistory: [push(1, 1)],
        baseWager: 1,
        holeNumber: 2,
      }),
    ).toEqual({
      wager: 2,
      carryOver: true,
      fromHole: 1,
      consecutiveBlocked: false,
    });
  });

  test('consecutive push keeps elevated wager but clears the badge', () => {
    expect(
      resolveCarryOverForHole({
        holeHistory: [push(1, 1), push(2, 2)],
        baseWager: 1,
        holeNumber: 3,
      }),
    ).toEqual({
      wager: 2,
      carryOver: false,
      fromHole: null,
      consecutiveBlocked: true,
    });
  });

  test('a win clears carry-over back to base', () => {
    expect(
      resolveCarryOverForHole({
        holeHistory: [push(1, 1), win(2, 2)],
        baseWager: 1,
        holeNumber: 3,
      }),
    ).toEqual({
      wager: 1,
      carryOver: false,
      fromHole: null,
      consecutiveBlocked: false,
    });
  });

  test('hole 1 has no prior hole to carry', () => {
    expect(
      resolveCarryOverForHole({
        holeHistory: [],
        baseWager: 1,
        holeNumber: 1,
      }),
    ).toMatchObject({ wager: 1, carryOver: false });
  });
});

describe('blocksHole18Push', () => {
  test('blocks a push on 18 when hole 17 carried over', () => {
    expect(
      blocksHole18Push({
        holeHistory: [push(17, 1)],
        holeNumber: 18,
        isPush: true,
      }),
    ).toBe(true);
  });

  test('allows a decided hole 18 under carry-over', () => {
    expect(
      blocksHole18Push({
        holeHistory: [push(17, 1)],
        holeNumber: 18,
        isPush: false,
      }),
    ).toBe(false);
  });

  test('allows a push on 18 with no carry-over', () => {
    expect(
      blocksHole18Push({
        holeHistory: [win(17, 1)],
        holeNumber: 18,
        isPush: true,
      }),
    ).toBe(false);
  });
});

describe('validateHoleQuarters', () => {
  const players = [
    { id: 'p1', name: 'Alice' },
    { id: 'p2', name: 'Bob' },
  ];
  const check = (quarters, holeHistory = [], holeNumber = 1) =>
    validateHoleQuarters({ players, quarters, holeHistory, holeNumber });

  test('accepts balanced quarters', () => {
    expect(check({ p1: '2', p2: '-2' })).toBeNull();
  });

  test('names the player with a half-typed entry', () => {
    expect(check({ p1: '-', p2: '2' })).toMatch(/Alice/);
  });

  test('requires every player', () => {
    expect(check({ p1: '2' })).toBe('Please enter quarters for all players');
  });

  test('rejects a non-zero sum', () => {
    expect(check({ p1: '2', p2: '-1' })).toMatch(/sum to zero.*\+1\.00/);
  });

  test('rejects a push on 18 under carry-over', () => {
    const hist = [win(16, 1), push(17, 1)];
    expect(check({ p1: '0', p2: '0' }, hist, 18)).toMatch(/hole 18/);
  });
});

describe('netScoresAndWinner', () => {
  const players = [{ id: 'a' }, { id: 'b' }, { id: 'c' }, { id: 'd' }];
  const base = {
    players,
    teamMode: 'partners',
    team1: ['a', 'b'],
    captain: null,
    opponents: [],
    holeNumber: 1,
  };

  test('waits for all scores', () => {
    expect(netScoresAndWinner({ ...base, scores: { a: 4 } }).suggestedWinner).toBeNull();
  });

  test('best ball after strokes picks the winner', () => {
    const r = netScoresAndWinner({
      ...base,
      scores: { a: 5, b: 6, c: 4, d: 7 },
      strokeAllocation: { a: { 1: 1 } },
    });
    expect([r.team1Net, r.team2Net]).toEqual([4, 4]);
    expect(r.suggestedWinner).toBe('push');
  });

  test('solo captain vs best opponent', () => {
    const r = netScoresAndWinner({
      ...base,
      teamMode: 'solo',
      captain: 'a',
      opponents: ['b', 'c', 'd'],
      scores: { a: 3, b: 4, c: 5, d: 6 },
    });
    expect(r.suggestedWinner).toBe('captain');
  });
});
