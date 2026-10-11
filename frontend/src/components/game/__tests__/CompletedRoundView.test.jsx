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
});
