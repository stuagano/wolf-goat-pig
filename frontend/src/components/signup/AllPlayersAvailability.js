import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || "";

const AllPlayersAvailability = () => {
  const [playersAvailability, setPlayersAvailability] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);

  const dayNames = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 
    'Friday', 'Saturday', 'Sunday'
  ];

  // Load all players' availability
  const loadAllAvailability = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/players/availability/all`);
      
      if (response.ok) {
        const data = await response.json();
        setPlayersAvailability(data);
      } else {
        throw new Error('Failed to load availability data');
      }
      
      setError(null);
    } catch (err) {
      console.error('Error loading all availability:', err);
      setError(err.message);
      setPlayersAvailability([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllAvailability();
  }, []);

  // Get players available on a specific day
  const getPlayersForDay = (dayIndex) => {
    return playersAvailability.filter(player => {
      const dayAvailability = player.availability.find(a => a.day_of_week === dayIndex);
      return dayAvailability && dayAvailability.is_available;
    });
  };

  // Format time display
  const formatTimeRange = (fromTime, toTime) => {
    if (!fromTime && !toTime) return 'Any time';
    if (!fromTime) return `Until ${toTime}`;
    if (!toTime) return `From ${fromTime}`;
    return `${fromTime} - ${toTime}`;
  };

  if (loading) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px',
        fontSize: '16px',
        color: '#6c757d'
      }}>
        Loading players' availability...
      </div>
    );
  }

  if (error) {
    return (
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
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '30px' }}>
        <h2 style={{ color: '#333', marginBottom: '10px' }}>👥 Players' Availability Calendar</h2>
        <p style={{ color: '#6c757d', fontSize: '14px' }}>
          View individual player schedules and find who's available when you are
        </p>
      </div>

      {/* Day Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '30px',
        overflowX: 'auto',
        paddingBottom: '10px'
      }}>
        <button
          onClick={() => setSelectedDay(null)}
          style={{
            padding: '10px 16px',
            background: selectedDay === null ? '#007bff' : '#f8f9fa',
            color: selectedDay === null ? 'white' : '#495057',
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '500',
            whiteSpace: 'nowrap'
          }}
        >
          All Days
        </button>
        {dayNames.map((day, index) => {
          const availableCount = getPlayersForDay(index).length;
          return (
            <button
              key={index}
              onClick={() => setSelectedDay(index)}
              style={{
                padding: '10px 16px',
                background: selectedDay === index ? '#007bff' : '#f8f9fa',
                color: selectedDay === index ? 'white' : '#495057',
                border: '1px solid #dee2e6',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                whiteSpace: 'nowrap',
                position: 'relative'
              }}
            >
              {day}
              {availableCount > 0 && (
                <span style={{
                  marginLeft: '8px',
                  padding: '2px 6px',
                  background: selectedDay === index ? 'rgba(255,255,255,0.3)' : '#28a745',
                  color: selectedDay === index ? 'white' : 'white',
                  borderRadius: '10px',
                  fontSize: '12px'
                }}>
                  {availableCount}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Availability Grid */}
      {selectedDay === null ? (
        // Show weekly overview
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '20px'
        }}>
          {dayNames.map((day, dayIndex) => {
            const availablePlayers = getPlayersForDay(dayIndex);
            return (
              <div key={dayIndex} style={{
                border: '1px solid #dee2e6',
                borderRadius: '8px',
                padding: '16px',
                background: '#ffffff'
              }}>
                <h4 style={{
                  color: '#495057',
                  fontSize: '16px',
                  fontWeight: '600',
                  marginBottom: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  {day}
                  {availablePlayers.length > 0 && (
                    <span style={{
                      padding: '2px 8px',
                      background: '#28a745',
                      color: 'white',
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: 'normal'
                    }}>
                      {availablePlayers.length} available
                    </span>
                  )}
                </h4>
                
                {availablePlayers.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {availablePlayers.map(player => {
                      const dayAvail = player.availability.find(a => a.day_of_week === dayIndex);
                      return (
                        <div key={player.player_id} style={{
                          padding: '8px',
                          background: '#f0f8ff',
                          borderRadius: '4px',
                          fontSize: '14px',
                          borderLeft: '3px solid #4CAF50'
                        }}>
                          <div style={{ fontWeight: '500', color: '#1a5490' }}>
                            👤 {player.player_name}
                          </div>
                          <div style={{ fontSize: '12px', color: '#5a6c7d', marginTop: '2px' }}>
                            ⏰ {formatTimeRange(dayAvail.available_from_time, dayAvail.available_to_time)}
                          </div>
                          {dayAvail.notes && (
                            <div style={{ fontSize: '12px', color: '#7a8a9a', marginTop: '2px', fontStyle: 'italic' }}>
                              💬 {dayAvail.notes}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p style={{ color: '#adb5bd', fontSize: '14px', margin: 0 }}>
                    No players available
                  </p>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        // Show detailed view for selected day
        <div>
          <h3 style={{
            color: '#495057',
            fontSize: '20px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            {dayNames[selectedDay]} Availability
            <span style={{
              padding: '4px 12px',
              background: '#28a745',
              color: 'white',
              borderRadius: '12px',
              fontSize: '14px',
              fontWeight: 'normal'
            }}>
              {getPlayersForDay(selectedDay).length} players available
            </span>
          </h3>
          
          {getPlayersForDay(selectedDay).length > 0 ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '16px'
            }}>
              {getPlayersForDay(selectedDay).map(player => {
                const dayAvail = player.availability.find(a => a.day_of_week === selectedDay);
                return (
                  <div key={player.player_id} style={{
                    border: '1px solid #dee2e6',
                    borderRadius: '8px',
                    padding: '16px',
                    background: '#ffffff'
                  }}>
                    <h5 style={{
                      color: '#333',
                      fontSize: '16px',
                      fontWeight: '600',
                      marginBottom: '8px'
                    }}>
                      {player.player_name}
                    </h5>
                    <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '4px' }}>
                      <strong>Time:</strong> {formatTimeRange(dayAvail.available_from_time, dayAvail.available_to_time)}
                    </div>
                    {dayAvail.notes && (
                      <div style={{ fontSize: '14px', color: '#6c757d' }}>
                        <strong>Notes:</strong> {dayAvail.notes}
                      </div>
                    )}
                    <div style={{ fontSize: '12px', color: '#adb5bd', marginTop: '8px' }}>
                      {player.email}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              background: '#f8f9fa',
              borderRadius: '8px',
              color: '#6c757d'
            }}>
              <p style={{ fontSize: '16px', margin: '0 0 8px 0' }}>
                No players available on {dayNames[selectedDay]}
              </p>
              <p style={{ fontSize: '14px', margin: 0 }}>
                Check other days or encourage players to update their availability
              </p>
            </div>
          )}
        </div>
      )}

      {/* Summary Stats */}
      <div style={{
        marginTop: '40px',
        padding: '20px',
        background: '#e8f5e8',
        borderRadius: '8px',
        border: '1px solid #c3e6c3'
      }}>
        <h4 style={{ color: '#2e7d32', marginBottom: '16px' }}>📊 Weekly Availability Overview</h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px'
        }}>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007bff' }}>
              {playersAvailability.length}
            </div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>Total Players</div>
          </div>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
              {Math.max(...dayNames.map((_, i) => getPlayersForDay(i).length))}
            </div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>Most Available (Single Day)</div>
          </div>
          <div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ffc107' }}>
              {dayNames[dayNames.map((_, i) => getPlayersForDay(i).length)
                .indexOf(Math.max(...dayNames.map((_, i) => getPlayersForDay(i).length)))]}
            </div>
            <div style={{ fontSize: '14px', color: '#6c757d' }}>Most Popular Day</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AllPlayersAvailability;