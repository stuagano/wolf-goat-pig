import { describe, test, expect } from 'vitest';
import { nudgeHittingOrder } from '../hittingOrder';

describe('nudgeHittingOrder', () => {
  const order = ['p1', 'p2', 'p3', 'p4'];

  test('moves a player down one slot', () => {
    expect(nudgeHittingOrder(order, 0, 1)).toEqual(['p2', 'p1', 'p3', 'p4']);
  });

  test('moves a player up one slot', () => {
    expect(nudgeHittingOrder(order, 2, -1)).toEqual(['p1', 'p3', 'p2', 'p4']);
  });

  test('returns the same array reference when the nudge is out of bounds', () => {
    expect(nudgeHittingOrder(order, 0, -1)).toBe(order);
    expect(nudgeHittingOrder(order, 3, 1)).toBe(order);
  });
});
