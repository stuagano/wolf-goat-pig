import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import GameSetup from '../GameSetup';

const mockCourses = {
  Augusta: {
    name: 'Augusta',
    holes: Array.from({ length: 18 }, (_, i) => ({
      hole_number: i + 1,
      par: 4,
      yards: 420,
      stroke_index: i + 1,
    })),
    total_par: 72,
    total_yards: 7560,
    hole_count: 18,
  },
};

const makeDefaultProps = () => ({
  humanPlayer: { id: 'human', name: '', handicap: '18', is_human: true },
  setHumanPlayer: jest.fn(),
  computerPlayers: [
    { id: 'comp1', name: '', handicap: '', personality: '', is_human: false },
    { id: 'comp2', name: '', handicap: '', personality: '', is_human: false },
    { id: 'comp3', name: '', handicap: '', personality: '', is_human: false },
  ],
  setComputerPlayers: jest.fn(),
  selectedCourse: null,
  setSelectedCourse: jest.fn(),
  courses: mockCourses,
  setCourses: jest.fn(),
  personalities: [],
  setPersonalities: jest.fn(),
  suggestedOpponents: [
    { name: 'Aggressive Bot', handicap: '10', personality: 'aggressive' },
  ],
  setSuggestedOpponents: jest.fn(),
  onStartGame: jest.fn(),
});

describe('GameSetup', () => {
  const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => undefined);

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch.mockImplementation((url) => {
      if (url.includes('/courses')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockCourses),
        });
      }
      if (url.includes('/personalities') || url.includes('/suggested')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([]),
      });
    });
  });

  afterAll(() => {
    alertSpy.mockRestore();
  });

  test('renders human player details section', () => {
    const props = makeDefaultProps();
    render(<GameSetup {...props} />);

    expect(screen.getByLabelText(/your name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/your handicap/i)).toBeInTheDocument();
    const lookupButtons = screen.getAllByRole('button', { name: /lookup ghin handicap/i });
    expect(lookupButtons.length).toBeGreaterThan(0);
  });

  test('updates human player name via setter', () => {
    const props = makeDefaultProps();
    render(<GameSetup {...props} />);

    fireEvent.change(screen.getByLabelText(/your name/i), { target: { value: 'Jane Player' } });
    expect(props.setHumanPlayer).toHaveBeenCalledWith(expect.objectContaining({ name: 'Jane Player' }));
  });

  test('opens ghin lookup panel for human player', () => {
    const props = makeDefaultProps();
    render(<GameSetup {...props} />);

    const lookupButtons = screen.getAllByRole('button', { name: /lookup ghin handicap/i });
    fireEvent.click(lookupButtons[0]);
    expect(screen.getByText(/ghin handicap lookup/i)).toBeInTheDocument();
  });

  test('invokes quick opponent loader when suggested opponent clicked', () => {
    const props = makeDefaultProps();
    render(<GameSetup {...props} />);

    const quickSelectButtons = screen.getAllByRole('button', { name: /aggressive bot/i });
    fireEvent.click(quickSelectButtons[0]);
    expect(props.setComputerPlayers).toHaveBeenCalled();
  });

  test('validates required data before starting game', () => {
    const props = makeDefaultProps();
    render(<GameSetup {...props} />);

    fireEvent.click(screen.getByRole('button', { name: /start simulation/i }));
    expect(alertSpy).toHaveBeenCalled();
    expect(props.onStartGame).not.toHaveBeenCalled();
  });

  test('submits when configuration is complete', async () => {
    const props = makeDefaultProps();
    props.humanPlayer.name = 'Human Player';
    props.computerPlayers = props.computerPlayers.map((player, idx) => ({
      ...player,
      name: `CPU ${idx + 1}`,
      handicap: '12',
    }));
    props.selectedCourse = 'Augusta';

    render(<GameSetup {...props} />);

    const startButton = screen.getByRole('button', { name: /start simulation/i });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(props.onStartGame).toHaveBeenCalled();
    });
  });

  test('allows choosing a course from dropdown', () => {
    const props = makeDefaultProps();
    render(<GameSetup {...props} />);

    const courseSelect = screen.getByLabelText(/select course/i);
    fireEvent.change(courseSelect, { target: { value: 'Augusta' } });

    expect(props.setSelectedCourse).toHaveBeenCalledWith('Augusta');
  });
});
