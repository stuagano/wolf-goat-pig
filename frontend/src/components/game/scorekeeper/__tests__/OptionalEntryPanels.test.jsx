// frontend/src/components/game/scorekeeper/__tests__/OptionalEntryPanels.test.jsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '../../../../theme/Provider';
import OptionalEntryPanels from '../OptionalEntryPanels';

// Mock CommissionerChat so the panel can render in isolation (it pulls in
// network/config when mounted). We never expand the Commissioner panel here.
vi.mock('../../CommissionerChat', () => ({
  default: () => <div data-testid="commissioner-chat" />,
}));

const theme = {
  colors: {
    primary: '#2196F3',
    paper: '#ffffff',
    backgroundSecondary: '#f5f5f5',
    border: '#e0e0e0',
    textPrimary: '#333',
    textSecondary: '#666',
    inputBackground: '#fff',
  },
};

const players = [
  { id: 'p1', name: 'Stuart', handicap: 15 },
  { id: 'p2', name: 'Steve', handicap: 1 },
];

const baseProps = {
  theme,
  players,
  scores: {},
  handleScoreChange: vi.fn(),
  currentHole: 1,
  playerStandings: {},
  holeNotes: '',
  setHoleNotes: vi.fn(),
  showGolfScores: true, // expanded — this is the path that crashed
  setShowGolfScores: vi.fn(),
  showCommissioner: false,
  setShowCommissioner: vi.fn(),
  showNotes: false,
  setShowNotes: vi.fn(),
};

const renderPanels = (props = {}) =>
  render(
    <ThemeProvider>
      <OptionalEntryPanels {...baseProps} {...props} />
    </ThemeProvider>,
  );

describe('OptionalEntryPanels — golf score entry', () => {
  // Regression: OptionalEntryPanels rendered <Input> without importing it.
  // Expanding the Golf Scores panel made Input undefined -> render crash
  // ("Element type is invalid"). Players hit this when entering golf scores
  // live, so they could only persist quarters then edit scores via the modal.
  test('renders a score Input per player when the Golf Scores panel is expanded', () => {
    renderPanels();
    expect(screen.getByTestId('score-input-p1')).toBeInTheDocument();
    expect(screen.getByTestId('score-input-p2')).toBeInTheDocument();
  });

  test('typing a strokes value calls handleScoreChange with the player id', () => {
    const handleScoreChange = vi.fn();
    renderPanels({ handleScoreChange });
    fireEvent.change(screen.getByTestId('score-input-p1'), {
      target: { value: '4' },
    });
    expect(handleScoreChange).toHaveBeenCalledWith('p1', '4');
  });
});
