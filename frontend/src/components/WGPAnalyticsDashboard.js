import React, { useState, useEffect, useCallback } from 'react';
import ghinService, { initializeGHIN } from '../services/ghinService';

const WGPAnalyticsDashboard = () => {
  const [leaderboardData, setLeaderboardData] = useState([]);
  const [topBestScores, setTopBestScores] = useState([]);
  const [topWorstScores, setTopWorstScores] = useState([]);
  const [mostRoundsPlayed, setMostRoundsPlayed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ghinLoading, setGhinLoading] = useState(false);
  const [ghinData, setGhinData] = useState({});
  const [ghinEnabled, setGhinEnabled] = useState(false);

  const calculateQB = useCallback((player, rank) => {
    const totalPlayers = 28;
    return totalPlayers * 10 + (totalPlayers - rank) * 10;
  }, []);

  const processLeaderboardData = useCallback((data) => {
    const sortedByQuarters = [...data].sort((a, b) => b.total_earnings - a.total_earnings);

    const leaderboard = sortedByQuarters.map((player, index) => ({
      ...player,
      quarters: Math.round(player.total_earnings),
      average: player.games_played > 0 ? Math.round(player.total_earnings / player.games_played) : 0,
      rounds: player.games_played,
      qb: calculateQB(player, index)
    }));

    setLeaderboardData(leaderboard);

    const bestScores = [...leaderboard]
      .filter(p => p.quarters > 0)
      .sort((a, b) => b.quarters - a.quarters)
      .slice(0, 5)
      .map(p => ({
        member: p.player_name,
        topScore: p.quarters,
        date: '27-Jul'
      }));
    setTopBestScores(bestScores);

    const worstScores = [...leaderboard]
      .filter(p => p.quarters < 0)
      .sort((a, b) => a.quarters - b.quarters)
      .slice(0, 5)
      .map(p => ({
        member: p.player_name,
        score: p.quarters,
        date: '23-Aug'
      }));
    setTopWorstScores(worstScores);

    const roundsPlayed = [...leaderboard]
      .sort((a, b) => b.rounds - a.rounds)
      .map(p => ({
        member: p.player_name,
        rounds: p.rounds,
        banquet: p.rounds >= 20
      }));
    setMostRoundsPlayed(roundsPlayed);
  }, [calculateQB]);

  const fetchGHINData = useCallback(async (players) => {
    if (!ghinService.isInitialized()) {
      return;
    }

    try {
      setGhinLoading(true);
      const ghinDataMap = {};

      const playersWithMockGHINIds = players.map(player => ({
        ...player,
        ghinId: `GHIN${player.player_name.replace(/\s/g, '').toUpperCase()}`
      }));

      const batchResults = await ghinService.getBatchGolferInfo(
        playersWithMockGHINIds.map(p => p.ghinId)
      );

      batchResults.success.forEach(ghinInfo => {
        const player = playersWithMockGHINIds.find(p => p.ghinId === ghinInfo.ghinId);
        if (player) {
          ghinDataMap[player.player_name] = {
            handicapIndex: ghinInfo.handicapIndex,
            recentScores: ghinInfo.recentScores,
            lastUpdated: ghinInfo.lastUpdated,
            club: ghinInfo.club
          };
        }
      });

      setGhinData(ghinDataMap);
      console.log(`Fetched GHIN data for ${Object.keys(ghinDataMap).length} players`);

    } catch (error) {
      console.error('Error fetching GHIN data:', error);
    } finally {
      setGhinLoading(false);
    }
  }, []);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      
      const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
      
      // Always use GHIN-enhanced leaderboard (shows stored handicap data even if GHIN API is offline)
      const leaderboardUrl = `${API_URL}/leaderboard/ghin-enhanced`;
      
      const leaderboardResponse = await fetch(leaderboardUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!leaderboardResponse.ok) {
        throw new Error(`Failed to fetch leaderboard data: ${leaderboardResponse.statusText}`);
      }
      
      const leaderboardData = await leaderboardResponse.json();
      
      // If no data available, show empty state
      if (!leaderboardData || leaderboardData.length === 0) {
        setLeaderboardData([]);
        setTopBestScores([]);
        setTopWorstScores([]);
        setMostRoundsPlayed([]);
        return;
      }
      
      // Process leaderboard data from database (filter out Grand Total if it exists)
      const leaderboard = leaderboardData
        .filter(player => {
          const name = (player.player_name || player.name || '').toLowerCase();
          return name !== 'grand total' && name !== 'total' && name !== '';
        })
        .map(player => ({
          player_name: player.player_name || player.name,
          games_played: player.games_played || 0,
          games_won: player.games_won || 0,
          win_rate: player.win_percentage ? player.win_percentage / 100 : 0,
          total_earnings: player.total_earnings || 0,
          avg_earnings_per_game: player.avg_earnings || 0,
          best_finish: player.best_finish || 99,
          holes_won: player.holes_won || 0,
          partnerships: player.partnerships_formed || 0,
          partnership_success: player.partnership_success ? player.partnership_success / 100 : 0,
          betting_success: player.betting_success || 0,
          solo_attempts: player.solo_attempts || 0,
          solo_wins: player.solo_wins || 0,
          // GHIN data (if available from enhanced endpoint)
          handicap: player.handicap,
          ghin_id: player.ghin_id,
          ghin_data: player.ghin_data,
          recent_form: player.recent_form
        }));
      
      // Process and format data
      processLeaderboardData(leaderboard);
      
      // Fetch GHIN data if available
      if (ghinEnabled && leaderboard.length > 0) {
        fetchGHINData(leaderboard);
      }
      
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchGHINData, ghinEnabled, processLeaderboardData]);

  const initializeServices = useCallback(async () => {
    try {
      const ghinInitialized = await initializeGHIN();
      setGhinEnabled(ghinInitialized);
      if (ghinInitialized) {
        console.log('GHIN service initialized successfully');
      } else {
        console.log('GHIN service not available - continuing without GHIN integration');
      }
    } catch (error) {
      console.error('Failed to initialize GHIN service:', error);
      setGhinEnabled(false);
    }
  }, []);

  useEffect(() => {
    initializeServices();
    fetchAnalytics();
  }, [fetchAnalytics, initializeServices]);
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading leaderboard data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show empty state if no data
  if (leaderboardData.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">No Leaderboard Data Available</h2>
            <p className="text-gray-600 mb-6">
              To display live leaderboard data, you need to set up Google Sheets synchronization.
            </p>
            <div className="bg-blue-50 p-6 rounded-lg mb-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">🔗 Setup Instructions</h3>
              <ol className="text-left space-y-2 text-sm text-blue-800">
                <li><strong>1.</strong> Go to the <a href="/live-sync" className="underline">Live Sync page</a></li>
                <li><strong>2.</strong> Enter your Google Sheets URL</li>
                <li><strong>3.</strong> Make sure your sheet is publicly viewable</li>
                <li><strong>4.</strong> Click "Sync Now" to import your data</li>
                <li><strong>5.</strong> Return here to view your leaderboard</li>
              </ol>
            </div>
            <button 
              onClick={() => window.location.href = '/live-sync'}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Set Up Google Sheets Sync
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-full mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow mb-4 p-4">
          <h1 className="text-2xl font-bold text-center">Wolf Goat Pig Leaderboard 2025-26 Season</h1>
          <div className="text-center mt-1">
            <p className="text-gray-600">Live data from Google Sheets sync</p>
            {ghinEnabled && (
              <div className="mt-1 flex justify-center items-center space-x-2">
                <span className="text-xs text-blue-600">🏌️ GHIN Integration Active</span>
                {ghinLoading && (
                  <span className="text-xs text-blue-500 animate-pulse">Syncing handicaps...</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-12 gap-4">
          
          {/* Main Leaderboard - Left Side (7 columns) */}
          <div className="col-span-7">
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full">
                <thead className="bg-gray-200">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-700">Member</th>
                    <th className="px-4 py-2 text-center text-xs font-medium text-gray-700">Quarters</th>
                    <th className="px-4 py-2 text-center text-xs font-medium text-gray-700">Average</th>
                    <th className="px-4 py-2 text-center text-xs font-medium text-gray-700">Rounds</th>
                    <th className="px-4 py-2 text-center text-xs font-medium text-gray-700">QB</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {leaderboardData.map((player, index) => (
                    <tr key={player.player_name} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-2 text-sm font-medium text-gray-900">
                        {player.player_name}
                        {(player.handicap !== undefined && player.handicap !== null) ? (
                          <span className="ml-2 text-blue-600 font-medium">
                            ({parseFloat(player.handicap).toFixed(1)})
                          </span>
                        ) : ghinData[player.player_name]?.handicapIndex !== undefined ? (
                          <span className="ml-2 text-blue-600 font-medium">
                            ({parseFloat(ghinData[player.player_name].handicapIndex).toFixed(1)})
                          </span>
                        ) : null}
                        {ghinData[player.player_name] && ghinLoading && (
                          <span className="ml-2 text-xs text-blue-500">🔄</span>
                        )}
                        {ghinData[player.player_name]?.lastUpdated && (
                          <span className="ml-2 text-xs text-green-500" title="GHIN data available">⚡</span>
                        )}
                        {player.recent_form && player.recent_form !== "N/A" && (
                          <div className="text-xs text-gray-500 mt-1">
                            Form: {player.recent_form}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-2 text-sm text-center font-bold">
                        <span className={player.quarters >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {player.quarters}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm text-center">{player.average}</td>
                      <td className="px-4 py-2 text-sm text-center">{player.rounds}</td>
                      <td className="px-4 py-2 text-sm text-center">{player.qb}</td>
                    </tr>
                  ))}
                  {/* Removed Grand Total Row - not a real player */}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right Side Stats (5 columns) */}
          <div className="col-span-5 space-y-4">
            
            {/* Top Row - Best and Worst Scores */}
            <div className="grid grid-cols-2 gap-4">
              
              {/* Top 5 Best Scores */}
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="bg-green-100 px-4 py-2">
                  <h3 className="font-semibold text-sm">Top 5 Best Scores</h3>
                </div>
                <table className="min-w-full">
                  <thead className="bg-pink-100">
                    <tr>
                      <th className="px-2 py-1 text-left text-xs">Date</th>
                      <th className="px-2 py-1 text-left text-xs">Member</th>
                      <th className="px-2 py-1 text-center text-xs">Top Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {topBestScores.map((score, index) => (
                      <tr key={index} className="bg-white">
                        <td className="px-2 py-1 text-xs">{score.date}</td>
                        <td className="px-2 py-1 text-xs">{score.member}</td>
                        <td className="px-2 py-1 text-xs text-center font-bold text-green-600">
                          {score.topScore}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Top 5 Worst Scores */}
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="bg-red-100 px-4 py-2">
                  <h3 className="font-semibold text-sm">Top 5 Worst Scores</h3>
                </div>
                <table className="min-w-full">
                  <thead className="bg-pink-100">
                    <tr>
                      <th className="px-2 py-1 text-left text-xs">Date</th>
                      <th className="px-2 py-1 text-left text-xs">Member</th>
                      <th className="px-2 py-1 text-center text-xs">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {topWorstScores.length > 0 ? topWorstScores.map((score, index) => (
                      <tr key={index} className="bg-white">
                        <td className="px-2 py-1 text-xs">{score.date}</td>
                        <td className="px-2 py-1 text-xs">{score.member}</td>
                        <td className="px-2 py-1 text-xs text-center font-bold text-red-600">
                          {score.score}
                        </td>
                      </tr>
                    )) : (
                      <tr><td colSpan="3" className="px-2 py-1 text-xs text-center">No negative scores</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Most Rounds Played */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-blue-100 px-4 py-2">
                <h3 className="font-semibold text-sm">Most Rounds Played</h3>
              </div>
              <table className="min-w-full">
                <thead className="bg-pink-100">
                  <tr>
                    <th className="px-2 py-1 text-left text-xs">Member</th>
                    <th className="px-2 py-1 text-center text-xs">Rounds</th>
                    <th className="px-2 py-1 text-center text-xs">Banquet</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {mostRoundsPlayed.slice(0, 20).map((player, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-2 py-1 text-xs">{player.member}</td>
                      <td className="px-2 py-1 text-xs text-center font-semibold">{player.rounds}</td>
                      <td className="px-2 py-1 text-xs text-center">
                        {player.banquet && <span className="text-yellow-500">🏆</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Group Size and Location Stats */}
            <div className="grid grid-cols-2 gap-4">
              
              {/* Group Size */}
              <div className="bg-white rounded-lg shadow p-3">
                <div className="bg-purple-100 px-2 py-1 rounded mb-2">
                  <h3 className="font-semibold text-sm">Group Size</h3>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>4 Players</span>
                    <span className="font-bold">Most</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span>5 Players</span>
                    <span className="font-bold">Some</span>
                  </div>
                </div>
              </div>

              {/* Locations */}
              <div className="bg-white rounded-lg shadow p-3">
                <div className="bg-orange-100 px-2 py-1 rounded mb-2">
                  <h3 className="font-semibold text-sm">Locations</h3>
                </div>
                <div className="space-y-1">
                  <div className="text-xs">Wing Point</div>
                  <div className="text-xs">Discovery Bay</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-white rounded-lg shadow mt-4 p-4 text-center text-sm text-gray-600">
          <p>Data synced from Google Sheets • Last updated: {new Date().toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
};

export default WGPAnalyticsDashboard;
