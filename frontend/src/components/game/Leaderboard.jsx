import React, { useEffect, useMemo, useState } from 'react';
import { Card } from '../ui';
import { useSheetSync } from '../../context';
import { api } from '../../api/client';
import { useFeatureFlags } from '../../hooks/useFeatureFlags';
import StandingsTable from './leaderboard/StandingsTable';
import ExtremeScores from './leaderboard/ExtremeScores';
import RoundsDetail from './leaderboard/RoundsDetail';
import { banquetEligible, sortStandings } from './leaderboard/standings';

const TABS = [
  { id: 'standings', label: 'Standings' },
  { id: 'best', label: 'Best scores' },
  { id: 'worst', label: 'Worst scores' },
  { id: 'rounds', label: 'Rounds' },
];

const Leaderboard = () => {
  const features = useFeatureFlags();
  const { syncData: liveLeaderboardData, syncStatus, error: syncError, performLiveSync } = useSheetSync();
  const [tab, setTab] = useState('standings');
  const [sortKey, setSortKey] = useState('rank');
  const [sortDir, setSortDir] = useState('asc');
  const [banquetOnly, setBanquetOnly] = useState(false);
  const [sheetUrl, setSheetUrl] = useState(null);
  const [teamMap, setTeamMap] = useState({});
  const [bestScores, setBestScores] = useState([]);
  const [worstScores, setWorstScores] = useState([]);
  const [seasonGames, setSeasonGames] = useState([]);
  const [detailError, setDetailError] = useState(null);

  useEffect(() => {
    api.GET('/data/leaderboard-config')
      .then(({ data }) => { if (data?.sheet_url) setSheetUrl(data.sheet_url); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!features.livsow) return;
    api.GET('/data/livsow/team-map')
      .then(({ data }) => { if (data) setTeamMap(data); })
      .catch(() => {});
  }, [features.livsow]);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.GET('/data/leaderboard/scores', { params: { query: { kind: 'best', limit: 5 } } }),
      api.GET('/data/leaderboard/scores', { params: { query: { kind: 'worst', limit: 5 } } }),
      api.GET('/data/leaderboard/rounds'),
    ]).then(([best, worst, rounds]) => {
      if (cancelled) return;
      if (best.error || worst.error || rounds.error) {
        setDetailError('Could not load season scores.');
        return;
      }
      setBestScores(best.data || []);
      setWorstScores(worst.data || []);
      setSeasonGames(rounds.data || []);
    }).catch(() => {
      if (!cancelled) setDetailError('Could not load season scores.');
    });
    return () => { cancelled = true; };
  }, []);

  const standings = useMemo(() => {
    const filtered = banquetOnly ? liveLeaderboardData.filter(banquetEligible) : liveLeaderboardData;
    return sortStandings(filtered, sortKey, sortDir);
  }, [liveLeaderboardData, banquetOnly, sortKey, sortDir]);

  const onSort = (key) => {
    if (key === sortKey) {
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'));
      return;
    }
    setSortKey(key);
    setSortDir(key === 'rank' || key === 'member' ? 'asc' : 'desc');
  };

  const loading = syncStatus === 'connecting' || syncStatus === 'syncing';

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <Card className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
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
          <div className="flex items-center justify-between flex-wrap gap-3">
            <h1 className="text-3xl font-bold text-gray-900">🏆 Leaderboard</h1>
            {sheetUrl && (
              <a
                href={sheetUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm font-medium hover:bg-green-100 transition-colors"
              >
                📊 View Spreadsheet
              </a>
            )}
          </div>
          <p className="text-gray-600 mt-2">Track player performance and rankings</p>
        </div>

        <div className="flex flex-wrap gap-2 mb-4" role="tablist" aria-label="Leaderboard views">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={tab === item.id}
              onClick={() => setTab(item.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                tab === item.id ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {item.label}
            </button>
          ))}
          {tab === 'standings' && (
            <button
              type="button"
              aria-pressed={banquetOnly}
              onClick={() => setBanquetOnly((on) => !on)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                banquetOnly ? 'bg-green-700 text-white' : 'bg-green-100 text-green-800 hover:bg-green-200'
              }`}
            >
              Banquet eligible
            </button>
          )}
        </div>

        <Card className="overflow-hidden">
          {tab === 'standings' && (
            syncError ? (
              <div className="p-8 text-center">
                <div className="text-red-600 mb-4">⚠️ Error loading leaderboard</div>
                <p className="text-gray-600 mb-4">{syncError}</p>
                <button type="button" onClick={() => performLiveSync()} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Try Again
                </button>
              </div>
            ) : standings.length === 0 ? (
              <div className="p-8 text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Data Yet</h3>
                <p className="text-gray-600">The leaderboard is empty. Start playing games to see rankings!</p>
              </div>
            ) : (
              <StandingsTable
                entries={standings}
                sortKey={sortKey}
                sortDir={sortDir}
                onSort={onSort}
                teamMap={teamMap}
                showTeams={features.livsow}
              />
            )
          )}
          {tab === 'best' && <ExtremeScores title="Best scores" scores={bestScores} emptyLabel={detailError || 'No season scores yet.'} />}
          {tab === 'worst' && <ExtremeScores title="Worst scores" scores={worstScores} emptyLabel={detailError || 'No season scores yet.'} />}
          {tab === 'rounds' && (
            detailError ? <div className="p-8 text-center text-red-600">{detailError}</div> : <RoundsDetail games={seasonGames} />
          )}
        </Card>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">📈 How Rankings Work</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Rank is the season standing by total quarters</li>
              <li>• Click a column header to sort up or down</li>
              <li>• Banquet eligible shows players with 20 or more rounds</li>
              <li>• Best and worst scores are single games, not season totals</li>
            </ul>
          </Card>
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">🎮 Quick Actions</h3>
            <div className="space-y-3">
              <button type="button" onClick={() => performLiveSync()} className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                🔄 Refresh Data
              </button>
              <button type="button" onClick={() => { window.location.href = '/players'; }} className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
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
