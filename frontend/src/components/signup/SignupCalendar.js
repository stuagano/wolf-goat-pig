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
  // const [selectedDate, setSelectedDate] = useState(null); // Removed - not currently used
  const [messageInputs, setMessageInputs] = useState({}); // Store message text for each date

  // Get current Monday as default week start
  const getCurrentMonday = () => {
    const today = new Date();
    const monday = new Date(today);
    monday.setDate(today.getDate() - today.getDay() + 1);
    return monday.toISOString().split('T')[0];
  };

  // Format date for display
  const formatDateDisplay = (dateStr) => {
    const date = new Date(dateStr);
    const options = { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    };
    return date.toLocaleDateString('en-US', options);
  };

  // Day names for header
  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  // Load weekly signup data with messages
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
      // Set empty data structure on error
      setWeekData({ daily_summaries: Array(7).fill(null).map((_, i) => ({
        date: '',
        signups: [],
        total_count: 0,
        messages: [],
        message_count: 0
      }))});
    } finally {
      setLoading(false);
    }
  };

  // Initialize with current week
  useEffect(() => {
    const monday = getCurrentMonday();
    setCurrentWeekStart(monday);
    loadWeeklyData(monday);
  }, []);

  // Navigate to previous/next week
  const navigateWeek = (direction) => {
    const currentDate = new Date(currentWeekStart);
    const newDate = new Date(currentDate);
    newDate.setDate(currentDate.getDate() + (direction * 7));
    const newWeekStart = newDate.toISOString().split('T')[0];
    
    setCurrentWeekStart(newWeekStart);
    loadWeeklyData(newWeekStart);
  };

  // Handle signing up for a day
  const handleSignup = async (date) => {
    if (!isAuthenticated || !user) {
      setError('Please log in to sign up');
      return;
    }

    try {
      // For now, we'll use the user's email as the player name
      // In a real app, you'd have a player profile lookup
      const playerName = user.name || user.email;
      
      const signupData = {
        date: date,
        player_profile_id: 1, // This would come from authenticated user
        player_name: playerName,
        preferred_start_time: null,
        notes: null
      };

      const response = await fetch(`${API_URL}/signups`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(signupData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to sign up');
      }

      // Reload the week data to show the new signup
      loadWeeklyData(currentWeekStart);
      
      if (onSignupChange) {
        onSignupChange();
      }
    } catch (err) {
      console.error('Signup error:', err);
      setError(err.message);
    }
  };

  // Handle cancelling a signup
  const handleCancelSignup = async (signupId) => {
    try {
      const response = await fetch(`${API_URL}/signups/${signupId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to cancel signup');
      }

      // Reload the week data
      loadWeeklyData(currentWeekStart);
      
      if (onSignupChange) {
        onSignupChange();
      }
    } catch (err) {
      console.error('Cancel error:', err);
      setError(err.message);
    }
  };

  // Check if current user is signed up for a date
  const isUserSignedUp = (dailySummary) => {
    if (!user) return null;
    
    const userEmail = user.email;
    return dailySummary.signups.find(signup => 
      signup.player_name === (user.name || userEmail) && 
      signup.status === 'signed_up'
    );
  };

  // Handle posting a new message
  const handlePostMessage = async (date, message) => {
    if (!isAuthenticated || !user) {
      setError('Please log in to post messages');
      return;
    }

    if (!message.trim()) {
      setError('Message cannot be empty');
      return;
    }

    try {
      const playerName = user.name || user.email;
      
      const messageData = {
        date: date,
        message: message.trim(),
        player_profile_id: 1, // This would come from authenticated user
        player_name: playerName
      };

      const response = await fetch(`${API_URL}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(messageData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to post message');
      }

      // Reload the week data to show the new message
      loadWeeklyData(currentWeekStart);
      
    } catch (err) {
      console.error('Message post error:', err);
      setError(err.message);
    }
  };

  // Handle deleting a message (only own messages)
  const handleDeleteMessage = async (messageId) => {
    if (!isAuthenticated || !user) {
      setError('Please log in to delete messages');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/messages/${messageId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error('Failed to delete message');
      }

      // Reload the week data
      loadWeeklyData(currentWeekStart);
      
    } catch (err) {
      console.error('Delete message error:', err);
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '300px',
        fontSize: '18px' 
      }}>
        Loading calendar...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {/* Header with navigation - mobile-optimized */}
      <div className="week-navigation" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        gap: '12px'
      }}>
        <button
          onClick={() => navigateWeek(-1)}
          className="week-nav-button"
          style={{
            minWidth: '48px',
            minHeight: '48px',
            padding: '12px 16px',
            background: '#047857',
            color: 'white',
            border: 'none',
            borderRadius: '10px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: '600',
            touchAction: 'manipulation',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          ←
        </button>

        <h3 className="week-nav-title" style={{
          margin: 0,
          color: '#1f2937',
          fontSize: '16px',
          fontWeight: '600',
          textAlign: 'center',
          flex: 1
        }}>
          Week of {formatDateDisplay(currentWeekStart)}
        </h3>

        <button
          onClick={() => navigateWeek(1)}
          className="week-nav-button"
          style={{
            minWidth: '48px',
            minHeight: '48px',
            padding: '12px 16px',
            background: '#047857',
            color: 'white',
            border: 'none',
            borderRadius: '10px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: '600',
            touchAction: 'manipulation',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          →
        </button>
      </div>

      {error && (
        <div style={{ 
          backgroundColor: '#f8d7da', 
          color: '#721c24', 
          padding: '12px', 
          borderRadius: '4px', 
          marginBottom: '20px',
          border: '1px solid #f5c6cb'
        }}>
          {error}
        </div>
      )}

      {/* Calendar Grid - responsive: 7 cols on desktop, 2 on tablet, 1 on mobile */}
      <div
        className="responsive-grid-7"
        style={{
          marginBottom: '20px'
        }}
      >
        {/* Day headers - hidden on mobile since each card shows the full date */}
        {dayNames.map(day => (
          <div key={day} className="day-header" style={{
            textAlign: 'center',
            fontWeight: '600',
            padding: '12px',
            backgroundColor: '#f3f4f6',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            fontSize: '14px',
            color: '#374151'
          }}>
            {day}
          </div>
        ))}

        {/* Day cards with message boards - mobile-optimized */}
        {weekData.daily_summaries.map((dailySummary, index) => {
          const userSignup = isUserSignedUp(dailySummary);
          const canSignUp = isAuthenticated && !userSignup;
          const currentMessageText = messageInputs[dailySummary.date] || '';

          return (
            <div
              key={index}
              className={`mobile-day-card ${userSignup ? 'signed-up' : ''}`}
              style={{
                border: userSignup ? '2px solid #047857' : '2px solid #e5e7eb',
                borderRadius: '12px',
                padding: '16px',
                backgroundColor: userSignup ? '#ecfdf5' : '#ffffff',
                minHeight: '280px',
                display: 'flex',
                flexDirection: 'column'
              }}
            >
              {/* Date - Clickable with larger touch target */}
              <div
                onClick={() => onDateSelect && onDateSelect(dailySummary.date)}
                style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  marginBottom: '12px',
                  color: onDateSelect ? '#047857' : '#1f2937',
                  textAlign: 'center',
                  borderBottom: '1px solid #e5e7eb',
                  paddingBottom: '12px',
                  cursor: onDateSelect ? 'pointer' : 'default',
                  minHeight: '44px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  touchAction: 'manipulation'
                }}
                title={onDateSelect ? 'Tap to view detailed signup for this day' : ''}
              >
                {formatDateDisplay(dailySummary.date)}
              </div>

              {/* Signups Section */}
              <div style={{ marginBottom: '16px' }}>
                <div className="mobile-section-label" style={{
                  fontSize: '13px',
                  color: '#6b7280',
                  marginBottom: '8px',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  ⛳ Golf ({dailySummary.total_count})
                </div>
                <div style={{ fontSize: '14px', maxHeight: '80px', overflowY: 'auto' }}>
                  {dailySummary.signups.slice(0, 3).map(signup => (
                    <div key={signup.id} style={{
                      color: '#374151',
                      marginBottom: '4px',
                      padding: '4px 0'
                    }}>
                      • {signup.player_name.split(' ')[0]}
                      {signup.preferred_start_time && (
                        <span style={{ color: '#6b7280' }}>
                          {' '}({signup.preferred_start_time})
                        </span>
                      )}
                    </div>
                  ))}
                  {dailySummary.signups.length > 3 && (
                    <div style={{ color: '#6b7280', fontSize: '13px', fontStyle: 'italic' }}>
                      +{dailySummary.signups.length - 3} more
                    </div>
                  )}
                </div>
              </div>

              {/* Messages Section */}
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <div className="mobile-section-label" style={{
                  fontSize: '13px',
                  color: '#6b7280',
                  marginBottom: '8px',
                  fontWeight: '600',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  💬 Messages ({dailySummary.message_count})
                </div>

                {/* Messages list */}
                <div style={{
                  flex: 1,
                  overflowY: 'auto',
                  maxHeight: '120px',
                  marginBottom: '12px',
                  fontSize: '14px'
                }}>
                  {dailySummary.messages && dailySummary.messages.length > 0 ? (
                    dailySummary.messages.map(message => (
                      <div key={message.id} style={{
                        backgroundColor: '#f9fafb',
                        padding: '10px',
                        marginBottom: '6px',
                        borderRadius: '8px',
                        border: '1px solid #e5e7eb'
                      }}>
                        <div style={{
                          fontWeight: '600',
                          color: '#374151',
                          marginBottom: '4px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '14px'
                        }}>
                          <span>{message.player_name.split(' ')[0]}</span>
                          {user && message.player_name === (user.name || user.email) && (
                            <button
                              onClick={() => handleDeleteMessage(message.id)}
                              style={{
                                background: '#fee2e2',
                                border: 'none',
                                color: '#dc2626',
                                cursor: 'pointer',
                                fontSize: '16px',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                minWidth: '32px',
                                minHeight: '32px',
                                touchAction: 'manipulation'
                              }}
                              title="Delete message"
                            >
                              ×
                            </button>
                          )}
                        </div>
                        <div style={{ color: '#6b7280', fontSize: '14px', lineHeight: '1.4' }}>
                          {message.message}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{
                      color: '#9ca3af',
                      fontStyle: 'italic',
                      textAlign: 'center',
                      padding: '16px',
                      fontSize: '14px'
                    }}>
                      No messages yet
                    </div>
                  )}
                </div>

                {/* Message input - mobile optimized */}
                {isAuthenticated ? (
                  <div style={{ marginBottom: '12px' }}>
                    <textarea
                      value={currentMessageText}
                      onChange={(e) => setMessageInputs(prev => ({
                        ...prev,
                        [dailySummary.date]: e.target.value
                      }))}
                      placeholder="Post a message..."
                      className="mobile-form-control"
                      style={{
                        width: '100%',
                        minHeight: '48px',
                        padding: '12px',
                        fontSize: '16px',
                        border: '2px solid #e5e7eb',
                        borderRadius: '8px',
                        resize: 'none',
                        boxSizing: 'border-box'
                      }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          if (currentMessageText.trim()) {
                            handlePostMessage(dailySummary.date, currentMessageText);
                            setMessageInputs(prev => ({
                              ...prev,
                              [dailySummary.date]: ''
                            }));
                          }
                        }
                      }}
                    />
                    <button
                      onClick={() => {
                        if (currentMessageText.trim()) {
                          handlePostMessage(dailySummary.date, currentMessageText);
                          setMessageInputs(prev => ({
                            ...prev,
                            [dailySummary.date]: ''
                          }));
                        }
                      }}
                      className="mobile-button mobile-button-primary mobile-button-full"
                      style={{
                        marginTop: '8px',
                        width: '100%',
                        minHeight: '44px',
                        padding: '12px',
                        background: currentMessageText.trim() ? '#047857' : '#9ca3af',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '15px',
                        fontWeight: '600',
                        cursor: currentMessageText.trim() ? 'pointer' : 'not-allowed',
                        touchAction: 'manipulation'
                      }}
                      disabled={!currentMessageText.trim()}
                    >
                      Post Message
                    </button>
                  </div>
                ) : null}
              </div>

              {/* Signup Action button - mobile optimized */}
              <div>
                {userSignup ? (
                  <button
                    onClick={() => handleCancelSignup(userSignup.id)}
                    className="mobile-button mobile-button-danger mobile-button-full"
                    style={{
                      width: '100%',
                      minHeight: '48px',
                      padding: '14px',
                      background: '#dc2626',
                      color: 'white',
                      border: 'none',
                      borderRadius: '10px',
                      fontSize: '15px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      touchAction: 'manipulation'
                    }}
                  >
                    Cancel Golf Signup
                  </button>
                ) : canSignUp ? (
                  <button
                    onClick={() => handleSignup(dailySummary.date)}
                    className="mobile-button mobile-button-primary mobile-button-full"
                    style={{
                      width: '100%',
                      minHeight: '48px',
                      padding: '14px',
                      background: '#047857',
                      color: 'white',
                      border: 'none',
                      borderRadius: '10px',
                      fontSize: '15px',
                      fontWeight: '600',
                      cursor: 'pointer',
                      touchAction: 'manipulation'
                    }}
                  >
                    ⛳ Sign Up for Golf
                  </button>
                ) : !isAuthenticated ? (
                  <div style={{
                    textAlign: 'center',
                    fontSize: '14px',
                    color: '#6b7280',
                    fontStyle: 'italic',
                    padding: '12px'
                  }}>
                    Login to sign up or post messages
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        gap: '20px', 
        fontSize: '12px',
        color: '#6c757d'
      }}>
        <div>
          <span style={{ 
            display: 'inline-block', 
            width: '12px', 
            height: '12px', 
            backgroundColor: '#d4edda', 
            marginRight: '5px',
            border: '1px solid #c3e6cb'
          }}></span>
          You're signed up
        </div>
        <div>
          <span style={{ 
            display: 'inline-block', 
            width: '12px', 
            height: '12px', 
            backgroundColor: '#ffffff', 
            marginRight: '5px',
            border: '1px solid #dee2e6'
          }}></span>
          Available to sign up
        </div>
      </div>
    </div>
  );
};

export default SignupCalendar;