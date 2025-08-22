import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import GameSetup from '../GameSetup';

// Mock data
const mockPersonalities = [
  { id: 'aggressive', name: 'Aggressive Player', description: 'Takes risks' },
  { id: 'conservative', name: 'Conservative Player', description: 'Plays safely' },
];

const mockSuggestedOpponents = [
  { id: 'comp1', name: 'Computer 1', handicap: 15, personality: 'aggressive' },
  { id: 'comp2', name: 'Computer 2', handicap: 12, personality: 'conservative' },
  { id: 'comp3', name: 'Computer 3', handicap: 8, personality: 'balanced' },
];

const mockCourses = {
  'Augusta National': { name: 'Augusta National', holes: 18 },
  'Pebble Beach': { name: 'Pebble Beach', holes: 18 },
};

const defaultProps = {
  humanPlayer: {
    id: 'human',
    name: '',
    handicap: 18,
    strength: 'Average',
    is_human: true,
  },
  setHumanPlayer: jest.fn(),
  computerPlayers: [],
  setComputerPlayers: jest.fn(),
  selectedCourse: '',
  setSelectedCourse: jest.fn(),
  courses: mockCourses,
  setCourses: jest.fn(),
  personalities: mockPersonalities,
  setPersonalities: jest.fn(),
  suggestedOpponents: mockSuggestedOpponents,
  setSuggestedOpponents: jest.fn(),
  onStartGame: jest.fn(),
};

describe('GameSetup', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders player setup form', () => {
    render(<GameSetup {...defaultProps} />);
    
    expect(screen.getByText(/player setup/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/your name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/handicap/i)).toBeInTheDocument();
  });

  test('updates human player name', () => {
    render(<GameSetup {...defaultProps} />);
    
    const nameInput = screen.getByLabelText(/your name/i);
    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    
    expect(defaultProps.setHumanPlayer).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'John Doe' })
    );
  });

  test('updates human player handicap', () => {
    render(<GameSetup {...defaultProps} />);
    
    const handicapInput = screen.getByLabelText(/handicap/i);
    fireEvent.change(handicapInput, { target: { value: '12' } });
    
    expect(defaultProps.setHumanPlayer).toHaveBeenCalledWith(
      expect.objectContaining({ handicap: 12 })
    );
  });

  test('renders course selection', () => {
    render(<GameSetup {...defaultProps} />);
    
    expect(screen.getByText(/course selection/i)).toBeInTheDocument();
    expect(screen.getByText('Augusta National')).toBeInTheDocument();
    expect(screen.getByText('Pebble Beach')).toBeInTheDocument();
  });

  test('selects course', () => {
    render(<GameSetup {...defaultProps} />);
    
    const courseButton = screen.getByText('Augusta National');
    fireEvent.click(courseButton);
    
    expect(defaultProps.setSelectedCourse).toHaveBeenCalledWith('Augusta National');
  });

  test('renders computer opponents section', () => {
    render(<GameSetup {...defaultProps} />);
    
    expect(screen.getByText(/computer opponents/i)).toBeInTheDocument();
  });

  test('shows suggested opponents', () => {
    render(<GameSetup {...defaultProps} />);
    
    expect(screen.getByText('Computer 1')).toBeInTheDocument();
    expect(screen.getByText('Computer 2')).toBeInTheDocument();
    expect(screen.getByText('Computer 3')).toBeInTheDocument();
  });

  test('updates computer player personality', () => {
    const computerPlayers = [
      { id: 'comp1', name: 'Computer 1', handicap: 15, personality: 'aggressive', is_human: false },
    ];
    
    render(<GameSetup {...defaultProps} computerPlayers={computerPlayers} />);
    
    const personalitySelect = screen.getAllByDisplayValue('aggressive')[0];
    fireEvent.change(personalitySelect, { target: { value: 'conservative' } });
    
    expect(defaultProps.setComputerPlayers).toHaveBeenCalledWith([
      expect.objectContaining({ personality: 'conservative' })
    ]);
  });

  test('calls onStartGame when start button clicked', () => {
    const propsWithName = {
      ...defaultProps,
      humanPlayer: { ...defaultProps.humanPlayer, name: 'John Doe' },
    };
    
    render(<GameSetup {...propsWithName} />);
    
    const startButton = screen.getByText(/start simulation/i);
    fireEvent.click(startButton);
    
    expect(defaultProps.onStartGame).toHaveBeenCalled();
  });

  test('validates required fields before starting', () => {
    render(<GameSetup {...defaultProps} />);
    
    const startButton = screen.getByText(/start simulation/i);
    expect(startButton).toBeDisabled();
  });

  test('enables start button when all fields are valid', () => {
    const validProps = {
      ...defaultProps,
      humanPlayer: { ...defaultProps.humanPlayer, name: 'John Doe' },
      selectedCourse: 'Augusta National',
      computerPlayers: [
        { id: 'comp1', name: 'Computer 1', handicap: 15, personality: 'aggressive', is_human: false },
        { id: 'comp2', name: 'Computer 2', handicap: 12, personality: 'conservative', is_human: false },
        { id: 'comp3', name: 'Computer 3', handicap: 8, personality: 'balanced', is_human: false },
      ],
    };
    
    render(<GameSetup {...validProps} />);
    
    const startButton = screen.getByText(/start simulation/i);
    expect(startButton).not.toBeDisabled();
  });

  test('handles empty suggested opponents gracefully', () => {
    const propsWithNoOpponents = {
      ...defaultProps,
      suggestedOpponents: [],
    };
    
    render(<GameSetup {...propsWithNoOpponents} />);
    
    expect(screen.getByText(/computer opponents/i)).toBeInTheDocument();
    expect(screen.queryByText('Computer 1')).not.toBeInTheDocument();
  });

  test('handles empty courses gracefully', () => {
    const propsWithNoCourses = {
      ...defaultProps,
      courses: {},
    };
    
    render(<GameSetup {...propsWithNoCourses} />);
    
    expect(screen.getByText(/course selection/i)).toBeInTheDocument();
    expect(screen.queryByText('Augusta National')).not.toBeInTheDocument();
  });

  test('allows customizing computer player handicaps', () => {
    const computerPlayers = [
      { id: 'comp1', name: 'Computer 1', handicap: 15, personality: 'aggressive', is_human: false },
    ];
    
    render(<GameSetup {...defaultProps} computerPlayers={computerPlayers} />);
    
    const handicapInput = screen.getByDisplayValue('15');
    fireEvent.change(handicapInput, { target: { value: '20' } });
    
    expect(defaultProps.setComputerPlayers).toHaveBeenCalledWith([
      expect.objectContaining({ handicap: 20 })
    ]);
  });
});