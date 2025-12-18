import React, { useState, useEffect, useCallback } from 'react';
import '../../styles/mobile-touch.css';

const API_URL = process.env.REACT_APP_API_URL || "";

const MatchmakingSuggestions = () => {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [minOverlapHours, setMinOverlapHours] = useState(2);
  const [selectedDays, setSelectedDays] = useState([]);
  const [sendingNotifications, setSendingNotifications] = useState(false);

  const dayNames = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 
    'Friday', 'Saturday', 'Sunday'
  ];

  // Load match suggestions
  const loadMatches = useCallback(async () => {
    try {
      setLoading(true);
      
      // Build query params
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

  // Send notifications for all matches
  const sendAllNotifications = async () => {
    try {
      setSendingNotifications(true);
      
      const response = await fetch(`${API_URL}/matchmaking/create-and-notify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Successfully sent ${result.notifications_sent} notifications for ${result.matches_created} matches!`);
        loadMatches(); // Reload to reflect changes
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

  // Toggle day selection
  const toggleDay = (dayIndex) => {
    setSelectedDays(prev => {
      if (prev.includes(dayIndex)) {
        return prev.filter(d => d !== dayIndex);
      } else {
        return [...prev, dayIndex];
      }
    });
  };

  // Format match quality score
  const formatQuality = (score) => {
    if (score >= 80) return { text: 'Excellent', color: '#28a745' };
    if (score >= 60) return { text: 'Very Good', color: '#17a2b8' };
    if (score >= 40) return { text: 'Good', color: '#ffc107' };
    return { text: 'Fair', color: '#6c757d' };
  };

  if (loading) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px',
        fontSize: '16px',
        color: '#6c757d'
      }}>
        Finding perfect golf matches...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 12px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ color: '#1f2937', marginBottom: '8px', fontSize: '20px' }}>
          🤖 Smart Matchmaking
        </h2>
        <p style={{ color: '#6b7280', fontSize: '14px', margin: 0 }}>
          Auto-generated 4-player groups based on schedules
        </p>
        <div style={{
          marginTop: '12px',
          padding: '12px',
          background: '#fef3c7',
          border: '1px solid #f59e0b',
          borderRadius: '10px',
          fontSize: '13px',
          color: '#92400e'
        }}>
          🔔 Groups are emailed daily at 10 AM
        </div>
      </div>

      {/* Filters */}
      <div style={{
        background: '#f9fafb',
        padding: '16px',
        borderRadius: '12px',
        marginBottom: '20px',
        border: '1px solid #e5e7eb'
      }}>
        <div style={{ marginBottom: '16px' }}>
          <label style={{
            display: 'block',
            fontSize: '14px',
            fontWeight: '600',
            color: '#374151',
            marginBottom: '10px'
          }}>
            Minimum Overlap Hours:
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <input
              type="range"
              min="1"
              max="6"
              step="0.5"
              value={minOverlapHours}
              onChange={(e) => setMinOverlapHours(parseFloat(e.target.value))}
              style={{ flex: 1, height: '8px' }}
            />
            <span style={{
              padding: '8px 14px',
              background: '#047857',
              color: 'white',
              borderRadius: '8px',
              fontSize: '15px',
              fontWeight: '700',
              minWidth: '50px',
              textAlign: 'center'
            }}>
              {minOverlapHours}h
            </span>
          </div>
        </div>

        <div>
          <label style={{
            display: 'block',
            fontSize: '14px',
            fontWeight: '600',
            color: '#374151',
            marginBottom: '10px'
          }}>
            Preferred Days:
          </label>
          <div
            className="mobile-date-picker"
            style={{
              display: 'flex',
              gap: '8px',
              overflowX: 'auto',
              WebkitOverflowScrolling: 'touch',
              padding: '4px',
              scrollbarWidth: 'none'
            }}
          >
            {dayNames.map((day, index) => {
              const shortDay = day.substring(0, 3);
              return (
                <button
                  key={index}
                  onClick={() => toggleDay(index)}
                  className="mobile-date-button"
                  style={{
                    flexShrink: 0,
                    minHeight: '44px',
                    padding: '10px 14px',
                    background: selectedDays.includes(index) ? '#047857' : 'white',
                    color: selectedDays.includes(index) ? 'white' : '#374151',
                    border: selectedDays.includes(index) ? '2px solid #047857' : '2px solid #e5e7eb',
                    borderRadius: '10px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    touchAction: 'manipulation'
                  }}
                >
                  {shortDay}
                </button>
              );
            })}
            {selectedDays.length > 0 && (
              <button
                onClick={() => setSelectedDays([])}
                style={{
                  flexShrink: 0,
                  minHeight: '44px',
                  padding: '10px 14px',
                  background: '#dc2626',
                  color: 'white',
                  border: 'none',
                  borderRadius: '10px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  touchAction: 'manipulation'
                }}
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Action Buttons - Mobile Stacked */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        marginBottom: '20px'
      }}>
        <div style={{ fontSize: '15px', color: '#374151', fontWeight: '600' }}>
          Found <span style={{ color: '#047857' }}>{matches.length}</span> potential matches
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={loadMatches}
            className="mobile-button mobile-button-secondary"
            style={{
              flex: 1,
              minHeight: '48px',
              padding: '12px 16px',
              background: '#f3f4f6',
              color: '#374151',
              border: '1px solid #d1d5db',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: 'pointer',
              touchAction: 'manipulation'
            }}
          >
            🔄 Refresh
          </button>
          <button
            onClick={sendAllNotifications}
            disabled={sendingNotifications || matches.length === 0}
            className="mobile-button mobile-button-primary"
            style={{
              flex: 2,
              minHeight: '48px',
              padding: '12px 16px',
              background: sendingNotifications || matches.length === 0 ? '#9ca3af' : '#047857',
              color: 'white',
              border: 'none',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: sendingNotifications || matches.length === 0 ? 'not-allowed' : 'pointer',
              touchAction: 'manipulation'
            }}
          >
            {sendingNotifications ? '⏳ Sending...' : '📧 Send Notifications'}
          </button>
        </div>
      </div>

      {/* Match Cards */}
      {matches.length > 0 ? (
        <div
          className="responsive-grid-3"
          style={{
            display: 'grid',
            gap: '16px'
          }}
        >
          {matches.map((match, index) => {
            const quality = formatQuality(match.match_quality);
            return (
              <div key={index} style={{
                border: '2px solid #dee2e6',
                borderRadius: '8px',
                padding: '20px',
                background: 'white',
                position: 'relative'
              }}>
                {/* Quality Badge */}
                <div style={{
                  position: 'absolute',
                  top: '10px',
                  right: '10px',
                  padding: '4px 8px',
                  background: quality.color,
                  color: 'white',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '600'
                }}>
                  {quality.text} Match
                </div>

                {/* Day and Time */}
                <h4 style={{
                  color: '#333',
                  fontSize: '18px',
                  marginBottom: '12px'
                }}>
                  {dayNames[match.day_of_week]}
                </h4>

                {/* Time Details */}
                <div style={{
                  background: '#f8f9fa',
                  padding: '12px',
                  borderRadius: '6px',
                  marginBottom: '16px'
                }}>
                  <div style={{ fontSize: '14px', color: '#495057', marginBottom: '6px' }}>
                    <strong>Available:</strong> {match.overlap_start} - {match.overlap_end}
                  </div>
                  <div style={{ fontSize: '14px', color: '#495057' }}>
                    <strong>Suggested Tee Time:</strong> 
                    <span style={{
                      marginLeft: '8px',
                      padding: '2px 8px',
                      background: '#007bff',
                      color: 'white',
                      borderRadius: '4px',
                      fontSize: '13px'
                    }}>
                      {match.suggested_tee_time}
                    </span>
                  </div>
                </div>

                {/* Players */}
                <div style={{ marginBottom: '16px' }}>
                  <h5 style={{
                    color: '#495057',
                    fontSize: '14px',
                    fontWeight: '600',
                    marginBottom: '8px'
                  }}>
                    Players ({match.players.length})
                  </h5>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {match.players.map((player, pidx) => (
                      <div key={pidx} style={{
                        padding: '6px 10px',
                        background: '#e9ecef',
                        borderRadius: '4px',
                        fontSize: '13px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <span style={{ fontWeight: '500' }}>{player.player_name}</span>
                        <span style={{ fontSize: '11px', color: '#6c757d' }}>
                          {player.available_from_time || 'Any'} - {player.available_to_time || 'Any'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Match Stats */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '8px 0',
                  borderTop: '1px solid #dee2e6',
                  fontSize: '12px',
                  color: '#6c757d'
                }}>
                  <span>
                    Overlap: {match.overlap_duration_hours.toFixed(1)}h
                  </span>
                  <span>
                    Score: {match.match_quality.toFixed(0)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div style={{
          padding: '60px',
          textAlign: 'center',
          background: '#f8f9fa',
          borderRadius: '8px',
          color: '#6c757d'
        }}>
          {error ? (
            <>
              <p style={{ fontSize: '16px', margin: '0 0 8px 0', color: '#dc3545' }}>
                {error}
              </p>
              <button
                onClick={loadMatches}
                style={{
                  marginTop: '10px',
                  padding: '8px 16px',
                  background: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                Try Again
              </button>
            </>
          ) : (
            <>
              <p style={{ fontSize: '16px', margin: '0 0 8px 0' }}>
                No matches found with current criteria
              </p>
              <p style={{ fontSize: '14px', margin: 0 }}>
                Try adjusting the minimum overlap hours or selecting different days
              </p>
            </>
          )}
        </div>
      )}

      {/* Info Section */}
      <div style={{
        marginTop: '40px',
        padding: '20px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '8px',
        color: 'white'
      }}>
        <h4 style={{ color: 'white', marginBottom: '10px' }}>
          🎯 Matchmaking Features
        </h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '15px',
          fontSize: '13px'
        }}>
          <div>
            <strong>🤝 Group Formation:</strong>
            <div style={{ marginTop: '4px', opacity: 0.9 }}>Automatically creates perfect 4-player groups</div>
          </div>
          <div>
            <strong>⏰ Time Optimization:</strong>
            <div style={{ marginTop: '4px', opacity: 0.9 }}>Finds optimal tee times for all players</div>
          </div>
          <div>
            <strong>📧 Email Invitations:</strong>
            <div style={{ marginTop: '4px', opacity: 0.9 }}>Sends notifications to matched players</div>
          </div>
          <div>
            <strong>🔄 Smart Rotation:</strong>
            <div style={{ marginTop: '4px', opacity: 0.9 }}>Avoids re-matching same groups (3-day cooldown)</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchmakingSuggestions;
