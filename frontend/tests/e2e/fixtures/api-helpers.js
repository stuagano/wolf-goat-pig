export class APIHelpers {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async completeHoles(gameId, startHole, endHole, holesData) {
    for (let hole = startHole; hole <= endHole; hole++) {
      const holeData = holesData[hole];
      if (!holeData) continue;

      const response = await fetch(`${this.baseURL}/games/${gameId}/holes/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hole_number: hole,
          scores: holeData.scores,
          captain_id: holeData.captain,
          partner_id: holeData.partnership?.partner || null,
          solo: holeData.solo || false,
          float_invoked_by: holeData.floatInvokedBy || null,
          option_invoked_by: holeData.optionInvokedBy || null,
          joes_special_wager: holeData.joesSpecialWager || null,
          hole_par: 4 // Default par
        })
      });

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`Failed to complete hole ${hole}: ${response.statusText}. Response: ${errorBody}`);
      }
    }
  }

  async deleteGame(gameId) {
    const response = await fetch(`${this.baseURL}/games/${gameId}`, {
      method: 'DELETE'
    });

    // Handle 404 gracefully on cleanup - game may already be deleted
    if (!response.ok && response.status !== 404) {
      const errorBody = await response.text();
      throw new Error(`Failed to delete game ${gameId}: ${response.statusText}. Response: ${errorBody}`);
    }
  }

  async createTestGame(playerCount = 4, courseName = 'Wing Point') {
    const response = await fetch(`${this.baseURL}/games/create-test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        player_count: playerCount,
        course_name: courseName
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to create test game: ${response.statusText}`);
    }

    return response.json();
  }
}
