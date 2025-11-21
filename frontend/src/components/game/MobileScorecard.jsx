// frontend/src/components/game/MobileScorecard.jsx
import React from 'react';
import { useTheme } from '../../theme/Provider';
import '../../styles/mobile-touch.css';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Mobile-optimized scorecard for game managers
 * Replaces traditional paper scorecard with easy-to-read digital version
 * Optimized for glove-friendly touch interaction on phones
 */
const MobileScorecard = ({ gameState }) => {
  const theme = useTheme();
  const [isMinimized, setIsMinimized] = React.useState(false);
  const [courseData, setCourseData] = React.useState(null);
  const [courseDataLoading, setCourseDataLoading] = React.useState(true);

  // Fetch course data to get hole par information
  React.useEffect(() => {
    // Guard against missing gameState
    if (!gameState || !gameState.course_name) return;

    const fetchCourseData = async () => {
      setCourseDataLoading(true);
      try {
        const courseName = gameState.course_name;
        if (courseName) {
          const courseResponse = await fetch(`${API_URL}/courses`);
          if (courseResponse.ok) {
            const coursesData = await courseResponse.json();
            const course = coursesData[courseName];
            if (course) {
              setCourseData(course);
            } else {
              console.warn(`Course "${courseName}" not found in courses data`);
            }
          }
        }
      } catch (err) {
        console.error('Error fetching course data:', err);
      } finally {
        setCourseDataLoading(false);
      }
    };

    fetchCourseData();
  }, [gameState?.course_name]);

  if (!gameState || !gameState.players) return null;

  // Calculate current standings (total quarters/points won)
  const getCurrentStandings = () => {
    return gameState.players
      .map(player => ({
        ...player,
        quarters: player.points || 0
      }))
      .sort((a, b) => b.quarters - a.quarters);
  };

  const standings = getCurrentStandings();
  const currentHole = gameState.current_hole || 1;

  // Get current hole par from course database ONLY - no defaults
  const currentHolePar = courseData?.holes?.find(h => h.hole_number === currentHole)?.par;

  // Render compact standings view (default for game manager)
  const renderStandingsView = () => (
    <div>
      {/* Current Hole Banner */}
      <div style={{
        background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.accent})`,
        color: 'white',
        padding: '20px',
        borderRadius: '16px 16px 0 0',
        textAlign: 'center',
        marginBottom: '2px'
      }}>
        <div style={{ fontSize: '18px', marginBottom: '8px', opacity: 0.9 }}>
          Current Hole
        </div>
        <div style={{ fontSize: '48px', fontWeight: 'bold', lineHeight: 1 }}>
          {currentHole}
        </div>
        <div style={{ fontSize: '16px', marginTop: '8px', opacity: 0.9 }}>
          {courseDataLoading ? '⏳ Loading...' : currentHolePar ? `Par ${currentHolePar}` : 'Par -'}
        </div>
      </div>

      {/* Current Hole Partnerships/Teams */}
      {gameState.teams && gameState.teams.type && gameState.teams.type !== 'pending' && (
        <div style={{
          background: theme.colors.paper,
          padding: '20px',
          borderBottom: `3px solid ${theme.colors.border}`,
          marginBottom: '2px'
        }}>
          <div style={{
            fontSize: '16px',
            fontWeight: 'bold',
            color: theme.colors.textPrimary,
            marginBottom: '12px',
            textAlign: 'center'
          }}>
            Current Hole Teams
          </div>

          {gameState.teams.type === 'partners' && (
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              {/* Team 1 */}
              <div style={{
                flex: 1,
                padding: '16px',
                background: 'rgba(0, 188, 212, 0.1)',
                border: '2px solid #00bcd4',
                borderRadius: '12px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '14px', color: '#00bcd4', fontWeight: 'bold', marginBottom: '8px' }}>
                  TEAM 1
                </div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
                  {gameState.players?.find(p => p.id === gameState.teams.team1[0])?.name}
                </div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
                  {gameState.players?.find(p => p.id === gameState.teams.team1[1])?.name}
                </div>
              </div>

              {/* VS */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                fontSize: '20px',
                fontWeight: 'bold',
                color: theme.colors.textSecondary
              }}>
                VS
              </div>

              {/* Team 2 */}
              <div style={{
                flex: 1,
                padding: '16px',
                background: 'rgba(255, 152, 0, 0.1)',
                border: '2px solid #ff9800',
                borderRadius: '12px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '14px', color: '#ff9800', fontWeight: 'bold', marginBottom: '8px' }}>
                  TEAM 2
                </div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
                  {gameState.players?.find(p => p.id === gameState.teams.team2[0])?.name}
                </div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
                  {gameState.players?.find(p => p.id === gameState.teams.team2[1])?.name}
                </div>
              </div>
            </div>
          )}

          {gameState.teams.type === 'solo' && (
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              {/* Solo Captain */}
              <div style={{
                flex: 1,
                padding: '16px',
                background: 'rgba(255, 193, 7, 0.1)',
                border: '2px solid #ffc107',
                borderRadius: '12px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '14px', color: '#ffc107', fontWeight: 'bold', marginBottom: '8px' }}>
                  CAPTAIN (SOLO)
                </div>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
                  ⭐ {gameState.players?.find(p => p.id === gameState.teams.captain)?.name}
                </div>
              </div>

              {/* VS */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                fontSize: '20px',
                fontWeight: 'bold',
                color: theme.colors.textSecondary
              }}>
                VS
              </div>

              {/* Opponents */}
              <div style={{
                flex: 1,
                padding: '16px',
                background: 'rgba(156, 39, 176, 0.1)',
                border: '2px solid #9c27b0',
                borderRadius: '12px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '14px', color: '#9c27b0', fontWeight: 'bold', marginBottom: '8px' }}>
                  OPPONENTS
                </div>
                {gameState.teams.opponents?.map(oppId => (
                  <div key={oppId} style={{ fontSize: '18px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
                    {gameState.players?.find(p => p.id === oppId)?.name}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Player Standings */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '0 0 16px 16px',
        overflow: 'hidden'
      }}>
        <div style={{
          padding: '16px 20px',
          background: theme.colors.backgroundSecondary,
          borderBottom: `3px solid ${theme.colors.border}`,
          fontSize: '18px',
          fontWeight: 'bold',
          color: theme.colors.textPrimary
        }}>
          Current Standings
        </div>

        {standings.map((player, index) => {
          const isLeader = index === 0 && player.quarters > 0;
          const isLast = index === standings.length - 1 && player.quarters < 0;

          return (
            <div
              key={player.id}
              className="touch-optimized"
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '20px',
                borderBottom: index < standings.length - 1 ? `2px solid ${theme.colors.border}` : 'none',
                background: isLeader ? 'rgba(76, 175, 80, 0.1)' :
                           isLast ? 'rgba(244, 67, 54, 0.1)' :
                           'white'
              }}
            >
              {/* Position & Name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: isLeader ? '#4CAF50' :
                             isLast ? '#f44336' :
                             theme.colors.backgroundSecondary,
                  color: isLeader || isLast ? 'white' : theme.colors.textSecondary,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '18px',
                  fontWeight: 'bold'
                }}>
                  {index + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '22px',
                    fontWeight: 'bold',
                    color: theme.colors.textPrimary
                  }}>
                    {player.name}
                  </div>
                  <div style={{
                    fontSize: '14px',
                    color: theme.colors.textSecondary,
                    marginTop: '2px'
                  }}>
                    Handicap {player.handicap}
                  </div>
                </div>
              </div>

              {/* Quarters/Points */}
              <div style={{
                fontSize: '32px',
                fontWeight: 'bold',
                color: player.quarters > 0 ? '#4CAF50' :
                       player.quarters < 0 ? '#f44336' :
                       theme.colors.textSecondary,
                minWidth: '100px',
                textAlign: 'right'
              }}>
                {player.quarters > 0 ? '+' : ''}{player.quarters}
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Stats */}
      <div style={{
        marginTop: '16px',
        padding: '20px',
        background: theme.colors.paper,
        borderRadius: '16px',
        border: `2px solid ${theme.colors.border}`
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '16px'
        }}>
          <div>
            <div style={{
              fontSize: '14px',
              color: theme.colors.textSecondary,
              marginBottom: '4px'
            }}>
              Base Wager
            </div>
            <div style={{
              fontSize: '24px',
              fontWeight: 'bold',
              color: theme.colors.primary
            }}>
              {gameState.base_wager || 1}Q
            </div>
          </div>
          <div>
            <div style={{
              fontSize: '14px',
              color: theme.colors.textSecondary,
              marginBottom: '4px'
            }}>
              Current Wager
            </div>
            <div style={{
              fontSize: '24px',
              fontWeight: 'bold',
              color: gameState.current_wager > gameState.base_wager ?
                theme.colors.warning : theme.colors.primary
            }}>
              {gameState.current_wager || gameState.base_wager || 1}Q
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="touch-optimized" style={{
      background: theme.colors.background,
      borderRadius: '16px',
      overflow: 'hidden',
      marginBottom: '8px'
    }}>
      {/* Minimize/Expand Toggle Button */}
      <button
        onClick={() => setIsMinimized(!isMinimized)}
        style={{
          width: '100%',
          padding: '12px 20px',
          background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.accent})`,
          color: 'white',
          border: 'none',
          borderRadius: isMinimized ? '16px' : '16px 16px 0 0',
          fontSize: '16px',
          fontWeight: 'bold',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
          touchAction: 'manipulation'
        }}
        className="touch-optimized"
      >
        <span>📊 Scorecard</span>
        <span style={{ fontSize: '20px' }}>{isMinimized ? '▼' : '▲'}</span>
      </button>

      {/* Scorecard Content - only show when not minimized */}
      {!isMinimized && renderStandingsView()}
    </div>
  );
};

export default MobileScorecard;
