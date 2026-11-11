import { describe, expect, test } from 'vitest';
import { DOLLARS_PER_QUARTER, settleUp, venmoPayUrl } from '../settleUp';

const p = (id, quarters, profile_id = null) => ({ id, name: id, quarters, profile_id });
const flows = result => result.payments.map(x => [x.from.id, x.to.id, x.dollars]);

describe('settleUp', () => {
  test('a quarter is worth 25 cents', () => {
    expect(DOLLARS_PER_QUARTER).toBe(0.25);
  });

  test('biggest loser pays biggest winner first, fewest payments', () => {
    const result = settleUp([p('Ann', 40), p('Bob', 8), p('Cy', -12), p('Dee', -36)]);
    expect(result.balanced).toBe(true);
    expect(flows(result)).toEqual([
      ['Dee', 'Ann', 9],
      ['Cy', 'Ann', 1],
      ['Cy', 'Bob', 2],
    ]);
  });

  test('one loser can pay several winners and the payments cover every debt', () => {
    const players = [p('Ann', 10), p('Bob', 6), p('Cy', 4), p('Dee', -20)];
    const result = settleUp(players);
    expect(flows(result)).toEqual([
      ['Dee', 'Ann', 2.5],
      ['Dee', 'Bob', 1.5],
      ['Dee', 'Cy', 1],
    ]);
    const paid = Object.fromEntries(players.map(x => [x.id, 0]));
    for (const { from, to, quarters } of result.payments) {
      paid[from.id] -= quarters;
      paid[to.id] += quarters;
    }
    expect(paid).toEqual({ Ann: 10, Bob: 6, Cy: 4, Dee: -20 });
  });

  test('fractional quarters settle exactly (no float drift)', () => {
    const result = settleUp([p('Ann', 0.1), p('Bob', 0.2), p('Cy', -0.3)]);
    expect(result.balanced).toBe(true);
    expect(result.payments.map(x => x.quarters)).toEqual([0.2, 0.1]);
  });

  test('a flat round needs no payments', () => {
    expect(settleUp([p('Ann', 0), p('Bob', 0)])).toEqual({ balanced: true, payments: [] });
  });

  test.each([
    ['quarters that do not sum to zero', [p('Ann', 10), p('Bob', -8)]],
    ['a missing total', [p('Ann', 10), p('Bob', null)]],
    ['no players', []],
  ])('refuses to settle with %s', (_, players) => {
    expect(settleUp(players)).toEqual({ balanced: false, payments: [] });
  });
});

describe('venmoPayUrl', () => {
  test('fills recipient, amount and note; strips the @', () => {
    const url = new URL(venmoPayUrl('@sg-golf', 9, 'Wolf Goat Pig · 2026-11-08'));
    expect(url.origin + url.pathname).toBe('https://venmo.com/');
    expect(Object.fromEntries(url.searchParams)).toEqual({
      txn: 'pay',
      recipients: 'sg-golf',
      amount: '9.00',
      note: 'Wolf Goat Pig · 2026-11-08',
    });
  });
});
