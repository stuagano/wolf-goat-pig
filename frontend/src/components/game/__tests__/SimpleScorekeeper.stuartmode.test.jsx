// Characterization tests for Stuart Mode — pinned BEFORE extracting the
// Stuart effects into useStuartMode, so the extraction can prove it changed
// nothing. Covers: toggle render, phase strip render, and the tee-phase AI
// captain decision (an aiMoves entry appears after the 800ms timer).
import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import SimpleScorekeeper from '../SimpleScorekeeper';

// Same mock set as SimpleScorekeeper.betting.test.jsx
vi.mock('../../../theme/Provider', async () => {
  const factories = await import('../../../test-utils/mockFactories');
  return {
    ThemeProvider: ({ children }) => <div>{children}</div>,
    useTheme: () =>
      factories.createMockTheme({
        colors: {
          primary: '#059669',
          textPrimary: '#1f2937',
          textSecondary: '#6b7280',
          border: '#d1d5db',
          paper: '#ffffff',
          backgroundSecondary: '#f3f4f6',
        },
      }),
  };
});

vi.mock('../../ui', () => ({
  Input: function Input({ value, onChange, inputStyle, ...props }) {
    return <input value={value} onChange={onChange} style={inputStyle} {...props} />;
  },
}));

vi.mock('../Scorecard', () => ({
  default: function MockScorecard() {
    return <div data-testid="mock-scorecard">Scorecard</div>;
  },
}));

vi.mock('../GameCompletionView', () => ({
  default: function MockGameCompletionView() {
    return <div data-testid="mock-game-completion">Game Complete</div>;
  },
}));

vi.mock('../BadgeNotification', () => ({
  triggerBadgeNotification: vi.fn(),
}));

const PLAYERS = [
  { id: 'p1', name: 'Bot Alice', handicap: 10, is_authenticated: false },
  { id: 'p2', name: 'Bot Alice', handicap: 12, is_authenticated: false },
  { id: 'p3', name: 'Bot Bob', handicap: 14, is_authenticated: false },
  { id: 'p4', name: 'Bot Carol', handicap: 16, is_authenticated: false },
];

const renderScorekeeper = () =>
  render(
    <SimpleScorekeeper
      gameId="stuart-test-game"
      players={PLAYERS}
      baseWager={1}
      initialHoleHistory={[]}
      initialCurrentHole={1}
    />,
  );

describe('Stuart Mode characterization', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('toggle renders and is OFF by default (no phase strip)', () => {
    renderScorekeeper();
    expect(screen.getByTestId('stuart-mode-toggle')).toBeInTheDocument();
    expect(screen.queryByTestId('hole-phase-strip')).not.toBeInTheDocument();
  });

  test('with wgp_stuart_mode=true the phase strip renders', () => {
    localStorage.setItem('wgp_stuart_mode', 'true');
    renderScorekeeper();
    expect(screen.getByTestId('hole-phase-strip')).toBeInTheDocument();
  });

  test('a new ghost game resolves to Auto even after a prior Coach session', () => {
    // Regression: CreateGamePage writes wgp_assist_mode='auto' for ghost games.
    // Without that, a stale 'coach' from a real round would shadow the legacy
    // boolean and the ghosts would silently stop auto-playing.
    localStorage.setItem('wgp_assist_mode', 'auto');
    localStorage.setItem('wgp_stuart_mode', 'true');
    renderScorekeeper();
    expect(screen.getByTestId('hole-phase-strip')).toBeInTheDocument();
  });

  test('Coach mode shows the strategy panel but does NOT auto-play (no phase strip)', () => {
    // Real round: everyone scores themselves, but tips still show.
    localStorage.setItem('wgp_assist_mode', 'coach');
    renderScorekeeper();
    // Strategy panel is present (whisperer lives inside it)...
    expect(screen.getByTestId('whisperer-toggle')).toBeInTheDocument();
    // ...but the AI hole-phase strip (auto-play UI) is not.
    expect(screen.queryByTestId('hole-phase-strip')).not.toBeInTheDocument();
  });

  test('tee phase: AI captain decision produces an aiMoves log entry', async () => {
    localStorage.setItem('wgp_stuart_mode', 'true');
    vi.useFakeTimers();
    try {
      renderScorekeeper();
      // AI captain effect schedules its move 800ms after mount (tee phase)
      await act(async () => {
        vi.advanceTimersByTime(1200);
      });
    } finally {
      vi.useRealTimers();
    }
    // Either "calls solo before tee" or "waits to see tee shots" — both
    // are logged with the robot emoji
    await waitFor(() => {
      expect(screen.getAllByText(/🤖/).length).toBeGreaterThan(0);
    });
  });
});
