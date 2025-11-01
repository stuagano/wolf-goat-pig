// frontend/src/components/simulation/RoundSummary.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Card, Button } from '../ui';
import { useTheme } from '../../theme/Provider';

const RoundSummary = ({ gameState, onPlayAgain, onExit }) => {
  const theme = useTheme();

  const players = gameState?.players || [];

  // Sort players by points (highest first)
  const sortedPlayers = [...players].sort((a, b) => (b.points || 0) - (a.points || 0));

  // Determine winner(s)
  const highestPoints = sortedPlayers[0]?.points || 0;
  const winners = sortedPlayers.filter(p => p.points === highestPoints);

  return (
    <div style={{
      padding: '32px',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      {/* Winner Announcement */}
      <Card
        variant="success"
        style={{
          textAlign: 'center',
          marginBottom: '24px',
          background: 'linear-gradient(135deg, #ffd700 0%, #ffed4e 100%)',
          border: `4px solid ${theme.colors.success}`
        }}
      >
        <h1 style={{
          fontSize: '48px',
          margin: '16px 0',
          color: '#333'
        }}>
          🏆
        </h1>
        <h2 style={{
          fontSize: '32px',
          marginBottom: '8px',
          color: '#333'
        }}>
          Round Complete!
        </h2>
        {winners.length === 1 ? (
          <p style={{ fontSize: '24px', marginBottom: '16px', color: '#333' }}>
            <strong>{winners[0].name}</strong> wins with {highestPoints} points!
          </p>
        ) : (
          <p style={{ fontSize: '24px', marginBottom: '16px', color: '#333' }}>
            Tie between {winners.map(w => w.name).join(' and ')} with {highestPoints} points!
          </p>
        )}
      </Card>

      {/* Final Scorecard */}
      <Card>
        <h3 style={{
          marginTop: 0,
          marginBottom: '16px',
          fontSize: '24px',
          color: theme.colors.primary
        }}>
          📊 Final Scorecard
        </h3>
        <div style={{
          borderRadius: '8px',
          overflow: 'hidden',
          border: `1px solid ${theme.colors.border}`
        }}>
          {/* Table Header */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '50px 1fr 120px',
            backgroundColor: theme.colors.primary,
            color: 'white',
            padding: '12px 16px',
            fontWeight: 'bold'
          }}>
            <div>Rank</div>
            <div>Player</div>
            <div style={{ textAlign: 'right' }}>Points</div>
          </div>

          {/* Player Rows */}
          {sortedPlayers.map((player, index) => (
            <div
              key={player.id}
              style={{
                display: 'grid',
                gridTemplateColumns: '50px 1fr 120px',
                padding: '12px 16px',
                backgroundColor: index % 2 === 0 ? 'white' : '#f5f5f5',
                borderTop: index > 0 ? `1px solid ${theme.colors.border}` : 'none'
              }}
            >
              <div style={{ fontWeight: 'bold', color: theme.colors.textSecondary }}>
                {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`}
              </div>
              <div style={{ fontWeight: player.points === highestPoints ? 'bold' : 'normal' }}>
                {player.name}
                {player.is_human && ' (You)'}
                <div style={{ fontSize: '12px', color: theme.colors.textSecondary }}>
                  Handicap: {player.handicap}
                </div>
              </div>
              <div style={{
                textAlign: 'right',
                fontSize: '20px',
                fontWeight: 'bold',
                color: player.points === highestPoints ? theme.colors.success : theme.colors.text
              }}>
                {player.points || 0}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Game Stats */}
      <Card style={{ marginTop: '24px' }}>
        <h3 style={{
          marginTop: 0,
          marginBottom: '16px',
          fontSize: '20px',
          color: theme.colors.primary
        }}>
          📈 Round Statistics
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px'
        }}>
          <div style={{
            padding: '12px',
            backgroundColor: '#f0f8ff',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
              Holes Played
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px' }}>
              {gameState?.current_hole || 18}
            </div>
          </div>

          <div style={{
            padding: '12px',
            backgroundColor: '#f0fff4',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
              Total Points Scored
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px' }}>
              {players.reduce((sum, p) => sum + (p.points || 0), 0)}
            </div>
          </div>

          <div style={{
            padding: '12px',
            backgroundColor: '#fff8e1',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
              Players
            </div>
            <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px' }}>
              {players.length}
            </div>
          </div>
        </div>
      </Card>

      {/* Action Buttons */}
      <div style={{
        display: 'flex',
        gap: '16px',
        justifyContent: 'center',
        marginTop: '32px'
      }}>
        {onPlayAgain && (
          <Button
            variant="primary"
            size="large"
            onClick={onPlayAgain}
            style={{ minWidth: '200px' }}
          >
            🔄 Play Another Round
          </Button>
        )}
        {onExit && (
          <Button
            variant="secondary"
            size="large"
            onClick={onExit}
            style={{ minWidth: '200px' }}
          >
            🏠 Exit to Menu
          </Button>
        )}
      </div>
    </div>
  );
};

RoundSummary.propTypes = {
  gameState: PropTypes.shape({
    players: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.string,
      name: PropTypes.string,
      points: PropTypes.number,
      handicap: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
      is_human: PropTypes.bool
    })),
    current_hole: PropTypes.number
  }).isRequired,
  onPlayAgain: PropTypes.func,
  onExit: PropTypes.func
};

export default RoundSummary;
