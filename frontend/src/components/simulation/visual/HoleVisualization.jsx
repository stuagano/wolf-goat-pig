// frontend/src/components/simulation/visual/HoleVisualization.jsx
import React from 'react';
import PropTypes from 'prop-types';

const COLORS = {
  teeBox: '#006400',
  fairway: '#90EE90',
  green: '#00FF00',
  rough: '#D2B48C',
  humanPlayer: '#2196F3',
  computerPlayers: ['#F44336', '#FFC107', '#FF9800']
};

const HoleVisualization = ({ hole, players = [] }) => {
  const SVG_WIDTH = 300;
  const SVG_HEIGHT = 500;

  // Calculate player Y positions based on their distance from tee
  const calculatePlayerPosition = (player, index) => {
    // Default positions if no position data
    const defaultY = 460 - (index * 40); // Space them out from tee

    if (typeof player.position === 'number') {
      // Position 0 = tee (y=475), position = hole yards = green (y=50)
      const maxYards = hole?.yards || 400;
      const progress = player.position / maxYards;
      return 475 - (progress * 425); // Map to SVG y coordinates
    }

    return defaultY;
  };

  return (
    <div style={{ width: '100%', maxWidth: '600px', margin: '0 auto', position: 'relative' }}>
      {/* Info overlay */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        background: 'rgba(255, 255, 255, 0.9)',
        padding: '8px 12px',
        borderRadius: '4px',
        fontSize: '14px',
        fontWeight: 'bold',
        zIndex: 10
      }}>
        Hole {hole?.hole_number || '?'} • Par {hole?.par || '?'}
      </div>

      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        style={{ width: '100%', height: 'auto', display: 'block' }}
        aria-label={`Golf hole ${hole?.hole_number || ''} visualization`}
      >
        {/* Background - Rough */}
        <rect
          width={SVG_WIDTH}
          height={SVG_HEIGHT}
          fill={COLORS.rough}
        />

        {/* Fairway - Light green ellipse */}
        <ellipse
          cx={SVG_WIDTH / 2}
          cy={SVG_HEIGHT / 2}
          rx={80}
          ry={200}
          fill={COLORS.fairway}
        />

        {/* Green - Bright green circle at top */}
        <circle
          cx={SVG_WIDTH / 2}
          cy={50}
          r={40}
          fill={COLORS.green}
        />

        {/* Flagstick */}
        <line
          x1={SVG_WIDTH / 2}
          y1={50}
          x2={SVG_WIDTH / 2}
          y2={30}
          stroke="red"
          strokeWidth={2}
        />
        <circle
          cx={SVG_WIDTH / 2}
          cy={30}
          r={5}
          fill="red"
        />

        {/* Tee Box - Dark green rectangle at bottom */}
        <rect
          x={(SVG_WIDTH / 2) - 30}
          y={460}
          width={60}
          height={30}
          fill={COLORS.teeBox}
        />

        {/* Player dots */}
        {players.map((player, index) => {
          const y = calculatePlayerPosition(player, index);
          const x = SVG_WIDTH / 2 + ((index % 2 === 0 ? 1 : -1) * (15 + index * 5)); // Offset for visibility
          const isHuman = player.is_human || player.id === 'human';
          const color = isHuman
            ? COLORS.humanPlayer
            : COLORS.computerPlayers[index % COLORS.computerPlayers.length];

          return (
            <g key={player.id}>
              <circle
                cx={x}
                cy={y}
                r={8}
                fill={color}
                stroke={isHuman ? 'white' : 'none'}
                strokeWidth={isHuman ? 2 : 0}
              />
              {/* Player name on hover - using title element */}
              <title>{player.name}</title>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

HoleVisualization.propTypes = {
  hole: PropTypes.shape({
    hole_number: PropTypes.number,
    par: PropTypes.number,
    yards: PropTypes.number
  }),
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    is_human: PropTypes.bool,
    position: PropTypes.number
  }))
};

export default HoleVisualization;
