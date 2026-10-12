// Tee times belong to their day: text entered for one date must never show on
// another, and must read back from the server after switching away and back.
import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useAuth0 as mockUseAuth0 } from '@auth0/auth0-react';
import DayTeeTimes from '../DayTeeTimes';

vi.mock('@auth0/auth0-react', () => ({ useAuth0: vi.fn() }));

const json = (data, status = 200) => new Response(JSON.stringify(data), {
  status,
  headers: { 'Content-Type': 'application/json' },
});

// In-memory stand-in for GET/PUT /signups/tee-times/{date}.
const fakeServer = (store = {}) => {
  fetch.mockImplementation(async (request) => {
    const date = new URL(request.url).pathname.split('/').pop();
    if (request.method === 'PUT') {
      store[date] = (await request.json()).tee_times;
    }
    return json({ date, tee_times: store[date] ?? '', updated_at: null });
  });
  return store;
};

const box = () => screen.getByRole('textbox', { name: 'Tee times' });
const loaded = () => waitFor(() => expect(box()).toBeEnabled());

describe('DayTeeTimes', () => {
  beforeEach(() => {
    mockUseAuth0.mockReturnValue({ isAuthenticated: true, getAccessTokenSilently: vi.fn().mockResolvedValue('t') });
  });

  test('tee times typed for one day stay on that day', async () => {
    const store = fakeServer();
    const { rerender } = render(<DayTeeTimes date="2026-10-18" />);
    await loaded();

    fireEvent.change(box(), { target: { value: '12:48 (1-4)' } });
    fireEvent.blur(box());
    expect(await screen.findByText('Saved')).toBeInTheDocument();
    expect(store['2026-10-18']).toBe('12:48 (1-4)');

    // A different day starts empty — the original bug showed Sunday's times here.
    rerender(<DayTeeTimes date="2026-10-19" />);
    await loaded();
    expect(box()).toHaveValue('');

    // Back to the first day: read back from the server, not leftover state.
    rerender(<DayTeeTimes date="2026-10-18" />);
    await loaded();
    expect(box()).toHaveValue('12:48 (1-4)');
  });

  test('a slow load for a day you already left does not overwrite the new day', async () => {
    let releaseSunday;
    fetch.mockImplementation((request) => {
      const date = new URL(request.url).pathname.split('/').pop();
      if (date === '2026-10-18') {
        return new Promise((resolve) => { releaseSunday = () => resolve(json({ date, tee_times: 'Sunday times' })); });
      }
      return Promise.resolve(json({ date, tee_times: 'Monday times' }));
    });

    const { rerender } = render(<DayTeeTimes date="2026-10-18" />);
    rerender(<DayTeeTimes date="2026-10-19" />);
    await waitFor(() => expect(box()).toHaveValue('Monday times'));

    await act(async () => releaseSunday());
    expect(box()).toHaveValue('Monday times');
  });

  test('signed-out visitors can read tee times but not edit them', async () => {
    mockUseAuth0.mockReturnValue({ isAuthenticated: false, getAccessTokenSilently: vi.fn() });
    fakeServer({ '2026-10-18': '12:48 (1-4)' });
    render(<DayTeeTimes date="2026-10-18" />);
    await loaded();
    expect(box()).toHaveValue('12:48 (1-4)');
    expect(box()).toHaveAttribute('readonly');
  });

  test('a failed save is shown, not silently dropped', async () => {
    fetch.mockImplementation(async (request) => (request.method === 'PUT'
      ? json({ detail: 'boom' }, 500)
      : json({ date: '2026-10-18', tee_times: '' })));
    render(<DayTeeTimes date="2026-10-18" />);
    await loaded();
    fireEvent.change(box(), { target: { value: '1:04 (9-12)' } });
    fireEvent.blur(box());
    expect(await screen.findByRole('alert')).toHaveTextContent(/Couldn’t save/);
  });
});
