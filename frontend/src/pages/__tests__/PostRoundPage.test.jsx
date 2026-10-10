import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import PostRoundPage from '../PostRoundPage';
import { postMyRound, fetchMyRounds, fetchPendingAttestations } from '../../services/rounds';

vi.mock('../../hooks/useAccessToken', () => ({
  useAccessToken: () => ({ getToken: token, isRecoverableAuthError: () => false }),
}));
const token = vi.fn();
vi.mock('../../hooks/usePlayerProfile', () => ({
  usePlayerProfile: () => ({ profile: { legacy_name: 'Stuart Gano' } }),
}));
vi.mock('../../hooks/useLegacyPlayers', () => ({
  useLegacyPlayers: () => ({ players: ['Stuart Gano', 'Jeff Smith', 'Bob Jones', 'Alice Park'] }),
}));
vi.mock('../../components/auth/LegacyNameSelector', () => ({ default: () => null }));
vi.mock('../../services/rounds', () => ({
  postMyRound: vi.fn(), fetchMyRounds: vi.fn(), fetchPendingAttestations: vi.fn(), attestRound: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  fetchMyRounds.mockResolvedValue([]);
  fetchPendingAttestations.mockResolvedValue([]);
  postMyRound.mockResolvedValue({ rounds: [{}, {}, {}, {}] });
});

test('one submission posts individual results for all four players without attestation', async () => {
  render(<PostRoundPage />);
  await screen.findByText('No posted rounds yet.');
  ['Jeff Smith', 'Bob Jones', 'Alice Park'].forEach(name => fireEvent.click(screen.getByRole('button', { name })));
  ['Stuart Gano', 'Jeff Smith', 'Bob Jones', 'Alice Park'].forEach((name, i) => {
    fireEvent.change(screen.getByLabelText(`${name} — quarters won/lost`), { target: { value: [5, -3, -2, 0][i] } });
  });
  fireEvent.click(screen.getByRole('button', { name: 'Post foursome results' }));
  await waitFor(() => expect(postMyRound).toHaveBeenCalledWith(token, expect.objectContaining({
    results: [
      { member: 'Stuart Gano', score: 5 }, { member: 'Jeff Smith', score: -3 },
      { member: 'Bob Jones', score: -2 }, { member: 'Alice Park', score: 0 },
    ],
  })));
  expect(await screen.findByText(/Results posted for all 4 players/)).toBeInTheDocument();
  expect(fetchPendingAttestations).not.toHaveBeenCalled();
  expect(screen.queryByText(/Awaiting Your Attestation/)).not.toBeInTheDocument();
});

test('shows posted history without an attestation column', async () => {
  fetchMyRounds.mockResolvedValue([{ id: 1, date: '2026-10-04', score: 5, status: 'posted', foursome: ['Jeff Smith'] }]);
  render(<PostRoundPage />);
  expect(await screen.findByText('Posted')).toBeInTheDocument();
  expect(screen.queryByRole('columnheader', { name: 'Attested By' })).not.toBeInTheDocument();
});

test('preserves a leading minus while typing and posts negative quarters', async () => {
  render(<PostRoundPage />);
  await screen.findByText('No posted rounds yet.');
  fireEvent.click(screen.getByRole('button', { name: 'Jeff Smith' }));
  const score = screen.getByLabelText('Stuart Gano — quarters won/lost');
  fireEvent.change(score, { target: { value: '-' } });
  expect(score).toHaveValue('-');
  expect(score).toHaveAttribute('inputmode', 'text');
  fireEvent.change(score, { target: { value: '-5' } });
  fireEvent.change(screen.getByLabelText('Jeff Smith — quarters won/lost'), { target: { value: '5' } });
  fireEvent.click(screen.getByRole('button', { name: 'Post foursome results' }));
  await waitFor(() => expect(postMyRound).toHaveBeenCalledWith(token, expect.objectContaining({
    results: [{ member: 'Stuart Gano', score: -5 }, { member: 'Jeff Smith', score: 5 }],
  })));
});

test('keeps group results for correction when another player already posted', async () => {
  postMyRound.mockRejectedValue(Object.assign(new Error('Jeff Smith already has a posted result for that date'), { status: 409 }));
  render(<PostRoundPage />);
  await screen.findByText('No posted rounds yet.');
  fireEvent.click(screen.getByRole('button', { name: 'Jeff Smith' }));
  fireEvent.change(screen.getByLabelText('Stuart Gano — quarters won/lost'), { target: { value: 5 } });
  fireEvent.change(screen.getByLabelText('Jeff Smith — quarters won/lost'), { target: { value: -5 } });
  fireEvent.click(screen.getByRole('button', { name: 'Post foursome results' }));
  expect(await screen.findByText(/Jeff Smith already has a posted result/)).toBeInTheDocument();
  expect(screen.getByLabelText('Stuart Gano — quarters won/lost')).toHaveValue('5');
  expect(screen.getByLabelText('Jeff Smith — quarters won/lost')).toHaveValue('-5');
  expect(screen.queryByRole('button', { name: 'Try again' })).not.toBeInTheDocument();
});

test.each(['-', '1.5', 'abc', '1e2', '2147483648', '-2147483649'])('rejects invalid quarters %s', async (value) => {
  render(<PostRoundPage />);
  await screen.findByText('No posted rounds yet.');
  fireEvent.click(screen.getByRole('button', { name: 'Jeff Smith' }));
  fireEvent.change(screen.getByLabelText('Stuart Gano — quarters won/lost'), { target: { value } });
  fireEvent.change(screen.getByLabelText('Jeff Smith — quarters won/lost'), { target: { value: '0' } });
  fireEvent.click(screen.getByRole('button', { name: 'Post foursome results' }));
  expect(await screen.findByText('Enter whole quarters won/lost for every player, including zero.')).toBeInTheDocument();
  expect(postMyRound).not.toHaveBeenCalled();
});
