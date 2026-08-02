import React from 'react';
import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TeamSelector from '../TeamSelector';

const theme = {
  colors: {
    primary: '#059669',
    paper: '#fff',
    border: '#e5e7eb',
    textPrimary: '#111',
    textSecondary: '#666',
  },
};

const players4 = [
  { id: 'p1', name: 'Alice Park', is_authenticated: true },
  { id: 'p2', name: 'Bob Smith', is_authenticated: false },
  { id: 'p3', name: 'Carol Lee', is_authenticated: false },
  { id: 'p4', name: 'Dave Ng', is_authenticated: false },
];

const players5 = [
  ...players4,
  { id: 'p5', name: 'Eve Aard', is_authenticated: false },
];

const base = {
  theme,
  team1: [],
  captain: 'p1',
  duncanInvoked: false,
  setDuncanInvoked: vi.fn(),
  setTeamMode: vi.fn(),
  togglePlayerTeam: vi.fn(),
  toggleCaptain: vi.fn(),
  announceAction: vi.fn(),
  showTeamSelection: true,
  setShowTeamSelection: vi.fn(),
  aardvarkRequestedTeam: null,
  setAardvarkRequestedTeam: vi.fn(),
  aardvarkTossed: false,
  setAardvarkTossed: vi.fn(),
  aardvarkSolo: false,
  setAardvarkSolo: vi.fn(),
  invisibleAardvarkTossed: false,
  setInvisibleAardvarkTossed: vi.fn(),
};

describe('TeamSelector', () => {
  test('switches to solo mode and shows Duncan control', () => {
    const setTeamMode = vi.fn();
    const { rerender } = render(
      <TeamSelector {...base} players={players4} teamMode="partners" setTeamMode={setTeamMode} />,
    );

    fireEvent.click(screen.getByTestId('go-solo-button'));
    expect(setTeamMode).toHaveBeenCalledWith('solo');

    rerender(
      <TeamSelector {...base} players={players4} teamMode="solo" setTeamMode={setTeamMode} />,
    );
    expect(screen.getByText(/Call The Duncan/i)).toBeInTheDocument();
  });

  test('calling Duncan toggles the flag and announces when captain is set', () => {
    const setDuncanInvoked = vi.fn();
    const announceAction = vi.fn();
    render(
      <TeamSelector
        {...base}
        players={players4}
        teamMode="solo"
        captain="p1"
        duncanInvoked={false}
        setDuncanInvoked={setDuncanInvoked}
        announceAction={announceAction}
      />,
    );

    fireEvent.click(screen.getByText(/Call The Duncan/i));
    expect(setDuncanInvoked).toHaveBeenCalledWith(true);
    expect(announceAction).toHaveBeenCalledWith('duncan', 'p1');
  });

  test('partners mode toggles a player onto Team 1', () => {
    const togglePlayerTeam = vi.fn();
    render(
      <TeamSelector
        {...base}
        players={players4}
        teamMode="partners"
        team1={[]}
        togglePlayerTeam={togglePlayerTeam}
      />,
    );

    fireEvent.click(screen.getByTestId('partner-p2'));
    expect(togglePlayerTeam).toHaveBeenCalledWith('p2');
  });

  test('5-man game shows aardvark controls once Team 1 has two players', () => {
    const setAardvarkRequestedTeam = vi.fn();
    const setAardvarkTossed = vi.fn();
    render(
      <TeamSelector
        {...base}
        players={players5}
        teamMode="partners"
        team1={['p1', 'p2']}
        setAardvarkRequestedTeam={setAardvarkRequestedTeam}
        setAardvarkTossed={setAardvarkTossed}
      />,
    );

    expect(screen.getByText(/Aardvark/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/→ T1/));
    expect(setAardvarkRequestedTeam).toHaveBeenCalledWith('team1');
    expect(setAardvarkTossed).toHaveBeenCalledWith(false);
  });

  test('aardvark Tossed is disabled until a team is requested', () => {
    render(
      <TeamSelector
        {...base}
        players={players5}
        teamMode="partners"
        team1={['p1', 'p2']}
        aardvarkRequestedTeam={null}
      />,
    );
    expect(screen.getByText('Tossed')).toBeDisabled();
  });
});
