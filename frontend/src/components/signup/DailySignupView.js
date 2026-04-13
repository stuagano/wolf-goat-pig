import React, { useState, useEffect, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import '../../styles/mobile-touch.css';
import { apiConfig } from '../../config/api.config';

const API_URL = apiConfig.baseUrl;

const DailySignupView = ({ selectedDate: initialDate, onBack }) => {
  const { user, isAuthenticated } = useAuth0();
  const [currentWeekStart, setCurrentWeekStart] = useState('');
  const [selectedDate, setSelectedDate] = useState(initialDate || '');
  const [weekData, setWeekData] = useState({ daily_summaries: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [teeTimesText, setTeeTimesText] = useState('');
  const [generatedPairings, setGeneratedPairings] = useState(null);
  const [pairingsLoading, setPairingsLoading] = useState(false);
  const [confirmingSignup, setConfirmingSignup] = useState(false);
  const [legacyReplicating, setLegacyReplicating] = useState(false);
  const [legacyResult, setLegacyResult] = useState(null);

  // Compute the Sunday that starts the week containing a given date
  const getSundayOfWeek = useCallback((dateStr) => {
    const d = new Date(dateStr + 'T12:00:00');
    const day = d.getDay(); // 0=Sun
    d.setDate(d.getDate() - day);
    return d.toISOString().split('T')[0];
  }, []);

  // Initialize dates
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    const startDate = initialDate || today;
    setSelectedDate(startDate);
    const sunday = getSundayOfWeek(startDate);
    setCurrentWeekStart(sunday);
  }, [initialDate, getSundayOfWeek]);

  // Load weekly data whenever week changes
  const loadWeeklyData = useCallback(async (weekStart) => {
    if (!weekStart) return;
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/signups/weekly-with-messages?week_start=${weekStart}`);
      if (response.ok) {
        const data = await response.json();
        setWeekData(data);
      } else {
        setWeekData({ daily_summaries: [] });
      }
      setError(null);
    } catch (err) {
      console.error('Error loading weekly data:', err);
      setError('Unable to load signup data');
      setWeekData({ daily_summaries: [] });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (currentWeekStart) {
      loadWeeklyData(currentWeekStart);
    }
  }, [currentWeekStart, loadWeeklyData]);

  // Load generated pairings for the selected date
  const loadGeneratedPairings = useCallback(async (date) => {
    if (!date) return;
    try {
      setPairingsLoading(true);
      const response = await fetch(`${API_URL}/pairings/${date}`);
      if (response.ok) {
        const data = await response.json();
        setGeneratedPairings(data.exists ? data : null);
      } else {
        setGeneratedPairings(null);
      }
    } catch (err) {
      setGeneratedPairings(null);
    } finally {
      setPairingsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedDate) {
      loadGeneratedPairings(selectedDate);
    }
    setConfirmingSignup(false);
    setLegacyResult(null);
  }, [selectedDate, loadGeneratedPairings]);

  // Get data for the currently selected day
  const getDayData = () => {
    if (!weekData.daily_summaries || !selectedDate) return null;
    return weekData.daily_summaries.find(day => day.date === selectedDate);
  };

  // Get the 7 days of the current week
  const getWeekDays = () => {
    if (!currentWeekStart) return [];
    const days = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(currentWeekStart + 'T12:00:00');
      d.setDate(d.getDate() + i);
      days.push(d.toISOString().split('T')[0]);
    }
    return days;
  };

  // Format for week range display: "Sun - Sun: Feb 16 - Feb 22"
  const formatWeekRange = () => {
    if (!currentWeekStart) return '';
    const start = new Date(currentWeekStart + 'T12:00:00');
    const end = new Date(currentWeekStart + 'T12:00:00');
    end.setDate(end.getDate() + 6);
    const startStr = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const endStr = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return `Sun - Sat: ${startStr} - ${endStr}`;
  };

  // Format full date for the day header
  const formatDateFull = (dateStr) => {
    const d = new Date(dateStr + 'T12:00:00');
    return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  };

  const getDayName = (dateStr) => {
    const d = new Date(dateStr + 'T12:00:00');
    return d.toLocaleDateString('en-US', { weekday: 'short' });
  };

  const isToday = (dateStr) => {
    return dateStr === new Date().toISOString().split('T')[0];
  };

  // Navigate weeks
  const navigateWeek = (direction) => {
    const d = new Date(currentWeekStart + 'T12:00:00');
    d.setDate(d.getDate() + (direction * 7));
    const newWeekStart = d.toISOString().split('T')[0];
    setCurrentWeekStart(newWeekStart);
    // Select the same day-of-week in the new week
    const currentDayIndex = getWeekDays().indexOf(selectedDate);
    const newDate = new Date(newWeekStart + 'T12:00:00');
    newDate.setDate(newDate.getDate() + (currentDayIndex >= 0 ? currentDayIndex : 0));
    setSelectedDate(newDate.toISOString().split('T')[0]);
  };

  // Handle signup with confirmation step
  const handleSignupClick = () => {
    if (confirmingSignup) {
      handleSignup();
    } else {
      setConfirmingSignup(true);
    }
  };

  const handleSignup = async () => {
    if (!isAuthenticated || !user) {
      setError('Please log in to sign up');
      return;
    }
    try {
      const playerName = user.name || user.email;
      const response = await fetch(`${API_URL}/signups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: selectedDate,
          player_profile_id: 1,
          player_name: playerName,
          preferred_start_time: null,
          notes: null
        })
      });
      if (response.ok) {
        loadWeeklyData(currentWeekStart);
        setError(null);
        setConfirmingSignup(false);
      } else {
        const errData = await response.json();
        throw new Error(errData.detail || 'Failed to sign up');
      }
    } catch (err) {
      console.error('Signup error:', err);
      setError(err.message || 'Failed to sign up. Please try again.');
      setConfirmingSignup(false);
    }
  };

  // Replicate signup to legacy page
  const handleLegacyReplicate = async () => {
    if (!isAuthenticated || !user || !userSignup) {
      setError('You must be signed up first to replicate to legacy');
      return;
    }
    try {
      setLegacyReplicating(true);
      setLegacyResult(null);
      const response = await fetch(`${API_URL}/signups/${userSignup.id}/replicate-legacy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      if (response.ok) {
        setLegacyResult({ success: true, message: data.message || 'Replicated to legacy signup page' });
      } else {
        setLegacyResult({ success: false, message: data.detail || 'Failed to replicate' });
      }
    } catch (err) {
      console.error('Legacy replicate error:', err);
      setLegacyResult({ success: false, message: 'Failed to replicate to legacy signup page' });
    } finally {
      setLegacyReplicating(false);
    }
  };

  // Handle cancel signup
  const handleCancelSignup = async (signupId) => {
    try {
      const response = await fetch(`${API_URL}/signups/${signupId}`, { method: 'DELETE' });
      if (response.ok) {
        loadWeeklyData(currentWeekStart);
        setError(null);
      } else {
        throw new Error('Failed to cancel signup');
      }
    } catch (err) {
      console.error('Cancel error:', err);
      setError('Failed to cancel signup');
    }
  };

  const dayData = getDayData();
  const weekDays = getWeekDays();
  const players = dayData?.signups || [];
  const userIsSignedUp = isAuthenticated && players.some(p =>
    p.player_name === (user?.name || user?.email) && p.status !== 'cancelled'
  );
  const userSignup = isAuthenticated ? players.find(p =>
    p.player_name === (user?.name || user?.email) && p.status !== 'cancelled'
  ) : null;

  if (loading && !weekData.daily_summaries.length) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '300px',
        fontSize: '16px',
        color: '#6b7280'
      }}>
        Loading signup sheet...
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: '900px',
      margin: '0 auto',
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
      overflow: 'hidden'
    }}>
      {/* Week Navigation Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#2d5016',
        color: 'white',
        padding: '10px 16px'
      }}>
        <button
          onClick={() => navigateWeek(-1)}
          style={{
            background: 'rgba(255,255,255,0.15)',
            color: 'white',
            border: '1px solid rgba(255,255,255,0.3)',
            borderRadius: '4px',
            padding: '8px 16px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            whiteSpace: 'nowrap'
          }}
        >
          Previous Week
        </button>

        <div style={{
          fontSize: '16px',
          fontWeight: '700',
          textAlign: 'center',
          flex: 1,
          padding: '0 12px'
        }}>
          {formatWeekRange()}
        </div>

        <button
          onClick={() => navigateWeek(1)}
          style={{
            background: 'rgba(255,255,255,0.15)',
            color: 'white',
            border: '1px solid rgba(255,255,255,0.3)',
            borderRadius: '4px',
            padding: '8px 16px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            whiteSpace: 'nowrap'
          }}
        >
          Next Week
        </button>
      </div>

      {/* Day Tabs */}
      <div style={{
        display: 'flex',
        background: '#f3f4f6',
        borderBottom: '2px solid #d1d5db'
      }}>
        {weekDays.map((dateStr) => {
          const isSelected = dateStr === selectedDate;
          const today = isToday(dateStr);
          const daySummary = weekData.daily_summaries?.find(d => d.date === dateStr);
          const count = daySummary?.total_count || 0;

          return (
            <button
              key={dateStr}
              onClick={() => setSelectedDate(dateStr)}
              style={{
                flex: 1,
                padding: '12px 4px 10px',
                background: isSelected ? '#2d5016' : today ? '#e8f5e9' : 'transparent',
                color: isSelected ? 'white' : today ? '#2d5016' : '#374151',
                border: 'none',
                borderBottom: isSelected ? '3px solid #4caf50' : '3px solid transparent',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: isSelected ? '700' : '600',
                textAlign: 'center',
                transition: 'all 0.15s ease',
                position: 'relative'
              }}
            >
              <div>{getDayName(dateStr)}</div>
              {count > 0 && (
                <div style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  marginTop: '2px',
                  color: isSelected ? 'rgba(255,255,255,0.8)' : '#047857'
                }}>
                  ({count})
                </div>
              )}
            </button>
          );
        })}
      </div>

      {error && (
        <div style={{
          background: '#fef2f2',
          color: '#dc2626',
          padding: '10px 16px',
          fontSize: '14px',
          borderBottom: '1px solid #fecaca',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          {error}
          <button
            onClick={() => setError(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px', color: '#dc2626' }}
          >
            x
          </button>
        </div>
      )}

      {legacyResult && (
        <div style={{
          background: legacyResult.success ? '#f0fdf4' : '#fef2f2',
          color: legacyResult.success ? '#166534' : '#dc2626',
          padding: '10px 16px',
          fontSize: '14px',
          borderBottom: `1px solid ${legacyResult.success ? '#bbf7d0' : '#fecaca'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          {legacyResult.message}
          <button
            onClick={() => setLegacyResult(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px', color: legacyResult.success ? '#166534' : '#dc2626' }}
          >
            x
          </button>
        </div>
      )}

      {/* Day Content */}
      <div style={{ padding: '16px' }}>
        {/* Day Header with Sign Up button */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          flexWrap: 'wrap',
          gap: '8px'
        }}>
          <h2 style={{
            margin: 0,
            fontSize: '18px',
            fontWeight: '700',
            color: '#1f2937'
          }}>
            Signed up for {selectedDate ? formatDateFull(selectedDate) : '...'}
          </h2>

          {isAuthenticated && !userIsSignedUp && (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button
                onClick={handleSignupClick}
                style={{
                  background: confirmingSignup ? '#b45309' : '#2d5016',
                  color: 'white',
                  border: confirmingSignup ? '2px solid #92400e' : 'none',
                  borderRadius: '6px',
                  padding: '10px 24px',
                  fontSize: '15px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                {confirmingSignup ? 'Confirm Sign Up' : 'Sign Up'}
              </button>
              {confirmingSignup && (
                <button
                  onClick={() => setConfirmingSignup(false)}
                  style={{
                    background: '#6b7280',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '10px 16px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap'
                  }}
                >
                  Cancel
                </button>
              )}
            </div>
          )}
          {isAuthenticated && userIsSignedUp && userSignup && (
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                onClick={() => handleCancelSignup(userSignup.id)}
                style={{
                  background: '#dc2626',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '10px 24px',
                  fontSize: '15px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                Cancel My Signup
              </button>
              <button
                onClick={handleLegacyReplicate}
                disabled={legacyReplicating}
                style={{
                  background: legacyReplicating ? '#9ca3af' : '#1d4ed8',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '10px 16px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: legacyReplicating ? 'not-allowed' : 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                {legacyReplicating ? 'Replicating...' : 'Replicate to Legacy Signup Page'}
              </button>
            </div>
          )}
        </div>

        {/* Main content: Player List and Tee Times side by side */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)',
          gap: '20px',
          alignItems: 'start'
        }}
          className="signup-day-grid"
        >
          {/* Player List Table */}
          <div>
            {players.length > 0 ? (
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '14px'
              }}>
                <thead>
                  <tr style={{
                    background: '#f9fafb',
                    borderBottom: '2px solid #d1d5db'
                  }}>
                    <th style={{ padding: '10px 8px', textAlign: 'left', fontWeight: '700', color: '#374151', width: '40px' }}>#</th>
                    <th style={{ padding: '10px 8px', textAlign: 'left', fontWeight: '700', color: '#374151' }}>Name</th>
                    <th style={{ padding: '10px 8px', textAlign: 'left', fontWeight: '700', color: '#374151' }}>Notes</th>
                    {isAuthenticated && (
                      <th style={{ padding: '10px 8px', textAlign: 'center', fontWeight: '700', color: '#374151', width: '70px' }}></th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {players.map((player, index) => {
                    const isCurrentUser = user && player.player_name === (user.name || user.email);
                    return (
                      <tr
                        key={player.id || index}
                        style={{
                          borderBottom: '1px solid #e5e7eb',
                          background: isCurrentUser ? '#f0fdf4' : (index % 2 === 0 ? '#fff' : '#fafafa')
                        }}
                      >
                        <td style={{ padding: '10px 8px', color: '#6b7280', fontWeight: '600' }}>
                          {index + 1}
                        </td>
                        <td style={{ padding: '10px 8px', fontWeight: isCurrentUser ? '700' : '500', color: '#1f2937' }}>
                          {player.player_name}
                          {isCurrentUser && (
                            <span style={{ color: '#047857', fontSize: '12px', marginLeft: '6px' }}>(you)</span>
                          )}
                        </td>
                        <td style={{ padding: '10px 8px', color: '#6b7280', fontSize: '13px' }}>
                          {player.notes || player.preferred_start_time || ''}
                        </td>
                        {isAuthenticated && (
                          <td style={{ padding: '10px 8px', textAlign: 'center' }}>
                            {isCurrentUser && (
                              <button
                                onClick={() => handleCancelSignup(player.id)}
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  color: '#dc2626',
                                  cursor: 'pointer',
                                  fontSize: '13px',
                                  fontWeight: '600',
                                  textDecoration: 'underline'
                                }}
                              >
                                Cancel
                              </button>
                            )}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div style={{
                textAlign: 'center',
                padding: '40px 20px',
                color: '#9ca3af',
                background: '#f9fafb',
                borderRadius: '8px'
              }}>
                <div style={{ fontSize: '28px', marginBottom: '8px' }}>No one signed up yet</div>
                {isAuthenticated && (
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', alignItems: 'center' }}>
                    <button
                      onClick={handleSignupClick}
                      style={{
                        marginTop: '12px',
                        background: confirmingSignup ? '#b45309' : '#2d5016',
                        color: 'white',
                        border: confirmingSignup ? '2px solid #92400e' : 'none',
                        borderRadius: '6px',
                        padding: '12px 28px',
                        fontSize: '15px',
                        fontWeight: '700',
                        cursor: 'pointer'
                      }}
                    >
                      {confirmingSignup ? 'Confirm Sign Up' : 'Be the first to sign up!'}
                    </button>
                    {confirmingSignup && (
                      <button
                        onClick={() => setConfirmingSignup(false)}
                        style={{
                          marginTop: '12px',
                          background: '#6b7280',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '12px 16px',
                          fontSize: '14px',
                          fontWeight: '600',
                          cursor: 'pointer'
                        }}
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Player count */}
            {players.length > 0 && (
              <div style={{
                marginTop: '8px',
                fontSize: '13px',
                color: '#6b7280',
                fontWeight: '600'
              }}>
                {players.length} player{players.length !== 1 ? 's' : ''} signed up
              </div>
            )}
          </div>

          {/* Tee Times Panel */}
          <div style={{
            background: '#f9fafb',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            padding: '16px'
          }}>
            <h3 style={{
              margin: '0 0 12px 0',
              fontSize: '15px',
              fontWeight: '700',
              color: '#374151'
            }}>
              Tee Times
            </h3>

            {/* Generated pairings tee times */}
            {generatedPairings && generatedPairings.pairings?.teams && (
              <div style={{ marginBottom: '12px' }}>
                {generatedPairings.pairings.teams.map((team, idx) => (
                  <div key={idx} style={{
                    padding: '6px 0',
                    fontSize: '14px',
                    color: '#374151',
                    borderBottom: idx < generatedPairings.pairings.teams.length - 1 ? '1px solid #e5e7eb' : 'none'
                  }}>
                    <span style={{ fontWeight: '600' }}>Group {idx + 1}:</span>{' '}
                    {team.players?.map(p => p.player_name).join(', ')}
                  </div>
                ))}
              </div>
            )}

            {/* Editable tee times */}
            <textarea
              placeholder={"Enter tee times...\ne.g., 12:48 (1-4)\n12:56 (5-8)\n1:04 (9-12)"}
              value={teeTimesText}
              onChange={(e) => setTeeTimesText(e.target.value)}
              style={{
                width: '100%',
                minHeight: '120px',
                padding: '10px',
                fontSize: '14px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                resize: 'vertical',
                boxSizing: 'border-box',
                fontFamily: 'inherit'
              }}
            />
          </div>
        </div>

        {/* Messages Section */}
        {dayData?.messages && dayData.messages.length > 0 && (
          <div style={{
            marginTop: '20px',
            padding: '14px',
            background: '#fffbeb',
            border: '1px solid #fbbf24',
            borderRadius: '8px'
          }}>
            <h3 style={{
              margin: '0 0 10px 0',
              fontSize: '14px',
              fontWeight: '700',
              color: '#92400e'
            }}>
              Messages
            </h3>
            {dayData.messages.map((msg, idx) => (
              <div key={msg.id || idx} style={{
                padding: '8px 0',
                fontSize: '14px',
                color: '#78350f',
                borderBottom: idx < dayData.messages.length - 1 ? '1px solid #fde68a' : 'none'
              }}>
                <span style={{ fontWeight: '600' }}>{msg.player_name}:</span> {msg.message}
              </div>
            ))}
          </div>
        )}

        {/* Official Pairings Section */}
        {generatedPairings && generatedPairings.pairings && (
          <div style={{
            marginTop: '20px',
            background: '#f0fdf4',
            border: '2px solid #22c55e',
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <div style={{
              background: '#22c55e',
              color: 'white',
              padding: '12px 16px',
              fontWeight: '700',
              fontSize: '16px',
              textAlign: 'center'
            }}>
              Official Pairings
            </div>
            <div style={{ padding: '16px' }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px'
              }}>
                {generatedPairings.pairings.teams?.map((team, idx) => (
                  <div key={idx} style={{
                    background: 'white',
                    borderRadius: '6px',
                    padding: '12px',
                    border: '1px solid #bbf7d0'
                  }}>
                    <div style={{
                      fontWeight: '700',
                      color: '#166534',
                      fontSize: '14px',
                      marginBottom: '8px'
                    }}>
                      Group {idx + 1}
                    </div>
                    {team.players?.map((p, pidx) => (
                      <div key={pidx} style={{
                        padding: '4px 0',
                        fontSize: '14px',
                        color: '#374151'
                      }}>
                        {p.player_name}
                        {p.handicap && (
                          <span style={{ color: '#6b7280', fontSize: '12px', marginLeft: '6px' }}>
                            ({p.handicap} HCP)
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              {generatedPairings.pairings.remaining_players?.length > 0 && (
                <div style={{
                  marginTop: '12px',
                  padding: '10px',
                  background: '#fef3c7',
                  borderRadius: '6px',
                  fontSize: '13px',
                  color: '#92400e'
                }}>
                  <span style={{ fontWeight: '600' }}>Alternates:</span>{' '}
                  {generatedPairings.pairings.remaining_players.map(p => p.player_name).join(', ')}
                </div>
              )}

              <div style={{
                marginTop: '10px',
                fontSize: '12px',
                color: '#6b7280',
                textAlign: 'center'
              }}>
                Generated {new Date(generatedPairings.generated_at).toLocaleString()}
                {generatedPairings.notification_sent && ' | Email notifications sent'}
              </div>
            </div>
          </div>
        )}

        {pairingsLoading && (
          <div style={{ marginTop: '16px', textAlign: 'center', color: '#6b7280', fontSize: '14px' }}>
            Loading pairings...
          </div>
        )}

        {/* Not authenticated prompt */}
        {!isAuthenticated && (
          <div style={{
            marginTop: '20px',
            padding: '16px',
            background: '#fef2f2',
            borderRadius: '8px',
            textAlign: 'center',
            color: '#991b1b',
            fontSize: '14px'
          }}>
            Please log in to sign up for golf.
          </div>
        )}
      </div>

      {/* Responsive style for mobile: stack grid vertically */}
      <style>{`
        @media (max-width: 640px) {
          .signup-day-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
};

export default DailySignupView;
