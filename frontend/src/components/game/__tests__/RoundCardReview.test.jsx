import React from 'react';
import { test, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import RoundCardReview from '../RoundCardReview';

vi.mock('../../../config/api.config', () => ({ apiConfig: { baseUrl: 'http://test-api' } }));
afterEach(() => vi.unstubAllGlobals());

test('keeps recorded scores visible through loading, missing photo, error and retry', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({ ok: false, status: 404 }).mockResolvedValueOnce({ ok: false, status: 503 }).mockResolvedValueOnce({ ok: true }));
  render(<RoundCardReview gameId="g1"><button>Recorded hole 1</button></RoundCardReview>);
  expect(screen.getByText(/loading card photo/i)).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Recorded hole 1' })).toBeVisible();
  expect(await screen.findByText(/no card photo/i)).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: /retry photo/i }));
  expect(await screen.findByText(/could not load/i)).toBeTruthy();
  fireEvent.click(screen.getByRole('button', { name: /retry photo/i }));
  const photo = await screen.findByAltText('scorecard');
  fireEvent.load(photo);
  expect(screen.queryByText(/loading card photo/i)).toBeNull();
  expect(screen.queryByRole('dialog')).toBeNull();
  expect(screen.getByRole('button', { name: 'Recorded hole 1' })).toBeVisible();
});

test('phone photo panel resizes without hiding the scores', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }));
  render(<RoundCardReview gameId="g1"><button>Recorded hole 1</button></RoundCardReview>);
  fireEvent.load(await screen.findByAltText('scorecard'));
  const slider = screen.getByLabelText(/photo panel height/i);
  fireEvent.change(slider, { target: { value: '360' } });
  expect(slider).toHaveValue('360');
  expect(document.querySelector('.round-card-review__viewport').style.getPropertyValue('--photo-height')).toBe('360px');
  expect(screen.getByRole('button', { name: 'Recorded hole 1' })).toBeVisible();
});
