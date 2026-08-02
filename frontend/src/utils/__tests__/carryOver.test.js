import { describe, test, expect } from 'vitest';
import {
  isHolePush,
  resolveCarryOverForHole,
  blocksHole18Push,
} from '../carryOver';

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
