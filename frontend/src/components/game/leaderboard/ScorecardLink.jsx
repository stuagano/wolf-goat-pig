import React from 'react';
import { Link } from 'react-router-dom';
import { scorecardPath } from './roundLink';

/**
 * Scorecard entry point for a round that the backend linked to a saved game.
 *
 * Rounds without a `game_id` (sheet-only rows, or app games the backend could
 * not match unambiguously) render nothing — a link that cannot resolve is
 * worse than no link, because it would open an unrelated card.
 */
export default function ScorecardLink({ gameId, className }) {
  const path = scorecardPath({ game_id: gameId });
  if (!path) return null;
  return (
    <Link to={path} className={className} title="View the hole-by-hole scorecard">
      📊 Scorecard
    </Link>
  );
}
