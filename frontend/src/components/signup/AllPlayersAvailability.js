import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || "";

const AllPlayersAvailability = () => {
  const [playersAvailability, setPlayersAvailability] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDay, setSelectedDay] = useState(null);

  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const dayNamesFull = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

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

  const getPlayersForDay = (dayIndex) => {
    return playersAvailability.filter(player => {
      const dayAvailability = player.availability.find(a => a.day_of_week === dayIndex);
      return dayAvailability && dayAvailability.is_available;
    });
  };

  const formatTimeRange = (fromTime, toTime) => {
    if (!fromTime && !toTime) return 'Any time';
    if (!fromTime) return `Until ${toTime}`;
    if (!toTime) return `From ${fromTime}`;
    return `${fromTime} - ${toTime}`;
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#6b7280' }}>
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        background: '#fef2f2',
        color: '#dc2626',
        padding: '12px',
        borderRadius: '8px',
        margin: '16px'
      }}>
        {error}
      </div>
    );
  }

  const selectedDayData = selectedDay !== null ? getPlayersForDay(selectedDay) : null;

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '16px' }}>
      {/* Day Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(7, 1fr)',
        gap: '8px',
        marginBottom: '24px'
      }}>
        {dayNames.map((day, index) => {
          const count = getPlayersForDay(index).length;
          const isSelected = selectedDay === index;

          return (
            <button
              key={index}
              onClick={() => setSelectedDay(isSelected ? null : index)}
              style={{
                padding: '12px 4px',
                border: isSelected ? '2px solid #047857' : '1px solid #e5e7eb',
                borderRadius: '10px',
                background: isSelected ? '#f0fdf4' : '#fff',
                cursor: 'pointer',
                textAlign: 'center'
              }}
            >
              <div style={{ fontSize: '11px', color: '#6b7280', fontWeight: '500', marginBottom: '4px' }}>
                {day}
              </div>
              <div style={{
                fontSize: '18px',
                fontWeight: '600',
                color: count > 0 ? '#047857' : '#9ca3af',
                marginBottom: '4px'
              }}>
                {count}
              </div>
              {count > 0 && (
                <div style={{
                  background: '#047857',
                  color: 'white',
                  fontSize: '10px',
                  fontWeight: '600',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  display: 'inline-block'
                }}>
                  ⛳
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
          <div style={{
            background: '#f9fafb',
            padding: '16px',
            borderBottom: '1px solid #e5e7eb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>
              {dayNamesFull[selectedDay]}
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

          <div style={{ padding: '16px' }}>
            <div style={{
              fontSize: '13px',
              fontWeight: '600',
              color: '#6b7280',
              marginBottom: '12px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              👥 Available Players ({selectedDayData.length})
            </div>

            {selectedDayData.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selectedDayData.map(player => {
                  const dayAvail = player.availability.find(a => a.day_of_week === selectedDay);
                  return (
                    <div
                      key={player.player_id}
                      style={{
                        background: '#ecfdf5',
                        padding: '12px',
                        borderRadius: '8px',
                        borderLeft: '4px solid #047857'
                      }}
                    >
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
              <p style={{ color: '#9ca3af', fontStyle: 'italic', margin: 0, textAlign: 'center', padding: '20px' }}>
                No one available
              </p>
            )}
          </div>
        </div>
      )}

      {/* No day selected prompt */}
      {selectedDay === null && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          color: '#9ca3af',
          background: '#f9fafb',
          borderRadius: '12px'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>👥</div>
          <p style={{ margin: 0 }}>Tap a day to see who's available</p>
        </div>
      )}

      {/* Summary Stats */}
      <div style={{
        marginTop: '24px',
        padding: '16px',
        background: '#f0fdf4',
        borderRadius: '12px',
        border: '1px solid #bbf7d0'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '16px',
          textAlign: 'center'
        }}>
          <div>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#047857' }}>
              {playersAvailability.length}
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>Total Players</div>
          </div>
          <div>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#047857' }}>
              {Math.max(...dayNames.map((_, i) => getPlayersForDay(i).length), 0)}
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>Best Day</div>
          </div>
          <div>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#047857' }}>
              {dayNamesFull[dayNames.map((_, i) => getPlayersForDay(i).length)
                .indexOf(Math.max(...dayNames.map((_, i) => getPlayersForDay(i).length), 0))]?.substring(0, 3) || '–'}
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>Most Popular</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AllPlayersAvailability;
