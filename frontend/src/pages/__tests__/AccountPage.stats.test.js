/**
 * Account personal stats used to come only from localStorage, so club history
 * vanished on a new device / domain. These cover mapping server history into
 * the panel shape (rounds, quarters, recent list).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchClubHistory, mapClubHistoryToStats } from '../AccountPage';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('mapClubHistoryToStats', () => {
  it('maps club history onto the stats panel shape', () => {
    expect(
      mapClubHistoryToStats({
        found: true,
        rounds_played: 61,
        total_quarters: -3372,
        average_per_round: -55.3,
        best_round: 716,
        recent_rounds: [
          {
            date: '2026-08-24',
            date_display: '24-Aug',
            score: -58,
            location: 'Wing Point',
          },
        ],
      }),
    ).toEqual({
      gamesPlayed: 61,
      totalEarnings: -3372,
      averageScore: -55.3,
      bestScore: 716,
      recentGames: [
        {
          date: '2026-08-24',
          score: -58,
          earnings: -58,
          course: 'Wing Point',
        },
      ],
    });
  });

  it('returns null when the member has no club history', () => {
    expect(mapClubHistoryToStats({ found: false, rounds_played: 0 })).toBeNull();
    expect(mapClubHistoryToStats(null)).toBeNull();
  });
});

describe('fetchClubHistory', () => {
  it('requests the authenticated history endpoint', async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        found: true,
        rounds_played: 2,
        total_quarters: 10,
        average_per_round: 5,
        best_round: 12,
        recent_rounds: [],
      }),
    }));
    vi.stubGlobal('fetch', fetchMock);

    await expect(fetchClubHistory('tok')).resolves.toMatchObject({
      gamesPlayed: 2,
      totalEarnings: 10,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain('/players/me/history');
    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer tok');
  });

  it('returns null instead of throwing when the request fails', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => {
      throw new Error('network down');
    }));

    await expect(fetchClubHistory('tok')).resolves.toBeNull();
  });

  it('returns null when the endpoint is not ok', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: false,
      status: 401,
      json: async () => ({}),
    })));

    await expect(fetchClubHistory('tok')).resolves.toBeNull();
  });
});
