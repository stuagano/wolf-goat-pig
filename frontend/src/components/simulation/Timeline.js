import React, { useState, useEffect, useRef } from 'react';
import { useTheme } from '../../theme/Provider';
import { Card } from '../ui';

const Timeline = ({ 
  events = [], 
  loading = false, 
  maxHeight = 400,
  autoScroll = true,
  showPokerStyle = true 
}) => {
  const theme = useTheme();
  const timelineRef = useRef(null);
  const [filter, setFilter] = useState('all'); // all, bets, shots, partnerships
  
  // Auto-scroll to top (most recent) when new events arrive
  useEffect(() => {
    if (autoScroll && timelineRef.current && events.length > 0) {
      timelineRef.current.scrollTop = 0;
    }
  }, [events, autoScroll]);
  
  // Filter events based on selected type
  const filteredEvents = events.filter(event => {
    if (filter === 'all') return true;
    if (filter === 'bets') return ['bet', 'fold', 'raise', 'call', 'check', 'all_in', 'double'].includes(event.type);
    if (filter === 'shots') return ['shot', 'hole_complete'].includes(event.type);
    if (filter === 'partnerships') return ['partnership', 'solo', 'captain'].includes(event.type);
    return true;
  });
  
  // Get color for event type
  const getEventColor = (type) => {
    const colors = {
      'bet': theme.colors.warning,
      'fold': theme.colors.error,
      'raise': theme.colors.success,
      'call': theme.colors.info,
      'check': theme.colors.secondary,
      'all_in': theme.colors.primary,
      'shot': theme.colors.success,
      'hole_complete': theme.colors.primary,
      'partnership': theme.colors.info,
      'solo': theme.colors.warning,
      'double': theme.colors.error,
      'captain': theme.colors.primary,
      'win': theme.colors.success,
      'loss': theme.colors.error
    };
    return colors[type] || theme.colors.text;
  };
  
  // Format event for poker-style display
  const formatPokerEvent = (event) => {
    if (!showPokerStyle) return event.description;
    
    const pokerTerms = {
      'partnership': 'teams up with',
      'solo': 'goes ALL-IN solo',
      'double': 'RAISES the stakes',
      'bet': 'BETS',
      'fold': 'FOLDS',
      'call': 'CALLS',
      'check': 'CHECKS'
    };
    
    let description = event.description;
    Object.keys(pokerTerms).forEach(term => {
      if (event.type === term) {
        description = description.replace(new RegExp(term, 'gi'), pokerTerms[term]);
      }
    });
    
    return description;
  };
  
  return (
    <Card style={{ padding: 0, overflow: 'hidden' }}>
      {/* Header with filter buttons */}
      <div style={{ 
        padding: '12px 16px',
        borderBottom: `1px solid ${theme.colors.border}`,
        background: theme.colors.background
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 'bold' }}>
            📜 Game Timeline {showPokerStyle && '(Wolf-Goat-Pig Style)'}
          </h3>
          
          {/* Filter buttons */}
          <div style={{ display: 'flex', gap: 8 }}>
            {['all', 'bets', 'shots', 'partnerships'].map(filterType => (
              <button
                key={filterType}
                onClick={() => setFilter(filterType)}
                style={{
                  padding: '4px 12px',
                  fontSize: 12,
                  border: 'none',
                  borderRadius: 12,
                  background: filter === filterType ? theme.colors.primary : theme.colors.secondary,
                  color: filter === filterType ? 'white' : theme.colors.text,
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {filterType}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      {/* Timeline content */}
      <div 
        ref={timelineRef}
        style={{ 
          maxHeight, 
          overflowY: 'auto',
          padding: 16
        }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <div style={{ 
              display: 'inline-block',
              width: 40,
              height: 40,
              border: `3px solid ${theme.colors.border}`,
              borderTop: `3px solid ${theme.colors.primary}`,
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            <p style={{ marginTop: 12, color: theme.colors.textSecondary }}>
              Loading timeline...
            </p>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 20, color: theme.colors.textSecondary }}>
            <p>No events yet. Start playing to see the timeline!</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {filteredEvents.map((event, index) => (
              <div
                key={event.id || index}
                style={{
                  display: 'flex',
                  gap: 12,
                  padding: 12,
                  background: index === 0 ? `${theme.colors.primary}10` : theme.colors.background,
                  borderRadius: 8,
                  border: `1px solid ${index === 0 ? theme.colors.primary : theme.colors.border}`,
                  transition: 'all 0.3s ease',
                  animation: index === 0 ? 'slideIn 0.3s ease' : 'none'
                }}
              >
                {/* Event icon */}
                <div style={{
                  fontSize: 24,
                  minWidth: 32,
                  textAlign: 'center'
                }}>
                  {event.icon}
                </div>
                
                {/* Event content */}
                <div style={{ flex: 1 }}>
                  {/* Description */}
                  <div style={{ 
                    fontWeight: index === 0 ? 'bold' : 'normal',
                    color: getEventColor(event.type),
                    marginBottom: 4
                  }}>
                    {formatPokerEvent(event)}
                  </div>
                  
                  {/* Details */}
                  {event.details && Object.keys(event.details).length > 0 && (
                    <div style={{ 
                      fontSize: 12, 
                      color: theme.colors.textSecondary,
                      marginTop: 4 
                    }}>
                      {event.details.club && `Club: ${event.details.club} • `}
                      {event.details.distance && `${event.details.distance} yards • `}
                      {event.details.result && `Result: ${event.details.result}`}
                      {event.details.amount && `Bet: $${event.details.amount}`}
                      {event.details.multiplier && ` (${event.details.multiplier}x)`}
                    </div>
                  )}
                  
                  {/* Player name */}
                  {event.player && (
                    <div style={{ 
                      fontSize: 11, 
                      color: theme.colors.textSecondary,
                      marginTop: 2
                    }}>
                      Player: {event.player}
                    </div>
                  )}
                </div>
                
                {/* Timestamp */}
                <div style={{
                  fontSize: 11,
                  color: theme.colors.textSecondary,
                  whiteSpace: 'nowrap'
                }}>
                  {event.time_ago || 'just now'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Footer with event count */}
      {filteredEvents.length > 0 && (
        <div style={{
          padding: '8px 16px',
          borderTop: `1px solid ${theme.colors.border}`,
          background: theme.colors.background,
          fontSize: 12,
          color: theme.colors.textSecondary,
          textAlign: 'center'
        }}>
          Showing {filteredEvents.length} {filter !== 'all' ? filter : 'events'} • Most recent first
        </div>
      )}
      
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </Card>
  );
};

export default Timeline;