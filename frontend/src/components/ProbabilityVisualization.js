import React, { useMemo } from 'react';

const COLORS = {
  primary: '#1976d2',
  accent: '#00bcd4',
  warning: '#ff9800',
  error: '#d32f2f',
  success: '#388e3c',
  bg: '#f9fafe',
  card: '#fff',
  border: '#e0e0e0',
  text: '#222',
  muted: '#888'
};

const ProbabilityVisualization = ({ 
  data = [], 
  currentOdds = null, 
  width = 400, 
  height = 200,
  showTrends = true,
  showDistribution = true 
}) => {
  
  // Process data for visualization
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return null;
    
    // Calculate trends
    const trends = data.map((point, index) => ({
      index,
      timestamp: point.timestamp,
      confidence: point.confidence,
      calculation_time: point.calculation_time,
      team_probabilities: point.team_probabilities || {}
    }));
    
    // Calculate probability distributions if current odds available
    let distributions = null;
    if (currentOdds?.player_probabilities) {
      distributions = Object.entries(currentOdds.player_probabilities).map(([id, data]) => ({
        id,
        name: data.name || id,
        probability: data.win_probability || 0,
        expected_score: data.expected_score || 0,
        score_distribution: data.score_distribution || {}
      })).sort((a, b) => b.probability - a.probability);
    }
    
    return { trends, distributions };
  }, [data, currentOdds]);

  if (!processedData) {
    return (
      <div style={{
        width,
        height,
        background: '#f8f9fa',
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: COLORS.muted,
        fontSize: 14
      }}>
        No data available for visualization
      </div>
    );
  }

  return (
    <div style={{
      background: COLORS.card,
      borderRadius: 12,
      padding: 16,
      border: `1px solid ${COLORS.border}`
    }}>
      {/* Probability bars */}
      {showDistribution && processedData.distributions && (
        <div style={{ marginBottom: showTrends ? 24 : 0 }}>
          <h4 style={{ margin: '0 0 16px 0', fontSize: 14, color: COLORS.text }}>
            Current Win Probabilities
          </h4>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {processedData.distributions.map((player, index) => (
              <div key={player.id} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                {/* Player name */}
                <div style={{
                  minWidth: 80,
                  fontSize: 12,
                  color: COLORS.text,
                  fontWeight: 500
                }}>
                  {player.name}
                </div>
                
                {/* Probability bar */}
                <div style={{
                  flex: 1,
                  height: 20,
                  background: COLORS.border,
                  borderRadius: 10,
                  overflow: 'hidden',
                  position: 'relative'
                }}>
                  <div style={{
                    width: `${player.probability * 100}%`,
                    height: '100%',
                    background: `linear-gradient(90deg, ${COLORS.primary}, ${COLORS.accent})`,
                    borderRadius: 10,
                    transition: 'width 0.3s ease'
                  }} />
                  
                  {/* Percentage label */}
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 11,
                    fontWeight: 600,
                    color: player.probability > 0.5 ? 'white' : COLORS.text
                  }}>
                    {(player.probability * 100).toFixed(1)}%
                  </div>
                </div>
                
                {/* Expected score */}
                <div style={{
                  minWidth: 40,
                  fontSize: 11,
                  color: COLORS.muted,
                  textAlign: 'right'
                }}>
                  {player.expected_score.toFixed(1)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trend chart */}
      {showTrends && processedData.trends.length > 1 && (
        <div>
          <h4 style={{ margin: '0 0 16px 0', fontSize: 14, color: COLORS.text }}>
            Calculation Trends
          </h4>
          
          <TrendChart 
            data={processedData.trends}
            width={width - 32}
            height={height}
          />
        </div>
      )}

      {/* Score distribution chart */}
      {showDistribution && processedData.distributions && (
        <div style={{ marginTop: 20 }}>
          <h4 style={{ margin: '0 0 16px 0', fontSize: 14, color: COLORS.text }}>
            Score Distribution (Leader)
          </h4>
          
          <ScoreDistributionChart 
            distribution={processedData.distributions[0]?.score_distribution || {}}
            playerName={processedData.distributions[0]?.name || 'Player'}
            width={width - 32}
            height={100}
          />
        </div>
      )}
    </div>
  );
};

// Simple trend chart component
const TrendChart = ({ data, width, height }) => {
  const svgWidth = width;
  const svgHeight = height;
  const margin = { top: 20, right: 20, bottom: 30, left: 40 };
  const chartWidth = svgWidth - margin.left - margin.right;
  const chartHeight = svgHeight - margin.top - margin.bottom;

  // Calculate scales - prevent division by zero
  const xDivisor = Math.max(data.length - 1, 1);
  const xScale = (index) => (index / xDivisor) * chartWidth;
  const yScale = (value) => chartHeight - (value * chartHeight);

  // Generate confidence line
  const confidenceLine = data.map((point, index) => ({
    x: margin.left + xScale(index),
    y: margin.top + yScale(point.confidence || 0)
  }));

  // Generate calculation time line (normalized) - prevent division by zero
  const calcTimes = data.map(d => d.calculation_time || 0);
  const maxCalcTime = calcTimes.length > 0 ? Math.max(...calcTimes) : 1;
  const safeMaxCalcTime = maxCalcTime || 1; // Prevent division by zero
  const calcTimeLine = data.map((point, index) => ({
    x: margin.left + xScale(index),
    y: margin.top + yScale((point.calculation_time || 0) / safeMaxCalcTime)
  }));

  const createPath = (points) => {
    if (points.length === 0) return '';
    
    let path = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      path += ` L ${points[i].x} ${points[i].y}`;
    }
    return path;
  };

  return (
    <div style={{ position: 'relative' }}>
      <svg width={svgWidth} height={svgHeight} style={{ background: '#f8f9fa', borderRadius: 8 }}>
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map(value => (
          <line
            key={value}
            x1={margin.left}
            y1={margin.top + yScale(value)}
            x2={margin.left + chartWidth}
            y2={margin.top + yScale(value)}
            stroke="#e0e0e0"
            strokeWidth="1"
          />
        ))}
        
        {/* Confidence line */}
        <path
          d={createPath(confidenceLine)}
          stroke={COLORS.primary}
          strokeWidth="2"
          fill="none"
        />
        
        {/* Calculation time line */}
        <path
          d={createPath(calcTimeLine)}
          stroke={COLORS.warning}
          strokeWidth="2"
          fill="none"
          strokeDasharray="4,4"
        />
        
        {/* Data points */}
        {confidenceLine.map((point, index) => (
          <circle
            key={`confidence-${index}`}
            cx={point.x}
            cy={point.y}
            r="3"
            fill={COLORS.primary}
          />
        ))}
        
        {/* Y-axis labels */}
        {[0, 0.5, 1].map(value => (
          <text
            key={value}
            x={margin.left - 8}
            y={margin.top + yScale(value) + 4}
            textAnchor="end"
            fontSize="10"
            fill={COLORS.muted}
          >
            {(value * 100).toFixed(0)}%
          </text>
        ))}
      </svg>
      
      {/* Legend */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: 20,
        marginTop: 8,
        fontSize: 11
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{
            width: 12,
            height: 2,
            background: COLORS.primary
          }} />
          <span style={{ color: COLORS.muted }}>Confidence</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{
            width: 12,
            height: 2,
            background: COLORS.warning,
            borderStyle: 'dashed',
            borderWidth: '1px 0'
          }} />
          <span style={{ color: COLORS.muted }}>Calc Time (normalized)</span>
        </div>
      </div>
    </div>
  );
};

// Score distribution chart
const ScoreDistributionChart = ({ distribution, playerName, width, height }) => {
  const scores = Object.keys(distribution || {}).map(Number).sort((a, b) => a - b);
  const probValues = Object.values(distribution || {});
  const maxProb = probValues.length > 0 ? Math.max(...probValues) : 1;
  
  const svgWidth = width;
  const svgHeight = height;
  const margin = { top: 10, right: 20, bottom: 20, left: 30 };
  const chartWidth = svgWidth - margin.left - margin.right;
  const chartHeight = svgHeight - margin.top - margin.bottom;

  if (scores.length === 0) {
    return (
      <div style={{
        width: svgWidth,
        height: svgHeight,
        background: '#f8f9fa',
        borderRadius: 8,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 12,
        color: COLORS.muted
      }}>
        No score distribution data
      </div>
    );
  }

  const barWidth = chartWidth / scores.length * 0.8;
  const barSpacing = chartWidth / scores.length * 0.2;

  return (
    <svg width={svgWidth} height={svgHeight} style={{ background: '#f8f9fa', borderRadius: 8 }}>
      {/* Bars */}
      {scores.map((score, index) => {
        const probability = distribution[score];
        const barHeight = (probability / maxProb) * chartHeight;
        const x = margin.left + index * (barWidth + barSpacing);
        const y = margin.top + chartHeight - barHeight;
        
        return (
          <g key={score}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              fill={COLORS.accent}
              rx="2"
            />
            
            {/* Score label */}
            <text
              x={x + barWidth / 2}
              y={margin.top + chartHeight + 12}
              textAnchor="middle"
              fontSize="9"
              fill={COLORS.muted}
            >
              {score}
            </text>
            
            {/* Probability label */}
            {probability > maxProb * 0.1 && (
              <text
                x={x + barWidth / 2}
                y={y - 2}
                textAnchor="middle"
                fontSize="8"
                fill={COLORS.text}
              >
                {(probability * 100).toFixed(0)}%
              </text>
            )}
          </g>
        );
      })}
      
      {/* X-axis label */}
      <text
        x={margin.left + chartWidth / 2}
        y={svgHeight - 2}
        textAnchor="middle"
        fontSize="10"
        fill={COLORS.muted}
      >
        Score
      </text>
    </svg>
  );
};

export default ProbabilityVisualization;