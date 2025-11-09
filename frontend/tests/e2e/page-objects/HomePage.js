export class HomePage {
  constructor(page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');

    // Click "Browse Without Login" to dismiss splash screen and access main app
    try {
      await this.page.click('text=/Browse Without Login/i', { timeout: 5000 });
      await this.page.waitForLoadState('networkidle');
    } catch (e) {
      // Splash screen may not appear, continue
    }
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
    // Wait for the navigation bar to be visible (indicates main app has loaded)
    await this.page.waitForSelector('button:has-text("Home")', { state: 'visible' });
    // Wait for the homepage welcome message
    await this.page.waitForSelector('text=/Welcome to Wolf Goat Pig/i', { state: 'visible' });
  }
}
