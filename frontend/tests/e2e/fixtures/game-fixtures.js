export const testGames = {
  standard4Man: {
    playerCount: 4,
    courseName: 'Wing Point',
    players: [
      { id: 'test-player-1', name: 'Test Player 1', handicap: 18 },
      { id: 'test-player-2', name: 'Test Player 2', handicap: 15 },
      { id: 'test-player-3', name: 'Test Player 3', handicap: 12 },
      { id: 'test-player-4', name: 'Test Player 4', handicap: 20 }
    ],
    holes: {
      1: {
        scores: {
          'test-player-1': 4,
          'test-player-2': 5,
          'test-player-3': 6,
          'test-player-4': 7
        },
        captain: 'test-player-1',
        partnership: {
          captain: 'test-player-1',
          partner: 'test-player-2'
        },
        expectedPoints: {
          'test-player-1': 3,
          'test-player-2': 3,
          'test-player-3': -3,
          'test-player-4': -3
        }
      },
      2: {
        scores: {
          'test-player-1': 3,
          'test-player-2': 5,
          'test-player-3': 5,
          'test-player-4': 6
        },
        captain: 'test-player-2',
        solo: true,
        expectedPoints: {
          'test-player-1': -3,
          'test-player-2': 9,
          'test-player-3': -3,
          'test-player-4': -3
        }
      },
      3: {
        scores: {
          'test-player-1': 5,
          'test-player-2': 4,
          'test-player-3': 5,
          'test-player-4': 6
        },
        captain: 'test-player-3',
        partnership: {
          captain: 'test-player-3',
          partner: 'test-player-4'
        },
        expectedPoints: {
          'test-player-1': -3,
          'test-player-2': -3,
          'test-player-3': 3,
          'test-player-4': 3
        }
      },
      // Middle holes (4-15) - will be completed via API
      4: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-4', solo: true },
      5: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-1', partnership: { captain: 'test-player-1', partner: 'test-player-3' } },
      6: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-2', solo: true },
      7: { scores: { 'test-player-1': 6, 'test-player-2': 4, 'test-player-3': 5, 'test-player-4': 5 }, captain: 'test-player-3', partnership: { captain: 'test-player-3', partner: 'test-player-1' } },
      8: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-4', partnership: { captain: 'test-player-4', partner: 'test-player-2' } },
      9: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-1', solo: true },
      10: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-2', partnership: { captain: 'test-player-2', partner: 'test-player-4' } },
      11: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-3', solo: true },
      12: { scores: { 'test-player-1': 4, 'test-player-2': 6, 'test-player-3': 5, 'test-player-4': 5 }, captain: 'test-player-4', partnership: { captain: 'test-player-4', partner: 'test-player-3' } },
      13: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-1', partnership: { captain: 'test-player-1', partner: 'test-player-2' } },
      14: { scores: { 'test-player-1': 4, 'test-player-2': 5, 'test-player-3': 5, 'test-player-4': 6 }, captain: 'test-player-2', solo: true },
      15: { scores: { 'test-player-1': 5, 'test-player-2': 4, 'test-player-3': 6, 'test-player-4': 5 }, captain: 'test-player-3', partnership: { captain: 'test-player-3', partner: 'test-player-4' } },
      // Final holes (16-18) - UI testing for special rules
      16: {
        scores: {
          'test-player-1': 4,
          'test-player-2': 5,
          'test-player-3': 6,
          'test-player-4': 5
        },
        captain: 'test-player-4',
        partnership: {
          captain: 'test-player-4',
          partner: 'test-player-1'
        }
      },
      17: {
        scores: {
          'test-player-1': 3,
          'test-player-2': 5,
          'test-player-3': 5,
          'test-player-4': 6
        },
        captain: 'test-player-1',
        hoepfinger: true,
        joesSpecialWager: 8,
        doublePoints: true // Hole 17 has 2x points
      },
      18: {
        scores: {
          'test-player-1': 4,
          'test-player-2': 5,
          'test-player-3': 5,
          'test-player-4': 6
        },
        captain: 'test-player-2',
        solo: true,
        doublePoints: true // Hole 18 has 2x points
      }
    }
  }
};
