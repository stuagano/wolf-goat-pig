import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DailySignupView from '../DailySignupView';

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({ isAuthenticated: false }),
}));
vi.mock('react-router-dom', () => ({ useNavigate: () => vi.fn() }));
vi.mock('../../../hooks/usePlayerProfile', () => ({
  usePlayerProfile: () => ({ profile: null, loading: false, isAdmin: false }),
}));

const dayButtons = () => screen.getAllByRole('button', {
  name: /^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)( \(\d+\))?$/,
}).map(button => button.textContent);

const requestedWeeks = () => fetch.mock.calls
  .map(([request]) => new URL(request.url))
  .filter(url => url.pathname === '/signups/weekly-with-messages')
  .map(url => url.searchParams.get('week_start'));

const emptyDay = date => ({ date, signups: [], total_count: 0, messages: [], message_count: 0 });

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] });
  fetch.mockImplementation(request => {
    const url = new URL(request.url);
    const weekStart = url.searchParams.get('week_start');
    const data = url.pathname === '/signups/weekly-with-messages'
      ? { week_start: weekStart, daily_summaries: [emptyDay(weekStart)] }
      : { text: '' };
    return Promise.resolve(new Response(JSON.stringify(data), {
      status: 200, headers: { 'Content-Type': 'application/json' },
    }));
  });
});

afterEach(() => vi.useRealTimers());

test.each([
  ['2026-10-10', 'Saturday, October 10', ['Sat', 'Sun'], 'Sat - Sun: Oct 10 - Oct 11', '2026-10-05'],
  ['2026-10-11', 'Sunday, October 11', ['Sun'], 'Sun: Oct 11', '2026-10-05'],
  ['2026-10-12', 'Monday, October 12', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], 'Mon - Sun: Oct 12 - Oct 18', '2026-10-12'],
])('opens on today with Sunday ending the week on %s', async (today, heading, days, range, weekStart) => {
  vi.setSystemTime(new Date(`${today}T19:00:00Z`));
  render(<DailySignupView />);

  expect(await screen.findByRole('heading', { name: `Signed up for ${heading}` })).toBeInTheDocument();
  expect(dayButtons()).toEqual(days);
  expect(screen.getByText(range)).toBeInTheDocument();
  expect(requestedWeeks()).toEqual([weekStart]);
  expect(screen.getByRole('button', { name: 'Previous Week' })).toBeDisabled();
});

test('keeps Sunday selected across next/previous weeks at a year boundary', async () => {
  vi.setSystemTime(new Date('2026-12-27T20:00:00Z'));
  render(<DailySignupView />);
  expect(await screen.findByRole('heading', { name: 'Signed up for Sunday, December 27' })).toBeInTheDocument();

  fireEvent.click(screen.getByRole('button', { name: 'Next Week' }));
  expect(await screen.findByRole('heading', { name: 'Signed up for Sunday, January 3' })).toBeInTheDocument();
  expect(dayButtons()).toEqual(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']);
  expect(screen.getByText('Mon - Sun: Dec 28 - Jan 3')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Previous Week' })).toBeEnabled();

  fireEvent.click(screen.getByRole('button', { name: 'Previous Week' }));
  expect(await screen.findByRole('heading', { name: 'Signed up for Sunday, December 27' })).toBeInTheDocument();
  expect(dayButtons()).toEqual(['Sun']);
  expect(requestedWeeks()).toEqual(['2026-12-21', '2026-12-28', '2026-12-21']);
  expect(screen.getByRole('button', { name: 'Previous Week' })).toBeDisabled();
});

test.each([
  ['2026-10-11', 'Sunday, October 11', '2026-10-05'],
  ['2026-10-18', 'Sunday, October 18', '2026-10-12'],
  ['2026-10-12', 'Monday, October 12', '2026-10-12'],
  ['2026-10-09', 'Saturday, October 10', '2026-10-05'],
])('honors upcoming initial date %s and clamps past dates to today', async (initialDate, heading, weekStart) => {
  vi.setSystemTime(new Date('2026-10-10T19:00:00Z'));
  render(<DailySignupView selectedDate={initialDate} />);
  expect(await screen.findByRole('heading', { name: `Signed up for ${heading}` })).toBeInTheDocument();
  expect(requestedWeeks()).toEqual([weekStart]);
});

test('loads Sunday players and messages from the Monday request without Next Week', async () => {
  vi.setSystemTime(new Date('2026-10-10T19:00:00Z'));
  fetch.mockImplementation(request => {
    const url = new URL(request.url);
    const data = url.pathname === '/signups/weekly-with-messages'
      ? {
        week_start: '2026-10-05',
        daily_summaries: [emptyDay('2026-10-10'), {
          date: '2026-10-11', total_count: 1, message_count: 1,
          signups: [{ id: 1, player_name: 'Sunday Golfer', status: 'signed_up' }],
          messages: [{ id: 2, player_name: 'Sunday Golfer', message: 'See you Sunday' }],
        }],
      }
      : { text: '' };
    return Promise.resolve(new Response(JSON.stringify(data), {
      status: 200, headers: { 'Content-Type': 'application/json' },
    }));
  });
  render(<DailySignupView />);
  expect(await screen.findByRole('heading', { name: 'Signed up for Saturday, October 10' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Sun (1)' }));
  expect(screen.getByRole('heading', { name: 'Signed up for Sunday, October 11' })).toBeInTheDocument();
  expect(screen.getByRole('cell', { name: 'Sunday Golfer' })).toBeInTheDocument();
  expect(screen.getByText('See you Sunday')).toBeInTheDocument();
  expect(requestedWeeks()).toEqual(['2026-10-05']);
});
