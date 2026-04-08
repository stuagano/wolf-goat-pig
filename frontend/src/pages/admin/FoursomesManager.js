import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../../components/ui';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const FoursomesManager = () => {
  const [selectedDate, setSelectedDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [existingPairings, setExistingPairings] = useState(null);

  // Get next Sunday as default
  useEffect(() => {
    const today = new Date();
    const daysUntilSunday = (7 - today.getDay()) % 7 || 7;
    const nextSunday = new Date(today);
    nextSunday.setDate(today.getDate() + daysUntilSunday);
    setSelectedDate(nextSunday.toISOString().split('T')[0]);
  }, []);

  // Check for existing pairings
  const checkExistingPairings = useCallback(async () => {
    if (!selectedDate) return;
    try {
      const response = await fetch(`${API_URL}/pairings/${selectedDate}`);
      if (response.ok) {
        const data = await response.json();
        setExistingPairings(data.exists ? data : null);
      }
    } catch (err) {
      console.error('Error checking pairings:', err);
    }
  }, [selectedDate]);

  // Check for existing pairings when date changes
  useEffect(() => {
    checkExistingPairings();
  }, [checkExistingPairings]);

  const generateFoursomes = async (force = false) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/pairings/${selectedDate}/generate?force=${force}&send_notifications=true`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        }
      );

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        checkExistingPairings();
      } else {
        setError(data.detail || 'Failed to generate foursomes');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const deletePairings = async () => {
    if (!window.confirm('Are you sure you want to delete these foursomes?')) return;

    try {
      const response = await fetch(`${API_URL}/pairings/${selectedDate}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setExistingPairings(null);
        setResult(null);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to delete');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    }
  };

  const runSaturdayJob = async () => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/pairings/run-saturday-job`, {
        method: 'POST'
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        setSelectedDate(data.game_date);
        checkExistingPairings();
      } else {
        setError(data.detail || 'Failed to run Saturday job');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">🎲 Sunday Foursomes Generator</h2>
        <p className="text-gray-600 mb-6">
          Generate random foursomes for Sunday games. This will email all signed-up players
          with their group assignments and send a tee time request to the pro shop.
        </p>

        {/* Date Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Game Date</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3 mb-6">
          <button
            onClick={() => generateFoursomes(false)}
            disabled={loading || !selectedDate}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
          >
            {loading ? 'Generating...' : '🎲 Generate Foursomes & Send Emails'}
          </button>

          <button
            onClick={runSaturdayJob}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {loading ? 'Running...' : '📅 Run Saturday Job (Next Sunday)'}
          </button>

          {existingPairings && (
            <>
              <button
                onClick={() => generateFoursomes(true)}
                disabled={loading}
                className="px-6 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 font-medium"
              >
                🔄 Regenerate (Replace Existing)
              </button>
              <button
                onClick={deletePairings}
                disabled={loading}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 font-medium"
              >
                🗑️ Delete Foursomes
              </button>
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Success Result */}
        {result && result.success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="font-semibold text-green-800 mb-2">✓ Foursomes Generated!</h3>
            <div className="text-green-700 space-y-1">
              <p><strong>Date:</strong> {result.date}</p>
              <p><strong>Players:</strong> {result.player_count}</p>
              <p><strong>Foursomes:</strong> {result.team_count}</p>
              <p><strong>Emails Sent:</strong> {result.notifications?.sent || 0}</p>
              {result.notifications?.failed > 0 && (
                <p className="text-yellow-700"><strong>Failed:</strong> {result.notifications.failed}</p>
              )}
            </div>
          </div>
        )}
      </Card>

      {/* Existing/Generated Foursomes Display */}
      {existingPairings && existingPairings.pairings && (
        <Card className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">
              📋 Foursomes for {existingPairings.date}
            </h3>
            <div className="text-sm text-gray-500">
              Generated: {new Date(existingPairings.generated_at).toLocaleString()}
              {existingPairings.notification_sent && ' • Emails sent ✓'}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {existingPairings.pairings.teams?.map((team, idx) => (
              <div key={idx} className="p-4 bg-gray-50 rounded-lg border-2 border-green-500">
                <h4 className="font-bold text-green-700 mb-3">Group {idx + 1}</h4>
                <ul className="space-y-2">
                  {team.players?.map((player, pIdx) => (
                    <li key={pIdx} className="flex justify-between">
                      <span>{player.player_name}</span>
                      {player.handicap && (
                        <span className="text-gray-500 text-sm">{player.handicap} HCP</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {existingPairings.pairings.remaining_players?.length > 0 && (
            <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-semibold text-yellow-800 mb-2">
                Alternates ({existingPairings.pairings.remaining_players.length})
              </h4>
              <div className="flex flex-wrap gap-2">
                {existingPairings.pairings.remaining_players.map((p, idx) => (
                  <span key={idx} className="px-3 py-1 bg-yellow-200 rounded-full text-sm">
                    {p.player_name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Info Card */}
      <Card className="p-6 bg-blue-50">
        <h3 className="font-semibold text-blue-900 mb-3">ℹ️ How it works</h3>
        <ul className="list-disc list-inside space-y-2 text-sm text-blue-800">
          <li>Foursomes are generated randomly from players signed up for the selected date</li>
          <li>Each player receives an email with their group assignment</li>
          <li>A tee time request is automatically sent to the pro shop (stuagano@gmail.com)</li>
          <li>The Saturday Job auto-runs every Saturday at 2 PM for the next Sunday</li>
          <li>You can regenerate foursomes if needed (will re-send all emails)</li>
        </ul>
      </Card>
    </div>
  );
};

export default FoursomesManager;
