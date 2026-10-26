import React from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import RoundCardReview from '../RoundCardReview';

const photoLoads = vi.hoisted(() => new Map());

vi.mock('../../../config/api.config', () => ({ apiConfig: { baseUrl: 'http://test-api' } }));
vi.mock('../ScorecardPhotoZoom', () => ({
  default: ({ src, onLoad }) => {
    photoLoads.set(src, onLoad);
    return <img src={src} alt="scorecard" onLoad={onLoad} />;
  },
}));

afterEach(() => {
  cleanup();
  photoLoads.clear();
  vi.unstubAllGlobals();
});

test('a late load from the previous photo cannot enable extraction for its replacement', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }));
  const props = { gameId: 'g1', players: [{ id: 'p1', name: 'Alice' }], holeHistory: [] };
  const { rerender } = render(<RoundCardReview {...props}>Recorded scores</RoundCardReview>);
  const oldPhoto = await screen.findByAltText('scorecard');
  const oldLoad = photoLoads.get(oldPhoto.getAttribute('src'));
  fireEvent.load(oldPhoto);
  expect(screen.getByRole('button', { name: 'Extract & compare card' })).toBeEnabled();

  rerender(<RoundCardReview {...props} photoVersion={1}>Recorded scores</RoundCardReview>);
  const replacement = await screen.findByAltText('scorecard');
  expect(replacement).toHaveAttribute('src', 'http://test-api/games/g1/scorecard-photo?v=1&retry=0');
  expect(screen.queryByRole('button', { name: 'Extract & compare card' })).toBeNull();

  // Deliver the captured old-image load after the URL change. This is explicit,
  // not dependent on browser image loading or React's effect scheduling speed.
  act(() => oldLoad());
  expect(screen.queryByRole('button', { name: 'Extract & compare card' })).toBeNull();

  fireEvent.load(replacement);
  expect(screen.getByRole('button', { name: 'Extract & compare card' })).toBeEnabled();
});
