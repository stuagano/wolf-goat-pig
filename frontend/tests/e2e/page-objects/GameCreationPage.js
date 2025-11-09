export class GameCreationPage {
  constructor(page) {
    this.page = page;
  }

  async createTestGame(options = {}) {
    const { playerCount = 4, courseName = 'Wing Point' } = options;

    // Wait for test game creation page to load
    await this.page.waitForSelector('[data-testid="create-test-game-button"]', {
      timeout: 10000
    });

    // Select player count if dropdown exists
    const playerCountSelector = await this.page.$('[data-testid="player-count-select"]');
    if (playerCountSelector) {
      await this.page.selectOption('[data-testid="player-count-select"]', playerCount.toString());
    }

    // Select course if dropdown exists
    const courseSelector = await this.page.$('[data-testid="course-select"]');
    if (courseSelector) {
      await this.page.selectOption('[data-testid="course-select"]', courseName);
    }

    // Click create button
    await this.page.click('[data-testid="create-test-game-button"]');

    // Wait for game to be created and redirected
    await this.page.waitForURL(/\/game\/.+/, { timeout: 15000 });

    // Extract game ID from URL
    const url = this.page.url();
    const gameId = url.match(/\/game\/([^\/]+)/)?.[1];

    if (!gameId) {
      throw new Error('Failed to extract game ID from URL');
    }

    return {
      gameId,
      playerCount,
      courseName
    };
  }

  async verifyGameCreated(gameId) {
    await this.page.waitForSelector(`[data-testid="game-id"][data-game="${gameId}"]`, {
      timeout: 5000
    });
  }
}
