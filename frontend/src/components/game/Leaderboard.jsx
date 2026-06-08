import React, { useState, useEffect } from 'react';
import { Card } from '../ui';
import { useSheetSync } from '../../context';

const Leaderboard = () => {
  const { syncData: liveLeaderboardData, syncStatus, error: syncError, performLiveSync } = useSheetSync();
  const [leaderboard, setLeaderboard] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState('overall');

  useEffect(() => {
    let sortedData = [...liveLeaderboardData];

    if (selectedMetric === 'worst_scores') {
      sortedData.sort((a, b) => (a.quarters || 0) - (b.quarters || 0));
    } else if (selectedMetric === 'total_games') {
      sortedData.sort((a, b) => (b.rounds || 0) - (a.rounds || 0));
    } else {
      sortedData.sort((a, b) => (b.quarters || 0) - (a.quarters || 0));
    }
    setLeaderboard(sortedData);
  }, [liveLeaderboardData, selectedMetric]);

  const loading = syncStatus === 'connecting' || syncStatus === 'syncing';
  const error = syncError;


  const metrics = [
    { value: 'overall', label: 'Overall Ranking' },
    { value: 'total_games', label: 'Most Rounds Played' },
    { value: 'worst_scores', label: 'Bottom 5 Scores' }
  ];
  
  const BANQUET_QUALIFICATION_ROUNDS = 20;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <Card className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading leaderboard...</p>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">🏆 Leaderboard</h1>
          <p className="text-gray-600">Track player performance and rankings</p>
        </div>

        {/* Metric Selector */}
        <Card className="p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Select Metric</h2>
          <div className="flex flex-wrap gap-3">
            {metrics.map(metric => (
              <button
                key={metric.value}
                onClick={() => setSelectedMetric(metric.value)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedMetric === metric.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {metric.label}
              </button>
            ))}
          </div>
        </Card>

        {/* Leaderboard */}
        <Card className="overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b">
            <h2 className="text-xl font-semibold text-gray-900">
              {metrics.find(m => m.value === selectedMetric)?.label || 'Leaderboard'}
            </h2>
          </div>

          {error ? (
            <div className="p-8 text-center">
              <div className="text-red-600 mb-4">⚠️ Error loading leaderboard</div>
              <p className="text-gray-600 mb-4">{error}</p>
              <button
                onClick={() => performLiveSync()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Try Again
              </button>
            </div>
          ) : leaderboard.length === 0 ? (
            <div className="p-8 text-center">
              <div className="text-6xl mb-4">📊</div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Data Yet</h3>
              <p className="text-gray-600 mb-4">
                The leaderboard is empty. Start playing games to see rankings!
              </p>
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-blue-800 text-sm">
                  💡 <strong>Tip:</strong> You can add players and record game results to populate the leaderboard.
                </p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Player
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quarters
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rounds
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg / Round
                    </th>
                    {selectedMetric === 'total_games' && (
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Banquet Status
                      </th>
                    )}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {(() => {
                    let displayData = [...leaderboard];
                    if (selectedMetric === 'worst_scores') {
                      displayData = displayData.slice(0, 5);
                    }
                    return displayData.map((entry, index) => (
                      <tr key={entry.member || index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <span className={`inline-flex items-center justify-center h-8 w-8 rounded-full text-sm font-medium ${
                              selectedMetric === 'worst_scores' ? 'bg-red-100 text-red-600' :
                              index === 0 ? 'bg-yellow-400 text-yellow-900' :
                              index === 1 ? 'bg-gray-300 text-gray-900' :
                              index === 2 ? 'bg-orange-400 text-orange-900' :
                              'bg-gray-100 text-gray-600'
                            }`}>
                              {index + 1}
                            </span>
                            {selectedMetric !== 'worst_scores' && index < 3 && (
                              <span className="ml-2 text-lg">
                                {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                              </span>
                            )}
                            {selectedMetric === 'worst_scores' && (
                              <span className="ml-2 text-lg">😢</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
                              {(entry.member || '?').charAt(0).toUpperCase()}
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {entry.member || 'Unknown Player'}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {entry.quarters ?? '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {entry.rounds ?? '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {entry.average != null ? entry.average.toFixed(1) : '—'}
                        </td>
                        {selectedMetric === 'total_games' && (
                          <td className="px-6 py-4 whitespace-nowrap">
                            {(entry.rounds || 0) >= BANQUET_QUALIFICATION_ROUNDS ? (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                ✅ Qualified
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                {BANQUET_QUALIFICATION_ROUNDS - (entry.rounds || 0)} more needed
                              </span>
                            )}
                          </td>
                        )}
                      </tr>
                    ));
                  })()}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Additional Info */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">📈 How Rankings Work</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Overall ranking by total quarters earned</li>
              <li>• Most Rounds sorts by rounds played (banquet eligibility: 20+)</li>
              <li>• Bottom 5 shows the lowest total quarter earners</li>
              <li>• Avg / Round = total quarters ÷ rounds played</li>
            </ul>
          </Card>
          
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">🎮 Quick Actions</h3>
            <div className="space-y-3">
              <button 
                onClick={() => performLiveSync()}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                🔄 Refresh Data
              </button>
              <button 
                onClick={() => window.location.href = '/players'}
                className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                👥 Manage Players
              </button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Leaderboard;