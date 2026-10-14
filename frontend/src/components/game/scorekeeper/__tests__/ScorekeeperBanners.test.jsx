import React from 'react';
import { describe, test, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ScorekeeperBanners from '../ScorekeeperBanners';

vi.mock('../../ScorecardPhotoButton', () => ({
  default: ({ gameId }) => <div>photo:{gameId}</div>,
}));

const props = {
  courseDataLoading: false,
  courseDataError: null,
  rotationError: null,
  achievementCheckFailed: false,
  setAchievementCheckFailed: vi.fn(),
  setIsEditingCompleteGame: vi.fn(),
  editingHole: null,
  setCurrentHole: vi.fn(),
  resetHole: vi.fn(),
  holeHistory: [],
  gameId: 'g1',
};

describe('ScorekeeperBanners', () => {
  test('editing a finished round shows the card photo button', () => {
    render(<ScorekeeperBanners {...props} isEditingCompleteGame />);
    expect(screen.getByText('photo:g1')).toBeTruthy();
  });

  test('live scoring does not', () => {
    render(<ScorekeeperBanners {...props} isEditingCompleteGame={false} />);
    expect(screen.queryByText('photo:g1')).toBeNull();
  });
});
