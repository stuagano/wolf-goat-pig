// frontend/src/components/game/GameCompletionView.jsx
import React, { useState, useRef } from 'react';
import PropTypes from 'prop-types';
import html2canvas from 'html2canvas';
import { useTheme } from '../../theme/Provider';
import Scorecard from './Scorecard';

/**
 * Game completion view shown after all 18 holes are played
 * Displays final standings and game summary
 */
const GameCompletionView = ({ players, playerStandings, holeHistory, onNewGame, onEditScores, onMarkComplete, isCompleted, courseHoles, strokeAllocation }) => {
  const theme = useTheme();
  const [isMarking, setIsMarking] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const scorecardRef = useRef(null);

  // Sort players by quarters (highest first)
  const sortedStandings = Object.values(playerStandings)
    .sort((a, b) => b.quarters - a.quarters);

  // Generate PNG and share scorecard
  const handleShareScorecard = async () => {
    if (!scorecardRef.current) return;

    setIsSharing(true);
    try {
      // Capture the scorecard as canvas
      const canvas = await html2canvas(scorecardRef.current, {
        backgroundColor: '#ffffff',
        scale: 2, // Higher resolution
        useCORS: true,
        logging: false,
      });

      // Convert to blob
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
      const file = new File([blob], 'wolf-scorecard.png', { type: 'image/png' });

      // Try Web Share API with file (works on iOS Safari, etc.)
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: 'Wolf Golf Scorecard',
          text: `Wolf Golf Game - ${new Date().toLocaleDateString()}`
        });
      } else {
        // Fallback: download the image
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `wolf-scorecard-${new Date().toISOString().split('T')[0]}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        alert('Scorecard image downloaded! You can share it from your downloads.');
      }
    } catch (error) {
      console.error('Error sharing scorecard:', error);
      alert('Failed to generate scorecard image. Please try again.');
    } finally {
      setIsSharing(false);
    }
  };

  return (
    <div style={{
      padding: '32px',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      {/* Full Scorecard at Top */}
      <div
        ref={scorecardRef}
        data-testid="final-standings"
        style={{
          background: theme.colors.paper,
          borderRadius: '16px',
          overflow: 'hidden',
          marginBottom: '24px',
          boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
        }}
      >
        <Scorecard
          players={players}
          holeHistory={holeHistory}
          currentHole={19}
          courseHoles={courseHoles || []}
          strokeAllocation={strokeAllocation || {}}
          isEditingCompleteGame={false}
        />
      </div>

      {/* Settlement Summary - Who Owes Whom */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        border: '2px solid #4CAF50'
      }}>
        <h3 style={{
          margin: '0 0 16px',
          fontSize: '20px',
          color: '#4CAF50',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          💰 Settlement
        </h3>
        <div style={{ fontSize: '13px', color: theme.colors.textSecondary, marginBottom: '16px' }}>
          Based on final quarters - positive players collect, negative players pay
        </div>
        {(() => {
          // Calculate settlements: simplify debts so minimum transactions needed
          const standings = [...sortedStandings];
          const winners = standings.filter(p => p.quarters > 0);
          const losers = standings.filter(p => p.quarters < 0);

          if (losers.length === 0 || winners.length === 0) {
            return (
              <div style={{ textAlign: 'center', padding: '20px', color: theme.colors.textSecondary }}>
                No settlements needed - all players broke even!
              </div>
            );
          }

          // Simple settlement: each loser pays proportionally to each winner
          const settlements = [];
          let losersCopy = losers.map(l => ({ ...l, remaining: Math.abs(l.quarters) }));
          let winnersCopy = winners.map(w => ({ ...w, remaining: w.quarters }));

          for (const loser of losersCopy) {
            for (const winner of winnersCopy) {
              if (loser.remaining <= 0 || winner.remaining <= 0) continue;
              const amount = Math.min(loser.remaining, winner.remaining);
              if (amount > 0) {
                settlements.push({
                  from: loser.name,
                  to: winner.name,
                  amount: amount
                });
                loser.remaining -= amount;
                winner.remaining -= amount;
              }
            }
          }

          return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {settlements.map((s, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    background: '#f5f5f5',
                    borderRadius: '8px',
                    fontSize: '16px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontWeight: 'bold', color: '#f44336' }}>{s.from}</span>
                    <span style={{ color: theme.colors.textSecondary }}>→</span>
                    <span style={{ fontWeight: 'bold', color: '#4CAF50' }}>{s.to}</span>
                  </div>
                  <div style={{
                    fontWeight: 'bold',
                    fontSize: '20px',
                    color: theme.colors.textPrimary
                  }}>
                    {s.amount}Q
                  </div>
                </div>
              ))}
            </div>
          );
        })()}
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
        justifyContent: 'center',
        flexWrap: 'wrap'
      }}>
        {onEditScores && (
          <button
            onClick={onEditScores}
            style={{
              padding: '16px 32px',
              fontSize: '18px',
              fontWeight: 'bold',
              borderRadius: '8px',
              border: 'none',
              background: '#ff9800',
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
            Edit Scores
          </button>
        )}
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
        {onMarkComplete && !isCompleted && (
          <button
            onClick={async () => {
              setIsMarking(true);
              try {
                await onMarkComplete();
              } finally {
                setIsMarking(false);
              }
            }}
            disabled={isMarking}
            style={{
              padding: '16px 32px',
              fontSize: '18px',
              fontWeight: 'bold',
              borderRadius: '8px',
              border: 'none',
              background: isMarking ? '#9e9e9e' : '#4CAF50',
              color: 'white',
              cursor: isMarking ? 'not-allowed' : 'pointer',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              if (!isMarking) {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 12px rgba(0,0,0,0.15)';
              }
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
            }}
          >
            {isMarking ? 'Saving...' : 'Save & Complete Game'}
          </button>
        )}
        {isCompleted && (
          <div style={{
            padding: '16px 32px',
            fontSize: '18px',
            fontWeight: 'bold',
            borderRadius: '8px',
            background: '#e8f5e9',
            color: '#2e7d32',
            border: '2px solid #4CAF50'
          }}>
            Game Saved
          </div>
        )}
        {/* Share Scorecard as Image */}
        <button
          onClick={handleShareScorecard}
          disabled={isSharing}
          style={{
            padding: '16px 32px',
            fontSize: '18px',
            fontWeight: 'bold',
            borderRadius: '8px',
            border: `2px solid ${theme.colors.primary}`,
            background: isSharing ? theme.colors.backgroundSecondary : 'white',
            color: theme.colors.primary,
            cursor: isSharing ? 'wait' : 'pointer',
            transition: 'all 0.2s',
            opacity: isSharing ? 0.7 : 1
          }}
          onMouseOver={(e) => {
            if (!isSharing) e.target.style.background = theme.colors.backgroundSecondary;
          }}
          onMouseOut={(e) => {
            if (!isSharing) e.target.style.background = 'white';
          }}
        >
          {isSharing ? '📸 Generating...' : '📤 Share Scorecard'}
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
  onEditScores: PropTypes.func,
  onMarkComplete: PropTypes.func,
  isCompleted: PropTypes.bool,
  courseHoles: PropTypes.array,
  strokeAllocation: PropTypes.object,
};

export default GameCompletionView;
