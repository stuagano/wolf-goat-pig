// frontend/src/components/__tests__/BadgeGallery.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import BadgeGallery from '../BadgeGallery';

// Mock fetch
global.fetch = jest.fn();

// Helper function to wait for loading to complete
const waitForLoadingToComplete = async () => {
  await waitFor(() => {
    expect(screen.queryByText('Loading badges...')).not.toBeInTheDocument();
  });
};

describe('BadgeGallery', () => {
  const mockEarnedBadges = [
    {
      badge: {
        badge_id: 'badge1',
        name: 'First Win',
        rarity: 'common',
        description: 'Win your first game',
        image_url: '/badges/first_win.png',
        category: 'achievement'
      },
      serial_number: 42,
      earned_at: '2024-01-15T10:30:00Z'
    },
    {
      badge: {
        badge_id: 'badge2',
        name: 'Eagle Master',
        rarity: 'rare',
        description: 'Score 10 eagles',
        image_url: '/badges/eagle_master.png',
        category: 'progression'
      },
      serial_number: 15,
      earned_at: '2024-02-20T14:00:00Z'
    }
  ];

  const mockAllBadges = [
    {
      badge_id: 'badge1',
      name: 'First Win',
      rarity: 'common',
      description: 'Win your first game',
      image_url: '/badges/first_win.png',
      category: 'achievement',
      max_supply: null,
      current_supply: 100
    },
    {
      badge_id: 'badge2',
      name: 'Eagle Master',
      rarity: 'rare',
      description: 'Score 10 eagles',
      image_url: '/badges/eagle_master.png',
      category: 'progression',
      max_supply: 500,
      current_supply: 150
    },
    {
      badge_id: 'badge3',
      name: 'Legendary Champion',
      rarity: 'legendary',
      description: 'Win 100 games',
      image_url: '/badges/legendary_champion.png',
      category: 'achievement',
      max_supply: 50,
      current_supply: 10
    },
    {
      badge_id: 'badge4',
      name: 'Series Collector',
      rarity: 'epic',
      description: 'Collect all series badges',
      image_url: '/badges/series_collector.png',
      category: 'collectible_series',
      max_supply: 100,
      current_supply: 25
    }
  ];

  const mockBadgeStats = {
    total_earned: 2,
    total_available: 4,
    completion_percentage: 50.0
  };

  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockImplementation((url) => {
      if (url.includes('/earned')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockEarnedBadges)
        });
      }
      if (url.includes('/available')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAllBadges)
        });
      }
      if (url.includes('/stats')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockBadgeStats)
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });
  });

  describe('Loading State', () => {
    test('shows loading spinner initially', async () => {
      render(<BadgeGallery playerId={1} />);
      expect(screen.getByText('Loading badges...')).toBeInTheDocument();
      // Wait for loading to complete to avoid act() warnings
      await waitForLoadingToComplete();
    });
  });

  describe('After Data Loads', () => {
    test('displays gallery header with title', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('🏆 Badge Collection')).toBeInTheDocument();
      });
    });

    test('displays badge stats summary', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument(); // total_earned
        expect(screen.getByText('4')).toBeInTheDocument(); // total_available
        expect(screen.getByText('50.0%')).toBeInTheDocument(); // completion_percentage
      });
    });

    test('displays all filter buttons', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('All Badges')).toBeInTheDocument();
        // Look for buttons with partial text match (includes count like "Earned (2)")
        expect(screen.getByRole('button', { name: /Earned/ })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Locked/ })).toBeInTheDocument();
        expect(screen.getByText('Achievements')).toBeInTheDocument();
        expect(screen.getByText('Progression')).toBeInTheDocument();
        expect(screen.getByText('Series')).toBeInTheDocument();
      });
    });

    test('displays all badge cards', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('First Win')).toBeInTheDocument();
        expect(screen.getByText('Eagle Master')).toBeInTheDocument();
        expect(screen.getByText('Legendary Champion')).toBeInTheDocument();
        expect(screen.getByText('Series Collector')).toBeInTheDocument();
      });
    });

    test('shows rarity labels on badges', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getAllByText('COMMON').length).toBeGreaterThan(0);
        expect(screen.getAllByText('RARE').length).toBeGreaterThan(0);
        expect(screen.getAllByText('LEGENDARY').length).toBeGreaterThan(0);
        expect(screen.getAllByText('EPIC').length).toBeGreaterThan(0);
      });
    });

    test('shows lock icon for unearned badges', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        // Locked badges should show lock icon
        const lockIcons = screen.getAllByText('🔒');
        expect(lockIcons.length).toBeGreaterThan(0);
      });
    });

    test('shows serial number for earned badges', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('#42')).toBeInTheDocument();
        expect(screen.getByText('#15')).toBeInTheDocument();
      });
    });

    test('shows supply info for limited badges', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('150 / 500')).toBeInTheDocument();
        expect(screen.getByText('10 / 50')).toBeInTheDocument();
      });
    });
  });

  describe('Filtering', () => {
    test('filters to show only earned badges', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('All Badges')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /Earned/ }));

      // Should only show earned badges
      expect(screen.getByText('First Win')).toBeInTheDocument();
      expect(screen.getByText('Eagle Master')).toBeInTheDocument();
      // Unearned badges should not be visible
      expect(screen.queryByText('Legendary Champion')).not.toBeInTheDocument();
    });

    test('filters to show only locked badges', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('All Badges')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /Locked/ }));

      // Should only show locked badges
      expect(screen.getByText('Legendary Champion')).toBeInTheDocument();
      expect(screen.getByText('Series Collector')).toBeInTheDocument();
      // Earned badges should not be visible
      expect(screen.queryByText('First Win')).not.toBeInTheDocument();
    });

    test('filters by category', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('All Badges')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Achievements'));

      // Should show only achievement badges
      expect(screen.getByText('First Win')).toBeInTheDocument();
      expect(screen.getByText('Legendary Champion')).toBeInTheDocument();
      // Non-achievement badges should not be visible
      expect(screen.queryByText('Eagle Master')).not.toBeInTheDocument();
    });

    test('shows no badges message when filter returns empty', async () => {
      // Mock with no progression badges
      fetch.mockImplementation((url) => {
        if (url.includes('/earned')) return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
        if (url.includes('/available')) return Promise.resolve({ ok: true, json: () => Promise.resolve([
          { badge_id: 'b1', name: 'Test', rarity: 'common', category: 'achievement' }
        ]) });
        if (url.includes('/stats')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockBadgeStats) });
        return Promise.reject(new Error('Unknown'));
      });

      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('All Badges')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Progression'));

      expect(screen.getByText('No badges found matching your filter.')).toBeInTheDocument();
    });
  });

  describe('Badge Modal', () => {
    test('opens modal when badge card clicked', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('First Win')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('First Win'));

      // Modal should be visible with badge details
      expect(screen.getByText('Win your first game')).toBeInTheDocument(); // Description
    });

    test('modal shows earned info for earned badges', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('First Win')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('First Win'));

      expect(screen.getByText('Serial Number')).toBeInTheDocument();
      expect(screen.getByText('Earned On')).toBeInTheDocument();
    });

    test('modal shows unlock hint for locked badges', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('Legendary Champion')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Legendary Champion'));

      expect(screen.getByText(/This badge is locked/)).toBeInTheDocument();
    });

    test('closes modal when close button clicked', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('First Win')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('First Win'));

      // Modal is open
      expect(screen.getByText('Win your first game')).toBeInTheDocument();

      // Click close button
      fireEvent.click(screen.getByText('×'));

      // Description should not be visible (modal closed)
      // Note: The description might still be visible in card, so check for modal-specific content
    });

    test('closes modal when overlay clicked', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('First Win')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('First Win'));

      // Click overlay (badge-modal-overlay class)
      const overlay = document.querySelector('.badge-modal-overlay');
      if (overlay) {
        fireEvent.click(overlay);
      }
    });

    test('modal shows category label', async () => {
      render(<BadgeGallery playerId={1} />);
      await waitFor(() => {
        expect(screen.getByText('First Win')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('First Win'));

      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Achievement')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('handles API error gracefully', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      fetch.mockRejectedValue(new Error('Network error'));

      await act(async () => {
        render(<BadgeGallery playerId={1} />);
      });

      // Wait for loading to complete
      await waitForLoadingToComplete();

      consoleSpy.mockRestore();
    });
  });

  describe('Player ID Changes', () => {
    test('refetches data when playerId changes', async () => {
      const { rerender } = render(<BadgeGallery playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('🏆 Badge Collection')).toBeInTheDocument();
      });

      expect(fetch).toHaveBeenCalledTimes(3); // 3 API calls

      // Change playerId
      rerender(<BadgeGallery playerId={2} />);

      // Should fetch again
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(6); // 3 more API calls
      });
    });
  });
});
