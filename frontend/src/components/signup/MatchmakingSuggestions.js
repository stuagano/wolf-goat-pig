import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import useTeeTimes from '../../hooks/useTeeTimes';
import BookingModal from '../foretees/BookingModal';
import { apiConfig } from '../../config/api.config';

const API_URL = apiConfig.baseUrl;

// Get the next occurrence of a day-of-week (0=Mon, 6=Sun)
const getNextDateForDay = (dayOfWeek) => {
  const today = new Date();
  const todayDay = (today.getDay() + 6) % 7; // JS Sun=0 → Mon=0
  let daysUntil = dayOfWeek - todayDay;
  if (daysUntil < 0) daysUntil += 7;
  const d = new Date(today);
  d.setDate(today.getDate() + daysUntil);
  return d.toISOString().split('T')[0];
};

// Parse "4:30 PM" or "07:30" to minutes since midnight
const parseTimeToMinutes = (timeStr) => {
  if (!timeStr) return 0;
  const ampm = timeStr.match(/(\d+):(\d+)\s*(AM|PM)/i);
  if (ampm) {
    let h = parseInt(ampm[1]);
    const m = parseInt(ampm[2]);
    if (ampm[3].toUpperCase() === 'PM' && h !== 12) h += 12;
    if (ampm[3].toUpperCase() === 'AM' && h === 12) h = 0;
    return h * 60 + m;
  }
  const h24 = timeStr.match(/(\d+):(\d+)/);
  return h24 ? parseInt(h24[1]) * 60 + parseInt(h24[2]) : 0;
};

const formatDateDisplay = (dateStr) => {
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
};

const MatchmakingSuggestions = () => {
  const navigate = useNavigate();
  const {
    fetchTeeTimes,
    bookTeeTime, bookingLoading, clearBookingError,
  } = useTeeTimes();

  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [minOverlapHours, setMinOverlapHours] = useState(2);
  const [selectedDays, setSelectedDays] = useState([]);
  const [sendingNotifications, setSendingNotifications] = useState(false);

  // ForeTees tee time state
  const [expandedIdx, setExpandedIdx] = useState(null);
  const [teeTimeCache, setTeeTimeCache] = useState({}); // keyed by match index
  const [teeTimeLoading, setTeeTimeLoading] = useState(false);
  const [bookingSlot, setBookingSlot] = useState(null);
  const [bookingResult, setBookingResult] = useState(null);

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
      setError(err.message);
      setMatches([]);
    } finally {
      setLoading(false);
    }
  }, [minOverlapHours, selectedDays]);

  useEffect(() => {
    loadMatches();
  }, [loadMatches]);

  useEffect(() => {
    if (bookingResult) {
      const t = setTimeout(() => setBookingResult(null), 5000);
      return () => clearTimeout(t);
    }
  }, [bookingResult]);

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

  const handleToggleTeeTimes = async (index, match) => {
    if (expandedIdx === index) {
      setExpandedIdx(null);
      return;
    }
    setExpandedIdx(index);

    // Use cached data if available
    if (teeTimeCache[index]) return;

    setTeeTimeLoading(true);
    try {
      const date = getNextDateForDay(match.day_of_week);
      const result = await fetchTeeTimes(date);
      if (result?.data) {
        const overlapStart = parseTimeToMinutes(match.overlap_start);
        const overlapEnd = parseTimeToMinutes(match.overlap_end);
        const inWindow = result.data.filter(slot => {
          const mins = parseTimeToMinutes(slot.time);
          return mins >= overlapStart && mins <= overlapEnd;
        });
        setTeeTimeCache(prev => ({
          ...prev,
          [index]: { date, inWindow, allCount: result.data.filter(s => s.open_slots > 0).length }
        }));
      } else {
        setTeeTimeCache(prev => ({
          ...prev,
          [index]: { date, error: result?.detail || result?.message || 'Could not load tee times' }
        }));
      }
    } catch (err) {
      setTeeTimeCache(prev => ({
        ...prev,
        [index]: { date: getNextDateForDay(match.day_of_week), error: err.message }
      }));
    } finally {
      setTeeTimeLoading(false);
    }
  };

  const handleBookConfirm = async ({ transportMode }) => {
    const result = await bookTeeTime(bookingSlot.ttdata, transportMode, bookingSlot.date, bookingSlot.time);
    if (result?.data?.success) {
      setBookingResult({ type: 'success', message: result.message || 'Tee time booked!' });
      setBookingSlot(null);
      // Clear cached tee times so they refresh on next expand
      setTeeTimeCache(prev => {
        const next = { ...prev };
        delete next[expandedIdx];
        return next;
      });
      setExpandedIdx(null);
    } else {
      const msg = result?.message || result?.detail || 'Booking failed';
      const isCredentialError = /credentials? not configured|login failed/i.test(msg);
      setBookingResult({ type: 'error', message: msg, showAccountLink: isCredentialError });
      setBookingSlot(null);
    }
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
      {/* Booking Result Toast */}
      {bookingResult && (
        <div
          style={{
            padding: 16,
            marginBottom: 16,
            background: bookingResult.type === 'success' ? '#ecfdf5' : '#fef2f2',
            color: bookingResult.type === 'success' ? '#166534' : '#991b1b',
            borderLeft: `4px solid ${bookingResult.type === 'success' ? '#10b981' : '#ef4444'}`,
            borderRadius: 8,
            cursor: 'pointer',
          }}
          onClick={() => setBookingResult(null)}
        >
          {bookingResult.message}
          {bookingResult.showAccountLink && (
            <button
              onClick={(e) => { e.stopPropagation(); navigate('/account'); }}
              style={{
                display: 'block',
                marginTop: 8,
                padding: '6px 16px',
                borderRadius: 8,
                border: '1px solid #991b1b',
                background: 'transparent',
                color: '#991b1b',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              Set up ForeTees credentials
            </button>
          )}
        </div>
      )}

      {/* Info Banner */}
      <div style={{
        background: '#ecfdf5',
        border: '1px solid #10b981',
        borderRadius: 10,
        padding: 12,
        marginBottom: 20,
        fontSize: 13,
        color: '#065f46'
      }}>
        Find your group, then book a tee time on ForeTees
      </div>

      {/* Filters */}
      <div style={{
        background: '#f9fafb',
        padding: 16,
        borderRadius: 12,
        marginBottom: 20,
        border: '1px solid #e5e7eb'
      }}>
        {/* Overlap Hours */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', fontSize: 14, fontWeight: 600, color: '#374151', marginBottom: 8 }}>
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
          <label style={{ display: 'block', fontSize: 14, fontWeight: 600, color: '#374151', marginBottom: 8 }}>
            Preferred Days
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 6 }}>
            {dayNames.map((day, index) => (
              <button
                key={index}
                onClick={() => toggleDay(index)}
                style={{
                  padding: '8px 4px',
                  background: selectedDays.includes(index) ? '#047857' : 'white',
                  color: selectedDays.includes(index) ? 'white' : '#374151',
                  border: selectedDays.includes(index) ? '2px solid #047857' : '1px solid #e5e7eb',
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: 600,
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
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        <button
          onClick={loadMatches}
          style={{
            flex: 1,
            padding: 12,
            background: '#f3f4f6',
            color: '#374151',
            border: '1px solid #d1d5db',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          Refresh
        </button>
        <button
          onClick={sendAllNotifications}
          disabled={sendingNotifications || matches.length === 0}
          style={{
            flex: 2,
            padding: 12,
            background: sendingNotifications || matches.length === 0 ? '#9ca3af' : '#047857',
            color: 'white',
            border: 'none',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 600,
            cursor: sendingNotifications || matches.length === 0 ? 'not-allowed' : 'pointer'
          }}
        >
          {sendingNotifications ? 'Sending...' : 'Notify All'}
        </button>
      </div>

      {/* Results Count */}
      <div style={{ marginBottom: 16, fontSize: 15, color: '#374151' }}>
        Found <span style={{ fontWeight: 700, color: '#047857' }}>{matches.length}</span> matches
      </div>

      {/* Match Cards */}
      {error ? (
        <div style={{
          background: '#fef2f2',
          color: '#dc2626',
          padding: 16,
          borderRadius: 8,
          textAlign: 'center'
        }}>
          {error}
          <button
            onClick={loadMatches}
            style={{
              marginTop: 10,
              padding: '8px 16px',
              background: '#dc2626',
              color: 'white',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer'
            }}
          >
            Try Again
          </button>
        </div>
      ) : matches.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {matches.map((match, index) => {
            const quality = formatQuality(match.match_quality);
            const isExpanded = expandedIdx === index;
            const ttData = teeTimeCache[index];

            return (
              <div
                key={index}
                style={{
                  background: '#fff',
                  border: '1px solid #e5e7eb',
                  borderRadius: 12,
                  padding: 16,
                  position: 'relative'
                }}
              >
                {/* Quality Badge */}
                <span style={{
                  position: 'absolute',
                  top: 12,
                  right: 12,
                  padding: '4px 8px',
                  background: quality.color,
                  color: 'white',
                  borderRadius: 6,
                  fontSize: 11,
                  fontWeight: 600
                }}>
                  {quality.text}
                </span>

                {/* Day */}
                <h4 style={{ margin: '0 0 12px', fontSize: 16, fontWeight: 600, color: '#1f2937' }}>
                  {dayNamesFull[match.day_of_week]}
                </h4>

                {/* Time */}
                <div style={{
                  background: '#f9fafb',
                  padding: 10,
                  borderRadius: 8,
                  marginBottom: 12,
                  fontSize: 13,
                  color: '#4b5563'
                }}>
                  <div>{match.overlap_start} - {match.overlap_end}</div>
                  <div style={{ marginTop: 4 }}>
                    Suggested: <span style={{
                      background: '#0369a1',
                      color: 'white',
                      padding: '2px 8px',
                      borderRadius: 4,
                      fontSize: 12
                    }}>{match.suggested_tee_time}</span>
                  </div>
                </div>

                {/* Players */}
                <div style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: '#6b7280',
                  marginBottom: 8
                }}>
                  Players ({match.players.length})
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {match.players.map((player, pidx) => (
                    <span
                      key={pidx}
                      style={{
                        background: '#ecfdf5',
                        padding: '6px 10px',
                        borderRadius: 6,
                        fontSize: 13,
                        fontWeight: 500,
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
                  marginTop: 12,
                  paddingTop: 12,
                  borderTop: '1px solid #e5e7eb',
                  fontSize: 12,
                  color: '#6b7280'
                }}>
                  <span>Overlap: {match.overlap_duration_hours.toFixed(1)}h</span>
                  <span>Score: {match.match_quality.toFixed(0)}</span>
                </div>

                {/* Find Tee Times Button */}
                <button
                  onClick={() => handleToggleTeeTimes(index, match)}
                  disabled={teeTimeLoading && expandedIdx === index}
                  style={{
                    width: '100%',
                    marginTop: 12,
                    padding: '10px 16px',
                    background: isExpanded ? '#f3f4f6' : '#10b981',
                    color: isExpanded ? '#374151' : '#fff',
                    border: isExpanded ? '1px solid #d1d5db' : 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  {teeTimeLoading && expandedIdx === index
                    ? 'Loading tee times...'
                    : isExpanded
                      ? 'Hide Tee Times'
                      : `Find Tee Times for ${formatDateDisplay(getNextDateForDay(match.day_of_week))}`}
                </button>

                {/* Expanded Tee Times Section */}
                {isExpanded && ttData && (
                  <div style={{
                    marginTop: 12,
                    padding: 12,
                    background: '#f0fdf4',
                    borderRadius: 8,
                    border: '1px solid #bbf7d0'
                  }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#166534', marginBottom: 8 }}>
                      Available Tee Times - {formatDateDisplay(ttData.date)} ({match.overlap_start} - {match.overlap_end})
                    </div>

                    {ttData.error ? (
                      <div style={{ color: '#991b1b', fontSize: 13 }}>
                        {ttData.error}
                        {/credentials? not configured/i.test(ttData.error) && (
                          <button
                            onClick={() => navigate('/account')}
                            style={{
                              display: 'block',
                              marginTop: 8,
                              padding: '6px 16px',
                              borderRadius: 6,
                              border: '1px solid #991b1b',
                              background: 'transparent',
                              color: '#991b1b',
                              fontSize: 13,
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            Set up ForeTees credentials
                          </button>
                        )}
                      </div>
                    ) : ttData.inWindow.length === 0 ? (
                      <div style={{ color: '#6b7280', fontSize: 13, fontStyle: 'italic' }}>
                        No open slots in this time window.
                        {ttData.allCount > 0 && (
                          <span> ({ttData.allCount} open at other times)</span>
                        )}
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {ttData.inWindow.map((slot, si) => (
                          <div
                            key={si}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              background: '#fff',
                              padding: '10px 12px',
                              borderRadius: 6,
                              border: '1px solid #e5e7eb'
                            }}
                          >
                            <div>
                              <div style={{ fontWeight: 700, fontSize: 15, color: '#1f2937' }}>
                                {slot.time}
                              </div>
                              <div style={{ fontSize: 12, color: '#6b7280' }}>
                                {slot.front_back === 'F' ? 'Front' : 'Back'} &middot; {slot.open_slots} open
                              </div>
                              {slot.players.length > 0 && (
                                <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 2 }}>
                                  {slot.players.map(p => p.name).join(', ')}
                                </div>
                              )}
                            </div>
                            {slot.open_slots > 0 && (
                              <button
                                onClick={() => {
                                  clearBookingError();
                                  setBookingSlot({ ...slot, date: formatDateDisplay(ttData.date) });
                                }}
                                style={{
                                  padding: '8px 16px',
                                  background: '#10b981',
                                  color: '#fff',
                                  border: 'none',
                                  borderRadius: 6,
                                  fontSize: 13,
                                  fontWeight: 600,
                                  cursor: 'pointer',
                                  flexShrink: 0,
                                }}
                              >
                                Book
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
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
          borderRadius: 12
        }}>
          <p style={{ margin: 0 }}>No matches found with current criteria</p>
          <p style={{ margin: '8px 0 0', fontSize: 13 }}>Try adjusting the overlap hours or selected days</p>
        </div>
      )}

      {/* Booking Modal */}
      <BookingModal
        isOpen={bookingSlot !== null}
        onClose={() => {
          setBookingSlot(null);
          clearBookingError();
        }}
        onConfirm={handleBookConfirm}
        slot={bookingSlot}
        loading={bookingLoading}
      />
    </div>
  );
};

export default MatchmakingSuggestions;
