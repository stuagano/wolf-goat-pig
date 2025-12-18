import React from 'react';
import PropTypes from 'prop-types';
import { UI_COLORS, GOLF_COLORS, getLieColor } from '../constants/colors';

const HoleVisualization = ({ holeState, players, gameState }) => {
  if (!holeState || !players) return null;

  // Get current hole info from game state
  const currentHole = gameState?.current_hole || 1;
  const PAR = holeState.hole_par || gameState?.hole_par || 4;
  const YARDAGE = holeState.hole_yardage || gameState?.hole_distance || 400;
  const HANDICAP = holeState.hole_handicap || gameState?.hole_stroke_index || 1;
  const DESCRIPTION = holeState.hole_description || gameState?.hole_description || '';
  
  // Hole dimensions for visualization
  const HOLE_LENGTH = 500; // pixels - increased for better visualization
  const HOLE_WIDTH = 250; // pixels - increased for better spacing

  // Get ball positions or create mock positions for testing
  const ballPositions = holeState.ball_positions || {};
  
  // Create mock data if no real ball positions exist
  const mockPositions = {
    p1: { distance_to_pin: 250, lie_type: 'fairway', holed: false, shot_count: 1 },
    p2: { distance_to_pin: 180, lie_type: 'rough', holed: false, shot_count: 1 },
    p3: { distance_to_pin: 320, lie_type: 'fairway', holed: false, shot_count: 1 },
    p4: { distance_to_pin: 15, lie_type: 'green', holed: false, shot_count: 2 }
  };

  const positions = Object.keys(ballPositions).length > 0 ? ballPositions : mockPositions;
  
  // Find line of scrimmage (furthest from hole)
  const lineOfScrimmage = holeState.line_of_scrimmage || 
    Object.keys(positions).reduce((furthest, playerId) => {
      if (!positions[furthest] || positions[playerId].distance_to_pin > positions[furthest].distance_to_pin) {
        return playerId;
      }
      return furthest;
    }, Object.keys(positions)[0]);

  // Convert distance to pixel position (0 = hole, HOLE_LENGTH = tee)
  const distanceToPixels = (distance) => {
    const maxDistance = Math.max(YARDAGE, 400);
    return HOLE_LENGTH - (distance / maxDistance) * HOLE_LENGTH;
  };

  // Get hole-specific background based on hole characteristics
  const getHoleBackground = (hole, par) => {
    const greenColor = GOLF_COLORS.green;
    const fairwayColor = GOLF_COLORS.fairway;

    // Special holes from Wing Point
    if (hole === 17) {
      // Hole 17 - Par 5 at 455 yards
      return `linear-gradient(to right, ${greenColor} 0%, ${fairwayColor} 15%, ${fairwayColor} 85%, ${greenColor} 100%)`;
    } else if (hole === 18) {
      // Hole 18 - Par 4 finishing hole at 372 yards
      return `linear-gradient(to right, ${greenColor} 0%, ${fairwayColor} 20%, ${fairwayColor} 80%, ${greenColor} 100%)`;
    } else if ([2, 4, 10, 12].includes(hole)) {
      // Par 3s
      return `linear-gradient(to right, ${greenColor} 0%, ${fairwayColor} 30%, ${greenColor} 100%)`;
    } else if (par === 5) {
      // Par 5s
      return `linear-gradient(to right, ${greenColor} 0%, ${fairwayColor} 15%, ${fairwayColor} 85%, ${greenColor} 100%)`;
    } else {
      // Default par 4
      return `linear-gradient(to right, ${greenColor} 0%, ${fairwayColor} 20%, ${fairwayColor} 80%, ${greenColor} 100%)`;
    }
  };

  // Get player colors
  const getPlayerColor = (playerId, index) => {
    const colors = [UI_COLORS.accent, UI_COLORS.success, UI_COLORS.warning, UI_COLORS.purple, UI_COLORS.error, UI_COLORS.gold];
    return colors[index % colors.length];
  };

  // Render hazards for specific holes
  const renderHazards = (hole) => {
    const hazards = [];
    
    // Add water hazards for specific holes
    if (hole === 12) {
      // Hole 12 - "Over Water" par 3
      hazards.push(
        <div key="water-12" style={{
          position: 'absolute',
          left: '60px',
          top: '40%',
          width: '80px',
          height: '40%',
          backgroundColor: GOLF_COLORS.waterLight,
          border: `2px solid ${GOLF_COLORS.water}`,
          borderRadius: '20px',
          zIndex: 0
        }}>
          <div style={{ textAlign: 'center', color: 'white', fontSize: '10px', marginTop: '10px' }}>Water</div>
        </div>
      );
    }
    
    // Add bunkers for difficult holes
    if ([3, 11, 16].includes(hole)) {
      hazards.push(
        <div key="bunker-1" style={{
          position: 'absolute',
          left: '120px',
          top: '30%',
          width: '30px',
          height: '25px',
          backgroundColor: GOLF_COLORS.bunker,
          borderRadius: '50%',
          border: `1px solid ${GOLF_COLORS.sandTrap}`,
          zIndex: 0
        }} />
      );
    }
    
    return hazards;
  };

  // Get strategic advice based on hole
  const getHoleStrategy = (hole, handicap) => {
    let strategy = '';
    
    // Special holes from Wing Point
    if (hole === 13) {
      strategy = 'Easiest hole (Handicap 18) - Attack aggressively! Vinnie\'s Variation starts here.';
    } else if (hole === 3) {
      strategy = 'Toughest hole (Handicap 1) - Play conservatively, avoid big numbers.';
    } else if (hole === 17) {
      strategy = 'Start of Hoepfinger phase - Par 5, reachable in two for long hitters.';
    } else if (hole === 18) {
      strategy = 'The Finale - Strong par 4 finish, Big Dick opportunity for aggressive play!';
    } else if ([5, 7, 13, 18].includes(hole)) {
      strategy = 'Risk/Reward hole - Consider aggressive play for betting opportunities.';
    } else if (handicap <= 4) {
      strategy = 'Difficult hole - Play smart, par is a good score.';
    } else if (handicap >= 15) {
      strategy = 'Scoring opportunity - Be aggressive with partnerships.';
    }
    
    return strategy ? (
      <>
        <br />
        • <strong>Wing Point Strategy:</strong> {strategy}
      </>
    ) : null;
  };

  return (
    <div style={{
      backgroundColor: 'white',
      padding: '20px',
      borderRadius: '12px',
      marginBottom: '20px',
      border: `2px solid ${UI_COLORS.accent}`,
      boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
    }}>
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ color: UI_COLORS.primary, marginTop: 0, marginBottom: '12px', textAlign: 'center' }}>
          🏌️ Wing Point Golf & Country Club - Hole {currentHole}
        </h3>
        <div style={{ textAlign: 'center', color: UI_COLORS.textSecondary, fontSize: '14px', marginBottom: '8px' }}>
          Par {PAR} • {YARDAGE} yards • Handicap {HANDICAP}
        </div>
        {DESCRIPTION && (
          <div style={{
            textAlign: 'center',
            color: UI_COLORS.textSecondary,
            fontSize: '12px',
            fontStyle: 'italic',
            padding: '8px 20px',
            backgroundColor: UI_COLORS.bg,
            borderRadius: '4px',
            margin: '0 auto',
            maxWidth: '500px'
          }}>
            {DESCRIPTION}
          </div>
        )}
      </div>

      {/* Hole Layout */}
      <div style={{
        position: 'relative',
        width: `${HOLE_LENGTH}px`,
        height: `${HOLE_WIDTH}px`,
        margin: '0 auto',
        background: getHoleBackground(currentHole, PAR),
        borderRadius: '8px',
        border: `2px solid ${GOLF_COLORS.rough}`,
        overflow: 'visible',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
      }}>
        
        {/* Tee Box */}
        <div style={{
          position: 'absolute',
          right: '-5px',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '30px',
          height: '60px',
          backgroundColor: GOLF_COLORS.teeBox,
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '12px',
          fontWeight: 'bold'
        }}>
          TEE
        </div>

        {/* Pin/Hole */}
        <div style={{
          position: 'absolute',
          left: '10px',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '20px',
          height: '20px',
          backgroundColor: GOLF_COLORS.hole,
          borderRadius: '50%',
          border: '3px solid white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px'
        }}>
          ⛳
        </div>

        {/* Green Circle */}
        <div style={{
          position: 'absolute',
          left: '5px',
          top: '50%',
          transform: 'translateY(-50%)',
          width: '80px',
          height: '80px',
          backgroundColor: 'rgba(0, 100, 0, 0.3)',
          borderRadius: '50%',
          border: `2px dashed ${GOLF_COLORS.green}`,
          pointerEvents: 'none'
        }} />

        {/* Line of Scrimmage */}
        {lineOfScrimmage && positions[lineOfScrimmage] && (
          <div style={{
            position: 'absolute',
            left: `${distanceToPixels(positions[lineOfScrimmage].distance_to_pin)}px`,
            top: '0',
            width: '2px',
            height: '100%',
            backgroundColor: GOLF_COLORS.lineOfScrimmage,
            opacity: 0.8,
            zIndex: 1
          }}>
            <div style={{
              position: 'absolute',
              top: '-25px',
              left: '-30px',
              backgroundColor: GOLF_COLORS.lineOfScrimmage,
              color: 'white',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '10px',
              fontWeight: 'bold',
              whiteSpace: 'nowrap'
            }}>
              LINE OF SCRIMMAGE
            </div>
          </div>
        )}

        {/* Player Balls */}
        {Object.entries(positions).map(([playerId, position], index) => {
          if (!position) return null;
          
          const player = players.find(p => p.id === playerId) || { name: `Player ${index + 1}`, id: playerId };
          const xPos = distanceToPixels(position.distance_to_pin || 0);
          const yPos = 50 + (index % 2 === 0 ? -30 : 30) + ((index % 4) - 1.5) * 15; // Spread vertically
          const playerColor = getPlayerColor(playerId, index);
          const lieColor = getLieColor(position.lie_type);
          const isLineOfScrimmage = playerId === lineOfScrimmage;

          return (
            <div key={playerId}>
              {/* Ball */}
              <div style={{
                position: 'absolute',
                left: `${xPos - 8}px`,
                top: `${yPos}px`,
                width: '16px',
                height: '16px',
                backgroundColor: position.holed ? '#000' : 'white',
                border: `3px solid ${playerColor}`,
                borderRadius: '50%',
                zIndex: 3,
                boxShadow: isLineOfScrimmage ? `0 0 10px ${GOLF_COLORS.lineOfScrimmage}` : '0 2px 4px rgba(0,0,0,0.3)'
              }} />

              {/* Lie Type Indicator */}
              <div style={{
                position: 'absolute',
                left: `${xPos - 6}px`,
                top: `${yPos + 20}px`,
                width: '12px',
                height: '4px',
                backgroundColor: lieColor,
                borderRadius: '2px',
                zIndex: 2
              }} />

              {/* Player Name Label */}
              <div style={{
                position: 'absolute',
                left: `${xPos - 25}px`,
                top: `${yPos + 28}px`,
                backgroundColor: playerColor,
                color: 'white',
                padding: '2px 6px',
                borderRadius: '10px',
                fontSize: '10px',
                fontWeight: 'bold',
                whiteSpace: 'nowrap',
                zIndex: 4,
                textAlign: 'center',
                minWidth: '50px',
                border: isLineOfScrimmage ? `2px solid ${GOLF_COLORS.lineOfScrimmage}` : 'none'
              }}>
                {player.name}
                <div style={{ fontSize: '8px', opacity: 0.9 }}>
                  {position.holed ? 'HOLED' : `${position.distance_to_pin || 0}yd`}
                </div>
              </div>
            </div>
          );
        })}

        {/* Distance Markers */}
        {[100, 150, 200, 250, 300, 350, 400, 450].map(distance => {
          if (distance >= YARDAGE) return null;
          return (
            <div key={distance} style={{
              position: 'absolute',
              left: `${distanceToPixels(distance)}px`,
              top: '-15px',
              fontSize: '8px',
              color: UI_COLORS.textSecondary,
              fontWeight: 'bold'
            }}>
              {distance}yd
            </div>
          );
        })}

        {/* Hazards for special holes */}
        {renderHazards(currentHole)}
      </div>

      {/* Legend */}
      <div style={{ marginTop: '20px', display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'center', fontSize: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '12px', height: '4px', backgroundColor: GOLF_COLORS.teeBox, borderRadius: '2px' }} />
          <span>Tee</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '12px', height: '4px', backgroundColor: GOLF_COLORS.fairway, borderRadius: '2px' }} />
          <span>Fairway</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '12px', height: '4px', backgroundColor: GOLF_COLORS.rough, borderRadius: '2px' }} />
          <span>Rough</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '12px', height: '4px', backgroundColor: GOLF_COLORS.bunker, borderRadius: '2px' }} />
          <span>Bunker</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '12px', height: '4px', backgroundColor: GOLF_COLORS.green, borderRadius: '2px' }} />
          <span>Green</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '12px', height: '2px', backgroundColor: GOLF_COLORS.lineOfScrimmage }} />
          <span>Line of Scrimmage</span>
        </div>
      </div>

      {/* Strategic Information */}
      <div style={{ marginTop: '15px', padding: '12px', backgroundColor: UI_COLORS.bg, borderRadius: '6px' }}>
        <div style={{ fontWeight: 'bold', color: UI_COLORS.primary, marginBottom: '8px' }}>Strategic Information:</div>
        <div style={{ fontSize: '12px', color: UI_COLORS.textSecondary }}>
          • <strong>Line of Scrimmage:</strong> {lineOfScrimmage ? 
            `${players.find(p => p.id === lineOfScrimmage)?.name || lineOfScrimmage} (${positions[lineOfScrimmage]?.distance_to_pin || 0}yd from pin)` : 
            'Not established'}
          <br />
          • <strong>Betting Restriction:</strong> Players closer to the hole than the line of scrimmage cannot offer doubles
          <br />
          • <strong>Current Wager:</strong> {holeState.betting?.current_wager || 1} quarters
          {getHoleStrategy(currentHole, HANDICAP)}
        </div>
      </div>
    </div>
  );
};

HoleVisualization.propTypes = {
  holeState: PropTypes.shape({
    hole_par: PropTypes.number,
    hole_yardage: PropTypes.number,
    hole_handicap: PropTypes.number,
    hole_description: PropTypes.string,
    betting: PropTypes.shape({
      current_wager: PropTypes.number,
    }),
  }),
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
  })),
  gameState: PropTypes.shape({
    current_hole: PropTypes.number,
    hole_par: PropTypes.number,
    hole_distance: PropTypes.number,
    hole_stroke_index: PropTypes.number,
    hole_description: PropTypes.string,
  }),
};

export default HoleVisualization;