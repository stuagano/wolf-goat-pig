import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import '../../styles/mobile-touch.css';

const API_URL = process.env.REACT_APP_API_URL || "";

const SignupCalendar = ({ onSignupChange, onDateSelect }) => {
  const { user, isAuthenticated } = useAuth0();
  const [weekData, setWeekData] = useState({ daily_summaries: [] });
  const [currentWeekStart, setCurrentWeekStart] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);
  const [messageInput, setMessageInput] = useState('');

  // Get current Sunday as default week start (to match day headers)
  const getCurrentSunday = () => {
    const today = new Date();
    const sunday = new Date(today);
    sunday.setDate(today.getDate() - today.getDay());
    return sunday.toISOString().split('T')[0];
  };

  // Format date for display
  const formatDateShort = (dateStr) => {
    const date = new Date(dateStr + 'T12:00:00');
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatDateFull = (dateStr) => {
    const date = new Date(dateStr + 'T12:00:00');
    return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  };

  const getDayName = (dateStr) => {
    const date = new Date(dateStr + 'T12:00:00');
    return date.toLocaleDateString('en-US', { weekday: 'short' });
  };

  // Check if date is today
  const isToday = (dateStr) => {
    const today = new Date().toISOString().split('T')[0];
    return dateStr === today;
  };

  // Load weekly signup data
  const loadWeeklyData = async (weekStart) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/signups/weekly-with-messages?week_start=${weekStart}`);

      if (!response.ok) {
        throw new Error(`Failed to load data: ${response.status}`);
      }

      const data = await response.json();
      setWeekData(data);
      setError(null);
    } catch (err) {
      console.error('Error loading weekly data:', err);
      setError(err.message);
      setWeekData({ daily_summaries: [] });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const sunday = getCurrentSunday();
    setCurrentWeekStart(sunday);
    loadWeeklyData(sunday);
  }, []);

  const navigateWeek = (direction) => {
    const currentDate = new Date(currentWeekStart);
    currentDate.setDate(currentDate.getDate() + (direction * 7));
    const newWeekStart = currentDate.toISOString().split('T')[0];
    setCurrentWeekStart(newWeekStart);
    setSelectedDay(null);
    loadWeeklyData(newWeekStart);
  };

  const handleSignup = async (date) => {
    if (!isAuthenticated || !user) {
      setError('Please log in to sign up');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/signups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date,
          player_profile_id: 1,
          player_name: user.name || user.email,
          preferred_start_time: null,
          notes: null
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to sign up');
      }

      loadWeeklyData(currentWeekStart);
      onSignupChange?.();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCancelSignup = async (signupId) => {
    try {
      const response = await fetch(`${API_URL}/signups/${signupId}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Failed to cancel signup');
      loadWeeklyData(currentWeekStart);
      onSignupChange?.();
    } catch (err) {
      setError(err.message);
    }
  };

  const handlePostMessage = async (date) => {
    if (!messageInput.trim()) return;

    try {
      const response = await fetch(`${API_URL}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date,
          message: messageInput.trim(),
          player_profile_id: 1,
          player_name: user.name || user.email
        })
      });

      if (!response.ok) throw new Error('Failed to post message');
      setMessageInput('');
      loadWeeklyData(currentWeekStart);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    try {
      await fetch(`${API_URL}/messages/${messageId}`, { method: 'DELETE' });
      loadWeeklyData(currentWeekStart);
    } catch (err) {
      setError(err.message);
    }
  };

  const getUserSignup = (dailySummary) => {
    if (!user) return null;
    return dailySummary.signups?.find(s =>
      s.player_name === (user.name || user.email) && s.status === 'signed_up'
    );
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#6b7280' }}>
        Loading...
      </div>
    );
  }

  const selectedDayData = selectedDay !== null ? weekData.daily_summaries[selectedDay] : null;

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '16px' }}>
      {/* Week Navigation */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        padding: '8px 0'
      }}>
        <button
          onClick={() => navigateWeek(-1)}
          style={{
            width: '44px',
            height: '44px',
            background: '#047857',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '18px',
            cursor: 'pointer'
          }}
        >
          ‹
        </button>
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: '600', color: '#1f2937' }}>
          Week of {formatDateShort(currentWeekStart)}
        </h2>
        <button
          onClick={() => navigateWeek(1)}
          style={{
            width: '44px',
            height: '44px',
            background: '#047857',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '18px',
            cursor: 'pointer'
          }}
        >
          ›
        </button>
      </div>

      {error && (
        <div style={{
          background: '#fef2f2',
          color: '#dc2626',
          padding: '12px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '14px'
        }}>
          {error}
          <button
            onClick={() => setError(null)}
            style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            ×
          </button>
        </div>
      )}

      {/* Week Grid - Clean 7-column layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(7, 1fr)',
        gap: '8px',
        marginBottom: '24px'
      }}>
        {weekData.daily_summaries.map((day, index) => {
          const userSignup = getUserSignup(day);
          const today = isToday(day.date);
          const isSelected = selectedDay === index;

          return (
            <button
              key={day.date || index}
              onClick={() => setSelectedDay(isSelected ? null : index)}
              style={{
                padding: '12px 4px',
                border: isSelected ? '2px solid #047857' : today ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                borderRadius: '10px',
                background: userSignup ? '#ecfdf5' : isSelected ? '#f0fdf4' : '#fff',
                cursor: 'pointer',
                textAlign: 'center',
                transition: 'all 0.15s ease'
              }}
            >
              <div style={{ fontSize: '11px', color: '#6b7280', fontWeight: '500', marginBottom: '4px' }}>
                {getDayName(day.date)}
              </div>
              <div style={{
                fontSize: '18px',
                fontWeight: '600',
                color: today ? '#3b82f6' : '#1f2937',
                marginBottom: '6px'
              }}>
                {new Date(day.date + 'T12:00:00').getDate()}
              </div>
              {day.total_count > 0 && (
                <div style={{
                  background: '#047857',
                  color: 'white',
                  fontSize: '11px',
                  fontWeight: '600',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  display: 'inline-block'
                }}>
                  {day.total_count} ⛳
                </div>
              )}
              {userSignup && (
                <div style={{ fontSize: '10px', color: '#047857', marginTop: '4px' }}>
                  ✓ You
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Selected Day Detail Panel */}
      {selectedDayData && (
        <div style={{
          background: '#fff',
          border: '1px solid #e5e7eb',
          borderRadius: '12px',
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            background: '#f9fafb',
            padding: '16px',
            borderBottom: '1px solid #e5e7eb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>
              {formatDateFull(selectedDayData.date)}
            </h3>
            <button
              onClick={() => setSelectedDay(null)}
              style={{
                background: 'none',
                border: 'none',
                fontSize: '20px',
                cursor: 'pointer',
                color: '#6b7280',
                padding: '4px 8px'
              }}
            >
              ×
            </button>
          </div>

          {/* Golfers Section */}
          <div style={{ padding: '16px', borderBottom: '1px solid #e5e7eb' }}>
            <div style={{
              fontSize: '13px',
              fontWeight: '600',
              color: '#6b7280',
              marginBottom: '12px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              ⛳ Golfers ({selectedDayData.total_count})
            </div>

            {selectedDayData.signups?.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
                {selectedDayData.signups.map(signup => (
                  <span
                    key={signup.id}
                    style={{
                      background: signup.player_name === (user?.name || user?.email) ? '#dcfce7' : '#f3f4f6',
                      padding: '6px 12px',
                      borderRadius: '16px',
                      fontSize: '14px',
                      fontWeight: '500'
                    }}
                  >
                    {signup.player_name.split(' ')[0]}
                    {signup.preferred_start_time && (
                      <span style={{ color: '#6b7280', marginLeft: '4px' }}>
                        @ {signup.preferred_start_time}
                      </span>
                    )}
                  </span>
                ))}
              </div>
            ) : (
              <p style={{ color: '#9ca3af', fontStyle: 'italic', margin: '0 0 12px' }}>
                No one signed up yet
              </p>
            )}

            {/* Signup/Cancel Button */}
            {isAuthenticated && (
              getUserSignup(selectedDayData) ? (
                <button
                  onClick={() => handleCancelSignup(getUserSignup(selectedDayData).id)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: '#fee2e2',
                    color: '#dc2626',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '15px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Cancel My Signup
                </button>
              ) : (
                <button
                  onClick={() => handleSignup(selectedDayData.date)}
                  style={{
                    width: '100%',
                    padding: '12px',
                    background: '#047857',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '15px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  ⛳ Sign Up to Play
                </button>
              )
            )}
          </div>

          {/* Messages Section */}
          <div style={{ padding: '16px' }}>
            <div style={{
              fontSize: '13px',
              fontWeight: '600',
              color: '#6b7280',
              marginBottom: '12px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              💬 Messages ({selectedDayData.message_count || 0})
            </div>

            {selectedDayData.messages?.length > 0 ? (
              <div style={{ marginBottom: '16px' }}>
                {selectedDayData.messages.map(msg => (
                  <div
                    key={msg.id}
                    style={{
                      background: '#f9fafb',
                      padding: '12px',
                      borderRadius: '8px',
                      marginBottom: '8px'
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '4px'
                    }}>
                      <span style={{ fontWeight: '600', fontSize: '14px' }}>
                        {msg.player_name.split(' ')[0]}
                      </span>
                      {user && msg.player_name === (user.name || user.email) && (
                        <button
                          onClick={() => handleDeleteMessage(msg.id)}
                          style={{
                            background: '#fee2e2',
                            border: 'none',
                            color: '#dc2626',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                    <p style={{ margin: 0, color: '#4b5563', fontSize: '14px', lineHeight: '1.4' }}>
                      {msg.message}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#9ca3af', fontStyle: 'italic', margin: '0 0 16px' }}>
                No messages yet
              </p>
            )}

            {/* Post Message */}
            {isAuthenticated && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  placeholder="Add a message..."
                  onKeyPress={(e) => e.key === 'Enter' && handlePostMessage(selectedDayData.date)}
                  style={{
                    flex: 1,
                    padding: '12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    fontSize: '15px'
                  }}
                />
                <button
                  onClick={() => handlePostMessage(selectedDayData.date)}
                  disabled={!messageInput.trim()}
                  style={{
                    padding: '12px 20px',
                    background: messageInput.trim() ? '#047857' : '#d1d5db',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '15px',
                    fontWeight: '600',
                    cursor: messageInput.trim() ? 'pointer' : 'not-allowed'
                  }}
                >
                  Send
                </button>
              </div>
            )}

            {!isAuthenticated && (
              <p style={{ color: '#6b7280', textAlign: 'center', fontSize: '14px', margin: 0 }}>
                Log in to sign up or post messages
              </p>
            )}
          </div>
        </div>
      )}

      {/* No day selected prompt */}
      {!selectedDayData && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          color: '#9ca3af',
          background: '#f9fafb',
          borderRadius: '12px'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>⛳</div>
          <p style={{ margin: 0 }}>Tap a day to view details and sign up</p>
        </div>
      )}
    </div>
  );
};

export default SignupCalendar;
