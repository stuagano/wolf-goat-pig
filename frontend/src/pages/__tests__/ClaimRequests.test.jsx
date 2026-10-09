import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import ClaimRequests from '../admin/ClaimRequests';

const request = vi.fn();
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => request }));

const ok = data => ({ ok: true, json: async () => data });
const claim = {
  id: 10, canonical_name: 'Gregg Colburn', requester_email: 'gregg@example.com', status: 'pending',
  created_at: '2026-10-09T10:00:00', requester: { id: 2 }, target: { id: 1 },
};

beforeEach(() => { request.mockReset(); vi.spyOn(window, 'confirm').mockReturnValue(true); });

test('lists pending claims', async () => {
  request.mockResolvedValueOnce(ok({ claims: [claim] }));
  render(<ClaimRequests />);
  expect(await screen.findByText('gregg@example.com')).toBeInTheDocument();
  expect(screen.getByText(/Original profile #1/)).toBeInTheDocument();
});

test('shows the empty state', async () => {
  request.mockResolvedValueOnce(ok({ claims: [] }));
  render(<ClaimRequests />);
  expect(await screen.findByText('No claim requests.')).toBeInTheDocument();
});

test('approve posts, confirms, and reloads', async () => {
  request.mockResolvedValueOnce(ok({ claims: [claim] }));
  render(<ClaimRequests />);
  request.mockResolvedValueOnce(ok({ ...claim, status: 'approved' })).mockResolvedValueOnce(ok({ claims: [] }));
  fireEvent.click(await screen.findByRole('button', { name: 'Approve claim for Gregg Colburn' }));
  expect(await screen.findByText(/Connected Gregg Colburn/)).toBeInTheDocument();
  expect(request.mock.calls[1][0]).toMatch(/\/players\/admin\/claims\/10\/approve$/);
  expect(request.mock.calls[1][1]).toEqual({ method: 'POST' });
  expect(window.confirm).toHaveBeenCalled();
});

test('dismiss posts without a confirm and shows server errors', async () => {
  request.mockResolvedValueOnce(ok({ claims: [claim] }));
  render(<ClaimRequests />);
  request.mockResolvedValueOnce({ ok: false, status: 409, json: async () => ({ detail: 'This claim is already dismissed.' }) });
  fireEvent.click(await screen.findByRole('button', { name: 'Dismiss claim for Gregg Colburn' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('already dismissed');
  expect(request.mock.calls[1][0]).toMatch(/\/claims\/10\/dismiss$/);
});
