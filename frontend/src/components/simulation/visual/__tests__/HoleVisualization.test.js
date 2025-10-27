// frontend/src/components/simulation/visual/__tests__/HoleVisualization.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import HoleVisualization from '../HoleVisualization';

describe('HoleVisualization', () => {
  const mockHole = {
    hole_number: 1,
    par: 4,
    yards: 380
  };

  const mockPlayers = [
    { id: 'human', name: 'You', is_human: true, position: 0 },
    { id: 'bot1', name: 'Alice', is_human: false, position: 100 },
    { id: 'bot2', name: 'Bob', is_human: false, position: 150 }
  ];

  test('renders SVG element', () => {
    render(<HoleVisualization hole={mockHole} players={mockPlayers} />);
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  test('displays hole number and par', () => {
    render(<HoleVisualization hole={mockHole} players={mockPlayers} />);
    expect(screen.getByText(/Hole 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Par 4/i)).toBeInTheDocument();
  });

  test('renders player dots', () => {
    render(<HoleVisualization hole={mockHole} players={mockPlayers} />);
    const svg = document.querySelector('svg');
    const circles = svg.querySelectorAll('circle');
    // Should have at least player dots (may have green circle too)
    expect(circles.length).toBeGreaterThanOrEqual(3);
  });

  test('highlights human player with border', () => {
    render(<HoleVisualization hole={mockHole} players={mockPlayers} />);
    const svg = document.querySelector('svg');
    const humanDot = Array.from(svg.querySelectorAll('circle')).find(
      circle => circle.getAttribute('stroke') === 'white'
    );
    expect(humanDot).toBeInTheDocument();
  });
});
