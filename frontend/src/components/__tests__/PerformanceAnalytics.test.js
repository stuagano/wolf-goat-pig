/**
 * Comprehensive test suite for PerformanceAnalytics component
 * 
 * Tests the performance analytics visualization system including:
 * - Analytics data loading and display
 * - Time range selection and filtering
 * - Chart rendering and visualization
 * - Performance metrics display
 * - Insights and recommendations
 * - Skill rating visualization
 * - Error handling and loading states
 * - Export functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Test utilities and providers
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context/GameProvider';

// Component under test
import PerformanceAnalytics from '../PerformanceAnalytics';

// Mock fetch globally
global.fetch = jest.fn();

// Mock UI components
jest.mock('../ui', () => ({
  Card: function MockCard({ children, className }) {
    return <div data-testid="card" className={className}>{children}</div>;
  }
}));

const mockTrendsData = {
  score_trend: [
    { date: '2024-01-01', value: 85 },
    { date: '2024-01-08', value: 82 },
    { date: '2024-01-15', value: 78 },
    { date: '2024-01-22', value: 80 },
    { date: '2024-01-29', value: 76 }
  ],
  earnings_trend: [
    { date: '2024-01-01', value: 10.50 },
    { date: '2024-01-08', value: 25.75 },
    { date: '2024-01-15', value: 45.20 },
    { date: '2024-01-22', value: 38.90 },
    { date: '2024-01-29', value: 55.30 }
  ],
  handicap_progression: [
    { date: '2024-01-01', value: 12.0 },
    { date: '2024-01-08', value: 11.5 },
    { date: '2024-01-15', value: 11.2 },
    { date: '2024-01-22', value: 10.8 },
    { date: '2024-01-29', value: 10.5 }
  ]
};

const mockMetricsData = {
  advanced_stats: {
    consistency_rating: 8.2,
    clutch_performance: 7.5,
    risk_tolerance: 6.8,
    strategic_adaptability: 8.9,
    pressure_handling: 7.2
  },
  comparative_stats: {
    vs_similar_handicap: {
      score_advantage: -2.1,
      earnings_ratio: 1.15,
      win_rate_difference: 0.08
    },
    vs_all_players: {
      percentile_rank: 72,
      skill_tier: 'advanced',
      improvement_rate: 0.12
    }
  },
  detailed_breakdown: {
    par3_average: 3.2,
    par4_average: 4.1,
    par5_average: 5.3,
    putting_average: 1.8,
    driving_accuracy: 0.68,
    greens_in_regulation: 0.45
  }
};

const mockInsightsData = {
  insights: [
    {
      type: 'improvement',
      title: 'Consistent Score Improvement',
      description: 'Your average score has improved by 9 strokes over the last 30 days',
      severity: 'positive',
      actionable: true,
      suggestions: ['Continue current practice routine', 'Focus on maintaining consistency']
    },
    {
      type: 'weakness',
      title: 'Par 5 Performance',
      description: 'Struggling with par 5 holes, averaging 0.8 strokes over par',
      severity: 'moderate',
      actionable: true,
      suggestions: ['Practice long iron shots', 'Work on course management for longer holes']
    },
    {
      type: 'strength',
      title: 'Putting Excellence',
      description: 'Putting performance in top 15% of all players',
      severity: 'positive',
      actionable: false,
      suggestions: ['Keep up excellent putting form', 'Help other players with putting tips']
    }
  ]
};

const mockSkillRatingData = {
  overall_rating: 1248,
  rating_history: [
    { date: '2024-01-01', rating: 1180 },
    { date: '2024-01-08', rating: 1195 },
    { date: '2024-01-15', rating: 1220 },
    { date: '2024-01-22', rating: 1235 },
    { date: '2024-01-29', rating: 1248 }
  ],
  skill_breakdown: {
    driving: { rating: 1200, percentile: 68 },
    approach: { rating: 1280, percentile: 75 },
    putting: { rating: 1320, percentile: 82 },
    strategy: { rating: 1190, percentile: 65 }
  },
  tier_info: {
    current_tier: 'Intermediate+',
    next_tier: 'Advanced',
    points_to_next: 152
  }
};

const TestWrapper = ({ children }) => (
  <ThemeProvider>
    <GameProvider>
      {children}
    </GameProvider>
  </ThemeProvider>
);

describe('PerformanceAnalytics', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  describe('Loading and Error States', () => {
    test('displays loading state initially', () => {
      // Mock pending fetch
      fetch.mockImplementation(() => new Promise(() => {}));

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      expect(screen.getByText(/Loading analytics/i)).toBeInTheDocument();
    });

    test('displays error state when API calls fail', async () => {
      fetch.mockRejectedValue(new Error('Network error'));

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Failed to load analytics data/)).toBeInTheDocument();
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });
    });

    test('displays retry button on error', async () => {
      const user = userEvent.setup();

      // First call fails
      fetch.mockRejectedValueOnce(new Error('Network error'));
      
      // Second call succeeds
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockTrendsData
      });

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Retry')).toBeInTheDocument();
      });

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.queryByText(/Failed to load analytics/)).not.toBeInTheDocument();
      });
    });

    test('does not load data when playerId is not provided', () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerName="No Player" />
        </TestWrapper>
      );

      expect(fetch).not.toHaveBeenCalled();
      expect(screen.getByText(/Please select a player/)).toBeInTheDocument();
    });
  });

  describe('Data Loading and API Integration', () => {
    test('makes correct API calls on mount', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({})
      });

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" timeRange={30} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(4);
      });

      expect(fetch).toHaveBeenCalledWith('/api/players/player1/trends?days=30');
      expect(fetch).toHaveBeenCalledWith('/api/players/player1/advanced-metrics');
      expect(fetch).toHaveBeenCalledWith('/api/players/player1/insights');
      expect(fetch).toHaveBeenCalledWith('/api/players/player1/skill-rating');
    });

    test('reloads data when playerId changes', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => ({})
      });

      const { rerender } = render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(4);
      });

      fetch.mockClear();

      rerender(
        <TestWrapper>
          <PerformanceAnalytics playerId="player2" playerName="Bob" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(4);
      });

      expect(fetch).toHaveBeenCalledWith('/api/players/player2/trends?days=30');
    });

    test('reloads data when time range changes', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockTrendsData
      });

      const { rerender } = render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice" timeRange={30} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players/player1/trends?days=30');
      });

      fetch.mockClear();

      rerender(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice" timeRange={90} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players/player1/trends?days=90');
      });
    });

    test('handles partial API failures gracefully', async () => {
      // Some APIs succeed, others fail
      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockTrendsData })
        .mockRejectedValueOnce(new Error('Metrics failed'))
        .mockResolvedValueOnce({ ok: true, json: async () => mockInsightsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockSkillRatingData });

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        // Should display available data despite some failures
        expect(screen.getByText('Performance Trends')).toBeInTheDocument();
        expect(screen.getByText('Insights & Recommendations')).toBeInTheDocument();
      });

      // Should show error for failed sections
      expect(screen.getByText(/Some analytics data could not be loaded/)).toBeInTheDocument();
    });
  });

  describe('Performance Trends Display', () => {
    beforeEach(async () => {
      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockTrendsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockMetricsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockInsightsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockSkillRatingData });
    });

    test('displays trend charts', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Performance Trends')).toBeInTheDocument();
        expect(screen.getByText('Score Trend')).toBeInTheDocument();
        expect(screen.getByText('Earnings Trend')).toBeInTheDocument();
        expect(screen.getByText('Handicap Progression')).toBeInTheDocument();
      });
    });

    test('renders SVG charts with correct data points', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        const svgElements = screen.getAllByRole('img', { hidden: true }); // SVG elements
        expect(svgElements.length).toBeGreaterThan(0);
      });

      // Check for SVG polyline elements (trend lines)
      const container = screen.getByTestId('trends-container');
      const polylines = container.querySelectorAll('polyline');
      expect(polylines.length).toBeGreaterThanOrEqual(3); // At least 3 trend lines
    });

    test('displays no data message when trends are empty', async () => {
      const emptyTrendsData = {
        score_trend: [],
        earnings_trend: [],
        handicap_progression: []
      };

      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => emptyTrendsData })
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
        .mockResolvedValueOnce({ ok: true, json: async () => ({ insights: [] }) })
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) });

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/No data available for Score Trend/)).toBeInTheDocument();
        expect(screen.getByText(/No data available for Earnings Trend/)).toBeInTheDocument();
        expect(screen.getByText(/No data available for Handicap Progression/)).toBeInTheDocument();
      });
    });
  });

  describe('Time Range Selection', () => {
    beforeEach(async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockTrendsData
      });
    });

    test('displays time range selector', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Time Range:')).toBeInTheDocument();
      });

      // Should have options for different time ranges
      expect(screen.getByText('7 days')).toBeInTheDocument();
      expect(screen.getByText('30 days')).toBeInTheDocument();
      expect(screen.getByText('90 days')).toBeInTheDocument();
      expect(screen.getByText('1 year')).toBeInTheDocument();
    });

    test('changes time range and reloads data', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" timeRange={30} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players/player1/trends?days=30');
      });

      fetch.mockClear();
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockTrendsData
      });

      const sevenDaysOption = screen.getByText('7 days');
      await user.click(sevenDaysOption);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players/player1/trends?days=7');
      });
    });

    test('highlights selected time range', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" timeRange={30} />
        </TestWrapper>
      );

      await waitFor(() => {
        const thirtyDaysOption = screen.getByText('30 days');
        expect(thirtyDaysOption).toHaveClass('selected', 'active'); // Assuming these classes
      });

      const ninetyDaysOption = screen.getByText('90 days');
      await user.click(ninetyDaysOption);

      expect(ninetyDaysOption).toHaveClass('selected', 'active');
      expect(screen.getByText('30 days')).not.toHaveClass('selected', 'active');
    });
  });

  describe('Advanced Metrics Display', () => {
    beforeEach(async () => {
      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockTrendsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockMetricsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockInsightsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockSkillRatingData });
    });

    test('displays advanced statistics', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Advanced Metrics')).toBeInTheDocument();
        expect(screen.getByText('8.2')).toBeInTheDocument(); // Consistency rating
        expect(screen.getByText('7.5')).toBeInTheDocument(); // Clutch performance
        expect(screen.getByText('8.9')).toBeInTheDocument(); // Strategic adaptability
      });
    });

    test('displays comparative statistics', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Comparative Analysis')).toBeInTheDocument();
        expect(screen.getByText(/vs similar handicap/i)).toBeInTheDocument();
        expect(screen.getByText('72nd percentile')).toBeInTheDocument();
        expect(screen.getByText('Advanced tier')).toBeInTheDocument();
      });
    });

    test('displays detailed golf statistics breakdown', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Detailed Breakdown')).toBeInTheDocument();
        expect(screen.getByText('Par 3 Average: 3.2')).toBeInTheDocument();
        expect(screen.getByText('Par 4 Average: 4.1')).toBeInTheDocument();
        expect(screen.getByText('Par 5 Average: 5.3')).toBeInTheDocument();
        expect(screen.getByText('68%')).toBeInTheDocument(); // Driving accuracy
        expect(screen.getByText('45%')).toBeInTheDocument(); // GIR
      });
    });

    test('handles missing metrics data gracefully', async () => {
      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockTrendsData })
        .mockResolvedValueOnce({ ok: true, json: async () => ({}) }) // Empty metrics
        .mockResolvedValueOnce({ ok: true, json: async () => mockInsightsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockSkillRatingData });

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Advanced metrics not available/)).toBeInTheDocument();
      });
    });
  });

  describe('Insights and Recommendations', () => {
    beforeEach(async () => {
      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockTrendsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockMetricsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockInsightsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockSkillRatingData });
    });

    test('displays insights with correct categories', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Insights & Recommendations')).toBeInTheDocument();
        expect(screen.getByText('Consistent Score Improvement')).toBeInTheDocument();
        expect(screen.getByText('Par 5 Performance')).toBeInTheDocument();
        expect(screen.getByText('Putting Excellence')).toBeInTheDocument();
      });
    });

    test('displays insight details and suggestions', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Your average score has improved by 9 strokes/)).toBeInTheDocument();
        expect(screen.getByText(/Continue current practice routine/)).toBeInTheDocument();
        expect(screen.getByText(/Practice long iron shots/)).toBeInTheDocument();
        expect(screen.getByText(/Putting performance in top 15%/)).toBeInTheDocument();
      });
    });

    test('categorizes insights by type with visual indicators', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        // Should have visual indicators for different insight types
        expect(screen.getByText('📈')).toBeInTheDocument(); // Improvement icon
        expect(screen.getByText('⚠️')).toBeInTheDocument(); // Weakness icon
        expect(screen.getByText('🎯')).toBeInTheDocument(); // Strength icon
      });
    });

    test('expands and collapses insight details', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Consistent Score Improvement')).toBeInTheDocument();
      });

      // Click to expand
      const insightTitle = screen.getByText('Consistent Score Improvement');
      await user.click(insightTitle);

      expect(screen.getByText(/Focus on maintaining consistency/)).toBeInTheDocument();

      // Click to collapse
      await user.click(insightTitle);

      expect(screen.queryByText(/Focus on maintaining consistency/)).not.toBeVisible();
    });
  });

  describe('Skill Rating Display', () => {
    beforeEach(async () => {
      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockTrendsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockMetricsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockInsightsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockSkillRatingData });
    });

    test('displays overall skill rating', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Skill Rating')).toBeInTheDocument();
        expect(screen.getByText('1248')).toBeInTheDocument(); // Overall rating
        expect(screen.getByText('Intermediate+')).toBeInTheDocument(); // Current tier
        expect(screen.getByText(/152 points to Advanced/)).toBeInTheDocument();
      });
    });

    test('displays skill breakdown by category', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Driving: 1200')).toBeInTheDocument();
        expect(screen.getByText('Approach: 1280')).toBeInTheDocument();
        expect(screen.getByText('Putting: 1320')).toBeInTheDocument();
        expect(screen.getByText('Strategy: 1190')).toBeInTheDocument();
      });
    });

    test('displays percentile rankings', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('68th percentile')).toBeInTheDocument(); // Driving
        expect(screen.getByText('82nd percentile')).toBeInTheDocument(); // Putting
      });
    });

    test('displays rating history chart', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Rating History')).toBeInTheDocument();
      });

      const ratingChart = screen.getByTestId('rating-history-chart');
      expect(ratingChart).toBeInTheDocument();
      
      // Should contain SVG elements for the chart
      const polylines = ratingChart.querySelectorAll('polyline');
      expect(polylines.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Export Functionality', () => {
    beforeEach(async () => {
      // Mock all successful API responses
      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => mockTrendsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockMetricsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockInsightsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockSkillRatingData });

      // Mock DOM methods for export
      global.URL.createObjectURL = jest.fn(() => 'mock-blob-url');
      global.URL.revokeObjectURL = jest.fn();
      
      const mockLink = {
        href: '',
        download: '',
        click: jest.fn()
      };
      
      document.createElement = jest.fn(() => mockLink);
      document.body.appendChild = jest.fn();
      document.body.removeChild = jest.fn();
    });

    test('displays export button', async () => {
      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Export Analytics')).toBeInTheDocument();
      });
    });

    test('exports analytics data as JSON', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Export Analytics')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export Analytics');
      await user.click(exportButton);

      expect(global.URL.createObjectURL).toHaveBeenCalled();
      expect(document.createElement).toHaveBeenCalledWith('a');
      expect(document.body.appendChild).toHaveBeenCalled();
      expect(document.body.removeChild).toHaveBeenCalled();
    });

    test('generates correct filename for export', async () => {
      const user = userEvent.setup();
      let capturedLink;

      document.createElement = jest.fn(() => {
        capturedLink = {
          href: '',
          download: '',
          click: jest.fn()
        };
        return capturedLink;
      });

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Export Analytics')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export Analytics');
      await user.click(exportButton);

      expect(capturedLink.download).toMatch(/^alice-johnson-analytics-\d{4}-\d{2}-\d{2}\.json$/i);
    });

    test('handles export errors gracefully', async () => {
      const user = userEvent.setup();

      // Mock URL.createObjectURL to throw error
      global.URL.createObjectURL = jest.fn(() => {
        throw new Error('Export failed');
      });

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Export Analytics')).toBeInTheDocument();
      });

      const exportButton = screen.getByText('Export Analytics');
      await user.click(exportButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to export analytics data/)).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design and Performance', () => {
    test('adapts to different screen sizes', () => {
      // Mock window.innerWidth
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768, // Tablet size
      });

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      const dashboard = screen.getByTestId('analytics-dashboard');
      expect(dashboard).toHaveClass('responsive', 'tablet'); // Assuming responsive classes
    });

    test('renders efficiently with large datasets', async () => {
      // Create large dataset
      const largeTrendsData = {
        score_trend: Array.from({ length: 365 }, (_, i) => ({
          date: new Date(2024, 0, i + 1).toISOString().split('T')[0],
          value: 80 + Math.random() * 10
        })),
        earnings_trend: Array.from({ length: 365 }, (_, i) => ({
          date: new Date(2024, 0, i + 1).toISOString().split('T')[0],
          value: Math.random() * 100
        })),
        handicap_progression: Array.from({ length: 365 }, (_, i) => ({
          date: new Date(2024, 0, i + 1).toISOString().split('T')[0],
          value: 15 - (i / 365) * 5
        }))
      };

      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => largeTrendsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockMetricsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockInsightsData })
        .mockResolvedValueOnce({ ok: true, json: async () => mockSkillRatingData });

      const start = performance.now();

      render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Performance Trends')).toBeInTheDocument();
      });

      const end = performance.now();

      // Should render large dataset efficiently (under 1 second)
      expect(end - start).toBeLessThan(1000);
    });

    test('handles concurrent data updates without race conditions', async () => {
      const { rerender } = render(
        <TestWrapper>
          <PerformanceAnalytics playerId="player1" playerName="Alice Johnson" />
        </TestWrapper>
      );

      // Simulate rapid prop changes
      for (let i = 0; i < 5; i++) {
        rerender(
          <TestWrapper>
            <PerformanceAnalytics playerId={`player${i}`} playerName={`Player ${i}`} />
          </TestWrapper>
        );
      }

      // Should not cause errors or inconsistent state
      await waitFor(() => {
        expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });
    });
  });
});