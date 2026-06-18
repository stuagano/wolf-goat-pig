import { describe, test, expect } from 'vitest';
import {
  parseQuarter,
  normalizeQuarterInput,
  flipSign,
  isNegativeInput,
} from '../quarters';

describe('parseQuarter', () => {
  test('parses complete numbers (incl. negatives and fractions)', () => {
    expect(parseQuarter('0')).toBe(0);
    expect(parseQuarter('3')).toBe(3);
    expect(parseQuarter('-2')).toBe(-2);
    expect(parseQuarter('0.5')).toBe(0.5);
    expect(parseQuarter('-0.5')).toBe(-0.5);
    expect(parseQuarter('1.')).toBe(1); // trailing dot still parses
    expect(parseQuarter('.5')).toBe(0.5);
    expect(parseQuarter(4)).toBe(4); // numeric input passes through
  });

  // Regression: these used to become 0 silently and trip "sum to zero".
  test('returns null for in-progress / blank / malformed strings (NOT 0)', () => {
    expect(parseQuarter('')).toBeNull();
    expect(parseQuarter('-')).toBeNull();
    expect(parseQuarter('.')).toBeNull();
    expect(parseQuarter('-.')).toBeNull();
    expect(parseQuarter(undefined)).toBeNull();
    expect(parseQuarter(null)).toBeNull();
    expect(parseQuarter(NaN)).toBeNull();
  });
});

describe('normalizeQuarterInput', () => {
  test('cleans up complete numbers', () => {
    expect(normalizeQuarterInput('1.')).toBe('1');
    expect(normalizeQuarterInput('-0')).toBe('0');
    expect(normalizeQuarterInput('.5')).toBe('0.5');
    expect(normalizeQuarterInput('-2')).toBe('-2');
    expect(normalizeQuarterInput('03')).toBe('3');
  });

  test('clears in-progress / malformed input to empty string', () => {
    expect(normalizeQuarterInput('-')).toBe('');
    expect(normalizeQuarterInput('.')).toBe('');
    expect(normalizeQuarterInput('')).toBe('');
  });
});

describe('flipSign — sign-toggle button', () => {
  // The headline feature: tap sign FIRST (arms negative), then type the amount.
  test('arms a negative from empty/zero so the next digits are negative', () => {
    expect(flipSign('')).toBe('-');
    expect(flipSign(undefined)).toBe('-');
    expect(flipSign('0')).toBe('-');
  });

  test('toggles back off when tapped again', () => {
    expect(flipSign('-')).toBe('');
  });

  test('flips the sign of a real number both ways', () => {
    expect(flipSign('3')).toBe('-3');
    expect(flipSign('-3')).toBe('3');
    expect(flipSign('0.5')).toBe('-0.5');
    expect(flipSign('-0.5')).toBe('0.5');
  });

  test('type-magnitude-then-arm-sign round trip yields a negative', () => {
    // user types "3", then taps the sign toggle
    expect(parseQuarter(flipSign('3'))).toBe(-3);
  });
});

describe('isNegativeInput', () => {
  test('detects negatives and the armed "-" state', () => {
    expect(isNegativeInput('-')).toBe(true);
    expect(isNegativeInput('-2')).toBe(true);
    expect(isNegativeInput(-2)).toBe(true);
    expect(isNegativeInput('')).toBe(false);
    expect(isNegativeInput('2')).toBe(false);
    expect(isNegativeInput(0)).toBe(false);
  });
});

// Mirrors the auto-balance + sum logic in useHoleSubmission's getEffectiveQuarters,
// proving that a half-typed "-" no longer silently zeroes a player.
describe('quarters auto-balance using parseQuarter', () => {
  const autoBalance = (players, quarters) => {
    const effective = { ...quarters };
    const entered = [];
    const empty = [];
    players.forEach((p) => {
      const n = parseQuarter(effective[p.id]);
      if (n === null) empty.push(p.id);
      else entered.push({ id: p.id, value: n });
    });
    if (empty.length === 1 && entered.length >= 1) {
      const sum = entered.reduce((acc, e) => acc + e.value, 0);
      effective[empty[0]] = String(-sum);
    }
    return effective;
  };

  const players = [{ id: 'a' }, { id: 'b' }, { id: 'c' }, { id: 'd' }];

  test('a lone half-typed "-" is treated as the empty slot and auto-filled', () => {
    const result = autoBalance(players, { a: '2', b: '1', c: '-1', d: '-' });
    expect(result.d).toBe('-2'); // -(2 + 1 - 1)
    const sum = players.reduce((s, p) => s + parseQuarter(result[p.id]), 0);
    expect(sum).toBe(0);
  });
});
