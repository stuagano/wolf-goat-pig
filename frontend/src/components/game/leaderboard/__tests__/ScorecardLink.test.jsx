/**
 * A round is only linkable to a scorecard when the backend gave it a saved
 * game id. Anything else (sheet-only rows, ambiguous matches) must render no
 * link at all — a guessed link would open someone else's card.
 */
import React from 'react';
import { describe, test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ScorecardLink from '../ScorecardLink';
import { scorecardPath, roundPath } from '../roundLink';

const GAME_ID = '11111111-2222-4333-8444-555555555555';

describe('scorecardPath', () => {
  test('builds /game/{game_id} for a real saved game', () => {
    expect(scorecardPath({ game_id: GAME_ID })).toBe(`/game/${GAME_ID}`);
  });

  test.each([
    ['missing key', {}],
    ['undefined', { game_id: undefined }],
    ['null', { game_id: null }],
    ['empty string', { game_id: '' }],
    ['whitespace', { game_id: '   ' }],
    ['no argument', undefined],
  ])('returns null for %s rather than a fake path', (_label, round) => {
    expect(scorecardPath(round)).toBeNull();
  });

  test('never derives an id from date, group, or location', () => {
    expect(scorecardPath({ date_sortable: '2026-10-25', group: 'A', location: 'Wing Point' })).toBeNull();
  });

  test('story links are unchanged by the scorecard helper', () => {
    expect(roundPath({ date: '25-Oct', date_sortable: '2026-10-25', group: 'A', location: 'Wing Point' }))
      .toBe('/rounds/2026-10-25/A?location=Wing+Point');
  });
});

describe('ScorecardLink', () => {
  test('renders a link to the card when a game id is present', () => {
    render(
      <MemoryRouter>
        <ScorecardLink gameId={GAME_ID} />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: /Scorecard/ })).toHaveAttribute('href', `/game/${GAME_ID}`);
  });

  test.each([null, undefined, ''])('renders nothing for game id %s', (gameId) => {
    const { container } = render(
      <MemoryRouter>
        <ScorecardLink gameId={gameId} />
      </MemoryRouter>,
    );
    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByRole('link')).toBeNull();
  });
});
