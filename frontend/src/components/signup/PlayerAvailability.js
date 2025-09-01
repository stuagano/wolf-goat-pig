import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || "";

const PlayerAvailability = () => {
  // const { user } = useAuth0(); // Removed - not currently used
  const [availability, setAvailability] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const dayNames = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 
    'Friday', 'Saturday', 'Sunday'
  ];

  // Time options for dropdowns
  const timeOptions = [
    '', '6:00 AM', '6:30 AM', '7:00 AM', '7:30 AM', '8:00 AM', '8:30 AM',
    '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM',
    '12:00 PM', '12:30 PM', '1:00 PM', '1:30 PM', '2:00 PM', '2:30 PM',
    '3:00 PM', '3:30 PM', '4:00 PM', '4:30 PM', '5:00 PM', '5:30 PM',
    '6:00 PM', '6:30 PM', '7:00 PM', '7:30 PM', '8:00 PM'
  ];

  // Initialize empty availability structure
  const initializeAvailability = () => {
    return dayNames.map((_, index) => ({
      day_of_week: index,
      is_available: false,
      available_from_time: '',
      available_to_time: '',
      notes: ''
    }));
  };

  // Load player's availability
  const loadAvailability = async () => {
    try {
      setLoading(true);
      // For now using player ID 1, in real app this would come from auth
      const response = await fetch(`${API_URL}/players/1/availability`);
      
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
  };

  useEffect(() => {
    loadAvailability();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only load on mount

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
        player_profile_id: 1, // Would come from authenticated user
        day_of_week: dayData.day_of_week,
        is_available: dayData.is_available,
        available_from_time: dayData.available_from_time || null,
        available_to_time: dayData.available_to_time || null,
        notes: dayData.notes || null
      };

      const response = await fetch(`${API_URL}/players/1/availability`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
        padding: '40px',
        fontSize: '16px',
        color: '#6c757d'
      }}>
        Loading your availability settings...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px' }}>
      {error && (
        <div style={{ 
          backgroundColor: '#f8d7da', 
          color: '#721c24', 
          padding: '12px', 
          borderRadius: '6px', 
          marginBottom: '20px',
          border: '1px solid #f5c6cb'
        }}>
          {error}
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <p style={{ color: '#6c757d', fontSize: '14px', margin: 0 }}>
          Set your typical availability for each day to help others know when you're usually free to play.
        </p>
      </div>

      {/* Availability Cards */}
      <div style={{
        display: 'grid',
        gap: '16px'
      }}>
        {availability.map((day, index) => (
          <div key={index} style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '20px',
            backgroundColor: day.is_available ? '#f8fff8' : '#ffffff'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '15px'
            }}>
              <h4 style={{ 
                margin: 0, 
                color: '#495057',
                fontSize: '16px',
                fontWeight: '600'
              }}>
                {dayNames[index]}
              </h4>
              
              <label style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                cursor: 'pointer',
                fontSize: '14px'
              }}>
                <input
                  type="checkbox"
                  checked={day.is_available}
                  onChange={(e) => updateDayAvailability(index, 'is_available', e.target.checked)}
                  style={{ transform: 'scale(1.1)' }}
                />
                Available to play
              </label>
            </div>

            {day.is_available && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '12px',
                marginBottom: '15px'
              }}>
                <div>
                  <label style={{ 
                    display: 'block', 
                    fontSize: '13px', 
                    color: '#495057',
                    marginBottom: '4px',
                    fontWeight: '500'
                  }}>
                    Available from:
                  </label>
                  <select
                    value={day.available_from_time}
                    onChange={(e) => updateDayAvailability(index, 'available_from_time', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      border: '1px solid #ced4da',
                      borderRadius: '4px',
                      fontSize: '14px'
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
                  <label style={{ 
                    display: 'block', 
                    fontSize: '13px', 
                    color: '#495057',
                    marginBottom: '4px',
                    fontWeight: '500'
                  }}>
                    Available until:
                  </label>
                  <select
                    value={day.available_to_time}
                    onChange={(e) => updateDayAvailability(index, 'available_to_time', e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      border: '1px solid #ced4da',
                      borderRadius: '4px',
                      fontSize: '14px'
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
              <div style={{ marginBottom: '15px' }}>
                <label style={{ 
                  display: 'block', 
                  fontSize: '13px', 
                  color: '#495057',
                  marginBottom: '4px',
                  fontWeight: '500'
                }}>
                  Notes (optional):
                </label>
                <input
                  type="text"
                  placeholder="e.g., 'Only after work', 'Prefer mornings', etc."
                  value={day.notes}
                  onChange={(e) => updateDayAvailability(index, 'notes', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ced4da',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </div>
            )}

            <div style={{ 
              display: 'flex', 
              justifyContent: 'flex-end',
              gap: '8px' 
            }}>
              <button
                onClick={() => saveDayAvailability(index)}
                disabled={saving}
                style={{
                  background: '#28a745',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  fontSize: '13px',
                  cursor: saving ? 'not-allowed' : 'pointer',
                  opacity: saving ? 0.7 : 1,
                  fontWeight: '500'
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
        marginTop: '20px',
        padding: '16px',
        background: '#f8f9fa',
        borderRadius: '6px',
        border: '1px solid #dee2e6'
      }}>
        <h5 style={{ color: '#495057', marginBottom: '10px' }}>Quick Actions</h5>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            onClick={() => {
              const weekdayAvailability = availability.map((day, index) => ({
                ...day,
                is_available: index < 5 // Mon-Fri
              }));
              setAvailability(weekdayAvailability);
            }}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Available Weekdays
          </button>
          
          <button
            onClick={() => {
              const weekendAvailability = availability.map((day, index) => ({
                ...day,
                is_available: index >= 5 // Sat-Sun
              }));
              setAvailability(weekendAvailability);
            }}
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Available Weekends
          </button>
          
          <button
            onClick={() => {
              const allAvailable = availability.map(day => ({
                ...day,
                is_available: true
              }));
              setAvailability(allAvailable);
            }}
            style={{
              background: '#28a745',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            Available All Days
          </button>
          
          <button
            onClick={() => {
              setAvailability(initializeAvailability());
            }}
            style={{
              background: '#6c757d',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer'
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