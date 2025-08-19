/**
 * Comprehensive test suite for PlayerProfileManager component
 * 
 * Tests the player profile management system including:
 * - Profile creation, editing, and deletion
 * - Profile selection and activation
 * - Form validation and error handling
 * - Loading states and API interactions
 * - Profile categorization by handicap
 * - User preferences management
 * - Responsive table display
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Test utilities and providers
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context/GameProvider';

// Component under test
import PlayerProfileManager from '../PlayerProfileManager';

// Mock fetch globally
global.fetch = jest.fn();

// Mock window.confirm
global.confirm = jest.fn();

// Mock UI components
jest.mock('../ui', () => ({
  Card: function MockCard({ children, className }) {
    return <div data-testid="card" className={className}>{children}</div>;
  }
}));

const mockProfiles = [
  {
    id: '1',
    name: 'Alice Johnson',
    handicap: 8.5,
    avatar_url: 'https://example.com/alice.jpg',
    last_played: '2024-01-15T10:30:00Z',
    created_date: '2024-01-01T00:00:00Z',
    preferences: {
      ai_difficulty: 'medium',
      preferred_game_modes: ['wolf_goat_pig'],
      preferred_player_count: 4,
      betting_style: 'conservative',
      display_hints: true
    },
    statistics: {
      games_played: 15,
      total_earnings: 125.50,
      win_rate: 0.67
    }
  },
  {
    id: '2',
    name: 'Bob Smith',
    handicap: 18.0,
    avatar_url: '',
    last_played: null,
    created_date: '2024-01-10T00:00:00Z',
    preferences: {
      ai_difficulty: 'easy',
      preferred_game_modes: ['wolf_goat_pig'],
      preferred_player_count: 4,
      betting_style: 'aggressive',
      display_hints: false
    },
    statistics: {
      games_played: 3,
      total_earnings: -45.25,
      win_rate: 0.33
    }
  },
  {
    id: '3',
    name: 'Carol Davis',
    handicap: 25.5,
    avatar_url: null,
    last_played: '2024-01-14T15:45:00Z',
    created_date: '2024-01-05T00:00:00Z',
    preferences: {
      ai_difficulty: 'hard',
      preferred_game_modes: ['wolf_goat_pig'],
      preferred_player_count: 6,
      betting_style: 'moderate',
      display_hints: true
    },
    statistics: {
      games_played: 8,
      total_earnings: 22.75,
      win_rate: 0.50
    }
  }
];

const TestWrapper = ({ children }) => (
  <ThemeProvider>
    <GameProvider>
      {children}
    </GameProvider>
  </ThemeProvider>
);

describe('PlayerProfileManager', () => {
  let mockOnProfileSelect;

  beforeEach(() => {
    mockOnProfileSelect = jest.fn();
    fetch.mockClear();
    confirm.mockClear();
  });

  describe('Initial Loading and Error Handling', () => {
    test('displays loading state initially', () => {
      // Mock pending fetch
      fetch.mockImplementation(() => new Promise(() => {}));

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      expect(screen.getByText('Loading player profiles...')).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
    });

    test('loads and displays profiles successfully', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Player Profiles')).toBeInTheDocument();
        expect(screen.getByText('All Profiles (3)')).toBeInTheDocument();
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
        expect(screen.getByText('Bob Smith')).toBeInTheDocument();
        expect(screen.getByText('Carol Davis')).toBeInTheDocument();
      });
    });

    test('displays error message when loading fails', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Failed to load profiles: Network error/)).toBeInTheDocument();
        expect(screen.getByText('⚠️')).toBeInTheDocument();
      });
    });

    test('can dismiss error message', async () => {
      const user = userEvent.setup();

      fetch.mockRejectedValueOnce(new Error('Network error'));

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Failed to load profiles/)).toBeInTheDocument();
      });

      const dismissButton = screen.getByText('✕');
      await user.click(dismissButton);

      expect(screen.queryByText(/Failed to load profiles/)).not.toBeInTheDocument();
    });

    test('shows empty state when no profiles exist', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => []
      });

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('No player profiles found.')).toBeInTheDocument();
        expect(screen.getByText('Create Your First Profile')).toBeInTheDocument();
      });
    });
  });

  describe('Profile Display and Categorization', () => {
    beforeEach(async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });
    });

    test('displays profile information in table format', async () => {
      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
        expect(screen.getByText('8.5')).toBeInTheDocument(); // Alice's handicap
        expect(screen.getByText('18')).toBeInTheDocument(); // Bob's handicap (displayed as 18, not 18.0)
        expect(screen.getByText('25.5')).toBeInTheDocument(); // Carol's handicap
      });

      // Check table headers
      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Handicap')).toBeInTheDocument();
      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Last Played')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    test('categorizes players by handicap correctly', async () => {
      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Low')).toBeInTheDocument(); // Alice (8.5 handicap)
        expect(screen.getByText('Mid')).toBeInTheDocument(); // Bob (18 handicap)
        expect(screen.getByText('Beginner')).toBeInTheDocument(); // Carol (25.5 handicap)
      });
    });

    test('formats dates correctly', async () => {
      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        // Alice has a valid last played date
        expect(screen.getByText('1/15/2024')).toBeInTheDocument();
        
        // Bob has null last played date
        expect(screen.getByText('Never')).toBeInTheDocument();
        
        // Carol has a valid last played date
        expect(screen.getByText('1/14/2024')).toBeInTheDocument();
      });
    });

    test('displays player avatars with initials', async () => {
      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('A')).toBeInTheDocument(); // Alice's initial
        expect(screen.getByText('B')).toBeInTheDocument(); // Bob's initial
        expect(screen.getByText('C')).toBeInTheDocument(); // Carol's initial
      });
    });
  });

  describe('Profile Selection', () => {
    beforeEach(async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });
    });

    test('displays profile selector when showSelector is true', async () => {
      render(
        <TestWrapper>
          <PlayerProfileManager 
            onProfileSelect={mockOnProfileSelect}
            showSelector={true}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Select Active Profile')).toBeInTheDocument();
      });
    });

    test('hides profile selector when showSelector is false', async () => {
      render(
        <TestWrapper>
          <PlayerProfileManager 
            onProfileSelect={mockOnProfileSelect}
            showSelector={false}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.queryByText('Select Active Profile')).not.toBeInTheDocument();
      });
    });

    test('calls onProfileSelect when profile is clicked in selector', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PlayerProfileManager 
            onProfileSelect={mockOnProfileSelect}
            showSelector={true}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Select Active Profile')).toBeInTheDocument();
      });

      const profileButton = screen.getByRole('button', { name: /Alice Johnson/ });
      await user.click(profileButton);

      expect(mockOnProfileSelect).toHaveBeenCalledWith(mockProfiles[0]);
    });

    test('highlights selected profile in selector', async () => {
      render(
        <TestWrapper>
          <PlayerProfileManager 
            onProfileSelect={mockOnProfileSelect}
            selectedProfile={mockProfiles[0]}
            showSelector={true}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        const selectedButton = screen.getByRole('button', { name: /Alice Johnson/ });
        expect(selectedButton).toHaveClass('border-blue-500', 'bg-blue-50');
      });
    });

    test('shows active indicator in profile table', async () => {
      render(
        <TestWrapper>
          <PlayerProfileManager 
            onProfileSelect={mockOnProfileSelect}
            selectedProfile={mockProfiles[1]}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Active')).toBeInTheDocument();
      });

      // Check that the active indicator is next to Bob's name
      const bobRow = screen.getByText('Bob Smith').closest('tr');
      expect(within(bobRow).getByText('Active')).toBeInTheDocument();
    });
  });

  describe('Profile Creation', () => {
    beforeEach(async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });
    });

    test('opens create form when Create New Profile clicked', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Create New Profile')).toBeInTheDocument();
      });

      const createButton = screen.getByText('Create New Profile');
      await user.click(createButton);

      expect(screen.getByText('Create New Profile')).toBeInTheDocument(); // Form title
      expect(screen.getByPlaceholderText('Enter player name')).toBeInTheDocument();
      expect(screen.getByDisplayValue('18')).toBeInTheDocument(); // Default handicap
    });

    test('creates new profile successfully', async () => {
      const user = userEvent.setup();

      const newProfile = {
        id: '4',
        name: 'David Wilson',
        handicap: 15.0,
        avatar_url: '',
        preferences: {
          ai_difficulty: 'medium',
          preferred_game_modes: ['wolf_goat_pig'],
          preferred_player_count: 4,
          betting_style: 'conservative',
          display_hints: true
        }
      };

      // First fetch for loading profiles
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Create New Profile')).toBeInTheDocument();
      });

      // Open create form
      const createButton = screen.getByText('Create New Profile');
      await user.click(createButton);

      // Fill out form
      const nameInput = screen.getByPlaceholderText('Enter player name');
      const handicapInput = screen.getByDisplayValue('18');

      await user.clear(nameInput);
      await user.type(nameInput, 'David Wilson');
      
      await user.clear(handicapInput);
      await user.type(handicapInput, '15');

      // Mock successful creation
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => newProfile
      });

      // Submit form
      const submitButton = screen.getByText('Create Profile');
      await user.click(submitButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: 'David Wilson',
            handicap: 15,
            avatar_url: '',
            preferences: {
              ai_difficulty: 'medium',
              preferred_game_modes: ['wolf_goat_pig'],
              preferred_player_count: 4,
              betting_style: 'conservative',
              display_hints: true
            }
          })
        });
      });

      // Should auto-select new profile
      expect(mockOnProfileSelect).toHaveBeenCalledWith(newProfile);
    });

    test('displays validation errors for invalid form data', async () => {
      const user = userEvent.setup();

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Create New Profile')).toBeInTheDocument();
      });

      // Open form and try to submit without name
      const createButton = screen.getByText('Create New Profile');
      await user.click(createButton);

      const nameInput = screen.getByPlaceholderText('Enter player name');
      await user.clear(nameInput);

      const submitButton = screen.getByText('Create Profile');
      await user.click(submitButton);

      // HTML5 validation should prevent submission
      expect(nameInput).toBeInvalid();
    });

    test('handles creation API errors', async () => {
      const user = userEvent.setup();

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Create New Profile')).toBeInTheDocument();
      });

      // Open form and fill it out
      const createButton = screen.getByText('Create New Profile');
      await user.click(createButton);

      const nameInput = screen.getByPlaceholderText('Enter player name');
      await user.type(nameInput, 'Test User');

      // Mock API error
      fetch.mockRejectedValueOnce(new Error('Server error'));

      const submitButton = screen.getByText('Create Profile');
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to create profile: Server error/)).toBeInTheDocument();
      });
    });

    test('can cancel profile creation', async () => {
      const user = userEvent.setup();

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Create New Profile')).toBeInTheDocument();
      });

      // Open form
      const createButton = screen.getByText('Create New Profile');
      await user.click(createButton);

      expect(screen.getByPlaceholderText('Enter player name')).toBeInTheDocument();

      // Cancel form
      const cancelButton = screen.getByText('Cancel');
      await user.click(cancelButton);

      expect(screen.queryByPlaceholderText('Enter player name')).not.toBeInTheDocument();
    });
  });

  describe('Profile Editing', () => {
    beforeEach(async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });
    });

    test('opens edit form when Edit button clicked', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByText('Edit');
      await user.click(editButtons[0]); // Edit Alice

      expect(screen.getByText('Edit Profile')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Alice Johnson')).toBeInTheDocument();
      expect(screen.getByDisplayValue('8.5')).toBeInTheDocument();
      expect(screen.getByText('Update Profile')).toBeInTheDocument();
    });

    test('pre-fills form with existing profile data', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Bob Smith')).toBeInTheDocument();
      });

      const editButtons = screen.getAllByText('Edit');
      await user.click(editButtons[1]); // Edit Bob

      expect(screen.getByDisplayValue('Bob Smith')).toBeInTheDocument();
      expect(screen.getByDisplayValue('18')).toBeInTheDocument();
      expect(screen.getByDisplayValue('easy')).toBeInTheDocument(); // AI difficulty
      expect(screen.getByDisplayValue('aggressive')).toBeInTheDocument(); // Betting style
      expect(screen.getByRole('checkbox', { checked: false })).toBeInTheDocument(); // Display hints
    });

    test('updates profile successfully', async () => {
      const user = userEvent.setup();

      const updatedProfile = {
        ...mockProfiles[0],
        name: 'Alice Johnson-Smith',
        handicap: 7.5
      };

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      // Start editing
      const editButtons = screen.getAllByText('Edit');
      await user.click(editButtons[0]);

      // Update form data
      const nameInput = screen.getByDisplayValue('Alice Johnson');
      const handicapInput = screen.getByDisplayValue('8.5');

      await user.clear(nameInput);
      await user.type(nameInput, 'Alice Johnson-Smith');
      
      await user.clear(handicapInput);
      await user.type(handicapInput, '7.5');

      // Mock successful update
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedProfile
      });

      // Submit update
      const updateButton = screen.getByText('Update Profile');
      await user.click(updateButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players/1', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: 'Alice Johnson-Smith',
            handicap: 7.5,
            avatar_url: 'https://example.com/alice.jpg',
            preferences: mockProfiles[0].preferences
          })
        });
      });
    });

    test('handles update API errors', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      // Start editing
      const editButtons = screen.getAllByText('Edit');
      await user.click(editButtons[0]);

      // Mock API error
      fetch.mockRejectedValueOnce(new Error('Update failed'));

      const updateButton = screen.getByText('Update Profile');
      await user.click(updateButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to update profile: Update failed/)).toBeInTheDocument();
      });
    });
  });

  describe('Profile Deletion', () => {
    beforeEach(async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });
    });

    test('confirms before deleting profile', async () => {
      const user = userEvent.setup();
      confirm.mockReturnValue(false); // User cancels

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByText('Delete');
      await user.click(deleteButtons[0]);

      expect(confirm).toHaveBeenCalledWith(
        'Are you sure you want to delete this profile? This action cannot be undone.'
      );
      
      // Should not make API call if user cancels
      expect(fetch).toHaveBeenCalledTimes(1); // Only the initial load
    });

    test('deletes profile when confirmed', async () => {
      const user = userEvent.setup();
      confirm.mockReturnValue(true); // User confirms

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      // Mock successful deletion
      fetch.mockResolvedValueOnce({ ok: true });

      const deleteButtons = screen.getAllByText('Delete');
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players/1', {
          method: 'DELETE'
        });
      });
    });

    test('clears selection when deleting selected profile', async () => {
      const user = userEvent.setup();
      confirm.mockReturnValue(true);

      render(
        <TestWrapper>
          <PlayerProfileManager 
            onProfileSelect={mockOnProfileSelect}
            selectedProfile={mockProfiles[0]} // Alice is selected
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Active')).toBeInTheDocument(); // Alice shows as active
      });

      // Mock successful deletion
      fetch.mockResolvedValueOnce({ ok: true });

      const deleteButtons = screen.getAllByText('Delete');
      await user.click(deleteButtons[0]); // Delete Alice

      await waitFor(() => {
        expect(mockOnProfileSelect).toHaveBeenCalledWith(null);
      });
    });

    test('handles deletion API errors', async () => {
      const user = userEvent.setup();
      confirm.mockReturnValue(true);

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
      });

      // Mock API error
      fetch.mockRejectedValueOnce(new Error('Deletion failed'));

      const deleteButtons = screen.getAllByText('Delete');
      await user.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/Failed to delete profile: Deletion failed/)).toBeInTheDocument();
      });
    });
  });

  describe('Form Preferences', () => {
    beforeEach(async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });
    });

    test('displays all preference options in create form', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Create New Profile')).toBeInTheDocument();
      });

      const createButton = screen.getByText('Create New Profile');
      await user.click(createButton);

      // Check all preference fields are present
      expect(screen.getByText('AI Difficulty')).toBeInTheDocument();
      expect(screen.getByText('Preferred Player Count')).toBeInTheDocument();
      expect(screen.getByText('Betting Style')).toBeInTheDocument();
      expect(screen.getByText('Show gameplay hints')).toBeInTheDocument();

      // Check default values
      expect(screen.getByDisplayValue('medium')).toBeInTheDocument(); // AI difficulty
      expect(screen.getByDisplayValue('4')).toBeInTheDocument(); // Player count
      expect(screen.getByDisplayValue('conservative')).toBeInTheDocument(); // Betting style
      expect(screen.getByRole('checkbox', { checked: true })).toBeInTheDocument(); // Display hints
    });

    test('can modify preference values', async () => {
      const user = userEvent.setup();

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Create New Profile')).toBeInTheDocument();
      });

      const createButton = screen.getByText('Create New Profile');
      await user.click(createButton);

      // Change preferences
      const aiDifficultySelect = screen.getByDisplayValue('medium');
      await user.selectOptions(aiDifficultySelect, 'hard');

      const playerCountSelect = screen.getByDisplayValue('4');
      await user.selectOptions(playerCountSelect, '6');

      const bettingStyleSelect = screen.getByDisplayValue('conservative');
      await user.selectOptions(bettingStyleSelect, 'aggressive');

      const hintsCheckbox = screen.getByRole('checkbox');
      await user.click(hintsCheckbox);

      // Fill in required fields
      const nameInput = screen.getByPlaceholderText('Enter player name');
      await user.type(nameInput, 'Test Player');

      // Mock successful creation
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: '4', name: 'Test Player' })
      });

      const submitButton = screen.getByText('Create Profile');
      await user.click(submitButton);

      await waitFor(() => {
        const call = fetch.mock.calls.find(call => call[1]?.method === 'POST');
        const requestBody = JSON.parse(call[1].body);
        
        expect(requestBody.preferences).toEqual({
          ai_difficulty: 'hard',
          preferred_game_modes: ['wolf_goat_pig'],
          preferred_player_count: 6,
          betting_style: 'aggressive',
          display_hints: false
        });
      });
    });
  });

  describe('Performance and Edge Cases', () => {
    test('handles large number of profiles efficiently', async () => {
      const largeProfileList = Array.from({ length: 100 }, (_, i) => ({
        id: `${i + 1}`,
        name: `Player ${i + 1}`,
        handicap: Math.random() * 36,
        avatar_url: '',
        last_played: null,
        preferences: {
          ai_difficulty: 'medium',
          preferred_game_modes: ['wolf_goat_pig'],
          preferred_player_count: 4,
          betting_style: 'conservative',
          display_hints: true
        }
      }));

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => largeProfileList
      });

      const start = performance.now();

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('All Profiles (100)')).toBeInTheDocument();
      });

      const end = performance.now();
      
      // Should render large list efficiently
      expect(end - start).toBeLessThan(1000); // Under 1 second
      expect(screen.getByText('Player 1')).toBeInTheDocument();
      expect(screen.getByText('Player 100')).toBeInTheDocument();
    });

    test('handles missing or invalid profile data gracefully', async () => {
      const invalidProfiles = [
        {
          id: '1',
          name: 'Valid Player',
          handicap: 12
          // Missing other fields
        },
        {
          id: '2',
          name: '',
          handicap: 'invalid'
          // Invalid data types
        },
        null, // Null profile
        {
          id: '3'
          // Missing required fields
        }
      ];

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => invalidProfiles
      });

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      // Should not crash with invalid data
      await waitFor(() => {
        expect(screen.getByText('All Profiles')).toBeInTheDocument();
      });
    });

    test('disables buttons during loading states', async () => {
      const user = userEvent.setup();

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });

      render(
        <TestWrapper>
          <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Create New Profile')).toBeInTheDocument();
      });

      // Open form
      const createButton = screen.getByText('Create New Profile');
      await user.click(createButton);

      // Fill form
      const nameInput = screen.getByPlaceholderText('Enter player name');
      await user.type(nameInput, 'Test Player');

      // Mock slow API response
      fetch.mockImplementation(() => new Promise(() => {}));

      const submitButton = screen.getByText('Create Profile');
      await user.click(submitButton);

      // Buttons should be disabled during loading
      expect(screen.getByText('Saving...')).toBeInTheDocument();
      expect(screen.getByText('Saving...')).toBeDisabled();
      expect(screen.getByText('Cancel')).toBeDisabled();
    });
  });
});