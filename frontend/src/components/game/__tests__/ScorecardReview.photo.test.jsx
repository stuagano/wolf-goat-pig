import React from 'react';
import { test, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ScorecardReview from '../ScorecardReview';

const ext = { players: [{ name: 'CK' }], running_totals: [{ player_index: 0, hole: 18, value: 6 }] };

test('shows "Check photo" and opens the zoom overlay when a photoUrl is present', () => {
  render(
    <ScorecardReview extraction={ext} players={[]} mode="new-round"
      rosterNames={[]} pickedPlayers={['CK']} photoUrl="blob:xyz"
      onConfirm={() => {}} onCancel={() => {}} />,
  );
  fireEvent.click(screen.getByRole('button', { name: /check photo/i }));
  expect(screen.getByAltText('scorecard').getAttribute('src')).toBe('blob:xyz');
});

test('no "Check photo" button without a photoUrl', () => {
  render(
    <ScorecardReview extraction={ext} players={[]} mode="new-round"
      rosterNames={[]} pickedPlayers={['CK']} onConfirm={() => {}} onCancel={() => {}} />,
  );
  expect(screen.queryByRole('button', { name: /check photo/i })).toBeNull();
});
