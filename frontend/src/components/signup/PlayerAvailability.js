import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || "";

const PlayerAvailability = () => {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();
  const [availability, setAvailability] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(null);

  const dayNames = useMemo(() => ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], []);
  const dayNamesFull = useMemo(() => ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], []);

  const timeOptions = [
    '', '6:00 AM', '6:30 AM', '7:00 AM', '7:30 AM', '8:00 AM', '8:30 AM',
    '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM', '11:00 AM', '11:30 AM',
    '12:00 PM', '12:30 PM', '1:00 PM', '1:30 PM', '2:00 PM', '2:30 PM',
    '3:00 PM', '3:30 PM', '4:00 PM', '4:30 PM', '5:00 PM', '5:30 PM'
  ];

  const initializeAvailability = useCallback(() => {
    return dayNamesFull.map((_, index) => ({
      day_of_week: index,
      is_available: false,
      available_from_time: '',
      available_to_time: '',
      notes: ''
    }));
  }, [dayNamesFull]);

  const loadAvailability = useCallback(async () => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      let token;
      try {
        token = await getAccessTokenSilently();
      } catch (e) {
        token = localStorage.getItem('auth_token');
      }

      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const response = await fetch(`${API_URL}/players/me/availability`, { headers });

      if (response.ok) {
        const data = await response.json();
        const completeAvailability = initializeAvailability();
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
  }, [loadAvailability]);

  const updateDayAvailability = (dayIndex, field, value) => {
    setAvailability(prev => prev.map((day, index) =>
      index === dayIndex ? { ...day, [field]: value } : day
    ));
    setSaveSuccess(null);
  };

  const saveDayAvailability = async (dayIndex) => {
    const dayData = availability[dayIndex];

    try {
      setSaving(true);
      let token;
      try {
        token = await getAccessTokenSilently();
      } catch (e) {
        token = localStorage.getItem('auth_token');
      }

      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const response = await fetch(`${API_URL}/players/me/availability`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          player_profile_id: 0,
          day_of_week: dayData.day_of_week,
          is_available: dayData.is_available,
          available_from_time: dayData.available_from_time || null,
          available_to_time: dayData.available_to_time || null,
          notes: dayData.notes || null
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save');
      }

      const updatedDay = await response.json();
      setAvailability(prev => prev.map((day, index) =>
        index === dayIndex ? { ...day, id: updatedDay.id } : day
      ));
      setSaveSuccess(dayIndex);
      setError(null);
      setTimeout(() => setSaveSuccess(null), 2000);
    } catch (err) {
      console.error('Save error:', err);
      setError(`Failed to save ${dayNamesFull[dayIndex]}: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const setQuickPreset = (preset) => {
    let newAvailability;
    switch (preset) {
      case 'weekdays':
        newAvailability = availability.map((day, index) => ({ ...day, is_available: index < 5 }));
        break;
      case 'weekends':
        newAvailability = availability.map((day, index) => ({ ...day, is_available: index >= 5 }));
        break;
      case 'all':
        newAvailability = availability.map(day => ({ ...day, is_available: true }));
        break;
      case 'none':
        newAvailability = initializeAvailability();
        break;
      default:
        return;
    }
    setAvailability(newAvailability);
    setSaveSuccess(null);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#6b7280' }}>
        Loading...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '16px' }}>
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
          <button onClick={() => setError(null)} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer' }}>×</button>
        </div>
      )}

      {/* Quick Presets */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '20px',
        flexWrap: 'wrap'
      }}>
        {[
          { key: 'weekdays', label: 'Weekdays', color: '#0369a1' },
          { key: 'weekends', label: 'Weekends', color: '#0369a1' },
          { key: 'all', label: 'All Days', color: '#047857' },
          { key: 'none', label: 'Clear', color: '#6b7280' }
        ].map(preset => (
          <button
            key={preset.key}
            onClick={() => setQuickPreset(preset.key)}
            style={{
              flex: 1,
              minWidth: '70px',
              padding: '10px 12px',
              background: preset.color,
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Day Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(7, 1fr)',
        gap: '8px',
        marginBottom: '24px'
      }}>
        {availability.map((day, index) => (
          <button
            key={index}
            onClick={() => updateDayAvailability(index, 'is_available', !day.is_available)}
            style={{
              padding: '12px 4px',
              border: day.is_available ? '2px solid #047857' : '1px solid #e5e7eb',
              borderRadius: '10px',
              background: day.is_available ? '#ecfdf5' : '#fff',
              cursor: 'pointer',
              textAlign: 'center'
            }}
          >
            <div style={{ fontSize: '11px', color: '#6b7280', fontWeight: '500', marginBottom: '4px' }}>
              {dayNames[index]}
            </div>
            <div style={{
              fontSize: '20px',
              marginBottom: '4px'
            }}>
              {day.is_available ? '✓' : '–'}
            </div>
            <div style={{
              fontSize: '10px',
              color: day.is_available ? '#047857' : '#9ca3af'
            }}>
              {day.is_available ? 'Available' : 'Off'}
            </div>
          </button>
        ))}
      </div>

      {/* Day Details */}
      {availability.map((day, index) => day.is_available && (
        <div
          key={index}
          style={{
            background: '#fff',
            border: saveSuccess === index ? '2px solid #047857' : '1px solid #e5e7eb',
            borderRadius: '12px',
            padding: '16px',
            marginBottom: '12px'
          }}
        >
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#1f2937' }}>
              {dayNamesFull[index]}
            </h4>
            {saveSuccess === index && (
              <span style={{ fontSize: '12px', color: '#047857' }}>✓ Saved</span>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>From</label>
              <select
                value={day.available_from_time}
                onChange={(e) => updateDayAvailability(index, 'available_from_time', e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '14px'
                }}
              >
                {timeOptions.map(time => (
                  <option key={time} value={time}>{time || 'Any time'}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>Until</label>
              <select
                value={day.available_to_time}
                onChange={(e) => updateDayAvailability(index, 'available_to_time', e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '14px'
                }}
              >
                {timeOptions.map(time => (
                  <option key={time} value={time}>{time || 'Any time'}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>Notes</label>
            <input
              type="text"
              placeholder="e.g., 'Prefer mornings'"
              value={day.notes}
              onChange={(e) => updateDayAvailability(index, 'notes', e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          <button
            onClick={() => saveDayAvailability(index)}
            disabled={saving}
            style={{
              width: '100%',
              padding: '12px',
              background: saving ? '#9ca3af' : '#047857',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: saving ? 'not-allowed' : 'pointer'
            }}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      ))}

      {/* No days selected prompt */}
      {!availability.some(d => d.is_available) && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          color: '#9ca3af',
          background: '#f9fafb',
          borderRadius: '12px'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🕒</div>
          <p style={{ margin: 0 }}>Tap days above to set your availability</p>
        </div>
      )}
    </div>
  );
};

export default PlayerAvailability;
