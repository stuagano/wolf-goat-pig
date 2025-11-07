# Karl Marx Rule - Future Implementation

## Rule Description
"If two players are Goat (tied for furthest down), and one is the leader (most quarters), 
the non-leader receives more quarters in the split."

## Implementation Notes
- Requires standings calculation in complete_hole
- Affects points_delta when splitting partners winnings
- Check if winner has tied Goats on their team
- Award extra Q to non-leader Goat

## Status
**Deferred** - Core Phase 2 mechanics (Option, Duncan, Float) are complete. 
Karl Marx is an edge-case tie-breaker that can be added in Phase 3.

## File to Modify
- `backend/app/main.py` - points calculation in complete_hole function
- Add after line ~1360 (partners points_delta calculation)

