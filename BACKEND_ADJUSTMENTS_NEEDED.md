# Backend Adjustments Needed

Based on comprehensive test coverage implementation, the following backend adjustments are needed:

## 1. ping_pong_count not exposed in API response
- **Issue**: The `ping_pong_count` field exists in `BettingState` (line 86 of wolf_goat_pig_simulation.py) but is not included in the betting dict returned by `get_game_state()`
- **Location**: `/backend/app/wolf_goat_pig_simulation.py` lines 1571-1583
- **Fix Required**: Add `"ping_pong_count": hole_state.betting.ping_pong_count,` to the betting dict

## 2. ball_positions_replace flag not working as expected
- **Issue**: The `ball_positions_replace` flag in the seed endpoint should clear all existing ball positions before adding new ones, but currently it only clears positions for players being updated
- **Location**: `/backend/app/main.py` around line 4635
- **Expected Behavior**: When `ball_positions_replace=True`, all existing ball positions should be cleared before adding the new ones
- **Current Behavior**: Other player positions remain even with replace flag set to True

## 3. line_of_scrimmage field placement
- **Issue**: The `line_of_scrimmage` is stored both at the hole_state level and in betting state, which can cause confusion
- **Recommendation**: Standardize on one location (preferably hole_state level) and ensure consistency

## Test Coverage Notes
- All validation tests for invalid player IDs are working correctly
- Team formation transitions (pending -> accepted/declined) are working as expected
- Betting state seeding works but ping_pong_count is not visible in responses
- Special rules invocation tracking is functional