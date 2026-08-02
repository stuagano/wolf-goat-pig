/**
 * Hole-submit payload contracts — partners/float/Duncan/aardvark flags must
 * survive into hole history and the /scores optional_details blob. Without
 * that, float-once UI never arms and money rules can't be reconstructed.
 */
import { describe, test, expect } from 'vitest';
import {
  buildHoleSubmitPayload,
  standingsFromHistory,
} from '../useHoleSubmission';

const PLAYERS = [
  { id: 'p1', name: 'Alice' },
  { id: 'p2', name: 'Bob' },
  { id: 'p3', name: 'Carol' },
  { id: 'p4', name: 'Dave' },
];

const FIVE = [
  ...PLAYERS,
  { id: 'p5', name: 'Eve' },
];

describe('buildHoleSubmitPayload', () => {
  test('partners mode fills team2 as everyone not on team1', () => {
    const { teams, holeResult, optionalDetails } = buildHoleSubmitPayload({
      players: PLAYERS,
      teamMode: 'partners',
      team1: ['p1', 'p3'],
      captain: null,
      opponents: [],
      currentHole: 4,
      currentWager: 2,
      phase: 'normal',
      rotationOrder: ['p1', 'p2', 'p3', 'p4'],
      captainIndex: 0,
      scores: { p1: 4, p2: 5, p3: 4, p4: 6 },
      holeNotes: '',
      effectiveQuarters: { p1: '2', p2: '-2', p3: '2', p4: '-2' },
      floatInvokedBy: 'p1',
    });

    expect(teams).toEqual({
      type: 'partners',
      team1: ['p1', 'p3'],
      team2: ['p2', 'p4'],
    });
    expect(holeResult.points_delta).toEqual({ p1: 2, p2: -2, p3: 2, p4: -2 });
    expect(holeResult.float_invoked_by).toBe('p1');
    expect(optionalDetails.float_invoked_by).toBe('p1');
    expect(optionalDetails.teams).toEqual(teams);
  });

  test('solo + Duncan flags land on the hole result and sync details', () => {
    const { holeResult, optionalDetails, teams } = buildHoleSubmitPayload({
      players: PLAYERS,
      teamMode: 'solo',
      team1: [],
      captain: 'p1',
      opponents: ['p2', 'p3', 'p4'],
      currentHole: 7,
      currentWager: 2,
      phase: 'normal',
      rotationOrder: ['p1', 'p2', 'p3', 'p4'],
      captainIndex: 0,
      scores: {},
      holeNotes: null,
      // Duncan 3-for-2 at wager 2: captain +3, opponents -1 each
      effectiveQuarters: { p1: '3', p2: '-1', p3: '-1', p4: '-1' },
      duncanInvoked: true,
    });

    expect(teams).toEqual({
      type: 'solo',
      captain: 'p1',
      opponents: ['p2', 'p3', 'p4'],
    });
    expect(holeResult.duncan_invoked).toBe(true);
    expect(optionalDetails.duncan_invoked).toBe(true);
    expect(Object.values(holeResult.points_delta).reduce((a, b) => a + b, 0)).toBe(0);
  });

  test('aardvark toss flags are persisted for a 5-player hole', () => {
    const { holeResult, optionalDetails } = buildHoleSubmitPayload({
      players: FIVE,
      teamMode: 'partners',
      team1: ['p1', 'p2', 'p5'],
      captain: null,
      opponents: [],
      currentHole: 3,
      currentWager: 1,
      phase: 'normal',
      rotationOrder: ['p1', 'p2', 'p3', 'p4', 'p5'],
      captainIndex: 0,
      scores: {},
      holeNotes: '',
      effectiveQuarters: { p1: '1', p2: '1', p3: '-1', p4: '-1', p5: '0' },
      aardvarkRequestedTeam: 'team1',
      aardvarkTossed: true,
    });

    expect(holeResult.aardvark_requested_team).toBe('team1');
    expect(holeResult.aardvark_tossed).toBe(true);
    expect(optionalDetails.aardvark_tossed).toBe(true);
    expect(optionalDetails.aardvark_requested_team).toBe('team1');
  });
});

describe('standingsFromHistory', () => {
  test('sums quarters and counts solo / float / option usage', () => {
    const history = [
      {
        hole: 1,
        points_delta: { p1: 2, p2: 2, p3: -2, p4: -2 },
        teams: { type: 'partners', team1: ['p1', 'p2'], team2: ['p3', 'p4'] },
        float_invoked_by: 'p1',
      },
      {
        hole: 2,
        points_delta: { p1: 3, p2: -1, p3: -1, p4: -1 },
        teams: { type: 'solo', captain: 'p1', opponents: ['p2', 'p3', 'p4'] },
        duncan_invoked: true,
        option_invoked_by: 'p2',
      },
    ];

    const standings = standingsFromHistory(PLAYERS, history);

    expect(standings.p1.quarters).toBe(5);
    expect(standings.p1.soloCount).toBe(1);
    expect(standings.p1.floatCount).toBe(1);
    expect(standings.p2.optionCount).toBe(1);
    expect(standings.p2.floatCount).toBe(0);
    expect(standings.p3.quarters).toBe(-3);
  });

  test('a second float on the same captain increments floatCount (UI can block)', () => {
    const history = [
      { hole: 1, points_delta: { p1: 0, p2: 0, p3: 0, p4: 0 }, float_invoked_by: 'p1', teams: { type: 'partners', team1: ['p1', 'p2'], team2: ['p3', 'p4'] } },
      { hole: 5, points_delta: { p1: 0, p2: 0, p3: 0, p4: 0 }, float_invoked_by: 'p1', teams: { type: 'partners', team1: ['p1', 'p2'], team2: ['p3', 'p4'] } },
    ];
    const standings = standingsFromHistory(PLAYERS, history);
    expect(standings.p1.floatCount).toBe(2);
  });
});
