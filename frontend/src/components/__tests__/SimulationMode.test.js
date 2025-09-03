/**
 * SimulationMode Component Tests
 * Tests the golf simulation mode functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { SimulationMode } from '../simulation';
import { ThemeProvider } from '../../theme/Provider';

// Mock API calls
global.fetch = jest.fn();

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      {children}
    </ThemeProvider>
  </BrowserRouter>
);

describe('SimulationMode', () => {
  beforeEach(() => {
    fetch.mockClear();
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        simulation_results: {
          outcomes: [],
          probabilities: {},
          recommendations: []
        }
      }),
    });
  });

  test('renders simulation mode interface', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    expect(screen.getByText(/simulation/i)).toBeInTheDocument();
  });

  test('displays hole selection controls', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should have hole selection
    expect(screen.getByText(/hole/i)).toBeInTheDocument();
    expect(screen.getByRole('button') || screen.getByRole('combobox')).toBeInTheDocument();
  });

  test('shows player configuration options', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should have player setup
    expect(screen.getByText(/players/i)).toBeInTheDocument();
  });

  test('displays course conditions settings', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should have course condition controls
    expect(screen.getByText(/conditions/i) || screen.getByText(/weather/i) || screen.getByText(/wind/i)).toBeInTheDocument();
  });

  test('runs simulation when requested', async () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    const runButton = screen.getByRole('button', { name: /run.*simulation/i });
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/simulation'),
        expect.any(Object)
      );
    });
  });

  test('displays simulation results', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        outcomes: [
          { player: 'Player 1', score: -1 },
          { player: 'Player 2', score: 0 }
        ],
        probabilities: { wolf_win: 0.6, goat_win: 0.4 }
      }),
    });

    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    const runButton = screen.getByRole('button', { name: /run.*simulation/i });
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(screen.getByText(/results/i)).toBeInTheDocument();
    });
  });

  test('shows probability calculations', async () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    const runButton = screen.getByRole('button', { name: /run.*simulation/i });
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(screen.getByText(/probability/i) || screen.getByText(/%/)).toBeInTheDocument();
    });
  });

  test('displays shot visualization', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should have shot visualization elements
    expect(screen.getByText(/visualization/i) || screen.getByRole('img')).toBeInTheDocument();
  });

  test('handles different game modes', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should support different WGP modes
    expect(screen.getByText(/wolf/i) || screen.getByText(/goat/i) || screen.getByText(/pig/i)).toBeInTheDocument();
  });

  test('allows parameter adjustment', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should have adjustable parameters
    const sliders = screen.getAllByRole('slider');
    expect(sliders.length).toBeGreaterThan(0);
  });

  test('shows Monte Carlo iteration controls', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should have iteration settings
    expect(screen.getByText(/iterations/i) || screen.getByText(/monte carlo/i)).toBeInTheDocument();
  });

  test('displays statistical analysis', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should show statistical data
    expect(screen.getByText(/statistics/i) || screen.getByText(/average/i) || screen.getByText(/mean/i)).toBeInTheDocument();
  });

  test('handles simulation errors gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('Simulation failed'));

    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    const runButton = screen.getByRole('button', { name: /run.*simulation/i });
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  test('shows loading state during simulation', () => {
    fetch.mockImplementationOnce(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    const runButton = screen.getByRole('button', { name: /run.*simulation/i });
    fireEvent.click(runButton);

    expect(screen.getByText(/running/i) || screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('exports simulation results', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should have export functionality
    expect(screen.getByText(/export/i) || screen.getByText(/download/i)).toBeInTheDocument();
  });

  test('saves simulation configurations', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should be able to save/load configurations
    expect(screen.getByText(/save/i) || screen.getByText(/preset/i)).toBeInTheDocument();
  });

  test('displays hole-specific information', () => {
    render(
      <TestWrapper>
        <SimulationMode />
      </TestWrapper>
    );

    // Should show hole details
    expect(screen.getByText(/par/i) || screen.getByText(/yards/i) || screen.getByText(/handicap/i)).toBeInTheDocument();
  });

  test('renders without crashing', () => {
    expect(() => {
      render(
        <TestWrapper>
          <SimulationMode />
        </TestWrapper>
      );
    }).not.toThrow();
  });
});