import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import FeedbackPage from '../FeedbackPage';

const { getToken, reauthenticate } = vi.hoisted(() => ({ getToken: vi.fn(), reauthenticate: vi.fn() }));
vi.mock('../../hooks/useAccessToken', () => ({
  useAccessToken: () => ({ getToken, reauthenticate, isRecoverableAuthError: () => false }),
}));

beforeEach(() => getToken.mockResolvedValue('app-access-token'));

const fillFeedback = () => {
  fireEvent.change(screen.getByLabelText('Title'), { target: { value: 'Scores disappear' } });
  fireEvent.change(screen.getByLabelText('Description'), { target: { value: 'After saving a round.' } });
};

test('submits authenticated feedback once and links to the created issue', async () => {
  let complete;
  fetch.mockImplementation(() => new Promise(resolve => { complete = resolve; }));
  render(<FeedbackPage />);
  expect(screen.getByText(/public GitHub issue/)).toBeInTheDocument();
  fillFeedback();
  fireEvent.change(screen.getByLabelText('Steps to reproduce (optional)'), { target: { value: 'Save, then reload.' } });
  fireEvent.click(screen.getByRole('button', { name: 'Submit feedback' }));
  expect(screen.getByRole('button', { name: 'Submitting…' })).toBeDisabled();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  expect(fetch).toHaveBeenCalledWith('http://test-api.com/feedback', expect.objectContaining({
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer app-access-token' },
    body: JSON.stringify({ type: 'bug', title: 'Scores disappear', description: 'After saving a round.', steps: 'Save, then reload.' }),
  }));
  complete({ ok: true, json: async () => ({ number: 123, url: 'https://github.com/stuagano/wolf-goat-pig/issues/123' }) });
  expect(await screen.findByRole('link', { name: 'View issue #123' })).toHaveAttribute('href', 'https://github.com/stuagano/wolf-goat-pig/issues/123');
  expect(screen.queryByRole('button', { name: 'Submit feedback' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Send more feedback' }));
  expect(screen.getByLabelText('Title')).toHaveValue('');
});

test('keeps the draft on failure and never retries automatically', async () => {
  fetch.mockResolvedValue({ ok: false, status: 504, json: async () => ({ detail: 'Check GitHub before submitting again.' }) });
  render(<FeedbackPage />);
  fillFeedback();
  fireEvent.click(screen.getByRole('button', { name: 'Submit feedback' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Check GitHub before submitting again.');
  expect(screen.getByLabelText('Title')).toHaveValue('Scores disappear');
  expect(screen.getByLabelText('Description')).toHaveValue('After saving a round.');
  expect(fetch).toHaveBeenCalledTimes(1);
});

test('does not send hidden bug steps with a feature request', async () => {
  fetch.mockResolvedValue({ ok: true, json: async () => ({ number: 123, url: 'https://github.com/stuagano/wolf-goat-pig/issues/123' }) });
  render(<FeedbackPage />);
  fillFeedback();
  fireEvent.change(screen.getByLabelText('Steps to reproduce (optional)'), { target: { value: 'Old bug steps' } });
  fireEvent.change(screen.getByLabelText('Feedback type'), { target: { value: 'feature' } });
  expect(screen.queryByLabelText('Steps to reproduce (optional)')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Submit feedback' }));
  await screen.findByRole('link', { name: 'View issue #123' });
  expect(JSON.parse(fetch.mock.calls[0][1].body)).toMatchObject({ type: 'feature', steps: '' });
});

test('rejects whitespace-only feedback without sending it', async () => {
  render(<FeedbackPage />);
  fillFeedback();
  fireEvent.change(screen.getByLabelText('Title'), { target: { value: '   ' } });
  fireEvent.click(screen.getByRole('button', { name: 'Submit feedback' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Enter a title and description.');
  expect(fetch).not.toHaveBeenCalled();
});
