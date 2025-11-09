import { assertPointsBalanceToZero, assertGameCompleted } from '../utils/assertions.js';

export class GameCompletionPage {
  constructor(page) {
    this.page = page;
  }

  async verifyFinalStandings() {
    await this.page.waitForSelector('[data-testid="final-standings"]', {
      timeout: 10000
    });

    await assertGameCompleted(this.page);
  }

  async verifyPointsBalanceToZero() {
    await assertPointsBalanceToZero(this.page);
  }

  async getFinalStandings() {
    const standings = [];
    const playerRows = await this.page.locator('[data-testid="player-standing-row"]').all();

    for (const row of playerRows) {
      const name = await row.locator('[data-testid="player-name"]').textContent();
      const points = await row.locator('[data-testid="player-total-points"]').textContent();

      standings.push({
        name: name.trim(),
        points: parseInt(points.replace(/[^0-9-]/g, ''))
      });
    }

    return standings;
  }

  async verifyWinner(expectedWinnerName) {
    const standings = await this.getFinalStandings();
    const winner = standings[0]; // Assuming sorted by points descending

    if (winner.name !== expectedWinnerName) {
      throw new Error(`Expected winner ${expectedWinnerName}, but got ${winner.name}`);
    }
  }

  async verifyGameStatus() {
    const status = await this.page.locator('[data-testid="game-status"]').textContent();
    return status.toLowerCase().includes('completed');
  }
}
