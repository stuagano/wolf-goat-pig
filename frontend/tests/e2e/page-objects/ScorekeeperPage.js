import { waitForHoleCompletion } from '../utils/test-helpers.js';

export class ScorekeeperPage {
  constructor(page) {
    this.page = page;
  }

  async verifyGameLoaded(gameId) {
    await this.page.waitForFunction(
      (id) => window.localStorage.getItem('wgp_current_game') === id,
      gameId,
      { timeout: 10000 }
    );

    await this.page.waitForSelector('[data-testid="scorekeeper-container"]', {
      timeout: 10000
    });
  }

  async playHole(holeNumber, scoreData) {
    // Verify we're on the correct hole
    await this.page.waitForSelector(`[data-testid="current-hole"]`, {
      timeout: 5000
    });

    const currentHole = await this.page.locator('[data-testid="current-hole"]').textContent();
    if (parseInt(currentHole) !== holeNumber) {
      throw new Error(`Expected hole ${holeNumber}, but on hole ${currentHole}`);
    }

    // Enter scores for all players
    for (const [playerId, score] of Object.entries(scoreData.scores)) {
      await this.enterScore(playerId, score);
    }

    // Handle team formation
    if (scoreData.solo) {
      await this.goSolo();
    } else if (scoreData.partnership) {
      await this.selectPartner(scoreData.partnership.partner);
    }

    // Handle special rules
    if (scoreData.floatInvokedBy) {
      await this.invokeFloat(scoreData.floatInvokedBy);
    }

    if (scoreData.joesSpecialWager) {
      await this.setJoesSpecialWager(scoreData.joesSpecialWager);
    }

    // Complete hole
    await this.clickCompleteHole();
    await waitForHoleCompletion(this.page, holeNumber);
  }

  async enterScore(playerId, score) {
    const selector = `[data-testid="score-input-${playerId}"]`;
    await this.page.fill(selector, score.toString());
  }

  async selectPartner(partnerId) {
    await this.page.click(`[data-testid="partner-${partnerId}"]`);
  }

  async goSolo() {
    await this.page.click('[data-testid="go-solo-button"]');
  }

  async invokeFloat(playerId) {
    await this.page.click(`[data-testid="float-button-${playerId}"]`);
  }

  async setJoesSpecialWager(wager) {
    await this.page.fill('[data-testid="joes-special-wager-input"]', wager.toString());
  }

  async clickCompleteHole() {
    await this.page.click('[data-testid="complete-hole-button"]');
  }

  async verifyHoleCompleted(holeNumber) {
    const nextHole = holeNumber + 1;
    await this.page.waitForSelector(`[data-testid="current-hole"]`, {
      timeout: 5000
    });

    const currentHole = await this.page.locator('[data-testid="current-hole"]').textContent();
    if (parseInt(currentHole) !== nextHole) {
      throw new Error(`Expected to advance to hole ${nextHole}, but on hole ${currentHole}`);
    }
  }

  async getCurrentHole() {
    const holeText = await this.page.locator('[data-testid="current-hole"]').textContent();
    return parseInt(holeText);
  }

  async getPlayerPoints(playerId) {
    const pointsText = await this.page.locator(`[data-testid="player-${playerId}-points"]`).textContent();
    return parseInt(pointsText.replace(/[^0-9-]/g, ''));
  }
}
