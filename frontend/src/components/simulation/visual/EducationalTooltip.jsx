// frontend/src/components/simulation/visual/EducationalTooltip.jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';

/**
 * Educational tooltip component
 * Shows contextual help and explanations for game concepts
 * Uses vanilla React (no Material-UI dependency)
 */
const EducationalTooltip = ({ title, content, type = 'info' }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseEnter = (e) => {
    setMousePosition({ x: e.clientX, y: e.clientY });
    setIsVisible(true);
  };

  const handleMouseMove = (e) => {
    setMousePosition({ x: e.clientX, y: e.clientY });
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  const getTypeIcon = () => {
    switch (type) {
      case 'tip': return '💡';
      case 'warning': return '⚠️';
      case 'concept': return '🎓';
      default: return 'ℹ️';
    }
  };

  const getTypeColor = () => {
    switch (type) {
      case 'tip': return '#ff9800';
      case 'warning': return '#d32f2f';
      case 'concept': return '#388e3c';
      default: return '#1976d2';
    }
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onMouseEnter={handleMouseEnter}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        aria-label={title}
        role="button"
        style={{
          background: 'transparent',
          border: 'none',
          cursor: 'help',
          padding: '4px',
          color: getTypeColor(),
          fontSize: '16px',
          lineHeight: 1,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {getTypeIcon()}
      </button>

      {isVisible && (
        <div
          style={{
            position: 'fixed',
            left: Math.min(mousePosition.x + 10, window.innerWidth - 320),
            top: Math.max(10, Math.min(mousePosition.y - 10, window.innerHeight - 150)),
            maxWidth: 300,
            background: '#2c2c2c',
            color: 'white',
            padding: 12,
            borderRadius: 8,
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            zIndex: 10000,
            fontSize: 14,
            lineHeight: 1.4,
            pointerEvents: 'none',
            wordBreak: 'break-word',
            overflowWrap: 'break-word'
          }}
        >
          {title && (
            <div style={{
              fontWeight: 600,
              marginBottom: 8,
              color: getTypeColor(),
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}>
              <span>{getTypeIcon()}</span>
              {title}
            </div>
          )}
          <div>{content}</div>
        </div>
      )}
    </div>
  );
};

EducationalTooltip.propTypes = {
  title: PropTypes.string.isRequired,
  content: PropTypes.string.isRequired,
  type: PropTypes.oneOf(['info', 'tip', 'warning', 'concept'])
};

export default EducationalTooltip;
