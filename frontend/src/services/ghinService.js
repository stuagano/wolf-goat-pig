import { GhinClient } from 'ghin';

class GHINService {
  constructor() {
    this.client = null;
    this.initialized = false;
  }

  /**
   * Initialize GHIN client with credentials
   * @param {string} username - GHIN username
   * @param {string} password - GHIN password
   */
  async initialize(username, password) {
    try {
      this.client = new GhinClient(username, password);
      await this.client.login();
      this.initialized = true;
      console.log('GHIN client initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize GHIN client:', error);
      this.initialized = false;
      return false;
    }
  }

  /**
   * Check if GHIN service is initialized and authenticated
   */
  isInitialized() {
    return this.initialized && this.client;
  }

  /**
   * Get golfer information by GHIN ID
   * @param {string} ghinId - GHIN ID of the golfer
   */
  async getGolferInfo(ghinId) {
    if (!this.isInitialized()) {
      throw new Error('GHIN service not initialized. Please login first.');
    }

    try {
      const golferInfo = await this.client.getGolfer(ghinId);
      return {
        ghinId: golferInfo.ghinId || ghinId,
        name: golferInfo.name,
        handicapIndex: golferInfo.handicapIndex,
        club: golferInfo.club,
        lastUpdated: golferInfo.lastUpdated,
        recentScores: golferInfo.recentScores || []
      };
    } catch (error) {
      console.error(`Failed to get golfer info for GHIN ID ${ghinId}:`, error);
      throw error;
    }
  }

  /**
   * Get recent scores for a golfer
   * @param {string} ghinId - GHIN ID of the golfer
   * @param {number} limit - Number of recent scores to fetch (default: 20)
   */
  async getRecentScores(ghinId, limit = 20) {
    if (!this.isInitialized()) {
      throw new Error('GHIN service not initialized. Please login first.');
    }

    try {
      const scores = await this.client.getScores(ghinId, limit);
      return scores.map(score => ({
        date: score.date,
        course: score.course,
        tees: score.tees,
        score: score.score,
        courseRating: score.courseRating,
        slopeRating: score.slopeRating,
        differential: score.differential,
        posted: score.posted
      }));
    } catch (error) {
      console.error(`Failed to get recent scores for GHIN ID ${ghinId}:`, error);
      throw error;
    }
  }

  /**
   * Get handicap index for a golfer
   * @param {string} ghinId - GHIN ID of the golfer
   */
  async getHandicapIndex(ghinId) {
    if (!this.isInitialized()) {
      throw new Error('GHIN service not initialized. Please login first.');
    }

    try {
      const golferInfo = await this.getGolferInfo(ghinId);
      return {
        ghinId: ghinId,
        handicapIndex: golferInfo.handicapIndex,
        lastUpdated: golferInfo.lastUpdated
      };
    } catch (error) {
      console.error(`Failed to get handicap index for GHIN ID ${ghinId}:`, error);
      throw error;
    }
  }

  /**
   * Get multiple golfers' information in batch
   * @param {string[]} ghinIds - Array of GHIN IDs
   */
  async getBatchGolferInfo(ghinIds) {
    if (!this.isInitialized()) {
      throw new Error('GHIN service not initialized. Please login first.');
    }

    const results = [];
    const errors = [];

    for (const ghinId of ghinIds) {
      try {
        const golferInfo = await this.getGolferInfo(ghinId);
        results.push(golferInfo);
      } catch (error) {
        errors.push({ ghinId, error: error.message });
        console.warn(`Failed to fetch data for GHIN ID ${ghinId}:`, error.message);
      }
    }

    return {
      success: results,
      errors: errors,
      totalRequested: ghinIds.length,
      totalSuccess: results.length,
      totalErrors: errors.length
    };
  }

  /**
   * Search for golfers by name (if supported by the API)
   * @param {string} name - Name to search for
   */
  async searchGolfers(name) {
    if (!this.isInitialized()) {
      throw new Error('GHIN service not initialized. Please login first.');
    }

    try {
      // Note: This method might not be available in all versions of the GHIN API
      const results = await this.client.searchGolfers(name);
      return results.map(golfer => ({
        ghinId: golfer.ghinId,
        name: golfer.name,
        club: golfer.club,
        handicapIndex: golfer.handicapIndex
      }));
    } catch (error) {
      console.error(`Failed to search for golfers named ${name}:`, error);
      throw error;
    }
  }

  /**
   * Post a score for a golfer (if supported)
   * @param {string} ghinId - GHIN ID of the golfer
   * @param {Object} scoreData - Score information
   */
  async postScore(ghinId, scoreData) {
    if (!this.isInitialized()) {
      throw new Error('GHIN service not initialized. Please login first.');
    }

    try {
      const result = await this.client.postScore(ghinId, {
        date: scoreData.date,
        course: scoreData.course,
        tees: scoreData.tees,
        score: scoreData.score,
        courseRating: scoreData.courseRating,
        slopeRating: scoreData.slopeRating
      });
      return result;
    } catch (error) {
      console.error(`Failed to post score for GHIN ID ${ghinId}:`, error);
      throw error;
    }
  }

  /**
   * Logout and cleanup
   */
  async logout() {
    if (this.client) {
      try {
        await this.client.logout();
      } catch (error) {
        console.warn('Error during logout:', error);
      }
      this.client = null;
      this.initialized = false;
    }
  }
}

// Create singleton instance
const ghinService = new GHINService();

// Helper function to initialize with environment variables or stored credentials
export const initializeGHIN = async (username, password) => {
  if (!username || !password) {
    // Try to get from environment variables
    username = process.env.REACT_APP_GHIN_USERNAME;
    password = process.env.REACT_APP_GHIN_PASSWORD;
  }

  if (!username || !password) {
    console.warn('GHIN credentials not provided. GHIN integration will be disabled.');
    return false;
  }

  return await ghinService.initialize(username, password);
};

export default ghinService;