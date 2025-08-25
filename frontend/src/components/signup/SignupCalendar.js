import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || "";

const SignupCalendar = ({ onSignupChange }) => {
  const { user, isAuthenticated } = useAuth0();
  const [weekData, setWeekData] = useState({ daily_summaries: [] });
  const [currentWeekStart, setCurrentWeekStart] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);

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

  // Load weekly signup data
  const loadWeeklyData = async (weekStart) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/signups/weekly?week_start=${weekStart}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load signups: ${response.status}`);
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
        total_count: 0
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

        {/* Day cards */}
        {weekData.daily_summaries.map((dailySummary, index) => {
          const userSignup = isUserSignedUp(dailySummary);
          const canSignUp = isAuthenticated && !userSignup;
          
          return (
            <div key={index} style={{
              border: '1px solid #dee2e6',
              borderRadius: '8px',
              padding: '10px',
              backgroundColor: userSignup ? '#d4edda' : '#ffffff',
              minHeight: '120px',
              position: 'relative'
            }}>
              {/* Date */}
              <div style={{ 
                fontSize: '14px', 
                fontWeight: 'bold', 
                marginBottom: '8px',
                color: '#495057'
              }}>
                {formatDateDisplay(dailySummary.date)}
              </div>

              {/* Signup count */}
              <div style={{ 
                fontSize: '12px', 
                color: '#6c757d', 
                marginBottom: '8px' 
              }}>
                {dailySummary.total_count} signed up
              </div>

              {/* Signups list (first few names) */}
              <div style={{ fontSize: '11px', marginBottom: '10px' }}>
                {dailySummary.signups.slice(0, 3).map(signup => (
                  <div key={signup.id} style={{ 
                    color: '#495057',
                    marginBottom: '2px',
                    truncate: true
                  }}>
                    • {signup.player_name.split(' ')[0]} {/* First name only */}
                    {signup.preferred_start_time && (
                      <span style={{ color: '#6c757d' }}>
                        {' '}({signup.preferred_start_time})
                      </span>
                    )}
                  </div>
                ))}
                {dailySummary.signups.length > 3 && (
                  <div style={{ color: '#6c757d', fontSize: '10px' }}>
                    +{dailySummary.signups.length - 3} more
                  </div>
                )}
              </div>

              {/* Action button */}
              <div style={{ 
                position: 'absolute', 
                bottom: '8px', 
                left: '8px', 
                right: '8px' 
              }}>
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
                    Cancel Signup
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
                    Sign Up
                  </button>
                ) : !isAuthenticated ? (
                  <div style={{
                    textAlign: 'center',
                    fontSize: '10px',
                    color: '#6c757d',
                    fontStyle: 'italic'
                  }}>
                    Login to sign up
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