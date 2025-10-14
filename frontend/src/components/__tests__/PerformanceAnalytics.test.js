import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import PerformanceAnalytics from '../PerformanceAnalytics';

global.fetch = jest.fn();

const trendsResponse = {
  trends: {
    position: [
      { timestamp: '2024-01-01T00:00:00Z', value: 1 },
      { timestamp: '2024-01-08T00:00:00Z', value: 2 }
    ],
    scoring: [
      { timestamp: '2024-01-01T00:00:00Z', value: 72 },
      { timestamp: '2024-01-08T00:00:00Z', value: 74 }
    ],
    putting: [
      { timestamp: '2024-01-01T00:00:00Z', value: 30 },
      { timestamp: '2024-01-08T00:00:00Z', value: 28 }
    ]
  }
};

const metricsResponse = {
  metrics: {
    scoringAverage: {
      name: 'Scoring Average',
      value: 73.2,
      change: 'improving'
    }
  }
};

const insightsResponse = {
  insights: [
    {
      title: 'Consistency',
      description: 'Back-to-back rounds under par',
      priority: 'medium'
    }
  ]
};

const ratingResponse = {
  skill_rating: {
    overall: 1240,
    confidence: 0.82,
    games_played: 12,
    win_component: 40,
    earnings_component: 30,
    betting_component: 25,
    partnership_component: 15
  }
};

const mockFetchSuccess = () => {
  fetch.mockImplementation((url) => {
    if (url.includes('trends')) {
      return Promise.resolve({ ok: true, json: async () => trendsResponse });
    }
    if (url.includes('advanced-metrics')) {
      return Promise.resolve({ ok: true, json: async () => metricsResponse });
    }
    if (url.includes('insights')) {
      return Promise.resolve({ ok: true, json: async () => insightsResponse });
    }
    if (url.includes('skill-rating')) {
      return Promise.resolve({ ok: true, json: async () => ratingResponse });
    }
    return Promise.resolve({ ok: true, json: async () => ({}) });
  });
};

describe('PerformanceAnalytics', () => {
  beforeEach(() => {
    fetch.mockReset();
  });

  test('renders analytics after data load', async () => {
    mockFetchSuccess();

    render(<PerformanceAnalytics playerId="player-1" playerName="Alice" />);

    expect(await screen.findByText('Scoring Average')).toBeInTheDocument();
    expect(screen.getByText('Skill Rating')).toBeInTheDocument();
  });

  test('shows error card when fetch fails', async () => {
    fetch.mockImplementation(() => Promise.reject(new Error('Network error')));

    render(<PerformanceAnalytics playerId="player-1" playerName="Alice" />);

    expect(
      await screen.findByText('Error Loading Analytics')
    ).toBeInTheDocument();
  });

  test('displays loading indicator while fetching', () => {
    fetch.mockImplementation(() => new Promise(() => {}));

    render(<PerformanceAnalytics playerId="player-1" playerName="Alice" />);

    expect(screen.getByText('Loading performance analytics...')).toBeInTheDocument();
  });
});
