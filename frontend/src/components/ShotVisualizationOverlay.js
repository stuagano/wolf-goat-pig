import React from 'react';
import { useTheme } from '../theme/Provider';

/**
 * Shot Visualization Overlay Component
 * Provides visual indicators for shot recommendations on hole visualization
 */
const ShotVisualizationOverlay = ({ 
  analysis, 
  holeState, 
  currentPlayer,
  showTargetZones = true,
  showRiskAreas = true,
  showOptimalPath = true 
}) => {
  const theme = useTheme();

  if (!analysis || !holeState || !currentPlayer) {
    return null;
  }

  const ballPosition = holeState.ball_positions[currentPlayer.id];
  if (!ballPosition) return null;

  // Calculate dimensions and positions (simplified for demo)
  const holeLength = 400; // Base length for visualization
  const holeWidth = 200;  // Base width for visualization
  
  // Convert real distances to visualization coordinates
  const scaleX = holeLength / (holeState.hole_distance || 400);
  const scaleY = holeWidth / 60; // Assume 60 yard width
  
  const playerX = (ballPosition.distance_to_pin / (holeState.hole_distance || 400)) * holeLength;
  const playerY = holeWidth / 2; // Center for simplicity
  const pinX = holeLength - 20; // Pin near the end
  const pinY = holeWidth / 2;

  // Risk zone colors
  const getRiskZoneColor = (riskLevel) => {
    if (riskLevel <= 30) return `${theme.colors.success}40`; // Green with transparency
    if (riskLevel <= 60) return `${theme.colors.warning}40`; // Yellow with transparency
    return `${theme.colors.error}40`; // Red with transparency
  };

  // Generate target zones based on analysis
  const generateTargetZones = () => {
    if (!analysis.all_ranges) return [];
    
    return analysis.all_ranges.slice(0, 3).map((range, index) => {
      const riskNum = parseInt(range.risk);
      const angle = (index - 1) * 20; // Spread zones around target line
      const distance = Math.min(parseInt(range.success_rate) * 2, 150); // Distance based on success rate
      
      return {
        id: index,
        type: range.type,
        riskLevel: riskNum,
        centerX: pinX - distance,
        centerY: pinY + (angle * 2),
        radius: 30 + (100 - riskNum) / 3, // Larger radius for lower risk
        successRate: range.success_rate,
        color: getRiskZoneColor(riskNum)
      };
    });
  };

  const targetZones = generateTargetZones();

  // Generate optimal shot path
  const generateOptimalPath = () => {
    if (!analysis.recommended_shot) return null;
    
    const pathPoints = [
      { x: playerX, y: playerY },
      { x: playerX + 50, y: playerY - 10 }, // Slight arc
      { x: pinX - 40, y: pinY + 5 },
      { x: pinX, y: pinY }
    ];
    
    return pathPoints.map((point, index) => 
      `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
    ).join(' ');
  };

  const optimalPath = generateOptimalPath();

  // Distance markers
  const generateDistanceMarkers = () => {
    const markers = [];
    const distances = [100, 150, 200, 250];
    
    distances.forEach(distance => {
      if (distance < ballPosition.distance_to_pin) {
        const x = pinX - (distance / (holeState.hole_distance || 400)) * holeLength;
        markers.push({
          distance,
          x,
          y: holeWidth - 20
        });
      }
    });
    
    return markers;
  };

  const distanceMarkers = generateDistanceMarkers();

  return (
    <div style={{
      position: 'relative',
      width: '100%',
      height: '300px',
      background: '#90EE90', // Light green fairway
      borderRadius: theme.borderRadius.base,
      overflow: 'hidden',
      border: `2px solid ${theme.colors.border}`
    }}>
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${holeLength} ${holeWidth}`}
        style={{ position: 'absolute', top: 0, left: 0 }}
      >
        {/* Fairway base */}
        <rect
          x="0"
          y="0"
          width={holeLength}
          height={holeWidth}
          fill="#90EE90"
        />
        
        {/* Rough areas */}
        <rect
          x="0"
          y="0"
          width={holeLength}
          height="20"
          fill="#228B22"
        />
        <rect
          x="0"
          y={holeWidth - 20}
          width={holeLength}
          height="20"
          fill="#228B22"
        />

        {/* Target zones */}
        {showTargetZones && targetZones.map(zone => (
          <g key={zone.id}>
            <circle
              cx={zone.centerX}
              cy={zone.centerY}
              r={zone.radius}
              fill={zone.color}
              stroke={zone.riskLevel <= 30 ? theme.colors.success : 
                     zone.riskLevel <= 60 ? theme.colors.warning : theme.colors.error}
              strokeWidth="2"
              strokeDasharray="5,5"
            />
            <text
              x={zone.centerX}
              y={zone.centerY - zone.radius - 5}
              textAnchor="middle"
              fontSize="10"
              fill={theme.colors.textPrimary}
              fontWeight="bold"
            >
              {zone.type.replace('_', ' ').toUpperCase()}
            </text>
            <text
              x={zone.centerX}
              y={zone.centerY + 3}
              textAnchor="middle"
              fontSize="8"
              fill={theme.colors.textSecondary}
            >
              {zone.successRate} success
            </text>
          </g>
        ))}

        {/* Optimal shot path */}
        {showOptimalPath && optimalPath && (
          <path
            d={optimalPath}
            stroke={theme.colors.primary}
            strokeWidth="3"
            fill="none"
            strokeDasharray="8,4"
            markerEnd="url(#arrowhead)"
          />
        )}

        {/* Risk areas (hazards, rough) */}
        {showRiskAreas && (
          <>
            {/* Water hazard example */}
            <ellipse
              cx={holeLength * 0.7}
              cy={holeWidth * 0.3}
              rx="40"
              ry="20"
              fill="#4682B4"
              opacity="0.6"
            />
            <text
              x={holeLength * 0.7}
              y={holeWidth * 0.3 + 3}
              textAnchor="middle"
              fontSize="8"
              fill="white"
              fontWeight="bold"
            >
              WATER
            </text>
            
            {/* Bunker example */}
            <ellipse
              cx={holeLength * 0.8}
              cy={holeWidth * 0.7}
              rx="25"
              ry="15"
              fill="#F4A460"
              opacity="0.8"
            />
            <text
              x={holeLength * 0.8}
              y={holeWidth * 0.7 + 3}
              textAnchor="middle"
              fontSize="8"
              fill={theme.colors.textPrimary}
              fontWeight="bold"
            >
              SAND
            </text>
          </>
        )}

        {/* Distance markers */}
        {distanceMarkers.map(marker => (
          <g key={marker.distance}>
            <line
              x1={marker.x}
              y1="20"
              x2={marker.x}
              y2={holeWidth - 20}
              stroke={theme.colors.textSecondary}
              strokeWidth="1"
              strokeDasharray="3,3"
              opacity="0.6"
            />
            <text
              x={marker.x}
              y={marker.y}
              textAnchor="middle"
              fontSize="9"
              fill={theme.colors.textSecondary}
              fontWeight="bold"
            >
              {marker.distance}y
            </text>
          </g>
        ))}

        {/* Player position */}
        <circle
          cx={playerX}
          cy={playerY}
          r="8"
          fill={theme.colors.primary}
          stroke="white"
          strokeWidth="2"
        />
        <text
          x={playerX}
          y={playerY - 15}
          textAnchor="middle"
          fontSize="10"
          fill={theme.colors.primary}
          fontWeight="bold"
        >
          YOU
        </text>

        {/* Pin position */}
        <circle
          cx={pinX}
          cy={pinY}
          r="4"
          fill="red"
        />
        <line
          x1={pinX}
          y1={pinY - 15}
          x2={pinX}
          y2={pinY - 4}
          stroke="red"
          strokeWidth="2"
        />
        <text
          x={pinX + 10}
          y={pinY + 3}
          fontSize="10"
          fill="red"
          fontWeight="bold"
        >
          PIN
        </text>

        {/* Arrow marker definition */}
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="10"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill={theme.colors.primary}
            />
          </marker>
        </defs>
      </svg>

      {/* Legend */}
      <div style={{
        position: 'absolute',
        top: theme.spacing[2],
        left: theme.spacing[2],
        background: 'rgba(255, 255, 255, 0.9)',
        padding: theme.spacing[2],
        borderRadius: theme.borderRadius.base,
        fontSize: theme.typography.xs,
        minWidth: '120px'
      }}>
        <div style={{ fontWeight: theme.typography.bold, marginBottom: theme.spacing[1] }}>
          Legend
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: theme.spacing[1] }}>
          <div style={{
            width: '12px',
            height: '12px',
            background: `${theme.colors.success}40`,
            border: `1px solid ${theme.colors.success}`,
            borderRadius: '50%',
            marginRight: theme.spacing[1]
          }}></div>
          Low Risk
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: theme.spacing[1] }}>
          <div style={{
            width: '12px',
            height: '12px',
            background: `${theme.colors.warning}40`,
            border: `1px solid ${theme.colors.warning}`,
            borderRadius: '50%',
            marginRight: theme.spacing[1]
          }}></div>
          Medium Risk
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: theme.spacing[1] }}>
          <div style={{
            width: '12px',
            height: '12px',
            background: `${theme.colors.error}40`,
            border: `1px solid ${theme.colors.error}`,
            borderRadius: '50%',
            marginRight: theme.spacing[1]
          }}></div>
          High Risk
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{
            width: '12px',
            height: '2px',
            background: theme.colors.primary,
            marginRight: theme.spacing[1]
          }}></div>
          Optimal Path
        </div>
      </div>

      {/* Shot recommendation overlay */}
      {analysis.recommended_shot && (
        <div style={{
          position: 'absolute',
          top: theme.spacing[2],
          right: theme.spacing[2],
          background: 'rgba(255, 255, 255, 0.95)',
          padding: theme.spacing[3],
          borderRadius: theme.borderRadius.base,
          border: `2px solid ${theme.colors.primary}`,
          minWidth: '160px'
        }}>
          <div style={{ 
            fontWeight: theme.typography.bold, 
            color: theme.colors.primary,
            marginBottom: theme.spacing[1],
            fontSize: theme.typography.sm
          }}>
            🎯 Recommended
          </div>
          <div style={{ 
            fontSize: theme.typography.base,
            fontWeight: theme.typography.bold,
            marginBottom: theme.spacing[1]
          }}>
            {analysis.recommended_shot.type?.replace('_', ' ').toUpperCase()}
          </div>
          <div style={{ 
            fontSize: theme.typography.xs,
            color: theme.colors.textSecondary,
            marginBottom: theme.spacing[1]
          }}>
            Success: {analysis.recommended_shot.success_rate}
          </div>
          <div style={{ 
            fontSize: theme.typography.xs,
            color: getRiskZoneColor(analysis.recommended_shot.risk_level) === `${theme.colors.success}40` 
              ? theme.colors.success 
              : getRiskZoneColor(analysis.recommended_shot.risk_level) === `${theme.colors.warning}40`
              ? theme.colors.warning
              : theme.colors.error
          }}>
            Risk: {analysis.recommended_shot.risk_level}
          </div>
        </div>
      )}
    </div>
  );
};

export default ShotVisualizationOverlay;