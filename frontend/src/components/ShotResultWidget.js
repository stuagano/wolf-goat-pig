import React from 'react';

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
  muted: '#888',
};

const getShotQualityColor = (quality) => {
  switch (quality) {
    case 'excellent': return COLORS.success;
    case 'good': return '#4caf50';
    case 'average': return COLORS.warning;
    case 'poor': return '#ff5722';
    case 'terrible': return COLORS.error;
    default: return COLORS.muted;
  }
};

const getShotQualityIcon = (quality) => {
  switch (quality) {
    case 'excellent': return '🏆';
    case 'good': return '👍';
    case 'average': return '➖';
    case 'poor': return '👎';
    case 'terrible': return '💥';
    default: return '❓';
  }
};

const ShotResultWidget = ({ shotResult, playerName, isComputer = false, strokeAdvantage = null }) => {
  if (!shotResult) return null;

  const {
    shot_number,
    lie_type,
    distance_to_pin,
    shot_quality,
    made_shot,
    penalty_strokes
  } = shotResult;

  const qualityColor = getShotQualityColor(shot_quality);
  const qualityIcon = getShotQualityIcon(shot_quality);

  return (
    <div style={{
      background: COLORS.card,
      borderRadius: 16,
      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      padding: 20,
      margin: '12px 0',
      border: `2px solid ${qualityColor}`,
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 24 }}>{qualityIcon}</span>
          <h3 style={{ margin: 0, color: COLORS.text }}>
            {playerName} {isComputer ? '(Computer)' : ''}
          </h3>
        </div>
        <div style={{
          background: qualityColor,
          color: 'white',
          padding: '4px 12px',
          borderRadius: 20,
          fontSize: 14,
          fontWeight: 600,
          textTransform: 'uppercase'
        }}>
          {shot_quality}
        </div>
      </div>

      {/* Shot Details Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: 16,
        marginBottom: 16
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
            Shot #{shot_number}
          </div>
          <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.text }}>
            {shot_number}
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
            Lie Type
          </div>
          <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.text, textTransform: 'capitalize' }}>
            {lie_type}
          </div>
        </div>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
            Distance to Pin
          </div>
          <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.text }}>
            {Math.round(distance_to_pin)} yds
          </div>
        </div>

        {penalty_strokes > 0 && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: COLORS.error, marginBottom: 4 }}>
              Penalty Strokes
            </div>
            <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.error }}>
              +{penalty_strokes}
            </div>
          </div>
        )}

        {strokeAdvantage && strokeAdvantage.strokes_received > 0 && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 12, color: COLORS.accent, marginBottom: 4 }}>
              Handicap Strokes
            </div>
            <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.accent }}>
              {strokeAdvantage.strokes_received === 1 ? '●' : 
               strokeAdvantage.strokes_received === 0.5 ? '◐' : 
               `●x${strokeAdvantage.strokes_received}`} 
              +{strokeAdvantage.strokes_received}
            </div>
          </div>
        )}
      </div>

      {/* Made Shot Indicator */}
      {made_shot && (
        <div style={{
          background: COLORS.success,
          color: 'white',
          padding: '8px 16px',
          borderRadius: 8,
          textAlign: 'center',
          fontWeight: 600,
          fontSize: 14
        }}>
          🎯 Ball in the hole!
        </div>
      )}

      {/* Visual Quality Bar */}
      <div style={{ marginTop: 12 }}>
        <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
          Shot Quality
        </div>
        <div style={{
          height: 8,
          background: '#f0f0f0',
          borderRadius: 4,
          overflow: 'hidden'
        }}>
          <div style={{
            height: '100%',
            background: qualityColor,
            width: `${(shot_quality === 'excellent' ? 100 : 
                     shot_quality === 'good' ? 80 :
                     shot_quality === 'average' ? 60 :
                     shot_quality === 'poor' ? 40 : 20)}%`,
            transition: 'width 0.3s ease'
          }} />
        </div>
      </div>
    </div>
  );
};

export default ShotResultWidget; 