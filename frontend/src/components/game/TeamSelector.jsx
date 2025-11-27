/**
 * TeamSelector - Team mode and player selection component
 *
 * Extracted from SimpleScorekeeper to handle:
 * - Team mode selection (partners vs solo)
 * - Player selection for Team 1 (partners mode)
 * - Captain selection (solo mode)
 * - The Duncan checkbox (solo mode)
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';
import '../../styles/mobile-touch.css';

/**
 * Helper component to display player name with authentication indicator
 */
const PlayerName = ({ name, isAuthenticated }) => (
  <>
    {name}
    {isAuthenticated && <span style={{ marginLeft: '4px', fontSize: '12px' }}>🔒</span>}
  </>
);

PlayerName.propTypes = {
  name: PropTypes.string.isRequired,
  isAuthenticated: PropTypes.bool,
};

/**
 * TeamSelector Component
 *
 * @param {Object} props
 * @param {Array} props.players - Array of player objects
 * @param {string} props.teamMode - Current team mode ('partners' or 'solo')
 * @param {Function} props.onTeamModeChange - Callback when team mode changes
 * @param {Array} props.team1 - Array of player IDs in team 1
 * @param {Function} props.onTeam1Change - Callback when team 1 changes
 * @param {string} props.captain - Captain player ID (solo mode)
 * @param {Function} props.onCaptainChange - Callback when captain changes
 * @param {boolean} props.duncanInvoked - Whether The Duncan is invoked
 * @param {Function} props.onDuncanChange - Callback when Duncan is toggled
 * @param {boolean} props.disabled - Disable all inputs
 */
const TeamSelector = ({
  players,
  teamMode,
  onTeamModeChange,
  team1,
  onTeam1Change,
  captain,
  onCaptainChange,
  duncanInvoked = false,
  onDuncanChange,
  disabled = false
}) => {
  const theme = useTheme();

  // Toggle player in/out of Team 1
  const togglePlayerTeam = (playerId) => {
    if (disabled) return;

    if (team1.includes(playerId)) {
      onTeam1Change(team1.filter(id => id !== playerId));
    } else {
      onTeam1Change([...team1, playerId]);
    }
  };

  // Toggle captain selection
  const toggleCaptain = (playerId) => {
    if (disabled) return;

    if (captain === playerId) {
      onCaptainChange(null);
    } else {
      onCaptainChange(playerId);
    }
  };

  return (
    <>
      {/* Team Mode Selection */}
      <div style={{
        background: theme.colors.paper,
        padding: '20px',
        borderRadius: '16px',
        marginBottom: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{
          margin: '0 0 16px',
          fontSize: '20px',
          fontWeight: 'bold',
          color: theme.colors.textPrimary
        }}>
          Team Mode
        </h3>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => !disabled && onTeamModeChange('partners')}
            disabled={disabled}
            className="touch-optimized"
            style={{
              flex: 1,
              padding: '16px',
              fontSize: '18px',
              fontWeight: 'bold',
              border: teamMode === 'partners' ? `3px solid ${theme.colors.primary}` : `2px solid ${theme.colors.border}`,
              borderRadius: '12px',
              background: teamMode === 'partners' ? theme.colors.primary : 'white',
              color: teamMode === 'partners' ? 'white' : theme.colors.textPrimary,
              cursor: disabled ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              boxShadow: teamMode === 'partners' ? '0 4px 6px rgba(0,0,0,0.2)' : 'none',
              opacity: disabled ? 0.5 : 1
            }}
          >
            Partners
          </button>
          <button
            data-testid="go-solo-button"
            onClick={() => !disabled && onTeamModeChange('solo')}
            disabled={disabled}
            className="touch-optimized"
            style={{
              flex: 1,
              padding: '16px',
              fontSize: '18px',
              fontWeight: 'bold',
              border: teamMode === 'solo' ? `3px solid ${theme.colors.primary}` : `2px solid ${theme.colors.border}`,
              borderRadius: '12px',
              background: teamMode === 'solo' ? theme.colors.primary : 'white',
              color: teamMode === 'solo' ? 'white' : theme.colors.textPrimary,
              cursor: disabled ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              boxShadow: teamMode === 'solo' ? '0 4px 6px rgba(0,0,0,0.2)' : 'none',
              opacity: disabled ? 0.5 : 1
            }}
          >
            Solo
          </button>
        </div>

        {/* The Duncan checkbox - only shown in Solo mode */}
        {teamMode === 'solo' && onDuncanChange && (
          <div style={{
            marginTop: '12px',
            padding: '12px',
            background: '#F3E5F5',
            borderRadius: '8px',
            border: '2px solid #9C27B0'
          }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: disabled ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 'bold',
              color: '#6A1B9A',
              opacity: disabled ? 0.5 : 1
            }}>
              <input
                type="checkbox"
                checked={duncanInvoked}
                onChange={(e) => !disabled && onDuncanChange(e.target.checked)}
                disabled={disabled}
                style={{ width: '18px', height: '18px', cursor: disabled ? 'not-allowed' : 'pointer' }}
              />
              <span>The Duncan (Captain goes solo before hitting - 3-for-2 payout)</span>
            </label>
          </div>
        )}
      </div>

      {/* Player Selection */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 8px' }}>
          {teamMode === 'partners' ? 'Select Team 1' : 'Select Captain'}
        </h3>

        {teamMode === 'partners' && (
          <p style={{
            margin: '0 0 12px',
            fontSize: '14px',
            color: theme.colors.textSecondary,
            fontStyle: 'italic'
          }}>
            Click players to add them to Team 1. Remaining players will automatically be Team 2.
          </p>
        )}

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '12px'
        }}>
          {teamMode === 'partners' ? (
            players.map(player => {
              const inTeam1 = team1.includes(player.id);
              const inTeam2 = !inTeam1;

              return (
                <button
                  key={player.id}
                  data-testid={`partner-${player.id}`}
                  onClick={() => togglePlayerTeam(player.id)}
                  disabled={disabled}
                  style={{
                    padding: '12px',
                    fontSize: '16px',
                    border: inTeam1 ? `3px solid #00bcd4` : `2px solid ${theme.colors.border}`,
                    borderRadius: '8px',
                    background: inTeam1 ? 'rgba(0, 188, 212, 0.1)' : inTeam2 ? 'rgba(255, 152, 0, 0.05)' : 'white',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    opacity: disabled ? 0.5 : (inTeam2 ? 0.8 : 1)
                  }}
                >
                  <PlayerName name={player.name} isAuthenticated={player.is_authenticated} />
                  {inTeam1 && ' (Team 1)'}
                  {inTeam2 && ' (Team 2)'}
                </button>
              );
            })
          ) : (
            players.map(player => {
              const isCaptain = captain === player.id;

              return (
                <button
                  key={player.id}
                  data-testid={`partner-${player.id}`}
                  onClick={() => toggleCaptain(player.id)}
                  disabled={disabled}
                  style={{
                    padding: '12px',
                    fontSize: '16px',
                    border: isCaptain ? `3px solid #ffc107` : `2px solid ${theme.colors.border}`,
                    borderRadius: '8px',
                    background: isCaptain ? 'rgba(255, 193, 7, 0.1)' : 'white',
                    cursor: disabled ? 'not-allowed' : 'pointer',
                    opacity: disabled ? 0.5 : 1
                  }}
                >
                  {isCaptain && '⭐ '}
                  <PlayerName name={player.name} isAuthenticated={player.is_authenticated} />
                </button>
              );
            })
          )}
        </div>
      </div>
    </>
  );
};

TeamSelector.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    is_authenticated: PropTypes.bool
  })).isRequired,
  teamMode: PropTypes.oneOf(['partners', 'solo']).isRequired,
  onTeamModeChange: PropTypes.func.isRequired,
  team1: PropTypes.arrayOf(PropTypes.string).isRequired,
  onTeam1Change: PropTypes.func.isRequired,
  captain: PropTypes.string,
  onCaptainChange: PropTypes.func.isRequired,
  duncanInvoked: PropTypes.bool,
  onDuncanChange: PropTypes.func,
  disabled: PropTypes.bool
};

export default TeamSelector;
