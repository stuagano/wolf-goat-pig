export class HomePage {
  constructor(page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async clickMultiplayerGame() {
    await this.page.click('text=/Create Game/i');
  }

  async clickPracticeMode() {
    await this.page.click('text=/Start Practice/i');
  }

  async clickTestGame() {
    // Open hamburger menu
    await this.page.click('button:has-text("☰")');

    // Click "Test Multiplayer (Dev)" menu item
    await this.page.click('text=/Test Multiplayer/i');
  }

  async verifyHomepageLoaded() {
    await this.page.waitForSelector('text=/Wolf Goat Pig/i');
    await this.page.waitForSelector('text=/Multiplayer Game/i');
  }
}
