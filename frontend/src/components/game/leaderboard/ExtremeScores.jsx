import React from 'react';
import { Link } from 'react-router-dom';
import PlayerName from './PlayerName';
import { roundPath } from './roundLink';

export default function ExtremeScores({ title, scores, emptyLabel }) {
  return (
    <div>
      <div className="px-6 py-4 bg-gray-50 border-b">
        <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
        <p className="text-sm text-gray-500 mt-1">Single-game quarters for the current season</p>
      </div>
      {scores.length === 0 ? (
        <div className="p-8 text-center text-gray-600">{emptyLabel}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Player</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quarters</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {scores.map((row) => (
                <tr key={`${row.date_sortable}-${row.member}-${row.quarters}-${row.group || ''}`}>
                  <td className="px-6 py-4 text-sm text-gray-700">
                    <Link to={roundPath(row)} className="hover:text-blue-600 hover:underline">{row.date}</Link>
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">
                    <PlayerName name={row.member} playerId={row.player_id} />
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{row.quarters}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
