// frontend/src/components/simulation/visual/__tests__/ProbabilityBar.test.js
import React from 'react';
import { render } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProbabilityBar from '../ProbabilityBar';

describe('ProbabilityBar', () => {
  test('renders 8 dots', () => {
    const { container } = render(<ProbabilityBar value={0.5} />);
    const dots = container.querySelectorAll('.probability-dot');
    expect(dots).toHaveLength(8);
  });

  test('fills 0 dots when value is 0', () => {
    const { container } = render(<ProbabilityBar value={0} />);
    const filledDots = container.querySelectorAll('.probability-dot.filled');
    expect(filledDots).toHaveLength(0);
  });

  test('fills all 8 dots when value is 1', () => {
    const { container } = render(<ProbabilityBar value={1} />);
    const filledDots = container.querySelectorAll('.probability-dot.filled');
    expect(filledDots).toHaveLength(8);
  });

  test('fills 5 dots when value is 0.65', () => {
    const { container } = render(<ProbabilityBar value={0.65} />);
    const filledDots = container.querySelectorAll('.probability-dot.filled');
    // 0.65 * 8 = 5.2, rounds to 5
    expect(filledDots).toHaveLength(5);
  });

  test('fills 4 dots when value is 0.5', () => {
    const { container } = render(<ProbabilityBar value={0.5} />);
    const filledDots = container.querySelectorAll('.probability-dot.filled');
    expect(filledDots).toHaveLength(4);
  });

  test('fills 1 dot when value is 0.1', () => {
    const { container } = render(<ProbabilityBar value={0.1} />);
    const filledDots = container.querySelectorAll('.probability-dot.filled');
    // 0.1 * 8 = 0.8, rounds to 1
    expect(filledDots).toHaveLength(1);
  });

  test('handles negative values gracefully (clamps to 0)', () => {
    const { container } = render(<ProbabilityBar value={-0.5} />);
    const filledDots = container.querySelectorAll('.probability-dot.filled');
    expect(filledDots).toHaveLength(0);
  });

  test('handles values > 1 gracefully (clamps to 1)', () => {
    const { container } = render(<ProbabilityBar value={1.5} />);
    const filledDots = container.querySelectorAll('.probability-dot.filled');
    expect(filledDots).toHaveLength(8);
  });

  test('renders with probability-bar class', () => {
    const { container } = render(<ProbabilityBar value={0.5} />);
    const bar = container.querySelector('.probability-bar');
    expect(bar).toBeInTheDocument();
  });

  test('all dots have probability-dot class', () => {
    const { container } = render(<ProbabilityBar value={0.5} />);
    const dots = container.querySelectorAll('.probability-dot');
    dots.forEach(dot => {
      expect(dot).toHaveClass('probability-dot');
    });
  });

  test('filled dots come first in sequence', () => {
    const { container } = render(<ProbabilityBar value={0.375} />); // 3 dots
    const dots = container.querySelectorAll('.probability-dot');

    // First 3 should be filled
    expect(dots[0]).toHaveClass('filled');
    expect(dots[1]).toHaveClass('filled');
    expect(dots[2]).toHaveClass('filled');

    // Last 5 should not be filled
    expect(dots[3]).not.toHaveClass('filled');
    expect(dots[4]).not.toHaveClass('filled');
    expect(dots[5]).not.toHaveClass('filled');
    expect(dots[6]).not.toHaveClass('filled');
    expect(dots[7]).not.toHaveClass('filled');
  });
});
