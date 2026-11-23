import React from 'react';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import CancelSignupPage from '../CancelSignupPage';

vi.mock('../../theme/Provider', async () => {
  const factories = await import('../../test-utils/mockFactories');
  return {
    ThemeProvider: ({ children }) => <div>{children}</div>,
    useTheme: () => factories.createMockTheme(),
  };
});

const TOKEN = 'signed-token';

const renderPage = () => render(
  <MemoryRouter initialEntries={[`/signup/cancel/${TOKEN}`]}>
    <Routes>
      <Route path="/signup/cancel/:token" element={<CancelSignupPage />} />
    </Routes>
  </MemoryRouter>,
);

const jsonResponse = (body, ok = true, status = 200) => ({
  ok,
  status,
  json: async () => body,
});

beforeEach(() => {
  global.fetch = vi.fn();
});

test('shows the signup and does not cancel until the player confirms', async () => {
  fetch.mockResolvedValue(jsonResponse({
    player_name: 'Stuart Gano',
    date: '2026-11-27',
    status: 'signed_up',
    can_cancel: true,
  }));

  renderPage();

  expect(await screen.findByRole('heading', { name: "Can't make it?" })).toBeInTheDocument();
  expect(screen.getByText(/Stuart Gano/)).toBeInTheDocument();
  expect(screen.getByText(/November 27, 2026/)).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith(
    `http://test-api.com/signups/cancel/${TOKEN}`,
    expect.objectContaining({ method: 'GET' }),
  );

  fetch.mockResolvedValueOnce(jsonResponse({
    message: 'Sign-up cancelled successfully',
    name: 'Stuart Gano',
    date: '2026-11-27',
    already_cancelled: false,
    legacy_sync: 'skipped',
    live_write: false,
  }));
  fireEvent.click(screen.getByRole('button', { name: 'Cancel my signup' }));

  expect(await screen.findByText(/You're off the sheet/)).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(fetch).toHaveBeenLastCalledWith(
    `http://test-api.com/signups/cancel/${TOKEN}`,
    expect.objectContaining({ method: 'POST' }),
  );
  expect(screen.queryByRole('button', { name: 'Cancel my signup' })).not.toBeInTheDocument();
});

test('tells the player when the signup is already cancelled', async () => {
  fetch.mockResolvedValue(jsonResponse({
    player_name: 'Stuart Gano',
    date: '2026-11-27',
    status: 'cancelled',
    can_cancel: false,
  }));

  renderPage();

  expect(await screen.findByText(/already cancelled/i)).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Cancel my signup' })).not.toBeInTheDocument();
  expect(fetch).toHaveBeenCalledTimes(1);
});

test('shows an invalid link without posting', async () => {
  fetch.mockResolvedValue(jsonResponse({ detail: 'This cancel link is not valid.' }, false, 404));

  renderPage();

  expect(await screen.findByRole('alert')).toHaveTextContent('This cancel link is not valid.');
  expect(fetch).toHaveBeenCalledTimes(1);
  await waitFor(() => expect(fetch.mock.calls.every(([, init]) => !init || init.method !== 'POST')).toBe(true));
});
