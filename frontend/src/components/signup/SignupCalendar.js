import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || "";

const SignupCalendar = ({ onSignupChange, onDateSelect }) => {
  const { user, isAuthenticated } = useAuth0();
  const [weekData, setWeekData] = useState({ daily_summaries: [] });
  const [currentWeekStart, setCurrentWeekStart] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
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
      {/* Header with navigation */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '20px' 
      }}>
        <button 
          onClick={() => navigateWeek(-1)}
          style={{
            padding: '8px 16px',
            background: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          ← Previous Week
        </button>
        
        <h3 style={{ margin: 0, color: '#333' }}>
          Week of {formatDateDisplay(currentWeekStart)}
        </h3>
        
        <button 
          onClick={() => navigateWeek(1)}
          style={{
            padding: '8px 16px',
            background: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Next Week →
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

      {/* Calendar Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(7, 1fr)',
        gap: '10px',
        marginBottom: '20px'
      }}>
        {/* Day headers */}
        {dayNames.map(day => (
          <div key={day} style={{
            textAlign: 'center',
            fontWeight: 'bold',
            padding: '10px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '4px'
          }}>
            {day}
          </div>
        ))}

        {/* Day cards with message boards */}
        {weekData.daily_summaries.map((dailySummary, index) => {
          const userSignup = isUserSignedUp(dailySummary);
          const canSignUp = isAuthenticated && !userSignup;
          const currentMessageText = messageInputs[dailySummary.date] || '';
          
          return (
            <div key={index} style={{
              border: '1px solid #dee2e6',
              borderRadius: '8px',
              padding: '10px',
              backgroundColor: userSignup ? '#d4edda' : '#ffffff',
              minHeight: '300px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              {/* Date - Clickable */}
              <div 
                onClick={() => onDateSelect && onDateSelect(dailySummary.date)}
                style={{ 
                  fontSize: '14px', 
                  fontWeight: 'bold', 
                  marginBottom: '8px',
                  color: onDateSelect ? '#007bff' : '#495057',
                  textAlign: 'center',
                  borderBottom: '1px solid #dee2e6',
                  paddingBottom: '8px',
                  cursor: onDateSelect ? 'pointer' : 'default',
                  textDecoration: onDateSelect ? 'underline' : 'none'
                }}
                title={onDateSelect ? 'Click to view detailed signup for this day' : ''}
              >
                {formatDateDisplay(dailySummary.date)}
              </div>

              {/* Signups Section */}
              <div style={{ marginBottom: '12px' }}>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#6c757d', 
                  marginBottom: '4px',
                  fontWeight: 'bold'
                }}>
                  ⛳ Golf ({dailySummary.total_count})
                </div>
                <div style={{ fontSize: '10px', maxHeight: '60px', overflowY: 'auto' }}>
                  {dailySummary.signups.slice(0, 2).map(signup => (
                    <div key={signup.id} style={{ 
                      color: '#495057',
                      marginBottom: '1px'
                    }}>
                      • {signup.player_name.split(' ')[0]}
                      {signup.preferred_start_time && (
                        <span style={{ color: '#6c757d' }}>
                          {' '}({signup.preferred_start_time})
                        </span>
                      )}
                    </div>
                  ))}
                  {dailySummary.signups.length > 2 && (
                    <div style={{ color: '#6c757d', fontSize: '9px' }}>
                      +{dailySummary.signups.length - 2} more
                    </div>
                  )}
                </div>
              </div>

              {/* Messages Section */}
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#6c757d', 
                  marginBottom: '4px',
                  fontWeight: 'bold'
                }}>
                  💬 Messages ({dailySummary.message_count})
                </div>
                
                {/* Messages list */}
                <div style={{ 
                  flex: 1, 
                  overflowY: 'auto', 
                  maxHeight: '120px',
                  marginBottom: '8px',
                  fontSize: '10px'
                }}>
                  {dailySummary.messages && dailySummary.messages.length > 0 ? (
                    dailySummary.messages.map(message => (
                      <div key={message.id} style={{
                        backgroundColor: '#f8f9fa',
                        padding: '6px',
                        marginBottom: '4px',
                        borderRadius: '4px',
                        border: '1px solid #e9ecef'
                      }}>
                        <div style={{ 
                          fontWeight: 'bold',
                          color: '#495057',
                          marginBottom: '2px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}>
                          <span>{message.player_name.split(' ')[0]}</span>
                          {user && message.player_name === (user.name || user.email) && (
                            <button
                              onClick={() => handleDeleteMessage(message.id)}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#dc3545',
                                cursor: 'pointer',
                                fontSize: '10px',
                                padding: '0'
                              }}
                              title="Delete message"
                            >
                              ×
                            </button>
                          )}
                        </div>
                        <div style={{ color: '#6c757d' }}>
                          {message.message}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ 
                      color: '#6c757d', 
                      fontStyle: 'italic',
                      textAlign: 'center',
                      padding: '10px'
                    }}>
                      No messages yet
                    </div>
                  )}
                </div>

                {/* Message input */}
                {isAuthenticated ? (
                  <div style={{ marginBottom: '8px' }}>
                    <textarea
                      value={currentMessageText}
                      onChange={(e) => setMessageInputs(prev => ({
                        ...prev,
                        [dailySummary.date]: e.target.value
                      }))}
                      placeholder="Post a message..."
                      style={{
                        width: '100%',
                        minHeight: '40px',
                        padding: '4px',
                        fontSize: '10px',
                        border: '1px solid #dee2e6',
                        borderRadius: '4px',
                        resize: 'none'
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
                      style={{
                        marginTop: '2px',
                        width: '100%',
                        padding: '4px',
                        background: '#007bff',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        fontSize: '10px',
                        cursor: 'pointer'
                      }}
                      disabled={!currentMessageText.trim()}
                    >
                      Post Message
                    </button>
                  </div>
                ) : null}
              </div>

              {/* Signup Action button */}
              <div>
                {userSignup ? (
                  <button
                    onClick={() => handleCancelSignup(userSignup.id)}
                    style={{
                      width: '100%',
                      padding: '6px',
                      background: '#dc3545',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '11px',
                      cursor: 'pointer'
                    }}
                  >
                    Cancel Golf Signup
                  </button>
                ) : canSignUp ? (
                  <button
                    onClick={() => handleSignup(dailySummary.date)}
                    style={{
                      width: '100%',
                      padding: '6px',
                      background: '#28a745',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '11px',
                      cursor: 'pointer'
                    }}
                  >
                    Sign Up for Golf
                  </button>
                ) : !isAuthenticated ? (
                  <div style={{
                    textAlign: 'center',
                    fontSize: '10px',
                    color: '#6c757d',
                    fontStyle: 'italic'
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