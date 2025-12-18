import React, { useState, useEffect } from 'react';
import '../../styles/mobile-touch.css';

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
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 12px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ color: '#1f2937', marginBottom: '8px', fontSize: '20px' }}>👥 Players' Availability</h2>
        <p style={{ color: '#6b7280', fontSize: '14px', margin: 0 }}>
          Find who's available when you are
        </p>
      </div>

      {/* Day Tabs - Mobile Scrollable */}
      <div
        className="mobile-date-picker"
        style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '20px',
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch',
          padding: '8px 4px',
          scrollbarWidth: 'none',
          msOverflowStyle: 'none'
        }}
      >
        <button
          onClick={() => setSelectedDay(null)}
          className="mobile-date-button"
          style={{
            flexShrink: 0,
            minHeight: '48px',
            padding: '12px 16px',
            background: selectedDay === null ? '#047857' : 'white',
            color: selectedDay === null ? 'white' : '#374151',
            border: selectedDay === null ? '2px solid #047857' : '2px solid #e5e7eb',
            borderRadius: '10px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            whiteSpace: 'nowrap',
            touchAction: 'manipulation'
          }}
        >
          All Days
        </button>
        {dayNames.map((day, index) => {
          const availableCount = getPlayersForDay(index).length;
          const shortDay = day.substring(0, 3);
          return (
            <button
              key={index}
              onClick={() => setSelectedDay(index)}
              className="mobile-date-button"
              style={{
                flexShrink: 0,
                minHeight: '48px',
                minWidth: '70px',
                padding: '8px 12px',
                background: selectedDay === index ? '#047857' : 'white',
                color: selectedDay === index ? 'white' : '#374151',
                border: selectedDay === index ? '2px solid #047857' : '2px solid #e5e7eb',
                borderRadius: '10px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                whiteSpace: 'nowrap',
                touchAction: 'manipulation',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '2px'
              }}
            >
              <span>{shortDay}</span>
              {availableCount > 0 && (
                <span style={{
                  padding: '2px 8px',
                  background: selectedDay === index ? 'rgba(255,255,255,0.25)' : '#047857',
                  color: 'white',
                  borderRadius: '10px',
                  fontSize: '12px',
                  fontWeight: '700'
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
        <div
          className="responsive-grid-3"
          style={{
            display: 'grid',
            gap: '16px'
          }}
        >
          {dayNames.map((day, dayIndex) => {
            const availablePlayers = getPlayersForDay(dayIndex);
            return (
              <div key={dayIndex} className="mobile-card" style={{
                border: '2px solid #e5e7eb',
                borderRadius: '12px',
                padding: '16px',
                background: '#ffffff'
              }}>
                <h4 style={{
                  color: '#1f2937',
                  fontSize: '16px',
                  fontWeight: '700',
                  marginBottom: '12px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  {day}
                  {availablePlayers.length > 0 && (
                    <span style={{
                      padding: '4px 10px',
                      background: '#047857',
                      color: 'white',
                      borderRadius: '12px',
                      fontSize: '13px',
                      fontWeight: '600'
                    }}>
                      {availablePlayers.length}
                    </span>
                  )}
                </h4>

                {availablePlayers.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {availablePlayers.map(player => {
                      const dayAvail = player.availability.find(a => a.day_of_week === dayIndex);
                      return (
                        <div key={player.player_id} style={{
                          padding: '12px',
                          background: '#ecfdf5',
                          borderRadius: '10px',
                          fontSize: '14px',
                          borderLeft: '4px solid #047857'
                        }}>
                          <div style={{ fontWeight: '600', color: '#065f46', fontSize: '15px' }}>
                            {player.player_name}
                          </div>
                          <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '4px' }}>
                            ⏰ {formatTimeRange(dayAvail.available_from_time, dayAvail.available_to_time)}
                          </div>
                          {dayAvail.notes && (
                            <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '4px', fontStyle: 'italic' }}>
                              💬 {dayAvail.notes}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p style={{ color: '#9ca3af', fontSize: '14px', margin: 0, textAlign: 'center', padding: '12px' }}>
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