import React, { useState, useEffect } from 'react';

const WGPAnalyticsDashboard = () => {
  const [leaderboardData, setLeaderboardData] = useState([]);
  const [topBestScores, setTopBestScores] = useState([]);
  const [topWorstScores, setTopWorstScores] = useState([]);
  const [mostRoundsPlayed, setMostRoundsPlayed] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      
      // First, fetch the CSV data from Google Sheets integration
      const csvResponse = await fetch('/sheet-integration/fetch-google-sheet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          csv_url: 'http://localhost:3000/sample_golf_data.csv' // Using local CSV for demo
        })
      });
      
      if (!csvResponse.ok) {
        throw new Error(`Failed to fetch sheet data: ${csvResponse.statusText}`);
      }
      
      const csvData = await csvResponse.json();
      
      // Convert CSV data to leaderboard format
      const leaderboard = (csvData.data || csvData).map(player => ({
        player_name: player['Player Name'] || player.name,
        games_played: parseInt(player['Games Played'] || player.games_played || '0'),
        games_won: parseInt(player['Games Won'] || player.games_won || '0'),
        win_rate: parseFloat((player['Win Rate'] || player.win_rate || '0%').replace('%', '')) / 100,
        total_earnings: parseFloat((player['Total Earnings'] || player.total_earnings || '$0').replace('$', '').replace(',', '')),
        avg_earnings_per_game: parseFloat((player['Avg Earnings Per Game'] || player.avg_earnings_per_game || '$0').replace('$', '').replace(',', '')),
        best_finish: parseInt(player['Best Finish'] || player.best_finish || '99'),
        holes_won: parseInt(player['Holes Won'] || player.holes_won || '0'),
        partnerships: parseInt(player['Partnerships'] || player.partnerships || '0'),
        partnership_success: parseFloat((player['Partnership Success'] || player.partnership_success || '0%').replace('%', '')) / 100,
        betting_success: parseFloat((player['Betting Success'] || player.betting_success || '0%').replace('%', '')) / 100,
        solo_attempts: parseInt(player['Solo Attempts'] || player.solo_attempts || '0'),
        solo_wins: parseInt(player['Solo Wins'] || player.solo_wins || '0')
      }));
      
      // Process and format data
      processLeaderboardData(leaderboard);
      
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const processLeaderboardData = (data) => {
    // Main leaderboard - sorted by total quarters (earnings)
    const sortedByQuarters = [...data].sort((a, b) => b.total_earnings - a.total_earnings);
    
    // Add QB (quarterback) column - calculate based on performance
    const leaderboard = sortedByQuarters.map((player, index) => ({
      ...player,
      quarters: Math.round(player.total_earnings), // Convert earnings to quarters
      average: player.games_played > 0 ? Math.round(player.total_earnings / player.games_played) : 0,
      rounds: player.games_played,
      qb: calculateQB(player, index) // QB calculation based on ranking
    }));
    
    setLeaderboardData(leaderboard);
    
    // Top 5 Best Scores (highest individual quarters)
    const bestScores = [...leaderboard]
      .filter(p => p.quarters > 0)
      .sort((a, b) => b.quarters - a.quarters)
      .slice(0, 5)
      .map(p => ({
        member: p.player_name,
        topScore: p.quarters,
        date: '27-Jul' // Would need actual dates from game records
      }));
    setTopBestScores(bestScores);
    
    // Top 5 Worst Scores (most negative quarters)
    const worstScores = [...leaderboard]
      .filter(p => p.quarters < 0)
      .sort((a, b) => a.quarters - b.quarters)
      .slice(0, 5)
      .map(p => ({
        member: p.player_name,
        score: p.quarters,
        date: '23-Aug' // Would need actual dates
      }));
    setTopWorstScores(worstScores);
    
    // Most Rounds Played
    const roundsPlayed = [...leaderboard]
      .sort((a, b) => b.rounds - a.rounds)
      .map(p => ({
        member: p.player_name,
        rounds: p.rounds,
        banquet: p.rounds >= 5 // Eligible for banquet if 5+ rounds
      }));
    setMostRoundsPlayed(roundsPlayed);
  };

  const calculateQB = (player, rank) => {
    // QB calculation: lower rank = higher QB value
    // This is a placeholder - you can adjust the logic
    const totalPlayers = 28;
    return totalPlayers * 10 + (totalPlayers - rank) * 10;
  };

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

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-full mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow mb-4 p-4">
          <h1 className="text-2xl font-bold text-center">Wolf Goat Pig Leaderboard 2025-26 Season</h1>
          <p className="text-center text-gray-600 mt-1">Scores through 24-Aug-25</p>
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
                      <td className="px-4 py-2 text-sm font-medium text-gray-900">{player.player_name}</td>
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
                  {/* Grand Total Row */}
                  <tr className="bg-gray-200 font-bold">
                    <td className="px-4 py-2 text-sm">Grand Total</td>
                    <td className="px-4 py-2 text-sm text-center">
                      {leaderboardData.reduce((sum, p) => sum + p.quarters, 0)}
                    </td>
                    <td className="px-4 py-2 text-sm text-center">
                      {Math.round(leaderboardData.reduce((sum, p) => sum + p.average, 0) / leaderboardData.length)}
                    </td>
                    <td className="px-4 py-2 text-sm text-center">
                      {leaderboardData.reduce((sum, p) => sum + p.rounds, 0)}
                    </td>
                    <td className="px-4 py-2 text-sm text-center">-</td>
                  </tr>
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
                  <div className="text-xs font-bold mt-2 pt-2 border-t">
                    Grand Total
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
                  <div className="text-xs font-bold mt-2 pt-2 border-t">
                    Grand Total
                  </div>
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