import React, { useState, useEffect, useCallback } from 'react';

const API_URL = process.env.REACT_APP_API_URL || "";

const MatchmakingSuggestions = () => {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [minOverlapHours, setMinOverlapHours] = useState(2);
  const [selectedDays, setSelectedDays] = useState([]);
  const [sendingNotifications, setSendingNotifications] = useState(false);

  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const dayNamesFull = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  const loadMatches = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append('min_overlap_hours', minOverlapHours);
      if (selectedDays.length > 0) {
        params.append('preferred_days', selectedDays.join(','));
      }

      const response = await fetch(`${API_URL}/matchmaking/suggestions?${params}`);

      if (response.ok) {
        const data = await response.json();
        setMatches(data.matches || []);
      } else {
        throw new Error('Failed to load match suggestions');
      }
      setError(null);
    } catch (err) {
      console.error('Error loading matches:', err);
      setError(err.message);
      setMatches([]);
    } finally {
      setLoading(false);
    }
  }, [minOverlapHours, selectedDays]);

  useEffect(() => {
    loadMatches();
  }, [loadMatches]);

  const sendAllNotifications = async () => {
    try {
      setSendingNotifications(true);
      const response = await fetch(`${API_URL}/matchmaking/create-and-notify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Sent ${result.notifications_sent} notifications for ${result.matches_created} matches!`);
        loadMatches();
      } else {
        throw new Error('Failed to send notifications');
      }
    } catch (err) {
      console.error('Error sending notifications:', err);
      alert('Failed to send notifications: ' + err.message);
    } finally {
      setSendingNotifications(false);
    }
  };

  const toggleDay = (dayIndex) => {
    setSelectedDays(prev =>
      prev.includes(dayIndex)
        ? prev.filter(d => d !== dayIndex)
        : [...prev, dayIndex]
    );
  };

  const formatQuality = (score) => {
    if (score >= 80) return { text: 'Excellent', color: '#047857' };
    if (score >= 60) return { text: 'Very Good', color: '#0369a1' };
    if (score >= 40) return { text: 'Good', color: '#ca8a04' };
    return { text: 'Fair', color: '#6b7280' };
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#6b7280' }}>
        Finding matches...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '16px' }}>
      {/* Info Banner */}
      <div style={{
        background: '#fef3c7',
        border: '1px solid #f59e0b',
        borderRadius: '10px',
        padding: '12px',
        marginBottom: '20px',
        fontSize: '13px',
        color: '#92400e'
      }}>
        🔔 Groups are emailed daily at 10 AM
      </div>

      {/* Filters */}
      <div style={{
        background: '#f9fafb',
        padding: '16px',
        borderRadius: '12px',
        marginBottom: '20px',
        border: '1px solid #e5e7eb'
      }}>
        {/* Overlap Hours */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
            Min Overlap: {minOverlapHours}h
          </label>
          <input
            type="range"
            min="1"
            max="6"
            step="0.5"
            value={minOverlapHours}
            onChange={(e) => setMinOverlapHours(parseFloat(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>

        {/* Day Filter */}
        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
            Preferred Days
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '6px' }}>
            {dayNames.map((day, index) => (
              <button
                key={index}
                onClick={() => toggleDay(index)}
                style={{
                  padding: '8px 4px',
                  background: selectedDays.includes(index) ? '#047857' : 'white',
                  color: selectedDays.includes(index) ? 'white' : '#374151',
                  border: selectedDays.includes(index) ? '2px solid #047857' : '1px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                {day}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button
          onClick={loadMatches}
          style={{
            flex: 1,
            padding: '12px',
            background: '#f3f4f6',
            color: '#374151',
            border: '1px solid #d1d5db',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          🔄 Refresh
        </button>
        <button
          onClick={sendAllNotifications}
          disabled={sendingNotifications || matches.length === 0}
          style={{
            flex: 2,
            padding: '12px',
            background: sendingNotifications || matches.length === 0 ? '#9ca3af' : '#047857',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '600',
            cursor: sendingNotifications || matches.length === 0 ? 'not-allowed' : 'pointer'
          }}
        >
          {sendingNotifications ? 'Sending...' : '📧 Notify All'}
        </button>
      </div>

      {/* Results Count */}
      <div style={{ marginBottom: '16px', fontSize: '15px', color: '#374151' }}>
        Found <span style={{ fontWeight: '700', color: '#047857' }}>{matches.length}</span> matches
      </div>

      {/* Match Cards */}
      {error ? (
        <div style={{
          background: '#fef2f2',
          color: '#dc2626',
          padding: '16px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          {error}
          <button
            onClick={loadMatches}
            style={{
              marginTop: '10px',
              padding: '8px 16px',
              background: '#dc2626',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Try Again
          </button>
        </div>
      ) : matches.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {matches.map((match, index) => {
            const quality = formatQuality(match.match_quality);
            return (
              <div
                key={index}
                style={{
                  background: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '12px',
                  padding: '16px',
                  position: 'relative'
                }}
              >
                {/* Quality Badge */}
                <span style={{
                  position: 'absolute',
                  top: '12px',
                  right: '12px',
                  padding: '4px 8px',
                  background: quality.color,
                  color: 'white',
                  borderRadius: '6px',
                  fontSize: '11px',
                  fontWeight: '600'
                }}>
                  {quality.text}
                </span>

                {/* Day */}
                <h4 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: '600', color: '#1f2937' }}>
                  {dayNamesFull[match.day_of_week]}
                </h4>

                {/* Time */}
                <div style={{
                  background: '#f9fafb',
                  padding: '10px',
                  borderRadius: '8px',
                  marginBottom: '12px',
                  fontSize: '13px',
                  color: '#4b5563'
                }}>
                  <div>⏰ {match.overlap_start} - {match.overlap_end}</div>
                  <div style={{ marginTop: '4px' }}>
                    Tee Time: <span style={{
                      background: '#0369a1',
                      color: 'white',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}>{match.suggested_tee_time}</span>
                  </div>
                </div>

                {/* Players */}
                <div style={{
                  fontSize: '13px',
                  fontWeight: '600',
                  color: '#6b7280',
                  marginBottom: '8px'
                }}>
                  Players ({match.players.length})
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {match.players.map((player, pidx) => (
                    <span
                      key={pidx}
                      style={{
                        background: '#ecfdf5',
                        padding: '6px 10px',
                        borderRadius: '6px',
                        fontSize: '13px',
                        fontWeight: '500',
                        color: '#065f46'
                      }}
                    >
                      {player.player_name}
                    </span>
                  ))}
                </div>

                {/* Stats */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginTop: '12px',
                  paddingTop: '12px',
                  borderTop: '1px solid #e5e7eb',
                  fontSize: '12px',
                  color: '#6b7280'
                }}>
                  <span>Overlap: {match.overlap_duration_hours.toFixed(1)}h</span>
                  <span>Score: {match.match_quality.toFixed(0)}</span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          color: '#9ca3af',
          background: '#f9fafb',
          borderRadius: '12px'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🤖</div>
          <p style={{ margin: 0 }}>No matches found with current criteria</p>
          <p style={{ margin: '8px 0 0', fontSize: '13px' }}>Try adjusting the overlap hours or selected days</p>
        </div>
      )}
    </div>
  );
};

export default MatchmakingSuggestions;
