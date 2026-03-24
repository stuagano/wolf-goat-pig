import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import useTeeTimes from '../../hooks/useTeeTimes';
import BookingModal from '../foretees/BookingModal';

const API_URL = process.env.REACT_APP_API_URL || '';

const dayNamesFull = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

// Get the next occurrence of a day-of-week (0=Mon, 6=Sun)
const getNextDateForDay = (dayOfWeek) => {
  const today = new Date();
  const todayDay = (today.getDay() + 6) % 7;
  let daysUntil = dayOfWeek - todayDay;
  if (daysUntil < 0) daysUntil += 7;
  const d = new Date(today);
  d.setDate(today.getDate() + daysUntil);
  return d.toISOString().split('T')[0];
};

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

const MyMatches = () => {
  const navigate = useNavigate();
  const { getAccessTokenSilently } = useAuth0();
  const { fetchTeeTimes, bookTeeTime, bookingLoading, bookingError, clearBookingError } = useTeeTimes();

  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [respondingTo, setRespondingTo] = useState(null);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [expandedMatchId, setExpandedMatchId] = useState(null);
  const [teeTimeData, setTeeTimeData] = useState({});
  const [teeTimeLoading, setTeeTimeLoading] = useState(false);
  const [bookingSlot, setBookingSlot] = useState(null);
  const [bookingResult, setBookingResult] = useState(null);

  const authFetch = useCallback(async (url, options = {}) => {
    const token = await getAccessTokenSilently();
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`;
    return fetch(fullUrl, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
  }, [getAccessTokenSilently]);

  const fetchMatches = useCallback(async (overrideStatus) => {
    setLoading(true);
    setError(null);
    try {
      const filter = overrideStatus !== undefined ? overrideStatus : statusFilter;
      const params = filter ? `?status=${filter}` : '';
      const resp = await authFetch(`/matchmaking/my-matches${params}`);
      if (resp.ok) {
        setMatches(await resp.json());
      } else {
        const err = await resp.json();
        setError(err.detail || 'Failed to load matches');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [authFetch, statusFilter]);

  useEffect(() => { fetchMatches(); }, [fetchMatches]);

  useEffect(() => {
    if (bookingResult) {
      const t = setTimeout(() => setBookingResult(null), 5000);
      return () => clearTimeout(t);
    }
  }, [bookingResult]);

  const handleRespond = async (matchId, response) => {
    setRespondingTo(matchId);
    try {
      const resp = await authFetch(`/matchmaking/matches/${matchId}/respond`, {
        method: 'POST',
        body: JSON.stringify({ response }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        setError(data.detail || `Failed to ${response}`);
      } else if (data.all_accepted) {
        // All players accepted — switch to "accepted" filter so the user
        // can see the "Book Tee Time" button that just became available.
        setStatusFilter('accepted');
        setBookingResult({
          type: 'success',
          message: 'All players confirmed! You can now book a tee time.',
        });
        // Fetch with the new filter immediately (state hasn't updated yet)
        await fetchMatches('accepted');
        return;
      }
      await fetchMatches();
    } catch (err) {
      setError(err.message);
    } finally {
      setRespondingTo(null);
    }
  };

  const handleToggleTeeTimes = async (match) => {
    const matchId = match.id;
    if (expandedMatchId === matchId) {
      setExpandedMatchId(null);
      return;
    }
    setExpandedMatchId(matchId);
    if (teeTimeData[matchId]) return;

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
        setTeeTimeData(prev => ({
          ...prev,
          [matchId]: { date, inWindow, allCount: result.data.filter(s => s.open_slots > 0).length }
        }));
      } else {
        setTeeTimeData(prev => ({
          ...prev,
          [matchId]: { date, error: result?.detail || result?.message || 'Could not load tee times' }
        }));
      }
    } catch (err) {
      setTeeTimeData(prev => ({
        ...prev,
        [matchId]: { date: getNextDateForDay(match.day_of_week), error: err.message }
      }));
    } finally {
      setTeeTimeLoading(false);
    }
  };

  const handleBookConfirm = async ({ transportMode }) => {
    const result = await bookTeeTime(bookingSlot.ttdata, transportMode);
    if (result?.data?.success) {
      setBookingResult({ type: 'success', message: result.message || 'Tee time booked!' });
      setBookingSlot(null);
      setTeeTimeData(prev => { const n = { ...prev }; delete n[expandedMatchId]; return n; });
      setExpandedMatchId(null);
    } else {
      const msg = result?.message || result?.detail || bookingError || 'Booking failed. Please try again.';
      const isCredentialError = /credentials? not configured|login failed/i.test(msg);
      setBookingResult({ type: 'error', message: msg, showAccountLink: isCredentialError });
      setBookingSlot(null);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: { bg: '#fef3c7', color: '#92400e', label: 'Pending' },
      accepted: { bg: '#d1fae5', color: '#065f46', label: 'Confirmed' },
      declined: { bg: '#fee2e2', color: '#991b1b', label: 'Declined' },
      expired: { bg: '#f3f4f6', color: '#6b7280', label: 'Expired' },
    };
    const s = styles[status] || styles.pending;
    return (
      <span style={{
        padding: '3px 8px', borderRadius: '6px', fontSize: '11px',
        fontWeight: '600', background: s.bg, color: s.color,
      }}>
        {s.label}
      </span>
    );
  };

  const getPlayerResponseIcon = (response) => {
    if (response === 'accepted') return '✓';
    if (response === 'declined') return '✗';
    return '?';
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#6b7280' }}>
        Loading your matches...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '16px' }}>
      {/* Booking Result Toast */}
      {bookingResult && (
        <div
          style={{
            padding: 16, marginBottom: 16,
            background: bookingResult.type === 'success' ? '#ecfdf5' : '#fef2f2',
            color: bookingResult.type === 'success' ? '#166534' : '#991b1b',
            borderLeft: `4px solid ${bookingResult.type === 'success' ? '#10b981' : '#ef4444'}`,
            borderRadius: 8, cursor: 'pointer',
          }}
          onClick={() => setBookingResult(null)}
        >
          {bookingResult.message}
          {bookingResult.showAccountLink && (
            <button
              onClick={(e) => { e.stopPropagation(); navigate('/account'); }}
              style={{
                display: 'block', marginTop: 8, padding: '6px 16px', borderRadius: 8,
                border: '1px solid #991b1b', background: 'transparent', color: '#991b1b',
                fontSize: 13, fontWeight: 600, cursor: 'pointer',
              }}
            >
              Set up ForeTees credentials
            </button>
          )}
        </div>
      )}

      {/* Info Banner */}
      <div style={{
        background: '#ecfdf5', border: '1px solid #10b981',
        borderRadius: 10, padding: 12, marginBottom: 20,
        fontSize: 13, color: '#065f46',
      }}>
        Accept matches to confirm your group, then book a tee time together on ForeTees
      </div>

      {/* Status Filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {['pending', 'accepted', 'declined', ''].map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            style={{
              flex: 1, padding: '10px 8px', borderRadius: 8, fontSize: 13,
              fontWeight: 600, cursor: 'pointer',
              background: statusFilter === s ? '#047857' : '#f3f4f6',
              color: statusFilter === s ? '#fff' : '#374151',
              border: statusFilter === s ? '2px solid #047857' : '1px solid #e5e7eb',
            }}
          >
            {s === '' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {error && (
        <div style={{
          background: '#fef2f2', color: '#dc2626', padding: 12,
          borderRadius: 8, marginBottom: 16, fontSize: 14,
        }}>
          {error}
          <button onClick={() => setError(null)} style={{
            float: 'right', background: 'none', border: 'none', cursor: 'pointer'
          }}>×</button>
        </div>
      )}

      {/* Match Cards */}
      {matches.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '40px 20px', color: '#9ca3af',
          background: '#f9fafb', borderRadius: 12,
        }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>🏌️</div>
          <p style={{ margin: 0 }}>No {statusFilter || ''} matches yet</p>
          <p style={{ margin: '8px 0 0', fontSize: 13 }}>
            Set your availability and we'll find compatible groups automatically
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {matches.map(match => {
            const isExpanded = expandedMatchId === match.id;
            const ttData = teeTimeData[match.id];
            const allAccepted = match.players.every(p => p.response === 'accepted');
            const canBook = match.status === 'accepted' && allAccepted;

            return (
              <div
                key={match.id}
                style={{
                  background: '#fff', border: '1px solid #e5e7eb',
                  borderRadius: 12, padding: 16, position: 'relative',
                }}
              >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <h4 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: '#1f2937' }}>
                    {dayNamesFull[match.day_of_week]}
                  </h4>
                  {getStatusBadge(match.status)}
                </div>

                {/* Time */}
                <div style={{
                  background: '#f9fafb', padding: 10, borderRadius: 8,
                  marginBottom: 12, fontSize: 13, color: '#4b5563',
                }}>
                  <div>{match.overlap_start} - {match.overlap_end}</div>
                  <div style={{ marginTop: 4 }}>
                    Suggested: <span style={{
                      background: '#0369a1', color: 'white',
                      padding: '2px 8px', borderRadius: 4, fontSize: 12,
                    }}>{match.suggested_tee_time}</span>
                  </div>
                </div>

                {/* Players with response status */}
                <div style={{ fontSize: 13, fontWeight: 600, color: '#6b7280', marginBottom: 8 }}>
                  Players ({match.players.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
                  {match.players.map((player) => (
                    <div
                      key={player.id}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        background: player.response === 'accepted' ? '#ecfdf5'
                          : player.response === 'declined' ? '#fef2f2'
                          : '#f9fafb',
                        padding: '8px 10px', borderRadius: 6,
                      }}
                    >
                      <span style={{
                        fontSize: 13, fontWeight: 500,
                        color: player.response === 'declined' ? '#991b1b' : '#065f46',
                      }}>
                        {player.player_name}
                      </span>
                      <span style={{
                        fontSize: 12, fontWeight: 600,
                        color: player.response === 'accepted' ? '#047857'
                          : player.response === 'declined' ? '#dc2626'
                          : '#9ca3af',
                      }}>
                        {getPlayerResponseIcon(player.response)}{' '}
                        {player.response ? player.response.charAt(0).toUpperCase() + player.response.slice(1) : 'Waiting'}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Accept / Decline Buttons */}
                {match.status === 'pending' && (
                  <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                    <button
                      onClick={() => handleRespond(match.id, 'accepted')}
                      disabled={respondingTo === match.id}
                      style={{
                        flex: 2, padding: 12, borderRadius: 8, fontSize: 14,
                        fontWeight: 600, border: 'none', cursor: 'pointer',
                        background: respondingTo === match.id ? '#9ca3af' : '#047857',
                        color: '#fff',
                      }}
                    >
                      {respondingTo === match.id ? 'Responding...' : 'Accept'}
                    </button>
                    <button
                      onClick={() => handleRespond(match.id, 'declined')}
                      disabled={respondingTo === match.id}
                      style={{
                        flex: 1, padding: 12, borderRadius: 8, fontSize: 14,
                        fontWeight: 600, cursor: 'pointer',
                        background: '#fff', color: '#dc2626',
                        border: '1px solid #fecaca',
                      }}
                    >
                      Decline
                    </button>
                  </div>
                )}

                {/* Book Tee Time Button (only when all accepted) */}
                {canBook && (
                  <button
                    onClick={() => handleToggleTeeTimes(match)}
                    disabled={teeTimeLoading && expandedMatchId === match.id}
                    style={{
                      width: '100%', padding: '12px 16px', borderRadius: 8,
                      fontSize: 14, fontWeight: 600, cursor: 'pointer',
                      background: isExpanded ? '#f3f4f6' : '#10b981',
                      color: isExpanded ? '#374151' : '#fff',
                      border: isExpanded ? '1px solid #d1d5db' : 'none',
                    }}
                  >
                    {teeTimeLoading && expandedMatchId === match.id
                      ? 'Loading tee times...'
                      : isExpanded
                        ? 'Hide Tee Times'
                        : `Book Tee Time for ${formatDateDisplay(getNextDateForDay(match.day_of_week))}`}
                  </button>
                )}

                {/* Expanded Tee Times Section */}
                {isExpanded && ttData && (
                  <div style={{
                    marginTop: 12, padding: 12, background: '#f0fdf4',
                    borderRadius: 8, border: '1px solid #bbf7d0',
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
                              display: 'block', marginTop: 8, padding: '6px 16px',
                              borderRadius: 6, border: '1px solid #991b1b',
                              background: 'transparent', color: '#991b1b',
                              fontSize: 13, fontWeight: 600, cursor: 'pointer',
                            }}
                          >
                            Set up ForeTees credentials
                          </button>
                        )}
                      </div>
                    ) : ttData.inWindow.length === 0 ? (
                      <div style={{ color: '#6b7280', fontSize: 13, fontStyle: 'italic' }}>
                        No open slots in this time window.
                        {ttData.allCount > 0 && <span> ({ttData.allCount} open at other times)</span>}
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {ttData.inWindow.map((slot, si) => (
                          <div
                            key={si}
                            style={{
                              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                              background: '#fff', padding: '10px 12px', borderRadius: 6,
                              border: '1px solid #e5e7eb',
                            }}
                          >
                            <div>
                              <div style={{ fontWeight: 700, fontSize: 15, color: '#1f2937' }}>{slot.time}</div>
                              <div style={{ fontSize: 12, color: '#6b7280' }}>
                                {slot.front_back === 'F' ? 'Front' : 'Back'} &middot; {slot.open_slots} open
                              </div>
                              {slot.players && slot.players.length > 0 && (
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
                                  padding: '8px 16px', background: '#10b981', color: '#fff',
                                  border: 'none', borderRadius: 6, fontSize: 13,
                                  fontWeight: 600, cursor: 'pointer', flexShrink: 0,
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
      )}

      {/* Booking Modal */}
      <BookingModal
        isOpen={bookingSlot !== null}
        onClose={() => { setBookingSlot(null); clearBookingError(); }}
        onConfirm={handleBookConfirm}
        slot={bookingSlot}
        loading={bookingLoading}
      />
    </div>
  );
};

export default MyMatches;
