// frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx
import React from 'react';
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import StuartModePanel from '../StuartModePanel';

const theme = {
  colors: {
    primary: '#2196F3',
    accent: '#FFD700',
    paper: '#ffffff',
    backgroundSecondary: '#f5f5f5',
    border: '#e0e0e0',
    textPrimary: '#333',
    textSecondary: '#666',
  },
};

const stuart = { id: 'p1', name: 'Stuart', handicap: 15, is_authenticated: true };
const steve  = { id: 'p2', name: 'Steve',  handicap: 1,  is_authenticated: false };
const dan    = { id: 'p3', name: 'Dan',    handicap: 12, is_authenticated: false };

const baseProps = {
  players: [stuart, steve, dan],
  currentHole: 5,
  strokeAllocation: {
    p1: { 5: 1 },
    p2: { 5: 0 },
    p3: { 5: 0 },
  },
  playerStandings: {
    p1: { quarters: 0, name: 'Stuart' },
    p2: { quarters: 0, name: 'Steve' },
    p3: { quarters: 0, name: 'Dan' },
  },
  courseData: { holes: [{ hole_number: 5, handicap: 4 }] },
  currentWager: 2,
  theme,
};

test('renders Stuart Mode heading', () => {
  render(<StuartModePanel {...baseProps} />);
  expect(screen.getByText(/Stuart Mode/i)).toBeInTheDocument();
});

test('renders headline from insights', () => {
  render(<StuartModePanel {...baseProps} />);
  expect(screen.getByText(/Watch out for Steve/i)).toBeInTheDocument();
});

test('renders solo recommendation badge', () => {
  render(<StuartModePanel {...baseProps} />);
  expect(screen.getByTestId('solo-recommendation')).toBeInTheDocument();
});

test('renders a standings row for each player', () => {
  render(<StuartModePanel {...baseProps} />);
  expect(screen.getByTestId('standing-p1')).toBeInTheDocument();
  expect(screen.getByTestId('standing-p2')).toBeInTheDocument();
  expect(screen.getByTestId('standing-p3')).toBeInTheDocument();
});

test('shows hungry indicator for player who is down and high threat', () => {
  const props = {
    ...baseProps,
    playerStandings: {
      p1: { quarters: 5,  name: 'Stuart' },
      p2: { quarters: -5, name: 'Steve' },
      p3: { quarters: 0,  name: 'Dan' },
    },
  };
  render(<StuartModePanel {...props} />);
  expect(screen.getByTestId('hungry-p2')).toBeInTheDocument();
});

// ── Whisperer: proactive briefing ──────────────────────────────────────

describe('whisperer proactive briefing', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      json: async () => ({ data: { response: 'Hole 5: Watch Steve.' } }),
    });
  });

  test('calls /api/commissioner/chat on mount', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const [url] = global.fetch.mock.calls[0];
    expect(url).toMatch(/commissioner\/chat/);
  });

  test('sends briefing prompt for the current hole', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.message).toMatch(/strategic briefing for hole 5/i);
  });

  test('includes whisperer_mode and insights in game_state', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.game_state.whisperer_mode).toBe(true);
    expect(body.game_state.insights).toBeDefined();
    expect(Array.isArray(body.game_state.insights.threats)).toBe(true);
    expect(typeof body.game_state.insights.solo_recommendation).toBe('string');
  });

  test('includes conversation_history string in game_state', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(typeof body.game_state.conversation_history).toBe('string');
  });
});

// ── Whisperer: UI ──────────────────────────────────────────────────────

describe('whisperer UI', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      json: async () => ({ data: { response: 'Hole 5: Watch Steve.' } }),
    });
  });

  test('renders "Ask Commissioner" toggle header', () => {
    render(<StuartModePanel {...baseProps} />);
    expect(screen.getByText(/Ask Commissioner/i)).toBeInTheDocument();
  });

  test('drawer opens on briefing and shows message', async () => {
    render(<StuartModePanel {...baseProps} />);
    // Drawer opens immediately due to callCommissioner
    await waitFor(() =>
      expect(screen.getByTestId('whisperer-messages')).toBeInTheDocument()
    );
    // After briefing resolves: message appears
    await waitFor(() =>
      expect(screen.getByText('Hole 5: Watch Steve.')).toBeInTheDocument()
    );
  });

  test('renders whisperer response with 🤫 prefix', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() =>
      expect(screen.getByText('Hole 5: Watch Steve.')).toBeInTheDocument()
    );
    // The 🤫 emoji should be adjacent in the same message row
    const messages = screen.getByTestId('whisperer-messages');
    expect(messages.textContent).toContain('🤫');
  });

  test('toggle button collapses the open drawer', async () => {
    render(<StuartModePanel {...baseProps} />);
    // Wait for drawer to auto-open
    await waitFor(() =>
      expect(screen.getByTestId('whisperer-messages')).toBeInTheDocument()
    );
    // Click toggle to close
    await act(async () => {
      fireEvent.click(screen.getByTestId('whisperer-toggle'));
    });
    expect(screen.queryByTestId('whisperer-messages')).not.toBeInTheDocument();
  });

  test('user message appears with "You" label after send', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    const input = screen.getByPlaceholderText(/ask something/i);
    await act(async () => {
      fireEvent.change(input, { target: { value: 'Should I go solo?' } });
      fireEvent.click(screen.getByTestId('whisperer-send'));
    });

    expect(screen.getByText('Should I go solo?')).toBeInTheDocument();
    expect(screen.getByText('You')).toBeInTheDocument();
  });

  test('input is disabled while loading', async () => {
    global.fetch = jest.fn().mockReturnValue(new Promise(() => {})); // never resolves
    render(<StuartModePanel {...baseProps} />);
    const input = screen.getByPlaceholderText(/ask something/i);
    expect(input).toBeDisabled();
  });

  test('Enter key sends message', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    const input = screen.getByPlaceholderText(/ask something/i);
    await act(async () => {
      fireEvent.change(input, { target: { value: 'Double down?' } });
      fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    });

    await waitFor(() =>
      expect(screen.getByText('Double down?')).toBeInTheDocument()
    );
  });

  test('shows error message on API failure', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() =>
      expect(screen.getByText('Connection error — try again.')).toBeInTheDocument()
    );
  });
});
