import React, { useState, useMemo } from 'react';
import { useTheme } from '../theme/Provider';
import { Card } from './ui';

const GameHistory = ({ gameData = null, timelineEvents = [] }) => {
  const theme = useTheme();
  const [filter, setFilter] = useState('all');
  const [expandedItems, setExpandedItems] = useState(new Set());
  
  // Parse feedback from gameData
  const parsedEvents = useMemo(() => {
    if (!gameData || !gameData.feedback) return [];
    
    const events = [];
    
    // Process feedback array
    gameData.feedback.forEach((item, index) => {
      if (Array.isArray(item)) {
        // Handle nested arrays like the first entry
        item.forEach(subItem => {
          if (typeof subItem === 'string') {
            events.push({
              id: `feedback-${index}-${events.length}`,
              type: 'game_start',
              description: subItem,
              icon: '🎮',
              timestamp: new Date(),
              raw: subItem
            });
          }
        });
      } else if (typeof item === 'string') {
        // Parse shot feedback strings
        let type = 'unknown';
        let icon = '📢';
        let description = item;
        
        if (item.includes('🏌️')) {
          type = 'shot';
          icon = '🏌️';
          // Extract player name and shot quality
          const match = item.match(/🏌️ (\w+) hits (\w+) shot from (\w+) - (\d+)yd to pin/);
          if (match) {
            const [, player, quality, lie, distance] = match;
            description = `${player} hits ${quality} shot from ${lie} (${distance}yd to pin)`;
          }
        } else if (item.includes('🎯')) {
          type = 'analysis';
          icon = '🎯';
        } else if (item.includes('🎮')) {
          type = 'game_event';
          icon = '🎮';
        }
        
        events.push({
          id: `feedback-${index}`,
          type,
          description,
          icon,
          timestamp: new Date(),
          raw: item
        });
      }
    });
    
    return events.reverse(); // Most recent first
  }, [gameData]);
  
  // Combine parsed events with timeline events
  const allEvents = useMemo(() => {
    const combined = [...parsedEvents];
    
    // Add timeline events if they exist
    timelineEvents.forEach(event => {
      combined.push({
        id: event.id || `timeline-${combined.length}`,
        type: event.type || 'timeline',
        description: event.description || 'Timeline event',
        icon: event.icon || '📋',
        timestamp: event.timestamp || new Date(),
        payload: event.payload,
        raw: event
      });
    });
    
    // Sort by timestamp, most recent first
    return combined.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  }, [parsedEvents, timelineEvents]);
  
  // Filter events
  const filteredEvents = useMemo(() => {
    if (filter === 'all') return allEvents;
    return allEvents.filter(event => {
      if (filter === 'shots') return event.type === 'shot';
      if (filter === 'game') return ['game_start', 'game_event', 'game_end'].includes(event.type);
      if (filter === 'analysis') return ['analysis', 'timeline'].includes(event.type);
      return true;
    });
  }, [allEvents, filter]);
  
  const toggleExpanded = (eventId) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId);
    } else {
      newExpanded.add(eventId);
    }
    setExpandedItems(newExpanded);
  };
  
  const getTypeColor = (type) => {
    const colors = {
      'shot': '#4CAF50',
      'game_start': '#2196F3',
      'game_event': '#2196F3',
      'analysis': '#FF9800',
      'timeline': '#9C27B0',
      'unknown': theme.colors.textSecondary
    };
    return colors[type] || theme.colors.primary;
  };
  
  const extractGameStats = () => {
    if (!gameData) return null;
    
    return {
      hole: gameData.hole || 1,
      par: gameData.par || 4,
      distance: gameData.distance || 0,
      currentShot: gameData.currentShot || 1,
      nextPlayer: gameData.nextPlayer || 'Unknown',
      players: gameData.players || [],
      ballPositions: gameData.ballPositions || {}
    };
  };
  
  const stats = extractGameStats();
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Game Stats Overview */}
      {stats && (
        <Card>
          <h3 style={{ 
            margin: '0 0 16px 0', 
            color: theme.colors.primary, 
            display: 'flex', 
            alignItems: 'center', 
            gap: 8 
          }}>
            ⛳ Current Game State
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 16,
            marginBottom: 20
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
                Hole
              </div>
              <div style={{ fontSize: 24, fontWeight: 'bold', color: theme.colors.primary }}>
                {stats.hole}
              </div>
              <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                Par {stats.par}
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
                Distance
              </div>
              <div style={{ fontSize: 18, fontWeight: 'bold', color: theme.colors.text }}>
                {stats.distance} yds
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
                Shot #
              </div>
              <div style={{ fontSize: 18, fontWeight: 'bold', color: theme.colors.warning }}>
                {stats.currentShot}
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginBottom: 4 }}>
                Next Player
              </div>
              <div style={{ fontSize: 16, fontWeight: 'bold', color: theme.colors.success }}>
                {stats.nextPlayer}
              </div>
            </div>
          </div>
          
          {/* Players Overview */}
          <div>
            <h4 style={{ margin: '0 0 12px 0', fontSize: 16, color: theme.colors.primary }}>
              Players
            </h4>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: 12
            }}>
              {stats.players.map(player => (
                <div
                  key={player.id}
                  style={{
                    padding: 12,
                    background: theme.colors.background,
                    borderRadius: 8,
                    border: `1px solid ${theme.colors.border}`
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <div style={{ 
                        fontWeight: 'bold', 
                        color: theme.colors.text,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6
                      }}>
                        {player.id === 'human' ? '👤' : '🤖'} {player.name}
                      </div>
                      <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                        Handicap: {player.handicap}
                      </div>
                    </div>
                    <div style={{
                      fontSize: 16,
                      fontWeight: 'bold',
                      color: player.points >= 0 ? theme.colors.success : theme.colors.error
                    }}>
                      {player.points >= 0 ? '+' : ''}{player.points}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}
      
      {/* History Timeline */}
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{
          padding: '16px 20px',
          borderBottom: `1px solid ${theme.colors.border}`,
          background: theme.colors.background
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <h3 style={{ margin: 0, fontSize: 18, fontWeight: 'bold', color: theme.colors.primary }}>
              📋 Game History
            </h3>
            
            {/* Filter buttons */}
            <div style={{ display: 'flex', gap: 8 }}>
              {[
                { key: 'all', label: 'All', icon: '📋' },
                { key: 'shots', label: 'Shots', icon: '🏌️' },
                { key: 'game', label: 'Game', icon: '🎮' },
                { key: 'analysis', label: 'Analysis', icon: '🎯' }
              ].map(({ key, label, icon }) => (
                <button
                  key={key}
                  onClick={() => setFilter(key)}
                  style={{
                    padding: '6px 12px',
                    fontSize: 13,
                    border: 'none',
                    borderRadius: 16,
                    background: filter === key ? theme.colors.primary : theme.colors.secondary,
                    color: filter === key ? 'white' : theme.colors.text,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    fontWeight: filter === key ? 'bold' : 'normal'
                  }}
                >
                  {icon} {label}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        <div style={{ maxHeight: 500, overflowY: 'auto', padding: 20 }}>
          {filteredEvents.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: 40,
              color: theme.colors.textSecondary
            }}>
              <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.5 }}>📝</div>
              <p>No events yet. Start playing to see the timeline!</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {filteredEvents.map((event, index) => (
                <div
                  key={event.id}
                  style={{
                    display: 'flex',
                    gap: 16,
                    padding: 16,
                    background: index === 0 ? `${getTypeColor(event.type)}10` : theme.colors.card,
                    borderRadius: 12,
                    border: `2px solid ${index === 0 ? getTypeColor(event.type) : theme.colors.border}`,
                    transition: 'all 0.3s ease',
                    cursor: event.raw ? 'pointer' : 'default'
                  }}
                  onClick={() => event.raw && toggleExpanded(event.id)}
                >
                  {/* Event Icon */}
                  <div style={{
                    fontSize: 32,
                    minWidth: 40,
                    textAlign: 'center',
                    alignSelf: 'flex-start'
                  }}>
                    {event.icon}
                  </div>
                  
                  {/* Event Content */}
                  <div style={{ flex: 1 }}>
                    <div style={{
                      fontWeight: index === 0 ? 'bold' : '600',
                      color: getTypeColor(event.type),
                      marginBottom: 8,
                      fontSize: 16
                    }}>
                      {event.description}
                    </div>
                    
                    {/* Event Type Badge */}
                    <div style={{
                      display: 'inline-block',
                      padding: '4px 8px',
                      background: getTypeColor(event.type),
                      color: 'white',
                      fontSize: 11,
                      borderRadius: 12,
                      textTransform: 'uppercase',
                      fontWeight: 'bold',
                      letterSpacing: '0.5px',
                      marginBottom: 8
                    }}>
                      {event.type.replace('_', ' ')}
                    </div>
                    
                    {/* Expanded Raw Data */}
                    {expandedItems.has(event.id) && event.raw && (
                      <div style={{
                        marginTop: 12,
                        padding: 12,
                        background: '#f8f9fa',
                        borderRadius: 6,
                        fontSize: 12,
                        fontFamily: 'monospace',
                        border: `1px solid ${theme.colors.border}`,
                        whiteSpace: 'pre-wrap',
                        maxHeight: 200,
                        overflowY: 'auto'
                      }}>
                        {typeof event.raw === 'string' 
                          ? event.raw 
                          : JSON.stringify(event.raw, null, 2)}
                      </div>
                    )}
                    
                    {event.raw && (
                      <div style={{
                        fontSize: 11,
                        color: theme.colors.textSecondary,
                        marginTop: 8,
                        fontStyle: 'italic'
                      }}>
                        {expandedItems.has(event.id) ? '🔽 Click to collapse' : '🔽 Click to expand raw data'}
                      </div>
                    )}
                  </div>
                  
                  {/* Timestamp */}
                  <div style={{
                    fontSize: 11,
                    color: theme.colors.textSecondary,
                    whiteSpace: 'nowrap',
                    alignSelf: 'flex-start',
                    marginTop: 4
                  }}>
                    {event.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Footer Stats */}
        {filteredEvents.length > 0 && (
          <div style={{
            padding: '12px 20px',
            borderTop: `1px solid ${theme.colors.border}`,
            background: theme.colors.background,
            fontSize: 13,
            color: theme.colors.textSecondary,
            textAlign: 'center'
          }}>
            Showing {filteredEvents.length} {filter !== 'all' ? `${filter} ` : ''}events
            {allEvents.length !== filteredEvents.length && (
              <span> of {allEvents.length} total</span>
            )}
          </div>
        )}
      </Card>
    </div>
  );
};

export default GameHistory;