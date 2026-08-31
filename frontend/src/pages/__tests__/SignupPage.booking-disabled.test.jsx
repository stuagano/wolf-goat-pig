import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { vi, test, expect } from 'vitest';
import SignupPage from '../SignupPage';

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({ isAuthenticated: true, user: { name: 'Player' } }),
}));
vi.mock('../../components/signup/DailySignupView', () => ({
  default: () => <div>Daily signup sheet</div>,
}));
vi.mock('../../components/foretees/ForeTeesTeeSheet', () => ({
  default: () => <div>ForeTees booking sheet</div>,
}));

function Location() {
  return <div data-testid="location">{useLocation().search}</div>;
}

test('retired booking links show daily signups and no booking tab', async () => {
  render(<MemoryRouter initialEntries={['/signup?tab=tee-times']}>
    <SignupPage /><Location />
  </MemoryRouter>);
  expect(screen.getByText('Daily signup sheet')).toBeInTheDocument();
  expect(screen.queryByText('ForeTees booking sheet')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /Book Tee Time/i })).not.toBeInTheDocument();
  await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('?tab=calendar'));
});
