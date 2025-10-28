// frontend/src/components/simulation/visual/utils/oddsHelpers.js

/**
 * Get color based on probability threshold
 * @param {number} probability - Probability value between 0 and 1
 * @returns {string} Material-UI color: 'success', 'warning', or 'disabled'
 */
export const getProbabilityColor = (probability) => {
  if (probability > 0.6) return 'success';
  if (probability >= 0.4) return 'warning';
  return 'disabled';
};

/**
 * Format expected value with +/- sign and one decimal place
 * @param {number} value - Expected value (can be positive or negative)
 * @returns {string} Formatted string like "+2.3" or "-1.5"
 */
export const formatExpectedValue = (value) => {
  const formatted = value.toFixed(1);
  return value >= 0 ? `+${formatted}` : formatted;
};

/**
 * Get color based on risk level
 * @param {string} riskLevel - Risk level: 'low', 'medium', 'high'
 * @returns {string} Material-UI color
 */
export const getRiskLevelColor = (riskLevel) => {
  const colors = {
    low: 'success',
    medium: 'warning',
    high: 'error'
  };
  return colors[riskLevel] || 'default';
};

/**
 * Get human-readable label for probability
 * @param {number} probability - Probability value between 0 and 1
 * @returns {string} Label: 'Likely', 'Possible', or 'Unlikely'
 */
export const getProbabilityLabel = (probability) => {
  if (probability > 0.6) return 'Likely';
  if (probability >= 0.4) return 'Possible';
  return 'Unlikely';
};
