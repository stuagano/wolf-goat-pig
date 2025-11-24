// frontend/src/components/game/GameCompletionView.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';

/**
 * Game completion view shown after all 18 holes are played
 * Displays final standings and game summary
 */
const GameCompletionView = ({ players, playerStandings, holeHistory, onNewGame }) => {
  const theme = useTheme();

  // Sort players by quarters (highest first)
  const sortedStandings = Object.values(playerStandings)
    .sort((a, b) => b.quarters - a.quarters);

  // Determine winner(s)
  const highestQuarters = sortedStandings[0]?.quarters || 0;
  const winners = sortedStandings.filter(p => p.quarters === highestQuarters);

  // Calculate total strokes for each player
  const totalStrokes = {};
  players.forEach(player => {
    totalStrokes[player.id] = holeHistory.reduce((sum, hole) => {
      return sum + (hole.gross_scores?.[player.id] || 0);
    }, 0);
  });

  return (
    <div style={{
      padding: '32px',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      {/* Winner Announcement */}
      <div
        data-testid="game-status"
        style={{
          textAlign: 'center',
          marginBottom: '32px',
          padding: '32px',
          borderRadius: '16px',
          background: 'linear-gradient(135deg, #ffd700 0%, #ffed4e 100%)',
          border: '4px solid #4CAF50',
          boxShadow: '0 8px 16px rgba(0,0,0,0.2)'
        }}
      >
        <div style={{ fontSize: '64px', marginBottom: '16px' }}>
          🏆
        </div>
        <h1 style={{
          fontSize: '36px',
          marginBottom: '12px',
          color: '#333',
          fontWeight: 'bold'
        }}>
          Game Complete!
        </h1>
        {winners.length === 1 ? (
          <p style={{ fontSize: '24px', marginBottom: '0', color: '#333' }}>
            <strong>{winners[0].name}</strong> wins with {highestQuarters > 0 ? '+' : ''}{highestQuarters} quarters!
          </p>
        ) : (
          <p style={{ fontSize: '24px', marginBottom: '0', color: '#333' }}>
            Tie between {winners.map(w => w.name).join(' and ')} with {highestQuarters > 0 ? '+' : ''}{highestQuarters} quarters!
          </p>
        )}
      </div>

      {/* Final Standings */}
      <div
        data-testid="final-standings"
        style={{
          background: theme.colors.paper,
          borderRadius: '16px',
          overflow: 'hidden',
          marginBottom: '24px',
          boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
        }}
      >
        <div style={{
          padding: '20px',
          background: theme.colors.primary,
          color: 'white',
          fontSize: '24px',
          fontWeight: 'bold'
        }}>
          Final Standings
        </div>

        {/* Table Header */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '60px 1fr 120px 120px',
          padding: '16px 20px',
          background: theme.colors.backgroundSecondary,
          borderBottom: `2px solid ${theme.colors.border}`,
          fontWeight: 'bold',
          fontSize: '14px',
          color: theme.colors.textSecondary
        }}>
          <div>RANK</div>
          <div>PLAYER</div>
          <div style={{ textAlign: 'right' }}>STROKES</div>
          <div style={{ textAlign: 'right' }}>QUARTERS</div>
        </div>

        {/* Player Rows */}
        {sortedStandings.map((standing, index) => {
          const player = players.find(p => p.name === standing.name);
          const playerId = player?.id;
          const isWinner = standing.quarters === highestQuarters;
          const strokes = totalStrokes[playerId] || 0;

          return (
            <div
              key={standing.name}
              data-testid="player-standing-row"
              style={{
                display: 'grid',
                gridTemplateColumns: '60px 1fr 120px 120px',
                padding: '20px',
                background: isWinner ? 'rgba(76, 175, 80, 0.1)' : (index % 2 === 0 ? 'white' : '#f9f9f9'),
                borderBottom: index < sortedStandings.length - 1 ? `1px solid ${theme.colors.border}` : 'none'
              }}
            >
              <div style={{
                fontSize: '24px',
                fontWeight: 'bold',
                color: theme.colors.textSecondary
              }}>
                {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`}
              </div>
              <div>
                <div
                  data-testid="player-name"
                  style={{
                    fontSize: '20px',
                    fontWeight: isWinner ? 'bold' : '600',
                    color: theme.colors.textPrimary,
                    marginBottom: '4px'
                  }}
                >
                  {standing.name}
                </div>
                <div style={{
                  fontSize: '12px',
                  color: theme.colors.textSecondary
                }}>
                  Solo: {standing.soloCount || 0} | Float: {standing.floatCount || 0} | Option: {standing.optionCount || 0}
                </div>
              </div>
              <div style={{
                textAlign: 'right',
                fontSize: '18px',
                fontWeight: '600',
                color: theme.colors.textSecondary
              }}>
                {strokes}
              </div>
              <div
                data-testid="player-total-points"
                style={{
                  textAlign: 'right',
                  fontSize: '24px',
                  fontWeight: 'bold',
                  color: standing.quarters > 0 ? '#4CAF50' : standing.quarters < 0 ? '#f44336' : theme.colors.textSecondary
                }}
              >
                {standing.quarters > 0 ? '+' : ''}{standing.quarters}Q
              </div>
            </div>
          );
        })}
      </div>

      {/* Game Statistics */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{
          margin: '0 0 16px',
          fontSize: '20px',
          color: theme.colors.primary
        }}>
          Game Statistics
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '16px'
        }}>
          <div style={{
            padding: '16px',
            background: '#e3f2fd',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
              Holes Played
            </div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '4px', color: theme.colors.primary }}>
              18
            </div>
          </div>

          <div style={{
            padding: '16px',
            background: '#f3e5f5',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
              Total Players
            </div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '4px', color: '#9C27B0' }}>
              {players.length}
            </div>
          </div>

          <div style={{
            padding: '16px',
            background: '#fff3e0',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
              Winning Margin
            </div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '4px', color: '#FF9800' }}>
              {sortedStandings.length > 1
                ? `${Math.abs(sortedStandings[0].quarters - sortedStandings[1].quarters)}Q`
                : 'N/A'
              }
            </div>
          </div>

          <div style={{
            padding: '16px',
            background: '#e8f5e9',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
              Solo Holes
            </div>
            <div style={{ fontSize: '28px', fontWeight: 'bold', marginTop: '4px', color: '#4CAF50' }}>
              {holeHistory.filter(h => h.teams?.type === 'solo').length}
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{
        display: 'flex',
        gap: '16px',
        justifyContent: 'center'
      }}>
        {onNewGame && (
          <button
            onClick={onNewGame}
            style={{
              padding: '16px 32px',
              fontSize: '18px',
              fontWeight: 'bold',
              borderRadius: '8px',
              border: 'none',
              background: theme.colors.primary,
              color: 'white',
              cursor: 'pointer',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 12px rgba(0,0,0,0.15)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
            }}
          >
            Start New Game
          </button>
        )}
        <button
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          style={{
            padding: '16px 32px',
            fontSize: '18px',
            fontWeight: 'bold',
            borderRadius: '8px',
            border: `2px solid ${theme.colors.border}`,
            background: 'white',
            color: theme.colors.textPrimary,
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          onMouseOver={(e) => {
            e.target.style.background = theme.colors.backgroundSecondary;
          }}
          onMouseOut={(e) => {
            e.target.style.background = 'white';
          }}
        >
          View Scorecard
        </button>
      </div>
    </div>
  );
};

GameCompletionView.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
  })).isRequired,
  playerStandings: PropTypes.objectOf(PropTypes.shape({
    quarters: PropTypes.number.isRequired,
    id: PropTypes.string,
    name: PropTypes.string,
  })).isRequired,
  holeHistory: PropTypes.arrayOf(PropTypes.shape({
    gross_scores: PropTypes.objectOf(PropTypes.number),
  })).isRequired,
  onNewGame: PropTypes.func.isRequired,
};

export default GameCompletionView;
