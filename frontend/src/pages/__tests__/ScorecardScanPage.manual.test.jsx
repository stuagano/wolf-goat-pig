import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ScorecardScanPage from '../ScorecardScanPage';

vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => fetch }));
it('real scan parent seeds an editable roster when players is empty and only pickedPlayers are supplied', async () => {
  const names = ['Avery', 'Blair', 'Casey', 'Drew'];
  fetch.mockImplementation(async url => ({ ok: true, json: async () => String(url).includes('legacy-players') ? { players: names } : [] }));
  render(<MemoryRouter><ScorecardScanPage /></MemoryRouter>);
  fireEvent.click(await screen.findByText(/Record a completed scorecard as a new round/));
  for (const name of names) fireEvent.click(await screen.findByRole('checkbox', { name }));
  fireEvent.click(screen.getByRole('button', { name: /Continue/ }));
  fireEvent.click(screen.getByRole('button', { name: /Enter manually/ }));
  names.forEach((name, index) => {
    expect(screen.getByLabelText(`Map scanned row ${index + 1}`)).toHaveValue(String(index));
    expect(screen.getByLabelText(`${name} final total`)).toHaveValue('');
  });
  fireEvent.change(screen.getByLabelText('Map scanned row 1'), { target: { value: '1' } });
  expect(screen.getByLabelText('Map scanned row 1')).toHaveValue('1');
  expect(fetch.mock.calls.every(([, options]) => !options?.method)).toBe(true);
});
