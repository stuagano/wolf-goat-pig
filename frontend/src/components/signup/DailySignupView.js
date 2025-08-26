import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || "";

const DailySignupView = ({ selectedDate, onBack }) => {
  const { user, isAuthenticated } = useAuth0();
  const [signupData, setSignupData] = useState({
    tee_times: [],
    players: [],
    notes: ''
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [availablePlayers, setAvailablePlayers] = useState([]);
  const [teeTimes, setTeeTimes] = useState([]);
  const [selectedPlayers, setSelectedPlayers] = useState({});

  // Format date for display
  const formatDateDisplay = (dateStr) => {
    const date = new Date(dateStr);
    const options = { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    };
    return date.toLocaleDateString('en-US', options);
  };

  // Load daily signup data
  const loadDailyData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/signups/daily/${selectedDate}`);
      
      if (!response.ok) {
        throw new Error(`Failed to load daily data: ${response.status}`);
      }
      
      const data = await response.json();
      setSignupData(data);
      setError(null);
    } catch (err) {
      console.error('Error loading daily data:', err);
      setError(err.message);
      // Set default data structure on error
      setSignupData({
        tee_times: [],
        players: [],
        notes: ''
      });
    } finally {
      setLoading(false);
    }
  };

  // Load available players for selection
  const loadAvailablePlayers = async () => {
    try {
      const response = await fetch(`${API_URL}/players`);
      if (response.ok) {
        const players = await response.json();
        setAvailablePlayers(players);
      }
    } catch (err) {
      console.error('Error loading players:', err);
      // Use mock players if API fails
      setAvailablePlayers([
        { id: 1, name: 'Stuart Gano' },
        { id: 2, name: 'John Smith' },
        { id: 3, name: 'Mike Johnson' },
        { id: 4, name: 'Dave Wilson' },
        { id: 5, name: 'Tom Brown' },
        { id: 6, name: 'Chris Davis' },
        { id: 7, name: 'Paul Miller' },
        { id: 8, name: 'Steve Clark' },
        { id: 9, name: 'Mark Taylor' },
        { id: 10, name: 'Jim Anderson' }
      ]);
    }
  };

  // Generate default tee times
  const generateTeeTimes = () => {
    const times = [];
    const startHour = 7; // 7 AM
    const endHour = 17;  // 5 PM
    
    for (let hour = startHour; hour <= endHour; hour++) {
      for (let minute of [0, 15, 30, 45]) {
        const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        times.push(timeString);
      }
    }
    return times;
  };

  // Initialize component
  useEffect(() => {
    if (selectedDate) {
      loadDailyData();
      loadAvailablePlayers();
      setTeeTimes(generateTeeTimes());
    }
  }, [selectedDate]);

  // Handle player selection for a specific slot
  const handlePlayerSelect = (slotIndex, playerId) => {
    setSelectedPlayers(prev => ({
      ...prev,
      [slotIndex]: playerId
    }));
  };

  // Handle tee time change
  const handleTeeTimeChange = (newTeeTime) => {
    setSignupData(prev => ({
      ...prev,
      tee_time: newTeeTime
    }));
  };

  // Handle notes update
  const handleNotesUpdate = (notes) => {
    setSignupData(prev => ({
      ...prev,
      notes: notes
    }));
  };

  // Save signup changes
  const handleSave = async () => {
    if (!isAuthenticated) {
      setError('Please log in to save signup');
      return;
    }

    try {
      const saveData = {
        date: selectedDate,
        players: Object.values(selectedPlayers).filter(Boolean),
        tee_time: signupData.tee_time,
        notes: signupData.notes
      };

      const response = await fetch(`${API_URL}/signups/daily/${selectedDate}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save signup');
      }

      // Show success message or reload data
      alert('Signup saved successfully!');
      loadDailyData();
      
    } catch (err) {
      console.error('Save error:', err);
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
        Loading daily signup...
      </div>
    );
  }

  return (
    <div style={{ 
      maxWidth: '1200px', 
      margin: '0 auto',
      background: 'white',
      borderRadius: '8px',
      padding: '20px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '30px',
        borderBottom: '2px solid #dee2e6',
        paddingBottom: '15px'
      }}>
        <div>
          <h2 style={{ 
            margin: 0, 
            color: '#333',
            fontSize: '24px',
            fontWeight: 'bold'
          }}>
            🏌️ Golf Sign-up & Daily Messages
          </h2>
          <p style={{ 
            margin: '5px 0 0 0',
            color: '#6c757d',
            fontSize: '14px'
          }}>
            Manage your daily golf sign-ups, post messages, and set preferences
          </p>
          {user && (
            <div style={{
              marginTop: '8px',
              padding: '4px 8px',
              background: '#e3f2fd',
              color: '#1976d2',
              borderRadius: '4px',
              fontSize: '12px',
              display: 'inline-block'
            }}>
              Welcome, {user.name || user.email}
            </div>
          )}
        </div>
        
        <button
          onClick={onBack}
          style={{
            padding: '8px 16px',
            background: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          ← Back to Week View
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

      {/* Date Selection Bar */}
      <div style={{
        background: '#f8f9fa',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        <h3 style={{ 
          margin: '0 0 10px 0',
          color: '#495057',
          fontSize: '18px'
        }}>
          Click a day
        </h3>
        <div style={{
          display: 'flex',
          gap: '10px',
          justifyContent: 'center',
          flexWrap: 'wrap'
        }}>
          {/* Generate week dates around selected date */}
          {Array.from({length: 8}, (_, i) => {
            const date = new Date(selectedDate);
            date.setDate(date.getDate() - 3 + i);
            const dateStr = date.toISOString().split('T')[0];
            const isSelected = dateStr === selectedDate;
            
            return (
              <button
                key={dateStr}
                onClick={() => window.location.hash = `#daily/${dateStr}`}
                style={{
                  padding: '8px 12px',
                  background: isSelected ? '#dc3545' : '#fff',
                  color: isSelected ? 'white' : '#333',
                  border: '1px solid #dee2e6',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  minWidth: '120px'
                }}
              >
                {date.toLocaleDateString('en-US', { 
                  weekday: 'short', 
                  month: 'short', 
                  day: 'numeric' 
                })}
              </button>
            );
          })}
        </div>
      </div>

      {/* Current Standings */}
      <div style={{
        background: '#fff3cd',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        <div style={{ 
          color: '#856404', 
          fontWeight: 'bold',
          marginBottom: '10px',
          fontSize: '16px'
        }}>
          Current Standings
        </div>
        <button style={{
          background: '#ffc107',
          color: '#000',
          border: 'none',
          padding: '10px 20px',
          borderRadius: '6px',
          fontWeight: 'bold',
          cursor: 'pointer',
          fontSize: '14px'
        }}>
          New Player? Click here to sign up.
        </button>
      </div>

      {/* Main Date Display */}
      <div style={{
        background: '#fff9c4',
        padding: '15px',
        borderRadius: '8px',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        <div style={{
          background: '#fff59d',
          display: 'inline-block',
          padding: '10px 25px',
          borderRadius: '6px',
          fontSize: '18px',
          fontWeight: 'bold',
          color: '#333'
        }}>
          {formatDateDisplay(selectedDate)}
        </div>
      </div>

      {/* Main Content Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 2fr',
        gap: '20px',
        border: '2px solid #dee2e6',
        borderRadius: '8px',
        overflow: 'hidden'
      }}>
        {/* Left Column - Tee Times */}
        <div style={{
          background: '#fff',
          borderRight: '1px solid #dee2e6'
        }}>
          <div style={{
            background: '#dc3545',
            color: 'white',
            padding: '12px',
            textAlign: 'center',
            fontWeight: 'bold',
            fontSize: '16px'
          }}>
            Tee Times
          </div>
          <div style={{
            background: '#f8f9fa',
            padding: '15px',
            textAlign: 'center',
            borderBottom: '1px solid #dee2e6'
          }}>
            <div style={{ marginBottom: '10px', fontSize: '14px', color: '#495057' }}>
              Add Tee Times
            </div>
            <textarea
              placeholder="Enter tee times, one per line (e.g. 8:00 AM)"
              style={{
                width: '100%',
                height: '100px',
                padding: '8px',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                resize: 'none',
                fontSize: '14px'
              }}
            />
          </div>
        </div>

        {/* Right Column - Players and Notes */}
        <div style={{ background: '#fff' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            height: '100%'
          }}>
            {/* Players Column */}
            <div style={{ borderRight: '1px solid #dee2e6' }}>
              <div style={{
                background: '#495057',
                color: 'white',
                padding: '12px',
                textAlign: 'center',
                fontWeight: 'bold',
                fontSize: '16px'
              }}>
                Players
              </div>
              <div style={{ padding: '15px' }}>
                {Array.from({length: 14}, (_, i) => (
                  <div key={i} style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '8px',
                    fontSize: '14px'
                  }}>
                    <div style={{
                      width: '20px',
                      textAlign: 'center',
                      marginRight: '10px',
                      fontWeight: 'bold'
                    }}>
                      {i + 1}
                    </div>
                    <select
                      value={selectedPlayers[i] || ''}
                      onChange={(e) => handlePlayerSelect(i, e.target.value)}
                      style={{
                        flex: 1,
                        padding: '4px 8px',
                        border: '1px solid #dee2e6',
                        borderRadius: '4px',
                        fontSize: '14px'
                      }}
                    >
                      <option value="">Select Player...</option>
                      {availablePlayers.map(player => (
                        <option key={player.id} value={player.id}>
                          {player.name}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>

            {/* Notes Column */}
            <div>
              <div style={{
                background: '#28a745',
                color: 'white',
                padding: '12px',
                textAlign: 'center',
                fontWeight: 'bold',
                fontSize: '16px'
              }}>
                Note
              </div>
              <div style={{ 
                padding: '15px',
                height: 'calc(100% - 48px)'
              }}>
                <div style={{ 
                  fontSize: '12px', 
                  color: '#6c757d', 
                  marginBottom: '8px' 
                }}>
                  (after adding note click anywhere to update)
                </div>
                <textarea
                  value={signupData.notes || ''}
                  onChange={(e) => handleNotesUpdate(e.target.value)}
                  placeholder="Add your notes here..."
                  style={{
                    width: '100%',
                    height: 'calc(100% - 30px)',
                    padding: '8px',
                    border: '1px solid #dee2e6',
                    borderRadius: '4px',
                    resize: 'none',
                    fontSize: '14px',
                    fontFamily: 'inherit'
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      {isAuthenticated && (
        <div style={{ 
          textAlign: 'center',
          marginTop: '20px'
        }}>
          <button
            onClick={handleSave}
            style={{
              padding: '12px 30px',
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            Save Signup Information
          </button>
        </div>
      )}

      {/* Not Authenticated Message */}
      {!isAuthenticated && (
        <div style={{
          background: '#f8d7da',
          color: '#721c24',
          padding: '15px',
          borderRadius: '8px',
          marginTop: '20px',
          textAlign: 'center'
        }}>
          Please log in to sign up for golf or post messages.
        </div>
      )}
    </div>
  );
};

export default DailySignupView;