import { waitForHoleCompletion } from '../utils/test-helpers.js';
import { setAllQuarters } from '../tests/scenarios/quarters-helpers.js';

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
    await this.page.waitForSelector('[data-testid="current-hole"]', {
      timeout: 5000
    });

    const currentHole = await this.page.locator('[data-testid="current-hole"]').textContent();
    const holeNum = parseInt(currentHole.replace(/[^0-9]/g, ''), 10);
    if (holeNum !== holeNumber) {
      throw new Error(`Expected hole ${holeNumber}, but on hole ${holeNum}`);
    }

    // Team formation (quarters-only flow — golf scores are optional)
    if (scoreData.solo) {
      await this.goSolo();
    } else if (scoreData.partnership) {
      await this.selectPartner(scoreData.partnership.partner);
    }

    if (scoreData.floatInvokedBy) {
      await this.invokeFloat(scoreData.floatInvokedBy);
    }

    if (scoreData.joesSpecialWager) {
      await this.setJoesSpecialWager(scoreData.joesSpecialWager);
    }

    if (scoreData.push) {
      await this.page.click('[data-testid="push-hole-button"]');
    } else if (scoreData.quarters) {
      const entries = Object.entries(scoreData.quarters);
      for (const [playerId, value] of entries) {
        await this.page.fill(`[data-testid="quarters-input-${playerId}"]`, String(value));
      }
    } else if (scoreData.quartersList && scoreData.players) {
      await setAllQuarters(this.page, scoreData.players, scoreData.quartersList);
    }

    // Optional golf scores (collapsed panel — expand if needed)
    if (scoreData.scores) {
      for (const [playerId, score] of Object.entries(scoreData.scores)) {
        await this.enterScore(playerId, score);
      }
    }

    await this.clickCompleteHole();
    await waitForHoleCompletion(this.page, holeNumber);
  }

  async enterScore(playerId, score) {
    const selector = `[data-testid="score-input-${playerId}"]`;
    const input = this.page.locator(selector);
    if (!(await input.isVisible().catch(() => false))) {
      const toggle = this.page.getByRole('button', { name: /golf scores/i });
      if (await toggle.isVisible().catch(() => false)) {
        await toggle.click();
      }
    }
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
    await this.page.waitForSelector('[data-testid="current-hole"]', {
      timeout: 5000
    });

    const currentHole = await this.page.locator('[data-testid="current-hole"]').textContent();
    const holeNum = parseInt(currentHole.replace(/[^0-9]/g, ''), 10);
    if (holeNum !== nextHole) {
      throw new Error(`Expected to advance to hole ${nextHole}, but on hole ${holeNum}`);
    }
  }

  async getCurrentHole() {
    const holeText = await this.page.locator('[data-testid="current-hole"]').textContent();
    return parseInt(holeText.replace(/[^0-9]/g, ''), 10);
  }

  async getCurrentWager() {
    const wagerText = await this.page.locator('[data-testid="current-wager"]').textContent();
    return parseInt(wagerText.replace(/[^0-9]/g, ''), 10);
  }

  async expectCarryOverBadge(visible) {
    const badge = this.page.locator('[data-testid="carry-over-badge"]');
    if (visible) {
      await badge.waitFor({ state: 'visible', timeout: 5000 });
    } else {
      await badge.waitFor({ state: 'hidden', timeout: 5000 });
    }
  }

  async getPlayerPoints(playerId) {
    const pointsText = await this.page.locator(`[data-testid="player-${playerId}-points"]`).textContent();
    return parseFloat(pointsText.replace(/[^0-9.-]/g, '')) || 0;
  }
}
