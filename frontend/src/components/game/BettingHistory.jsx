// frontend/src/components/game/BettingHistory.jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';

const BettingHistory = ({ eventHistory }) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState('current');

  const tabContainerStyle = {
    display: 'flex',
    borderBottom: `2px solid ${theme.colors.border}`,
    marginBottom: theme.spacing[3]
  };

  const tabStyle = (isActive) => ({
    padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
    background: isActive ? theme.colors.primary : 'transparent',
    color: isActive ? 'white' : theme.colors.textPrimary,
    border: 'none',
    cursor: 'pointer',
    fontSize: theme.typography.md,
    borderRadius: `${theme.borderRadius.md} ${theme.borderRadius.md} 0 0`
  });

  const eventListStyle = {
    maxHeight: 300,
    overflowY: 'auto'
  };

  const eventItemStyle = {
    padding: theme.spacing[3],
    background: theme.colors.paper,
    borderRadius: theme.borderRadius.md,
    marginBottom: theme.spacing[2],
    borderLeft: `4px solid ${theme.colors.primary}`
  };

  const getEvents = () => {
    switch (activeTab) {
      case 'current':
        return eventHistory.currentHole;
      case 'last':
        return eventHistory.lastHole;
      case 'game':
        return eventHistory.gameHistory;
      default:
        return [];
    }
  };

  const events = getEvents();

  return (
    <div>
      <div style={tabContainerStyle}>
        <button
          role="tab"
          aria-selected={activeTab === 'current'}
          style={tabStyle(activeTab === 'current')}
          onClick={() => setActiveTab('current')}
        >
          Current Hole
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'last'}
          style={tabStyle(activeTab === 'last')}
          onClick={() => setActiveTab('last')}
        >
          Last Hole
        </button>
        <button
          role="tab"
          aria-selected={activeTab === 'game'}
          style={tabStyle(activeTab === 'game')}
          onClick={() => setActiveTab('game')}
        >
          Game History
        </button>
      </div>

      <div style={eventListStyle}>
        {events.length === 0 && (
          <div style={{ textAlign: 'center', color: theme.colors.textSecondary }}>
            No events yet
          </div>
        )}
        {events.map((event) => (
          <div key={event.eventId} style={eventItemStyle}>
            <div style={{ fontWeight: theme.typography.bold, marginBottom: theme.spacing[1] }}>
              {event.eventType}
            </div>
            <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
              {event.actor} at {new Date(event.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

BettingHistory.propTypes = {
  eventHistory: PropTypes.shape({
    current: PropTypes.arrayOf(PropTypes.shape({
      type: PropTypes.string,
      actor: PropTypes.string,
      timestamp: PropTypes.string,
    })),
    lastHole: PropTypes.arrayOf(PropTypes.shape({
      type: PropTypes.string,
      actor: PropTypes.string,
      timestamp: PropTypes.string,
    })),
    game: PropTypes.arrayOf(PropTypes.shape({
      type: PropTypes.string,
      actor: PropTypes.string,
      timestamp: PropTypes.string,
    })),
  }).isRequired,
};

export default BettingHistory;
