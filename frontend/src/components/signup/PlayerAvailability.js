import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import '../../styles/mobile-touch.css';

const API_URL = process.env.REACT_APP_API_URL || "";

const PlayerAvailability = () => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();
  const [availability, setAvailability] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const dayNames = useMemo(() => (
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  ), []);

  // Time options for dropdowns
  const timeOptions = [
    '', '6:00 AM', '6:30 AM', '7:00 AM', '7:30 AM', '8:00 AM', '8:30 AM',
    '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM',
    '12:00 PM', '12:30 PM', '1:00 PM', '1:30 PM', '2:00 PM', '2:30 PM',
    '3:00 PM', '3:30 PM', '4:00 PM', '4:30 PM', '5:00 PM', '5:30 PM',
    '6:00 PM', '6:30 PM', '7:00 PM', '7:30 PM', '8:00 PM'
  ];

  // Initialize empty availability structure
  const initializeAvailability = useCallback(() => {
    return dayNames.map((_, index) => ({
      day_of_week: index,
      is_available: false,
      available_from_time: '',
      available_to_time: '',
      notes: ''
    }));
  }, [dayNames]);

  // Load player's availability
  const loadAvailability = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      // Get token from Auth0
      let token;
      try {
        token = await getAccessTokenSilently();
      } catch (e) {
        // Fallback to localStorage if Auth0 token fails
        token = localStorage.getItem('auth_token');
      }
      
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${API_URL}/players/me/availability`, {
        headers
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Create a complete array with all days
        const completeAvailability = initializeAvailability();
        
        // Merge in the saved availability
        data.forEach(item => {
          if (item.day_of_week >= 0 && item.day_of_week <= 6) {
            completeAvailability[item.day_of_week] = {
              id: item.id,
              day_of_week: item.day_of_week,
              is_available: item.is_available,
              available_from_time: item.available_from_time || '',
              available_to_time: item.available_to_time || '',
              notes: item.notes || ''
            };
          }
        });
        
        setAvailability(completeAvailability);
      } else {
        // If no availability exists yet, start with empty structure
        setAvailability(initializeAvailability());
      }
      
      setError(null);
    } catch (err) {
      console.error('Error loading availability:', err);
      setError(err.message);
      setAvailability(initializeAvailability());
    } finally {
      setLoading(false);
    }
  }, [getAccessTokenSilently, initializeAvailability, isAuthenticated]);

  useEffect(() => {
    loadAvailability();
  }, [loadAvailability]); // Reload when dependencies change

  // Update a specific day's availability
  const updateDayAvailability = (dayIndex, field, value) => {
    setAvailability(prev => prev.map((day, index) => {
      if (index === dayIndex) {
        return { ...day, [field]: value };
      }
      return day;
    }));
  };

  // Save availability for a specific day
  const saveDayAvailability = async (dayIndex) => {
    const dayData = availability[dayIndex];
    
    try {
      setSaving(true);
      
      const payload = {
        player_profile_id: 0, // Will be overridden by backend with actual user ID
        day_of_week: dayData.day_of_week,
        is_available: dayData.is_available,
        available_from_time: dayData.available_from_time || null,
        available_to_time: dayData.available_to_time || null,
        notes: dayData.notes || null
      };

      // Get token from Auth0 or localStorage
      let token;
      try {
        token = await getAccessTokenSilently();
      } catch (e) {
        token = localStorage.getItem('auth_token');
      }
      
      const headers = {
        'Content-Type': 'application/json'
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${API_URL}/players/me/availability`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save availability');
      }

      const updatedDay = await response.json();
      
      // Update the local state with the saved data
      setAvailability(prev => prev.map((day, index) => {
        if (index === dayIndex) {
          return {
            ...day,
            id: updatedDay.id
          };
        }
        return day;
      }));
      
      setError(null);
    } catch (err) {
      console.error('Save error:', err);
      setError(`Failed to save ${dayNames[dayIndex]} availability: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '48px 20px',
        fontSize: '16px',
        color: '#6b7280'
      }}>
        Loading your availability settings...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', padding: '0 16px' }}>
      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          color: '#991b1b',
          padding: '16px',
          borderRadius: '12px',
          marginBottom: '20px',
          border: '1px solid #fecaca',
          fontSize: '15px'
        }}>
          {error}
        </div>
      )}

      <div style={{ marginBottom: '24px' }}>
        <p style={{ color: '#6b7280', fontSize: '16px', margin: 0, lineHeight: '1.5' }}>
          Set your typical availability for each day to help others know when you're usually free to play.
        </p>
      </div>

      {/* Availability Cards */}
      <div style={{
        display: 'grid',
        gap: '16px'
      }}>
        {availability.map((day, index) => (
          <div
            key={index}
            className="mobile-card"
            style={{
              border: day.is_available ? '2px solid #047857' : '2px solid #e5e7eb',
              borderRadius: '12px',
              padding: '20px',
              backgroundColor: day.is_available ? '#ecfdf5' : '#ffffff',
              transition: 'all 0.15s ease'
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <h4 style={{
                margin: 0,
                color: '#1f2937',
                fontSize: '18px',
                fontWeight: '600'
              }}>
                {dayNames[index]}
              </h4>

              <label
                className="mobile-checkbox-container"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  cursor: 'pointer',
                  fontSize: '16px',
                  color: '#374151',
                  padding: '8px 12px',
                  background: day.is_available ? '#d1fae5' : '#f3f4f6',
                  borderRadius: '8px',
                  minHeight: '48px',
                  touchAction: 'manipulation'
                }}
              >
                <input
                  type="checkbox"
                  checked={day.is_available}
                  onChange={(e) => updateDayAvailability(index, 'is_available', e.target.checked)}
                  className="mobile-checkbox"
                  style={{
                    width: '28px',
                    height: '28px',
                    minWidth: '28px',
                    accentColor: '#047857'
                  }}
                />
                <span style={{ fontWeight: '500' }}>Available to play</span>
              </label>
            </div>

            {day.is_available && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                gap: '16px',
                marginBottom: '16px'
              }}>
                <div>
                  <label className="mobile-text-label" style={{
                    display: 'block',
                    fontSize: '15px',
                    color: '#374151',
                    marginBottom: '8px',
                    fontWeight: '500'
                  }}>
                    Available from:
                  </label>
                  <select
                    value={day.available_from_time}
                    onChange={(e) => updateDayAvailability(index, 'available_from_time', e.target.value)}
                    className="mobile-select"
                    style={{
                      width: '100%',
                      minHeight: '48px',
                      padding: '12px 40px 12px 16px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '8px',
                      fontSize: '16px',
                      backgroundColor: 'white',
                      appearance: 'none',
                      WebkitAppearance: 'none',
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23495057' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 16px center',
                      backgroundSize: '12px'
                    }}
                  >
                    {timeOptions.map(time => (
                      <option key={time} value={time}>
                        {time || 'Any time'}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mobile-text-label" style={{
                    display: 'block',
                    fontSize: '15px',
                    color: '#374151',
                    marginBottom: '8px',
                    fontWeight: '500'
                  }}>
                    Available until:
                  </label>
                  <select
                    value={day.available_to_time}
                    onChange={(e) => updateDayAvailability(index, 'available_to_time', e.target.value)}
                    className="mobile-select"
                    style={{
                      width: '100%',
                      minHeight: '48px',
                      padding: '12px 40px 12px 16px',
                      border: '2px solid #e5e7eb',
                      borderRadius: '8px',
                      fontSize: '16px',
                      backgroundColor: 'white',
                      appearance: 'none',
                      WebkitAppearance: 'none',
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23495057' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
                      backgroundRepeat: 'no-repeat',
                      backgroundPosition: 'right 16px center',
                      backgroundSize: '12px'
                    }}
                  >
                    {timeOptions.map(time => (
                      <option key={time} value={time}>
                        {time || 'Any time'}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {day.is_available && (
              <div style={{ marginBottom: '16px' }}>
                <label className="mobile-text-label" style={{
                  display: 'block',
                  fontSize: '15px',
                  color: '#374151',
                  marginBottom: '8px',
                  fontWeight: '500'
                }}>
                  Notes (optional):
                </label>
                <input
                  type="text"
                  placeholder="e.g., 'Only after work', 'Prefer mornings'"
                  value={day.notes}
                  onChange={(e) => updateDayAvailability(index, 'notes', e.target.value)}
                  className="mobile-form-control"
                  style={{
                    width: '100%',
                    minHeight: '48px',
                    padding: '12px 16px',
                    border: '2px solid #e5e7eb',
                    borderRadius: '8px',
                    fontSize: '16px',
                    boxSizing: 'border-box'
                  }}
                />
              </div>
            )}

            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '12px'
            }}>
              <button
                onClick={() => saveDayAvailability(index)}
                disabled={saving}
                className="mobile-button mobile-button-primary"
                style={{
                  background: saving ? '#9ca3af' : '#047857',
                  color: 'white',
                  border: 'none',
                  minHeight: '48px',
                  padding: '12px 24px',
                  borderRadius: '10px',
                  fontSize: '16px',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  fontWeight: '600',
                  touchAction: 'manipulation',
                  transition: 'all 0.15s ease'
                }}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div style={{
        marginTop: '24px',
        padding: '20px',
        background: '#f9fafb',
        borderRadius: '12px',
        border: '1px solid #e5e7eb'
      }}>
        <h5 style={{ color: '#1f2937', marginBottom: '16px', fontSize: '16px', fontWeight: '600' }}>Quick Actions</h5>
        <div className="mobile-quick-actions" style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button
            onClick={() => {
              const weekdayAvailability = availability.map((day, index) => ({
                ...day,
                is_available: index < 5 // Mon-Fri
              }));
              setAvailability(weekdayAvailability);
            }}
            className="mobile-quick-action"
            style={{
              flex: '1 1 auto',
              minWidth: '120px',
              background: '#0369a1',
              color: 'white',
              border: 'none',
              minHeight: '48px',
              padding: '12px 16px',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: 'pointer',
              touchAction: 'manipulation'
            }}
          >
            Weekdays
          </button>

          <button
            onClick={() => {
              const weekendAvailability = availability.map((day, index) => ({
                ...day,
                is_available: index >= 5 // Sat-Sun
              }));
              setAvailability(weekendAvailability);
            }}
            className="mobile-quick-action"
            style={{
              flex: '1 1 auto',
              minWidth: '120px',
              background: '#0369a1',
              color: 'white',
              border: 'none',
              minHeight: '48px',
              padding: '12px 16px',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: 'pointer',
              touchAction: 'manipulation'
            }}
          >
            Weekends
          </button>

          <button
            onClick={() => {
              const allAvailable = availability.map(day => ({
                ...day,
                is_available: true
              }));
              setAvailability(allAvailable);
            }}
            className="mobile-quick-action"
            style={{
              flex: '1 1 auto',
              minWidth: '120px',
              background: '#047857',
              color: 'white',
              border: 'none',
              minHeight: '48px',
              padding: '12px 16px',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: 'pointer',
              touchAction: 'manipulation'
            }}
          >
            All Days
          </button>

          <button
            onClick={() => {
              setAvailability(initializeAvailability());
            }}
            className="mobile-quick-action"
            style={{
              flex: '1 1 auto',
              minWidth: '120px',
              background: '#6b7280',
              color: 'white',
              border: 'none',
              minHeight: '48px',
              padding: '12px 16px',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: 'pointer',
              touchAction: 'manipulation'
            }}
          >
            Clear All
          </button>
        </div>
      </div>
    </div>
  );
};

export default PlayerAvailability;
