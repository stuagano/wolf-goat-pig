import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CompletedRoundView from '../CompletedRoundView';
import { fetchJson } from '../../../services/fetchJson';

vi.mock('../../../config/api.config', () => ({
  apiConfig: { baseUrl: 'http://test-api' },
}));

vi.mock('../../../services/fetchJson', () => ({ fetchJson: vi.fn() }));

// Stub the children: this test covers the wiring CompletedRoundView owns.
vi.mock('../GameCompletionView', () => ({
  default: ({ onMarkComplete, onEditScores, isCompleted }) => (
    <div>
      <span>{isCompleted ? 'saved' : 'unsaved'}</span>
      <button onClick={onMarkComplete}>mark</button>
      <button onClick={onEditScores}>edit</button>
    </div>
  ),
}));

vi.mock('../ScorecardPhotoButton', () => ({
  default: ({ gameId }) => <div>photo:{gameId}</div>,
}));

const authFetch = vi.fn();
vi.mock('../../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => authFetch }));

const card = (body) => Promise.resolve({ ok: true, json: async () => body });
const NO_PHOTO = { has_photo: false, can_edit: true, edited_by: null, edited_at: null };

const baseProps = {
  players: [{ id: 'p1', name: 'Alice' }],
  playerStandings: {},
  holeHistory: [],
  courseHoles: [],
  strokeAllocation: {},
  isMarkedComplete: false,
};

beforeEach(() => {
  vi.resetAllMocks();
  authFetch.mockReturnValue(card({ has_photo: true, can_edit: false }));
});

describe('CompletedRoundView', () => {
  test('marking complete POSTs /complete and reports success', async () => {
    fetchJson.mockResolvedValueOnce({});
    const onMarkedComplete = vi.fn();
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={onMarkedComplete} onEditScores={vi.fn()} />);

    fireEvent.click(screen.getByText('mark'));

    await waitFor(() => expect(onMarkedComplete).toHaveBeenCalled());
    expect(fetchJson).toHaveBeenCalledWith('http://test-api/games/g1/complete', { method: 'POST' });
  });

  test('a failed save alerts and does not report success', async () => {
    fetchJson.mockRejectedValueOnce(new Error('boom'));
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const onMarkedComplete = vi.fn();
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={onMarkedComplete} onEditScores={vi.fn()} />);

    fireEvent.click(screen.getByText('mark'));

    await waitFor(() => expect(alertSpy).toHaveBeenCalledWith('Failed to save game: boom'));
    expect(onMarkedComplete).not.toHaveBeenCalled();
  });

  test('shows the photo button only when there is a game id, and forwards edit', () => {
    const onEditScores = vi.fn();
    const { rerender } = render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={onEditScores} />);
    expect(screen.getByText('photo:g1')).toBeInTheDocument();

    fireEvent.click(screen.getByText('edit'));
    expect(onEditScores).toHaveBeenCalled();

    rerender(<CompletedRoundView {...baseProps} gameId={null} onMarkedComplete={vi.fn()} onEditScores={onEditScores} />);
    expect(screen.queryByText(/photo:/)).not.toBeInTheDocument();
  });

  test('a member sees "Add the card photo" when the round has no photo, and the upload sends the file', async () => {
    authFetch.mockReturnValueOnce(card(NO_PHOTO)).mockReturnValueOnce(Promise.resolve({ ok: true, json: async () => ({}) }));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);

    const input = await screen.findByLabelText(/add the card photo/i);
    const file = new File(['x'], 'card.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() =>
      expect(authFetch).toHaveBeenCalledWith('http://test-api/games/g1/scorecard-photo', expect.objectContaining({ method: 'PUT' })),
    );
    const body = authFetch.mock.calls.find(([, o]) => o?.method === 'PUT')[1].body;
    expect(body.get('file')).toBe(file);
  });

  test('hides add button when the viewer may not edit', async () => {
    authFetch.mockReturnValueOnce(card({ ...NO_PHOTO, can_edit: false }));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);
    await waitFor(() => expect(authFetch).toHaveBeenCalled());
    expect(screen.queryByLabelText(/add the card photo/i)).toBeNull();
  });

  test('hides add button when signed out', async () => {
    authFetch.mockReturnValueOnce(Promise.reject(new Error('Login required')));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);
    await waitFor(() => expect(authFetch).toHaveBeenCalled());
    expect(screen.queryByLabelText(/add the card photo/i)).toBeNull();
    expect(screen.getByText('photo:g1')).toBeTruthy();
  });

  test('shows an error when the upload fails', async () => {
    authFetch.mockReturnValueOnce(card(NO_PHOTO)).mockReturnValueOnce(Promise.resolve({ ok: false, status: 403 }));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);
    fireEvent.change(await screen.findByLabelText(/add the card photo/i), {
      target: { files: [new File(['x'], 'card.jpg', { type: 'image/jpeg' })] },
    });
    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('403');
    expect(screen.getByLabelText(/add the card photo/i)).toBeTruthy();
  });

  test('shows who last edited the card', async () => {
    authFetch.mockReturnValueOnce(card({ has_photo: true, can_edit: false, edited_by: 'Alice', edited_at: '2026-10-14T18:00:00' }));
    render(<CompletedRoundView {...baseProps} gameId="g1" onMarkedComplete={vi.fn()} onEditScores={vi.fn()} />);
    expect(await screen.findByText(/Card edited by Alice ·/)).toBeTruthy();
  });
});
