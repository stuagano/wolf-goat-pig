import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Leaderboard from '../Leaderboard';
import { api } from '../../../api/client';
import { FeaturesProvider } from '../../../hooks/useFeatureFlags';

vi.mock('../../../context', () => {
  const syncData = [];
  return { useSheetSync: () => ({ syncData, syncStatus: 'idle' }) };
});
vi.mock('../../../api/client', () => ({ api: { GET: vi.fn() } }));

test.each([false, true])('LivSow team lookup respects the runtime flag: %s', async (enabled) => {
  api.GET.mockReset().mockResolvedValue({ data: {} });
  global.fetch.mockResolvedValue({
    json: async () => ({ features: { livsow: enabled } }),
  });
  render(<MemoryRouter><FeaturesProvider><Leaderboard /></FeaturesProvider></MemoryRouter>);
  await screen.findByText('No Data Yet');
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  if (enabled) {
    await waitFor(() => expect(api.GET).toHaveBeenCalledWith('/data/livsow/team-map'));
  } else {
    expect(api.GET).not.toHaveBeenCalledWith('/data/livsow/team-map');
  }
});
