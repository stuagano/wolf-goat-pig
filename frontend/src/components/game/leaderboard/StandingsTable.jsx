import React from 'react';
import { BANQUET_QUALIFICATION_ROUNDS, SORT_COLUMNS } from './standings';
import PlayerName from './PlayerName';

function SortGlyph({ active, dir }) {
  return (
    <span className="ml-1 inline-flex flex-col leading-none" aria-hidden="true">
      <span className={active && dir === 'asc' ? 'text-blue-700' : 'text-gray-300'}>▲</span>
      <span className={active && dir === 'desc' ? 'text-blue-700' : 'text-gray-300'}>▼</span>
    </span>
  );
}

export default function StandingsTable({
  entries,
  sortKey,
  sortDir,
  onSort,
  teamMap,
  showTeams,
}) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {SORT_COLUMNS.map((column) => {
              const active = sortKey === column.key;
              const label = `Sort by ${column.label}`;
              return (
                <th key={column.key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    type="button"
                    aria-label={label}
                    onClick={() => onSort(column.key)}
                    className="inline-flex items-center uppercase tracking-wider hover:text-gray-900"
                  >
                    {column.label}
                    <SortGlyph active={active} dir={sortDir} />
                  </button>
                </th>
              );
            })}
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Banquet
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {entries.map((entry, index) => {
            const medal = sortKey === 'rank' && sortDir === 'asc' && index < 3;
            const qualified = (entry.rounds || 0) >= BANQUET_QUALIFICATION_ROUNDS;
            return (
              <tr key={`${entry.member || 'player'}-${entry.rank ?? index}`} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center justify-center h-8 w-8 rounded-full text-sm font-medium ${
                    medal && index === 0 ? 'bg-yellow-400 text-yellow-900'
                      : medal && index === 1 ? 'bg-gray-300 text-gray-900'
                        : medal && index === 2 ? 'bg-orange-400 text-orange-900'
                          : 'bg-gray-100 text-gray-600'
                  }`}>
                    {entry.rank ?? index + 1}
                  </span>
                  {medal && <span className="ml-2 text-lg">{index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}</span>}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    <PlayerName name={entry.member} playerId={entry.player_id} />
                  </div>
                  {showTeams && teamMap[entry.member] && (
                    <div className="text-xs text-blue-600 mt-0.5">⛳ {teamMap[entry.member].team}</div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{entry.quarters ?? '—'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{entry.rounds ?? '—'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {entry.average != null ? Number(entry.average).toFixed(1) : '—'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {qualified ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Qualified
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      {BANQUET_QUALIFICATION_ROUNDS - (entry.rounds || 0)} more needed
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
