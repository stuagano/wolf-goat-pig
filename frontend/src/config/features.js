// Booking is paused. Re-enable alongside the API's FORETEES_ENABLED setting.
export const FORETEES_ENABLED = false;

// Static defaults — overridden at runtime by /config/features API response.
export const FEATURE_DEFAULTS = {
  foretees: false,
  scorecard_scan: true,
  livsow: false,
  commissioner_chat: true,
  stuart_mode: false,
};
