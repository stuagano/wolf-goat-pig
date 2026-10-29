import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ParticipantCorrection from '../admin/ParticipantCorrection';

const { request } = vi.hoisted(() => ({ request: vi.fn() }));
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => request }));
const view = {
  game_id: 'a93b258a-3c0e-4531-b0ff-cab5a22d5073', game_record_id: 10, epoch: 0, snapshot: 'a'.repeat(64),
  result: { id: 20, player_name: 'Stuart Gano', player_profile_id: 21, total_earnings: -257 },
  current_profile: { id: 21, name: 'Kevin Gent' }, replacement_profile: { id: 20, name: 'Stuart Gano' },
};
const response = (data, ok = true) => ({ ok, json: async () => data });
async function openPreview() {
  render(<ParticipantCorrection />);
  fireEvent.change(screen.getByLabelText('Saved result ID'), { target: { value: '20' } });
  fireEvent.change(screen.getByLabelText('Replacement profile ID'), { target: { value: '20' } });
  fireEvent.click(screen.getByRole('button', { name: 'Preview correction' }));
  await screen.findByRole('region', { name: 'Correction preview' });
}
beforeEach(() => { request.mockReset(); request.mockResolvedValue(response(view)); });

describe('bounded participant correction', () => {
  it('previews exact identities and requires reason and confirmation before server readback', async () => {
    await openPreview();
    expect(screen.getByText(view.game_id)).toBeInTheDocument();
    expect(screen.getByText('#21 — Kevin Gent')).toBeInTheDocument();
    expect(screen.getByText('#20 — Stuart Gano')).toBeInTheDocument();
    expect(screen.getByText('-257')).toBeInTheDocument();
    const apply = screen.getByRole('button', { name: 'Confirm participant correction' });
    expect(apply).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'Verified identity' } });
    expect(apply).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox'));
    expect(apply).not.toBeDisabled();
    request.mockResolvedValueOnce(response({ audit_id: 'audit-1', game_id: view.game_id, result: { ...view.result, player_profile_id: 20 } }));
    fireEvent.click(apply);
    await screen.findByRole('status');
    expect(screen.getByRole('status')).toHaveTextContent('Saved and read back from the server.');
    expect(screen.getByRole('status')).toHaveTextContent('profile #20; earnings -257');
    const payload = JSON.parse(request.mock.calls[1][1].body);
    expect(payload).toMatchObject({ replacement_profile_id: 20, expected_old_profile_id: 21, expected_epoch: 0,
      expected_snapshot: view.snapshot, reason: 'Verified identity', confirmed: true });
    expect(payload.actor_profile_id).toBeUndefined();
    expect(payload.request_key).toBeTruthy();
  });

  it('invalidates preview when target changes and confirmation when reason changes', async () => {
    await openPreview();
    fireEvent.click(screen.getByRole('checkbox'));
    fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'new reason' } });
    expect(screen.getByRole('checkbox')).not.toBeChecked();
    fireEvent.change(screen.getByLabelText('Replacement profile ID'), { target: { value: '22' } });
    expect(screen.queryByRole('region', { name: 'Correction preview' })).not.toBeInTheDocument();
    expect(request).toHaveBeenCalledTimes(1);
  });

  it('shows stale rejection without success and requires a fresh preview', async () => {
    await openPreview();
    fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'Verified identity' } });
    fireEvent.click(screen.getByRole('checkbox'));
    request.mockResolvedValueOnce(response({ detail: 'Saved participant changed; preview again before confirming' }, false));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm participant correction' }));
    await screen.findByRole('alert');
    expect(screen.getByRole('alert')).toHaveTextContent('Saved participant changed');
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Correction preview' })).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Preview correction' })).not.toBeDisabled());
  });
});
