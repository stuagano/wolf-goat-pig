import React, { useState, useEffect } from 'react';
import { Card } from './ui';

const Leaderboard = () => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('overall');

  useEffect(() => {
    fetchLeaderboard();
  }, [selectedMetric]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
      
      // Fetch leaderboard data from the database (previously synced from Google Sheets)
      const leaderboardResponse = await fetch(`${API_URL}/leaderboard`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!leaderboardResponse.ok) {
        throw new Error(`Failed to fetch leaderboard data: ${leaderboardResponse.statusText}`);
      }
      
      const data = await leaderboardResponse.json();
      
      // Handle different response formats
      if (selectedMetric === 'overall') {
        setLeaderboard(data.leaderboard || data);
      } else {
        // For now, use the same data for all metrics (can be enhanced later)
        setLeaderboard(data.leaderboard || data);
      }
    } catch (err) {
      setError(err.message);
      setLeaderboard([]);
    } finally {
      setLoading(false);
    }
  };

  const metrics = [
    { value: 'overall', label: 'Overall Ranking' },
    { value: 'avg_score', label: 'Average Score' },
    { value: 'total_games', label: 'Games Played' },
    { value: 'win_rate', label: 'Win Rate' },
    { value: 'points_earned', label: 'Points Earned' }
  ];

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
                onClick={fetchLeaderboard}
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
                      Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Games
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Played
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {leaderboard.map((player, index) => (
                    <tr key={player.id || index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className={`inline-flex items-center justify-center h-8 w-8 rounded-full text-sm font-medium ${
                            index === 0 ? 'bg-yellow-400 text-yellow-900' :
                            index === 1 ? 'bg-gray-300 text-gray-900' :
                            index === 2 ? 'bg-orange-400 text-orange-900' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            {index + 1}
                          </span>
                          {index < 3 && (
                            <span className="ml-2 text-lg">
                              {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
                            {(player.name || 'Unknown').charAt(0).toUpperCase()}
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {player.name || 'Unknown Player'}
                            </div>
                            <div className="text-sm text-gray-500">
                              Handicap: {player.handicap || 'N/A'}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {player.score || player.total_points || player.value || 'N/A'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {player.games_played || player.total_games || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {player.last_played ? new Date(player.last_played).toLocaleDateString() : 'Never'}
                      </td>
                    </tr>
                  ))}
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
              <li>• Overall ranking based on cumulative performance</li>
              <li>• Win rate shows percentage of games won</li>
              <li>• Average score calculated from all recorded games</li>
              <li>• Points earned from Wolf Goat Pig betting outcomes</li>
            </ul>
          </Card>
          
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">🎮 Quick Actions</h3>
            <div className="space-y-3">
              <button 
                onClick={fetchLeaderboard}
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