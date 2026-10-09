import React, { useMemo, useState } from 'react';

function matches(game, filters) {
  const player = filters.player.trim().toLowerCase();
  const date = filters.date.trim().toLowerCase();
  const location = filters.location.trim().toLowerCase();
  const score = filters.score.trim();
  if (player && !game.players.some((p) => p.member.toLowerCase().includes(player))) return false;
  if (date && !`${game.date} ${game.date_sortable}`.toLowerCase().includes(date)) return false;
  if (location && !(game.location || '').toLowerCase().includes(location)) return false;
  if (score !== '' && !game.players.some((p) => String(p.quarters) === score)) return false;
  return true;
}

export default function RoundsDetail({ games }) {
  const [filters, setFilters] = useState({ player: '', date: '', score: '', location: '' });
  const visible = useMemo(() => games.filter((game) => matches(game, filters)), [games, filters]);

  const set = (key) => (event) => setFilters((prev) => ({ ...prev, [key]: event.target.value }));

  return (
    <div>
      <div className="px-6 py-4 bg-gray-50 border-b">
        <h2 className="text-xl font-semibold text-gray-900">Round details</h2>
        <p className="text-sm text-gray-500 mt-1">Most recent current-season rounds first</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 p-4 border-b">
        <label className="text-xs font-medium text-gray-600">
          Player
          <input aria-label="Filter by player" value={filters.player} onChange={set('player')} className="mt-1 w-full border rounded px-2 py-1 text-sm" />
        </label>
        <label className="text-xs font-medium text-gray-600">
          Date
          <input aria-label="Filter by date" value={filters.date} onChange={set('date')} className="mt-1 w-full border rounded px-2 py-1 text-sm" />
        </label>
        <label className="text-xs font-medium text-gray-600">
          Score
          <input aria-label="Filter by score" value={filters.score} onChange={set('score')} className="mt-1 w-full border rounded px-2 py-1 text-sm" />
        </label>
        <label className="text-xs font-medium text-gray-600">
          Location
          <input aria-label="Filter by location" value={filters.location} onChange={set('location')} className="mt-1 w-full border rounded px-2 py-1 text-sm" />
        </label>
      </div>
      {visible.length === 0 ? (
        <div className="p-8 text-center text-gray-600">No rounds match those filters.</div>
      ) : (
        <ul className="divide-y divide-gray-200">
          {visible.map((game) => (
            <li key={`${game.date_sortable}-${game.group}-${game.location}`} className="px-6 py-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div className="text-sm font-semibold text-gray-900">{game.date}</div>
                <div className="text-sm text-gray-600">{game.location || 'Unknown location'}</div>
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {game.players.map((player) => (
                  <span key={player.member} className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-1 text-sm">
                    <span className="font-medium text-gray-900">{player.member}</span>
                    <span className="text-gray-600">{player.quarters}</span>
                  </span>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
