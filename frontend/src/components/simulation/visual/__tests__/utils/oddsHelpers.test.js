// frontend/src/components/simulation/visual/__tests__/utils/oddsHelpers.test.js
import {
  getProbabilityColor,
  formatExpectedValue,
  getRiskLevelColor,
  getProbabilityLabel
} from '../../utils/oddsHelpers';

describe('oddsHelpers', () => {
  describe('getProbabilityColor', () => {
    test('returns success for probability > 0.6', () => {
      expect(getProbabilityColor(0.7)).toBe('success');
      expect(getProbabilityColor(0.65)).toBe('success');
      expect(getProbabilityColor(1.0)).toBe('success');
    });

    test('returns warning for probability 0.4-0.6', () => {
      expect(getProbabilityColor(0.5)).toBe('warning');
      expect(getProbabilityColor(0.4)).toBe('warning');
      expect(getProbabilityColor(0.6)).toBe('warning');
    });

    test('returns disabled for probability < 0.4', () => {
      expect(getProbabilityColor(0.3)).toBe('disabled');
      expect(getProbabilityColor(0.1)).toBe('disabled');
      expect(getProbabilityColor(0)).toBe('disabled');
    });

    test('handles edge cases', () => {
      expect(getProbabilityColor(0.61)).toBe('success');
      expect(getProbabilityColor(0.39)).toBe('disabled');
    });
  });

  describe('formatExpectedValue', () => {
    test('adds + sign for positive numbers', () => {
      expect(formatExpectedValue(2.3)).toBe('+2.3');
      expect(formatExpectedValue(10.5)).toBe('+10.5');
      expect(formatExpectedValue(0.1)).toBe('+0.1');
    });

    test('preserves - sign for negative numbers', () => {
      expect(formatExpectedValue(-2.3)).toBe('-2.3');
      expect(formatExpectedValue(-10.5)).toBe('-10.5');
      expect(formatExpectedValue(-0.1)).toBe('-0.1');
    });

    test('adds + for zero', () => {
      expect(formatExpectedValue(0)).toBe('+0.0');
    });

    test('rounds to 1 decimal place', () => {
      expect(formatExpectedValue(2.34)).toBe('+2.3');
      expect(formatExpectedValue(2.36)).toBe('+2.4');
      expect(formatExpectedValue(-2.36)).toBe('-2.4');
    });
  });

  describe('getRiskLevelColor', () => {
    test('returns success for low risk', () => {
      expect(getRiskLevelColor('low')).toBe('success');
    });

    test('returns warning for medium risk', () => {
      expect(getRiskLevelColor('medium')).toBe('warning');
    });

    test('returns error for high risk', () => {
      expect(getRiskLevelColor('high')).toBe('error');
    });

    test('returns default for unknown risk level', () => {
      expect(getRiskLevelColor('unknown')).toBe('default');
      expect(getRiskLevelColor('')).toBe('default');
      expect(getRiskLevelColor(null)).toBe('default');
    });
  });

  describe('getProbabilityLabel', () => {
    test('returns "Likely" for probability > 0.6', () => {
      expect(getProbabilityLabel(0.7)).toBe('Likely');
      expect(getProbabilityLabel(0.65)).toBe('Likely');
      expect(getProbabilityLabel(1.0)).toBe('Likely');
    });

    test('returns "Possible" for probability 0.4-0.6', () => {
      expect(getProbabilityLabel(0.5)).toBe('Possible');
      expect(getProbabilityLabel(0.4)).toBe('Possible');
      expect(getProbabilityLabel(0.6)).toBe('Possible');
    });

    test('returns "Unlikely" for probability < 0.4', () => {
      expect(getProbabilityLabel(0.3)).toBe('Unlikely');
      expect(getProbabilityLabel(0.1)).toBe('Unlikely');
      expect(getProbabilityLabel(0)).toBe('Unlikely');
    });

    test('handles edge cases', () => {
      expect(getProbabilityLabel(0.61)).toBe('Likely');
      expect(getProbabilityLabel(0.39)).toBe('Unlikely');
    });
  });
});
